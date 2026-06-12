"""
rag_core_v1.py — RagBgeM3 메인 클래스
PdfLoaderMixin, VectorstoreMixin, RagChainMixin을 조합해
BGE-M3 + Chroma + Gemini 기반 Multimodal RAG 클래스를 구성합니다.
"""

from dotenv import load_dotenv

from .config_v1 import (
    PDF_PATH, DB_PATH, COLLECTION_NAME,
    IMAGE_OUTPUT_DIR, FILTERED_IMG_DIR, VISION_MODEL,
)
from .pdf_loader_v1 import PdfLoaderMixin
from .rag_chain_v1 import RagChainMixin
from .vectorstore_v1 import VectorstoreMixin


class RagBgeM3(PdfLoaderMixin, VectorstoreMixin, RagChainMixin):
    """BGE-M3 + Chroma + Gemini 기반 Multimodal RAG 클래스

    사용 예시
    ---------
    from multimodal_rag import RagBgeM3

    rag       = RagBgeM3()
    llm       = rag.get_llm()
    retriever = rag.build_rag_components()
    answer    = rag.basic_rag_chain(retriever, llm, "차16-3 과실비율은?")
    """

    def __init__(
        self,
        pdf_path: str = PDF_PATH,
        db_path: str = DB_PATH,
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        search_k: int = 3,
        embedding_device: str = "cuda",
        llm_model: str = "gemini-2.5-flash",
        temperature: float = 0,
        image_output_dir: str = IMAGE_OUTPUT_DIR,
        filtered_img_dir: str = FILTERED_IMG_DIR,
        vision_model: str = VISION_MODEL,
    ):
        load_dotenv()
        self.pdf_path         = pdf_path
        self.db_path          = db_path
        self.collection_name  = collection_name
        self.chunk_size       = chunk_size
        self.chunk_overlap    = chunk_overlap
        self.search_k         = search_k

        # CUDA 요청 시 가용성 확인 — 없으면 CPU로 자동 폴백
        import torch
        if embedding_device == "cuda" and not torch.cuda.is_available():
            print("[경고] CUDA를 사용할 수 없습니다. CPU로 자동 전환합니다.")
            embedding_device = "cpu"
        self.embedding_device = embedding_device

        self.llm_model        = llm_model
        self.temperature      = temperature
        self.image_output_dir = image_output_dir
        self.filtered_img_dir = filtered_img_dir
        self.vision_model     = vision_model

    def run_cli(self):
        """질문을 입력받아 RAG 답변을 출력하는 CLI 루프입니다."""
        try:
            llm       = self.get_llm()
            retriever = self.build_rag_components()
        except Exception as exc:
            print("llm, vectorDB 호출에 실패하였습니다.")
            print(f"[상세 오류] {exc}")
            return

        while True:
            human_message = input("[질문(q:종료)] ")
            if human_message.strip().lower() == "q":
                return
            answer = self.basic_rag_chain(retriever, llm, human_message)
            print("\n" + "=" * 60)
            print(answer)
            print("=" * 60 + "\n")


if __name__ == "__main__":
    RagBgeM3().run_cli()
