import os
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

_SYSTEM_PROMPT = (
    "당신은 교통사고 과실비율 및 도로교통법 전문 AI 어시스턴트입니다.\n"
    "아래 참고 문서(텍스트 및 표)를 바탕으로 과실비율 및 법률 조항에 대한 의견을 제공합니다.\n"
    "\n"
    "[답변 규칙]\n"
    "1. 반드시 아래 컨텍스트 문서만을 근거로 답하세요.\n"
    "2. 컨텍스트에 근거가 없으면 '제공된 문서에서 해당 사고 유형을 찾을 수 없습니다'라고 답하세요.\n"
    "3. 답변 말미에 반드시 출처(source, page)를 표기하세요.\n"
    "4. 컨텍스트에 [참조 이미지]가 있는 경우 파일명을 답변 말미에 나열하세요.\n"
    "\n"
    "[검색 문서와 질문의 동치 판단 기준]\n"
    "검색된 문서(사고유형 항목)가 질문에 답할 수 있는지 판단할 때,\n"
    "단어가 정확히 일치하는지가 아니라 다음 핵심 요소들이 의미적으로 일치하는지를 기준으로 판단하라.\n"
    "\n"
    "비교해야 할 핵심 요소:\n"
    "  (a) 각 차량의 출발 위치 관계 (동일 도로/교차 도로, 좌측/우측)\n"
    "  (b) 각 차량의 진행 동작 (직진/좌회전/우회전/차로변경 등)\n"
    "  (c) 교차로의 신호 유무 및 도로폭 동일 여부\n"
    "  (d) 사고가 발생하는 구조적 원인 (예: 회전반경 차이, 진입 순서, 우선권 등)\n"
    "\n"
    "질문에 사용된 표현이 문서의 표현과 다르더라도, 위 핵심 요소 (a)~(d)가 모두 부합하면\n"
    "동일한 사고유형으로 간주하고 해당 항목을 근거로 답변하라.\n"
    "예) 질문의 '동일방향으로 진행하다 회전반경 차이로 충돌'과\n"
    "    문서의 '크게 또는 작게 좌회전하다 충돌'은 같은 사고 구조를 가리키는 의미적 동의 표현이다.\n"
    "표현의 차이(어순, 동의어, 풀어쓴 문장 등)를 근거 부족의 이유로 삼지 말라.\n"
    "\n"
    "'찾을 수 없다'고 답하기 전에 반드시 다음을 자문하라:\n"
    "  → 검색된 문서 중 핵심 요소 (a)~(d)가 질문과 모두 일치하는 항목이 있는가?\n"
    "  → 있다면 그 항목 번호를 명시하고 답변하라.\n"
    "  → 일치하지 않는 요소가 있다면, 어떤 요소가 다른지 구체적으로 지적한 뒤 '찾을 수 없다'고 답하라.\n"
    "  → 단순히 '표현이 다르다'는 이유만으로 일치하지 않는다고 판단해서는 안 된다.\n"
    "\n"
    "판단이 애매한 경우, 답변을 회피하는 대신 다음 형식으로 조건부 답변하라:\n"
    "  '질문의 표현은 문서의 [항목번호] 표현과 다르지만, [핵심요소]가 동일하여\n"
    "   같은 사고유형으로 판단됩니다. 다만 표현 차이가 있으니 원문을 확인해 주세요.'\n"
    "\n"
    "※ 중요: 컨텍스트에 여러 문서가 있을 경우, 첫 번째 문서가 일치하지 않더라도\n"
    "   반드시 나머지 문서 전체를 검토한 뒤 판단하라.\n"
    "   '찾을 수 없다'는 결론은 모든 문서를 검토한 이후에만 내려야 한다.\n"
    "\n"
    "[동치 판단 예시 — few-shot]\n"
    "예시 1)\n"
    "  질문: '교차로에서 동일 방향으로 진행 중, A(왼쪽)와 B(오른쪽)가 각각 좌회전하다 충돌 —\n"
    "         A는 크게, B는 작게 좌회전하여 회전반경 차이로 사고 발생'\n"
    "  핵심요소 대조:\n"
    "    (a) 동일 도로, A는 왼쪽 차로 / B는 오른쪽 차로 → 문서 '오른쪽 도로 좌회전 대 왼쪽 도로 좌회전'과 일치\n"
    "    (b) A·B 모두 좌회전 → 일치\n"
    "    (c) 무신호 교차로, 동일폭 도로 → 일치\n"
    "    (d) 회전반경 차이(대회전/소회전) → 문서의 '크게 또는 작게 좌회전' 구조와 동일\n"
    "  판정: 차17-1 '오른쪽 도로 좌회전 대 왼쪽 도로 좌회전 사고'와 동일 유형 → 차17-1 기준으로 답변\n"
    "\n"
    "예시 2)\n"
    "  질문: '같은 방향 두 차량이 교차로 좌회전 중 안쪽 차량과 바깥쪽 차량이 부딪힌 사고'\n"
    "  핵심요소 대조:\n"
    "    (a) 동일 도로 진행, 좌우 차로 관계 → 일치\n"
    "    (b) 둘 다 좌회전 중 → 일치\n"
    "    (c) 조건 명시 없음이나 구조상 무신호 동일폭과 부합\n"
    "    (d) 안쪽/바깥쪽 = 소회전/대회전 구조 → 일치\n"
    "  판정: 차17-1과 동일 유형 → 차17-1 기준으로 답변\n"
    "\n"
    "[컨텍스트 유형별 활용 방법]\n"
    "- [텍스트]: 사고 상황 설명, 법적 근거, 판례를 인용할 때 활용하세요.\n"
    "- [표]: 기본 과실비율 수치와 수정요소(+/- 값)를 반드시 정확히 계산하여 적용하세요.\n"
    "- [조항]: 법률 조항 번호(article_id)와 section(본문/부칙)을 명시하여 인용하세요.\n"
    "\n"
    "[과실비율 최종 계산 공식]\n"
    "사고발생·손해 확대와의 인과관계를 감안하여 기본 과실비율을 가(+)·감(-) 조정합니다.\n"
    "수정요소는 영합(zero-sum) 방식으로 적용됩니다: A가 −N 조정을 받으면 B는 자동으로 +N이 됩니다.\n"
    "\n"
    "  ① A 수정합계 = Σ(각 수정요소의 A 측 가감값)\n"
    "  ② A 최종(%) = A 기본값 + A 수정합계\n"
    "     B 최종(%) = 100 − A 최종(%)   ← B는 항상 A의 보수\n"
    "  ③ 과실비율은 0∼100 범위를 벗어나지 않도록 조정하세요.\n"
    "\n"
    "답변에 기본값·수정요소별 가감값·수정합계·최종값을 모두 명시하세요.\n"
    "\n"
    "[답변 형식]\n"
    "1. 사고 유형 : 해당 차|회전 N-N 유형 또는 법률 조항 명시\n"
    "2. 기본 과실비율 : A N% : B N%\n"
    "3. 수정요소 적용 : 항목·가감값 나열 → A 수정합계 계산 → A·B 최종 과실비율 산출\n"
    "4. 근거 : 관련 법조문 또는 판례\n"
    "5. 출처 : source / page / 사례번호\n"
    "6. 참조 이미지 : (해당 페이지 이미지 파일명, 없으면 생략)\n"
    "\n"
    "한국어로, 전문적이되 이해하기 쉽게 답변하세요."
)


