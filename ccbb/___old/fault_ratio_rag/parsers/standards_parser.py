import re
import pdfplumber
from collections import Counter
from typing import Dict, List, Optional
from parsers.pedestrian_parser import PedestrianParser
from models.chunk import Chunk

# 본문 헤딩 패턴 (TOC 기반 제N편/장 제거 → 본문 직접 파싱)
LEVEL1_PAREN_RE = re.compile(r'^\s*\((\d+)\)\s+(.+)')   # (1) 제목 텍스트
LEVEL2_PAREN_RE = re.compile(r'^\s*(\d+)\)\s+(.+)')     # 1) 제목 텍스트
LEVEL2_DOT_RE   = re.compile(r'^\s*(\d+)\.\s+(.+)')     # 1. 제목 텍스트
LEVEL3_CASE_RE  = re.compile(r'(?:보|차)\s*\d+')         # 보1, 차1 등


class StandardsParser(PedestrianParser):
    """
    2023 과실비율 인정기준서 파서.
    본문 헤딩 패턴(괄호숫자 / 폰트크기 / bold) 기반 3단계 계층 추적.
    document_type = 'standards'
    """

    document_type = "standards"

    def __init__(self):
        super().__init__()
        self._hierarchy_map: Dict[str, Dict] = {}

    # ------------------------------------------------------------------ #
    # 폰트 정보 추출 헬퍼                                                    #
    # ------------------------------------------------------------------ #

    def _get_body_font_size(self, pdf_path: str) -> float:
        """가장 빈도 높은 폰트 크기를 본문 기준 크기로 반환."""
        sizes = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for char in (page.chars or []):
                    sz = char.get("size")
                    if sz:
                        sizes.append(round(float(sz), 1))
        if not sizes:
            return 10.0
        return Counter(sizes).most_common(1)[0][0]

    def _load_pages_with_font(self, pdf_path: str) -> List[List[Dict]]:
        """페이지별 단어 블록(text, size, fontname, top, x0) 리스트 반환."""
        result = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=["fontname", "size"]) or []
                result.append(words)
        return result

    def _group_words_to_lines(
        self, words: List[Dict], tolerance: float = 3.0
    ) -> List[List[Dict]]:
        """단어 목록을 top 좌표 기준으로 줄 단위로 그룹핑."""
        if not words:
            return []
        sorted_words = sorted(
            words,
            key=lambda w: (round(w.get("top", 0) / tolerance) * tolerance, w.get("x0", 0)),
        )
        lines: List[List[Dict]] = []
        current_line: List[Dict] = []
        current_top: Optional[float] = None

        for word in sorted_words:
            top = word.get("top", 0)
            if current_top is None or abs(top - current_top) <= tolerance:
                current_line.append(word)
                current_top = top
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [word]
                current_top = top

        if current_line:
            lines.append(current_line)
        return lines

    def _is_bold(self, fontname: str) -> bool:
        fn = fontname.lower()
        return "bold" in fn or "b+" in fn or fn.endswith("b")

    def _is_heading_by_font(
        self, line_words: List[Dict], body_font_size: float
    ) -> bool:
        """줄 단어 중 하나라도 본문보다 크거나 bold이면 True."""
        for word in line_words:
            size = word.get("size")
            fontname = word.get("fontname", "")
            if size and float(size) > body_font_size + 0.5:
                return True
            if self._is_bold(fontname):
                return True
        return False

    # ------------------------------------------------------------------ #
    # 계층 구조 빌드 (본문 직접 파싱)                                        #
    # ------------------------------------------------------------------ #

    def _build_hierarchy_map(
        self, pdf_path: str, pages: List[str]
    ) -> Dict[str, Dict]:
        """
        본문 헤딩을 직접 파싱해 case_id → {level1, level2, level3} 매핑 생성.
          level1: (1), (2) 괄호숫자 패턴 또는 bold/대형 폰트 헤딩
          level2: 1), 2) 또는 1., 2. 숫자 패턴
          level3: 보N, 차N 등 case ID 자체
        """
        body_font_size = self._get_body_font_size(pdf_path)
        pages_words = self._load_pages_with_font(pdf_path)

        hierarchy: Dict[str, Dict] = {}
        current_level1 = ""
        current_level2 = ""

        for page_idx, page_text in enumerate(pages):
            if self.is_skippable_page(page_text):
                continue

            words = pages_words[page_idx] if page_idx < len(pages_words) else []
            lines = self._group_words_to_lines(words)

            for line_words in lines:
                if not line_words:
                    continue
                line_text = " ".join(w["text"] for w in line_words).strip()
                if not line_text:
                    continue

                # ① (1), (2) 괄호 숫자 → level1
                m1 = LEVEL1_PAREN_RE.match(line_text)
                if m1:
                    current_level1 = m1.group(2).strip()
                    current_level2 = ""
                    continue

                # ② 폰트 기반 level1 탐지 (level2 / case ID 패턴이 아닌 경우만)
                if self._is_heading_by_font(line_words, body_font_size):
                    if (not LEVEL2_PAREN_RE.match(line_text)
                            and not LEVEL2_DOT_RE.match(line_text)
                            and not LEVEL3_CASE_RE.search(line_text)):
                        current_level1 = line_text
                        current_level2 = ""
                        continue

                # ③ 1), 2) 또는 1., 2. → level2
                m2 = LEVEL2_PAREN_RE.match(line_text) or LEVEL2_DOT_RE.match(line_text)
                if m2:
                    current_level2 = m2.group(2).strip()
                    continue

                # ④ 보N, 차N → 직전 level1/level2 할당
                for m in LEVEL3_CASE_RE.finditer(line_text):
                    cid = re.sub(r'\s+', '', m.group(0))  # "보 1" → "보1"
                    if cid not in hierarchy:
                        hierarchy[cid] = {
                            "level1": current_level1,
                            "level2": current_level2,
                            "level3": cid,
                        }

        return hierarchy

    # ------------------------------------------------------------------ #
    # BaseParser 구현 (오버라이드)                                           #
    # ------------------------------------------------------------------ #

    def extract_chunks(self, pdf_path: str) -> List[Chunk]:
        pages = self._load_pages(pdf_path)
        self._hierarchy_map = self._build_hierarchy_map(pdf_path, pages)
        chunks = self._extract_from_pages(pages)
        self._attach_hierarchy(chunks)
        return chunks

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                             #
    # ------------------------------------------------------------------ #

    def _attach_hierarchy(self, chunks: List[Chunk]) -> None:
        """각 Chunk metadata에 hierarchy 딕셔너리를 주입한다."""
        for chunk in chunks:
            cid = chunk.metadata.case_id
            chunk.metadata.hierarchy = self._hierarchy_map.get(
                cid,
                {"level1": "", "level2": "", "level3": cid},
            )
