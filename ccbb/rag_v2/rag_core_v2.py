"""
rag_core_v2.py — RagBgeM3v2 메인 클래스
PdfLoaderMixin, VectorstoreMixin, RagChainMixin을 조합해
BGE-M3 + Chroma + Gemini 기반 텍스트·표 RAG 클래스를 구성합니다.

v1(RagBgeM3)과의 차이
----------------------
- vision_model, filtered_img_dir 파라미터 제거 (VL 처리 없음)
- LLM 인증: GOOGLE_API_KEY (GOOGLE_API_KEY_VISION 폴백 지원)
- 이미지는 image_output_dir 에 저장만 되며, 각 청크 메타데이터의
  image_refs 필드를 통해 출처 파일명을 추적할 수 있습니다.
"""

from dotenv import load_dotenv

from .config_v2 import (
    PDF_PATH, DB_PATH, COLLECTION_NAME, IMAGE_OUTPUT_DIR,
)
from .pdf_loader_v2 import PdfLoaderMixin
from .rag_chain_v2 import RagChainMixin
from .vectorstore_v2 import VectorstoreMixin


class RagBgeM3v2(PdfLoaderMixin, VectorstoreMixin, RagChainMixin):
    """BGE-M3 + Chroma + Gemini 기반 텍스트·표 RAG 클래스

    이미지는 파일로 저장·관리되며, 각 청크 메타데이터의 image_refs 필드를 통해
    어떤 페이지 이미지와 연관되는지 추적합니다. VL 모델은 사용하지 않습니다.

    사용 예시
    ---------
    from rag_v2 import RagBgeM3v2

    rag       = RagBgeM3v2()
    llm       = rag.get_llm()
    retriever = rag.build_rag_components()
    answer    = rag.basic_rag_chain(retriever, llm, "차16-3 과실비율은?")
    """

    def __init__(
        self,
        pdf_path:         str   = PDF_PATH,
        db_path:          str   = DB_PATH,
        collection_name:  str   = COLLECTION_NAME,
        image_output_dir: str   = IMAGE_OUTPUT_DIR,
        llm_model:        str   = "gemini-3.1-flash-lite",
        temperature:      float = 0.0,
        embedding_device: str   = "cpu",
        search_k:         int   = 4,
    ):
        load_dotenv()
        self.pdf_path         = pdf_path
        self.db_path          = db_path
        self.collection_name  = collection_name
        self.image_output_dir = image_output_dir
        self.llm_model        = llm_model
        self.temperature      = temperature
        self.embedding_device = embedding_device
        self.search_k         = search_k