# Document 리스트를 출처·doc_type 레이블 포함 텍스트 블록으로 변환
def _format_docs_to_context(docs: list) -> str:
    blocks = []
    for d in docs:
        dtype      = d.metadata.get("doc_type", "text")
        source     = d.metadata.get("source", "?")
        page       = d.metadata.get("page", "?")
        case_id    = d.metadata.get("case_id", "")
        image_refs = d.metadata.get("image_refs", "")

        case_str = f" │ 사례: {case_id}" if case_id else ""
        label = (f"[출처: {source} p.{page}{case_str}] [표]"
                 if dtype == "table"
                 else f"[출처: {source} p.{page}{case_str}] [텍스트]")

        content = d.page_content
        if image_refs:
            content += f"\n[참조 이미지] {image_refs}"

        blocks.append(f"{label}\n{content}")

    return "\n\n".join(blocks)


# 참조 Document 메타데이터를 유사도 점수 포함하여 포맷팅
def _build_meta_lines(docs_with_scores: list) -> str:
    lines = "\n" + "─" * 50 + "\n[참조 문서 메타데이터 — 유사도 높은 순]\n"
    for i, item in enumerate(docs_with_scores, 1):
        if isinstance(item, tuple) and len(item) == 2:
            doc, score = item
        else:
            doc, score = item, None

        dtype      = doc.metadata.get("doc_type", "?")
        page       = doc.metadata.get("page", "?")
        source     = doc.metadata.get("source", "?")
        case_id    = doc.metadata.get("case_id", "")
        image_refs = doc.metadata.get("image_refs", "")
        score_str  = f"{score:.4f}" if score is not None else "N/A"

        case_str = f"  │  사례번호: {case_id}" if case_id else ""
        lines += (f"  [{i}] source: {source}  │  page: {page}{case_str}  │  "
                  f"유사도: {score_str}  │  doc_type: {dtype:<6}")

        if dtype == "table":
            lines += (f"\n       표 인덱스: {doc.metadata.get('table_index','')} / "
                      f"행: {doc.metadata.get('row_count','?')} × "
                      f"열: {doc.metadata.get('col_count','?')}")

        article_id = doc.metadata.get("article_id", "")
        section    = doc.metadata.get("section", "")
        if article_id:
            lines += f"\n       조항: {article_id}"
        if section:
            lines += f"  │  section: {section}"

        if image_refs:
            lines += f"\n       참조 이미지: {image_refs}"
        lines += "\n"
    return lines


