from abc import ABC, abstractmethod
from typing import List
import pdfplumber
from models.chunk import Chunk

SKIP_KEYWORDS = ["목차", "발간사", "머리말", "개정경과", "운영현황"]


class BaseParser(ABC):

    def is_skippable_page(self, page_text: str) -> bool:
        """페이지가 목차·서문 등 파싱 불필요 페이지이면 True를 반환한다."""
        return any(kw in page_text for kw in SKIP_KEYWORDS)

    def _load_pages(self, pdf_path: str) -> List[str]:
        """pdfplumber로 PDF 전체 페이지 텍스트를 리스트로 반환한다."""
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
        return pages

    @abstractmethod
    def detect_cases(self, pages: List[str]) -> List[str]:
        """
        모든 페이지 텍스트를 스캔해 문서에 등장하는 순서대로
        case ID 목록을 반환한다.
        """

    @abstractmethod
    def detect_pattern(self, case_id: str, pages: List[str]) -> str:
        """
        해당 case_id의 레이아웃 패턴을 반환한다.

        Pattern A: case table 직후에 사고상황 섹션이 따라오는 경우
        Pattern B: 사고상황 섹션 없이 case table이 연속으로 나오는 경우
        Returns: "A" or "B"
        """

    @abstractmethod
    def extract_chunks(self, pdf_path: str) -> List[Chunk]:
        """PDF 파일을 파싱해 Chunk 리스트를 반환하는 전체 파이프라인."""
