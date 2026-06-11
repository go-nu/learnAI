import re
from typing import Dict, List
from parsers.base_parser import BaseParser
from models.chunk import Chunk, ChunkMetadata
from chunkers.core_chunker import CoreChunker
from chunkers.legal_chunker import LegalChunker
from chunkers.precedent_chunker import PrecedentChunker

# 페이지 상단의 사례 제목 — 한글 10~60자 독립 줄
CASE_TITLE_RE = re.compile(r'^([가-힣][가-힣\s,·\-\(\)]{8,58}[가-힣\)])\s*$', re.MULTILINE)

# 섹션 마커
SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "accident_situation": re.compile(r'(?:[▶■●○◎\[【]?\s*)?사\s*고\s*상\s*황(?:\s*[\]】])?'),
    "basic_ratio_exp":    re.compile(r'(?:[▶■●○◎\[【]?\s*)?기\s*본\s*과\s*실\s*비\s*율\s*(?:의\s*)?해\s*설(?:\s*[\]】])?'),
    "modifier_exp":       re.compile(r'(?:[▶■●○◎\[【]?\s*)?수\s*정\s*요\s*소\s*(?:의\s*)?해\s*설(?:\s*[\]】])?'),
    "usage_notes":        re.compile(r'(?:[▶■●○◎\[【]?\s*)?활\s*용.*?참\s*고\s*사\s*항(?:\s*[\]】])?'),
    "legal":              re.compile(r'(?:[▶■●○◎\[【]?\s*)?관\s*련\s*법\s*규(?:\s*[\]】])?'),
    "precedent":          re.compile(r'(?:[▶■●○◎\[【]?\s*)?참\s*고\s*판\s*례(?:\s*[\]】])?'),
}


class ReviewCasesParser(BaseParser):
    """
    과실비율 심의사례 파서.
    case_id = 페이지 헤더의 전체 사례 제목 문자열 (보N 형식 없음).
    document_type = 'review_cases'
    """

    document_type = "review_cases"

    def __init__(self):
        self.core_chunker = CoreChunker()
        self.legal_chunker = LegalChunker()
        self.precedent_chunker = PrecedentChunker()

    # ------------------------------------------------------------------ #
    # BaseParser 구현                                                       #
    # ------------------------------------------------------------------ #

    def detect_cases(self, pages: List[str]) -> List[str]:
        seen: set = set()
        result: List[str] = []
        for page in pages:
            if self.is_skippable_page(page):
                continue
            title = self._extract_page_title(page)
            if title and title not in seen:
                seen.add(title)
                result.append(title)
        return result

    def detect_pattern(self, case_id: str, pages: List[str]) -> str:
        # 심의사례는 A/B 레이아웃 구분이 적용되지 않는다.
        return ""

    def extract_chunks(self, pdf_path: str) -> List[Chunk]:
        pages = self._load_pages(pdf_path)
        return self._extract_from_pages(pages)

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                             #
    # ------------------------------------------------------------------ #

    def _extract_page_title(self, page_text: str) -> str:
        """페이지 첫 번째 유효 제목 줄을 반환한다."""
        for m in CASE_TITLE_RE.finditer(page_text):
            candidate = m.group(1).strip()
            # 지나치게 짧은 문서 헤더(기관명·날짜 등) 제외
            if len(candidate) >= 10:
                return candidate
        return ""

    def _extract_from_pages(self, pages: List[str]) -> List[Chunk]:
        case_ids = self.detect_cases(pages)
        # 제목→해당 텍스트 블록 매핑
        blocks = self._build_case_blocks(case_ids, pages)
        chunks: List[Chunk] = []
        for case_id in case_ids:
            case_text = blocks.get(case_id, "")
            if not case_text:
                continue
            chunks.extend(self._make_chunks(case_id, case_text))
        return chunks

    def _build_case_blocks(
        self, case_ids: List[str], pages: List[str]
    ) -> Dict[str, str]:
        """각 case_id가 처음 등장하는 페이지부터 다음 case_id 등장 전까지의 텍스트를 수집한다."""
        # 페이지별 case_id 할당
        page_owner: List[str] = []
        current = ""
        for page in pages:
            if self.is_skippable_page(page):
                page_owner.append("")
                continue
            title = self._extract_page_title(page)
            if title in case_ids:
                current = title
            page_owner.append(current)

        blocks: Dict[str, str] = {cid: "" for cid in case_ids}
        for page, owner in zip(pages, page_owner):
            if owner:
                blocks[owner] = (blocks[owner] + "\n" + page).strip()
        return blocks

    def _split_sections(self, text: str) -> Dict[str, str]:
        markers = []
        for name, pattern in SECTION_PATTERNS.items():
            m = pattern.search(text)
            if m:
                markers.append((m.start(), m.end(), name))
        markers.sort(key=lambda x: x[0])

        sections: Dict[str, str] = {}
        for idx, (start, end, name) in enumerate(markers):
            next_start = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
            sections[name] = text[end:next_start].strip()
        return sections

    def _make_chunks(self, case_id: str, case_text: str) -> List[Chunk]:
        sections = self._split_sections(case_text)
        metadata_partial = {
            "document_type": self.document_type,
            "chapter": case_id,
            "layout_pattern": "",
            "group_id": "",
        }
        result: List[Chunk] = []

        result.append(
            self.core_chunker.create_chunk(
                case_id=case_id,
                case_title=case_id,
                accident_situation=sections.get("accident_situation", ""),
                basic_ratio_explanation=sections.get("basic_ratio_exp", ""),
                modifier_explanation=sections.get("modifier_exp", ""),
                usage_notes=sections.get("usage_notes", ""),
                basic_fault_ratio={},
                metadata_partial=metadata_partial,
            )
        )

        if sections.get("legal"):
            result.append(
                self.legal_chunker.create_chunk(
                    case_ids=[case_id],
                    legal_text=sections["legal"],
                    metadata_partial=metadata_partial,
                )
            )

        if sections.get("precedent"):
            result.append(
                self.precedent_chunker.create_chunk(
                    case_id=case_id,
                    precedent_text=sections["precedent"],
                    metadata_partial=metadata_partial,
                )
            )

        return result