# rerank된 final에 누락된 TABLE을 case_id 보유 문서의 인접 페이지(±1)에서 사후 fetch
def _fetch_missing_tables(vectorstore, final: list) -> list:
    existing_keys = {
        (d.metadata.get("source"), d.metadata.get("page"), d.metadata.get("doc_type"))
        for d, _ in final
    }
    table_case_ids = {
        d.metadata.get("case_id", "")
        for d, _ in final
        if d.metadata.get("doc_type") == "table" and d.metadata.get("case_id")
    }

    extra        = []
    checked      = set()

    for doc, _ in final:
        cid   = doc.metadata.get("case_id", "")
        dtype = doc.metadata.get("doc_type", "")
        page  = doc.metadata.get("page")
        src   = doc.metadata.get("source", "")

        if dtype == "table" or not cid or cid in table_case_ids:
            continue

        for p in [page - 1, page, page + 1]:
            if (src, p) in checked:
                continue
            checked.add((src, p))
            try:
                result = vectorstore._collection.get(
                    where={"$and": [
                        {"source":   {"$eq": src}},
                        {"page":     {"$eq": p}},
                        {"doc_type": {"$eq": "table"}},
                    ]},
                    include=["documents", "metadatas"],
                )
                for text, meta in zip(
                    result.get("documents", []), result.get("metadatas", [])
                ):
                    key = (meta.get("source"), meta.get("page"), "table")
                    if key not in existing_keys:
                        existing_keys.add(key)
                        extra.append((Document(page_content=text, metadata=meta), None))
            except Exception:
                pass

    return extra


# case_title 기반 Jaccard 유사도 재순위화 (Chroma L2 점수 낮을수록 유사 → boost 차감)
def _rerank_by_case_title(
    results: List[Tuple],
    query: str,
    boost: float = 0.3,
) -> List[Tuple]:
    query_clean  = query.strip()
    query_tokens = set(query_clean.split())

    scored = []
    for doc, score in results:
        case_title = doc.metadata.get("case_title", "")
        if not case_title or not query_tokens:
            scored.append((doc, score))
            continue

        if case_title == query_clean:
            title_sim = 1.0
        else:
            title_tokens = set(case_title.split())
            union        = query_tokens | title_tokens
            title_sim    = len(query_tokens & title_tokens) / len(union) if union else 0.0

        scored.append((doc, score - boost * title_sim))

    scored.sort(key=lambda x: x[1])
    return scored


