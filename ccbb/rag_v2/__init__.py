"""
rag_v2 — BGE-M3 + Chroma + Gemini 텍스트·표 RAG 패키지

multimodal_rag(v1)에서 이미지 VL 해석을 제거하고
image_refs 메타데이터를 통한 출처 매핑 방식으로 변경한 버전입니다.

빠른 시작
---------
from rag_v2 import RagBgeM3v2

rag       = RagBgeM3v2()
llm       = rag.get_llm()
retriever = rag.build_rag_components()
answer    = rag.basic_rag_chain(retriever, llm, "차16-3 과실비율은?")

모듈 구조
---------
config_v2      경로·청킹 전역 상수 (VL 관련 상수 제거)
pdf_loader_v2  PDF 텍스트/표 추출, 사례별 청킹, 이미지 저장 + image_refs 매핑 (PdfLoaderMixin)
vectorstore_v2 BGE-M3 임베딩, Chroma VectorStore, 검색 (VectorstoreMixin)
rag_chain_v2   Gemini LLM, basic_rag_chain, runnable_lambda (RagChainMixin)
rag_core_v2    RagBgeM3v2 메인 클래스 (위 Mixin 조합)
rag_runner_v2  CLI 실행 스크립트
"""

from .rag_core_v2 import RagBgeM3v2
from .config_v2 import (
    PDF_PATH, DB_PATH, COLLECTION_NAME,
    CASE_PATTERN, MAX_CASE_CHARS,
)

__all__ = [
    "RagBgeM3v2",
    "PDF_PATH",
    "DB_PATH",
    "COLLECTION_NAME",
    "CASE_PATTERN",
    "MAX_CASE_CHARS",
]
