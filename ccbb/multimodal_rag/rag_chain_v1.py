"""
rag_chain_v1.py — LLM·프롬프트·RAG 체인 Mixin
Gemini LLM 초기화, basic_rag_chain(LCEL), runnable_lambda(전처리/후처리) 메서드 모음입니다.
RagBgeM3 클래스에 mixin으로 조합됩니다.

[프롬프트 공통 규칙]
- 컨텍스트 문서만 근거로 답변
- 수정요소 적용 후 비례 조정 공식으로 최종 과실비율 산출 (소수점 첫째 자리 반올림)
  A 최종(%) = A 수정값 / (A 수정값 + B 수정값) × 100
  B 최종(%) = B 수정값 / (A 수정값 + B 수정값) × 100
"""

import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

_SYSTEM_PROMPT = (
    "당신은 교통사고 과실비율 전문 AI 어시스턴트입니다.\n"
    "블랙박스 영상 분석 결과와 아래 참고 문서를 바탕으로 과실비율에 대한 의견을 제공합니다.\n"
    "\n"
    "[답변 규칙]\n"
    "1. 반드시 아래 컨텍스트 문서만을 근거로 답하세요.\n"
    "2. 컨텍스트에 근거가 없으면 '제공된 문서에서 해당 사고 유형을 찾을 수 없습니다'라고 답하세요.\n"
    "3. 답변 말미에 반드시 출처(source, page)를 표기하세요.\n"
    "\n"
    "[컨텍스트 유형별 활용 방법]\n"
    "- [텍스트]: 사고 상황 설명, 법적 근거, 판례를 인용할 때 활용하세요.\n"
    "- [표]: 기본 과실비율 수치와 수정요소(+/- 값)를 반드시 정확히 계산하여 적용하세요.\n"
    "- [이미지]: 교차로 구조, 차량 진입 방향, 충돌 위치 등 공간적 배치 정보를 설명할 때 활용하세요.\n"
    "\n"
    "[과실비율 최종 계산 공식]\n"
    "수정요소 적용 후 반드시 아래 비례 조정 공식으로 최종 과실비율을 산출하세요.\n"
    "  A 최종(%) = A 수정값 / (A 수정값 + B 수정값) × 100\n"
    "  B 최종(%) = B 수정값 / (A 수정값 + B 수정값) × 100\n"
    "  소수점 첫째 자리에서 반올림하여 정수로 표기하세요.\n"
    "답변에 수정값과 최종값을 모두 명시하세요.\n"
    "\n"
    "[답변 형식]\n"
    "1. 사고 유형 : 해당 차N-N 유형 명시\n"
    "2. 기본 과실비율 : A N% : B N%\n"
    "3. 수정요소 적용 : 항목·수치 나열 → 비례 조정 공식 적용 → 최종 과실비율 산출\n"
    "4. 근거 : 관련 법조문 또는 판례\n"
    "5. 출처 : source / page\n"
    "\n"
    "한국어로, 전문적이되 이해하기 쉽게 답변하세요."
)


def _format_docs_to_context(docs: list) -> str:
    """Document 리스트를 출처·doc_type 레이블 포함 텍스트 블록으로 변환합니다."""
    blocks = []
    for d in docs:
        dtype  = d.metadata.get("doc_type", "text")
        source = d.metadata.get("source", "?")
        page   = d.metadata.get("page", "?")

        if dtype == "table":
            label = f"[출처: {source} p.{page}] [표]"
            blocks.append(f"{label}\n{d.page_content}")
        elif dtype == "image":
            label = f"[출처: {source} p.{page}] [이미지]"
            content = d.page_content
            page_context = d.metadata.get("page_context", "")
            if page_context:
                content += f"\n[동일 페이지 텍스트 참고]\n{page_context}"
            blocks.append(f"{label}\n{content}")
        else:
            label = f"[출처: {source} p.{page}] [텍스트]"
            blocks.append(f"{label}\n{d.page_content}")

    return "\n\n".join(blocks)


def _build_meta_lines(docs: list) -> str:
    """참조 Document 메타데이터를 포맷팅해 반환합니다."""
    lines = "\n" + "─" * 50 + "\n[참조 문서 메타데이터]\n"
    for i, doc in enumerate(docs, 1):
        dtype  = doc.metadata.get("doc_type", "?")
        page   = doc.metadata.get("page", "?")
        source = doc.metadata.get("source", "?")
        lines += f"  [{i}] doc_type: {dtype:<6}  │  source: {source}  │  page: {page}"

        if dtype == "table":
            lines += (f"\n       표 인덱스: {doc.metadata.get('table_index','')} / "
                      f"행: {doc.metadata.get('row_count','?')} × "
                      f"열: {doc.metadata.get('col_count','?')}")
        elif dtype == "image":
            extra = f"\n       이미지 파일: {doc.metadata.get('images','')}"
            p_ctx = doc.metadata.get("page_context", "")
            if p_ctx:
                extra += f" / 페이지 텍스트 앞 50자: {p_ctx[:50]}..."
            lines += extra
        lines += "\n"
    return lines


class RagChainMixin:
    """LLM·RAG 체인 관련 메서드 Mixin"""

    def get_llm(self):
        """Gemini LLM을 초기화합니다. GOOGLE_API_KEY_VISION 환경변수 필요."""
        api_key = os.getenv("GOOGLE_API_KEY_VISION")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY_VISION 환경 변수를 설정해주세요.")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=api_key,
            temperature=self.temperature,
        )

    def basic_rag_chain(self, retriever, llm, human_message: str) -> str:
        """
        LCEL 기본 RAG 체인을 실행합니다.

        retriever → format_docs → prompt → llm → StrOutputParser 파이프라인.
        답변 말미에 참조 Document 메타데이터를 첨부합니다.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
        ])

        _retrieved: list = []

        def format_docs(docs: list) -> str:
            _retrieved.clear()
            _retrieved.extend(docs)
            return _format_docs_to_context(docs)

        rag_chain = (
            {"context": retriever | RunnableLambda(format_docs),
             "question": RunnablePassthrough()}
            | prompt | llm | StrOutputParser()
        )

        answer = rag_chain.invoke(human_message)
        return answer + _build_meta_lines(_retrieved)

    def runnable_lambda(self, retriever, llm, human_message: str) -> str:
        """
        RunnableLambda 방식으로 전처리/후처리를 포함한 RAG를 실행합니다.

        preprocess → LLM → postprocess 파이프라인.
        전처리에서 질문을 정제하고 컨텍스트를 구성합니다.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
        ])

        def preprocess(query: str) -> dict:
            cleaned = query.strip().rstrip("?!.")
            docs    = retriever.invoke(cleaned)
            return {
                "context":       _format_docs_to_context(docs),
                "question":      cleaned,
                "retrieved_docs": docs,
            }

        def postprocess(inputs: dict) -> str:
            answer = inputs.get("answer", "")
            docs   = inputs.get("retrieved_docs", [])
            result = f"[교통사고 과실비율 기반 답변]\n{answer.strip()}\n"
            result += _build_meta_lines(docs)
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
