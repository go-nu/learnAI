"""
rag_v4 — BGE-M3 + Chroma + Gemini 텍스트·표 RAG 패키지

v4 개선사항
-----------
- table 셀 기반 case_title 추출 (_build_case_title_map_from_tables, 1순위)
- title-summary chunk 추가 생성 (사례명 검색 정확도 강화)
- case_title 기반 rerank (방향 반전 사례 구분)
- 검색·rerank 단계 디버그 로그

모듈 구조
---------
config_v4        경로·청킹 전역 상수
pdf_loader_v4    다중 PDF 로드, 자동 감지 청킹, title-summary chunk (PdfLoaderMixin)
vectorstore_v4   BGE-M3 임베딩, Chroma VectorStore, 검색 (VectorstoreMixin)
rag_chain_v4     Gemini LLM, rerank, basic_rag_chain (RagChainMixin)
rag_core_v4      RagBgeM3v4 메인 클래스 (위 Mixin 조합)
rag_runner_v4    CLI 실행 스크립트 (--source 옵션 지원)
"""

from .rag_core_v4 import RagBgeM3v4
from .config_v4 import (
    SOURCE_DIR, DB_PATH, COLLECTION_NAME,
    CASE_PATTERN, MAX_CASE_CHARS,
    LEGAL_ARTICLE_PATTERN, LEGAL_ADDENDUM_PATTERN,
)

__all__ = [
    "RagBgeM3v4",
    "SOURCE_DIR",
    "DB_PATH",
    "COLLECTION_NAME",
    "CASE_PATTERN",
    "MAX_CASE_CHARS",
    "LEGAL_ARTICLE_PATTERN",
    "LEGAL_ADDENDUM_PATTERN",
]
