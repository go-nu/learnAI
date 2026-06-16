"""
rag_v3 — BGE-M3 + Chroma + Gemini 텍스트·표 RAG 패키지 (법률 문서 + 다중 PDF 지원)

v2에서 법률 문서 조항별/부칙별 청킹 및 다중 PDF 동시 처리를 추가한 버전입니다.
source_dir 내의 모든 PDF를 자동 로드하고, 문서 유형을 자동 감지해 청킹합니다.

빠른 시작
---------
from rag_v3 import RagBgeM3v3

# ./source 디렉토리의 모든 PDF 처리 (기본)
rag = RagBgeM3v3()

# 별도 소스 디렉토리 지정
rag = RagBgeM3v3(source_dir="./my_docs")

retriever = rag.build_rag_components()
llm       = rag.get_llm()
answer    = rag.basic_rag_chain(retriever, llm, "제44조 음주운전 처벌 기준은?")

모듈 구조
---------
config_v3        경로·청킹 전역 상수 (SOURCE_DIR, 법률 조항 패턴 추가)
pdf_loader_v3    다중 PDF 로드, 자동 감지 청킹, 이미지 저장 (PdfLoaderMixin)
vectorstore_v3   BGE-M3 임베딩, Chroma VectorStore, 검색 (VectorstoreMixin)
rag_chain_v3     Gemini LLM, basic_rag_chain, runnable_lambda (RagChainMixin)
rag_core_v3      RagBgeM3v3 메인 클래스 (위 Mixin 조합)
rag_runner_v3    CLI 실행 스크립트 (--source 옵션 지원)
"""

from .rag_core_v3 import RagBgeM3v3
from .config_v3 import (
    SOURCE_DIR, DB_PATH, COLLECTION_NAME,
    CASE_PATTERN, MAX_CASE_CHARS,
    LEGAL_ARTICLE_PATTERN, LEGAL_ADDENDUM_PATTERN,
)

__all__ = [
    "RagBgeM3v3",
    "SOURCE_DIR",
    "DB_PATH",
    "COLLECTION_NAME",
    "CASE_PATTERN",
    "MAX_CASE_CHARS",
    "LEGAL_ARTICLE_PATTERN",
    "LEGAL_ADDENDUM_PATTERN",
]
