from dotenv import load_dotenv

from .config_v4 import (
    SOURCE_DIR, DB_PATH, COLLECTION_NAME, IMAGE_OUTPUT_DIR,
)
from .pdf_loader_v4 import PdfLoaderMixin
from .rag_chain_v4_1 import RagChainMixin
from .vectorstore_v4 import VectorstoreMixin


# BGE-M3 + Chroma + Gemini 기반 텍스트·표 RAG 클래스 (v4)
class RagBgeM3(PdfLoaderMixin, VectorstoreMixin, RagChainMixin):

    def __init__(
        self,
        source_dir:       str   = SOURCE_DIR,
        db_path:          str   = DB_PATH,
        collection_name:  str   = COLLECTION_NAME,
        image_output_dir: str   = IMAGE_OUTPUT_DIR,
        llm_model:        str   = "gemini-3.5-flash",
        temperature:      float = 0.0,
        embedding_device: str   = "auto",
        search_k:         int   = 3,
    ):
        load_dotenv()
        self.source_dir       = source_dir
        self.pdf_path         = ""      # load_docs 에서 PDF 순회 시 동적으로 설정
        self.db_path          = db_path
        self.collection_name  = collection_name
        self.image_output_dir = image_output_dir
        self.llm_model        = llm_model
        self.temperature      = temperature
        self.embedding_device = self._resolve_device(embedding_device)
        self.search_k         = search_k

    # "auto" → CUDA 가용 여부에 따라 "cuda" / "cpu" 결정
    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            resolved = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            resolved = "cpu"
        print(f"  임베딩 디바이스 자동 감지: {resolved.upper()}")
        return resolved