class RagChainMixin:

    # GOOGLE_API_KEY로 Gemini LLM 초기화
    def get_llm(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY_VISION")
        if not api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY 환경 변수를 설정해주세요. "
                "(또는 GOOGLE_API_KEY_VISION도 허용됩니다)"
            )

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=api_key,
            temperature=self.temperature,
        )

    # LCEL 기반 RAG 체인 — 2배 후보 검색 → rerank → 답변 생성
    def basic_rag_chain(self, retriever, llm, human_message: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
        ])

        _retrieved_with_scores: list = []

        def retrieve_and_format(query: str) -> str:
            try:
                # 후보군 2배 확보 후 rerank (case_title 방향 혼동 방지)
                candidates = retriever.vectorstore.similarity_search_with_score(
                    query, k=self.search_k * 2
                )
                candidates.sort(key=lambda x: x[1])
            except AttributeError:
                candidates = [(d, None) for d in retriever.invoke(query)]

            # [디버그] 원본 검색 결과
            # print(f"\n[Retrieval] 검색 결과 Top{len(candidates)}")
            # for rank, (doc, score) in enumerate(candidates, 1):
            #     cid     = doc.metadata.get("case_id", "-")
            #     ctitle  = doc.metadata.get("case_title", "-")
            #     dtype   = doc.metadata.get("doc_type", "-")
            #     score_s = f"{score:.4f}" if score is not None else "N/A"
            #     print(f"  {rank}. [{dtype}] {cid} │ {ctitle} │ score={score_s}")

            # case_title 기반 rerank → 상위 search_k 선택
            scored   = [(d, s) for d, s in candidates if s is not None]
            unscored = [(d, s) for d, s in candidates if s is None]
            reranked = _rerank_by_case_title(scored, query)
            final    = (reranked + unscored)[: self.search_k]

            # [디버그] rerank 결과
            # print(f"\n[Rerank] 재순위화 후 Top{len(final)}")
            # for rank, (doc, score) in enumerate(final, 1):
            #     cid     = doc.metadata.get("case_id", "-")
            #     ctitle  = doc.metadata.get("case_title", "-")
            #     score_s = f"{score:.4f}" if score is not None else "N/A"
            #     print(f"  {rank}. {cid} │ {ctitle} │ adj_score={score_s}")

            # 사후 fetch: final에 case_id는 있으나 TABLE이 없는 사례의 표를 인접 페이지에서 추가
            try:
                extra_tables = _fetch_missing_tables(retriever.vectorstore, final)
                final = final + extra_tables
            except Exception:
                pass

            _retrieved_with_scores.clear()
            _retrieved_with_scores.extend(final)
            return _format_docs_to_context([doc for doc, _ in final])

        rag_chain = (
            {"context": RunnableLambda(retrieve_and_format),
             "question": RunnablePassthrough()}
            | prompt | llm | StrOutputParser()
        )

        answer = rag_chain.invoke(human_message)
        return answer + _build_meta_lines(_retrieved_with_scores)

    # RunnableLambda 기반 RAG — 전처리·LLM·후처리 파이프라인
    def runnable_lambda(self, retriever, llm, human_message: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
        ])

        def preprocess(query: str) -> dict:
            cleaned = query.strip().rstrip("?!.")
            try:
                results = retriever.vectorstore.similarity_search_with_score(
                    cleaned, k=self.search_k
                )
                results.sort(key=lambda x: x[1])
            except AttributeError:
                results = [(d, None) for d in retriever.invoke(cleaned)]

            return {
                "context":        _format_docs_to_context([doc for doc, _ in results]),
                "question":       cleaned,
                "retrieved_docs": results,
            }

        def postprocess(inputs: dict) -> str:
            answer       = inputs.get("answer", "")
            docs_scores  = inputs.get("retrieved_docs", [])
            result = f"[교통사고 과실비율 기반 답변]\n{answer.strip()}\n"
            result += _build_meta_lines(docs_scores)
            return result

        def merge_llm_output(inputs: dict) -> dict:
            return {"answer": inputs["answer"], "retrieved_docs": inputs["retrieved_docs"]}

        chain = (
            RunnableLambda(preprocess)
            | RunnablePassthrough.assign(
                answer=(
                    (lambda x: {"context": x["context"], "question": x["question"]})
                    | prompt | llm | StrOutputParser()
                )
            )
            | RunnableLambda(merge_llm_output)
            | RunnableLambda(postprocess)
        )

        return chain.invoke(human_message)
