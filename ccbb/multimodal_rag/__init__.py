"""
multimodal_rag — BGE-M3 + Chroma + Gemini Multimodal RAG 패키지

빠른 시작
---------
from multimodal_rag import RagBgeM3

rag       = RagBgeM3()
llm       = rag.get_llm()
retriever = rag.build_rag_components()
answer    = rag.basic_rag_chain(retriever, llm, "차16-3 과실비율은?")

모듈 구조
---------
config_v1      경로·이미지·청킹 전역 상수
pdf_loader_v1  PDF 텍스트/이미지/표 추출, 사례별 청킹 (PdfLoaderMixin)
vectorstore_v1 BGE-M3 임베딩, Chroma VectorStore, 검색 (VectorstoreMixin)
rag_chain_v1   Gemini LLM, basic_rag_chain, runnable_lambda (RagChainMixin)
rag_core_v1    RagBgeM3 메인 클래스 (위 Mixin 조합)
rag_runner_v1  CLI 실행 스크립트
"""

from .rag_core_v1 import RagBgeM3
from .config_v1 import (
    PDF_PATH, DB_PATH, COLLECTION_NAME,
    CASE_PATTERN, MAX_CASE_CHARS,
)

__all__ = [
    "RagBgeM3",
    "PDF_PATH",
    "DB_PATH",
    "COLLECTION_NAME",
    "CASE_PATTERN",
    "MAX_CASE_CHARS",
]
