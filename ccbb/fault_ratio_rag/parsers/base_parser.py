from abc import ABC, abstractmethod
from typing import List
from models.chunk import Chunk


class BaseParser(ABC):

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
