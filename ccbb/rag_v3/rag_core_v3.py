"""
rag_core_v3.py — RagBgeM3v3 메인 클래스
PdfLoaderMixin, VectorstoreMixin, RagChainMixin을 조합해
BGE-M3 + Chroma + Gemini 기반 텍스트·표 RAG 클래스를 구성합니다.

v2와의 차이
-----------
- source_dir: 단일 pdf_path 대신 디렉토리 내 전체 PDF 자동 로드
- 법률 문서(조항별/부칙별) 청킹 지원 추가 (pdf_loader_v3)
- DB_PATH: chroma_bge_m3_v3 (v2와 분리)
- search_k 기본값: 3 (top-3 통일)
"""

from dotenv import load_dotenv

from .config_v3 import (
    SOURCE_DIR, DB_PATH, COLLECTION_NAME, IMAGE_OUTPUT_DIR,
)
from .pdf_loader_v3 import PdfLoaderMixin
from .rag_chain_v3 import RagChainMixin
from .vectorstore_v3 import VectorstoreMixin


class RagBgeM3v3(PdfLoaderMixin, VectorstoreMixin, RagChainMixin):
    """BGE-M3 + Chroma + Gemini 기반 텍스트·표 RAG 클래스 (v3)

    source_dir 내의 모든 PDF를 자동으로 로드하고,
    법률 문서·과실비율 문서·일반 문서를 자동 감지해 청킹합니다.

    사용 예시
    ---------
    from rag_v3 import RagBgeM3v3

    # ./source 디렉토리의 모든 PDF 처리 (기본)
    rag = RagBgeM3v3()

    # 별도 소스 디렉토리 지정
    rag = RagBgeM3v3(source_dir="./my_docs")

    retriever = rag.build_rag_components()
    llm       = rag.get_llm()
    answer    = rag.basic_rag_chain(retriever, llm, "제44조 음주운전 처벌 기준은?")
    """

    def __init__(
        self,
        source_dir:       str   = SOURCE_DIR,
        db_path:          str   = DB_PATH,
        collection_name:  str   = COLLECTION_NAME,
        image_output_dir: str   = IMAGE_OUTPUT_DIR,
        llm_model:        str   = "gemini-3.1-flash-lite",
        temperature:      float = 0.0,
        embedding_device: str   = "cpu",
        search_k:         int   = 3,    # top-k 통일
    ):
        load_dotenv()
        self.source_dir       = source_dir
        self.pdf_path         = ""      # load_docs 에서 PDF 순회 시 동적으로 설정
        self.db_path          = db_path
        self.collection_name  = collection_name
        self.image_output_dir = image_output_dir
        self.llm_model        = llm_model
        self.temperature      = temperature
        self.embedding_device = embedding_device
        self.search_k         = search_k
