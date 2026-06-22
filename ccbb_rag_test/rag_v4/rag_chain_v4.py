import os
from typing import List, Tuple

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
