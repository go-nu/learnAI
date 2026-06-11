import re
from typing import Dict, List
from parsers.base_parser import BaseParser
from models.chunk import Chunk
from chunkers.core_chunker import CoreChunker
from chunkers.legal_chunker import LegalChunker
from chunkers.precedent_chunker import PrecedentChunker

# 회전교차로 case header: 회전-1, 회전1, 회1 등
CASE_HEADER_RE = re.compile(
    r'(?:【|〔|「|\[)?(?:회전\s*[-\-]?\s*(\d+)|회\s*(\d+))(?:】|〕|」|\])?(?:\s|\.)'
)

GROUP_RE = re.compile(
    r'(?:회전\s*[-]?\s*|회\s*)(\d+)\s*[~∼～\-]\s*(?:회전\s*[-]?\s*|회\s*)(\d+)'
)

SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "accident_situation": re.compile(r'(?:[▶■●○◎\[【]?\s*)?사\s*고\s*상\s*황(?:\s*[\]】])?'),
    "basic_ratio_exp":    re.compile(r'(?:[▶■●○◎\[【]?\s*)?기\s*본\s*과\s*실\s*비\s*율\s*(?:의\s*)?해\s*설(?:\s*[\]】])?'),
    "modifier_exp":       re.compile(r'(?:[▶■●○◎\[【]?\s*)?수\s*정\s*요\s*소\s*(?:의\s*)?해\s*설(?:\s*[\]】])?'),
    "usage_notes":        re.compile(r'(?:[▶■●○◎\[【]?\s*)?활\s*용.*?참\s*고\s*사\s*항(?:\s*[\]】])?'),
    "legal":              re.compile(r'(?:[▶■●○◎\[【]?\s*)?관\s*련\s*법\s*규(?:\s*[\]】])?'),
    "precedent":          re.compile(r'(?:[▶■●○◎\[【]?\s*)?참\s*고\s*판\s*례(?:\s*[\]】])?'),
}

RATIO_RE = re.compile(
    r'([가-힣A-Za-z\(\)]+)\s*:?\s*(\d+)\s*%?\s*[：:]\s*([가-힣A-Za-z\(\)]+)\s*:?\s*(\d+)\s*%?'
)


class RoundaboutParser(BaseParser):
    """
    회전교차로 과실비율 기준서 파서.
    document_type = 'roundabout'
    """

    document_type = "roundabout"

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
            for m in CASE_HEADER_RE.finditer(page):
                num = m.group(1) or m.group(2)
                cid = f"회전-{num}"
                if cid not in seen:
                    seen.add(cid)
                    result.append(cid)
        return result

    def detect_pattern(self, case_id: str, pages: List[str]) -> str:
        num_str = re.search(r"\d+", case_id)
        if not num_str:
            return "A"
        num = int(num_str.group())
        for page in pages:
            if self.is_skippable_page(page):
                continue
            for m in GROUP_RE.finditer(page):
                if int(m.group(1)) <= num <= int(m.group(2)):
                    return "B"
        return "A"

    def extract_chunks(self, pdf_path: str) -> List[Chunk]:
        pages = self._load_pages(pdf_path)
        case_ids = self.detect_cases(pages)
        chunks: List[Chunk] = []
        for case_id in case_ids:
            case_text = self._extract_case_text(case_id, pages)
            if not case_text:
                continue
            chunks.extend(self._make_chunks(case_id, case_text, pages))
        return chunks

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                             #
    # ------------------------------------------------------------------ #

    def _find_case_page_indices(self, case_id: str, pages: List[str]) -> List[int]:
        num = re.search(r"\d+", case_id).group()
        pattern = re.compile(
            rf'(?:【|〔|「|\[)?(?:회전\s*[-]?\s*{num}|회\s*{num})(?:】|〕|」|\])?(?:\s|\.)'
        )
        return [
            i for i, p in enumerate(pages)
            if pattern.search(p) and not self.is_skippable_page(p)
        ]

    def _extract_case_text(self, case_id: str, pages: List[str]) -> str:
        indices = self._find_case_page_indices(case_id, pages)
        return "\n".join(pages[i] for i in indices) if indices else ""

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

    def _extract_fault_ratio(self, case_text: str) -> Dict:
        m = RATIO_RE.search(case_text[:800])
        if m:
            return {
                m.group(1).strip(): int(m.group(2)),
                m.group(3).strip(): int(m.group(4)),
            }
        return {}

    def _make_chunks(
        self, case_id: str, case_text: str, pages: List[str]
    ) -> List[Chunk]:
        pattern = self.detect_pattern(case_id, pages)
        sections = self._split_sections(case_text)
        chapter = case_id

        metadata_partial = {
            "document_type": self.document_type,
            "chapter": chapter,
            "layout_pattern": pattern,
            "group_id": "",
        }

        result: List[Chunk] = []
        result.append(
            self.core_chunker.create_chunk(
                case_id=case_id,
                case_title=chapter,
                accident_situation=sections.get("accident_situation", ""),
                basic_ratio_explanation=sections.get("basic_ratio_exp", ""),
                modifier_explanation=sections.get("modifier_exp", ""),
                usage_notes=sections.get("usage_notes", ""),
                basic_fault_ratio=self._extract_fault_ratio(case_text),
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
