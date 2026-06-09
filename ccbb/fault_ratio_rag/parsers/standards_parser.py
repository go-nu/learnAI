import re
from typing import Dict, List
from parsers.pedestrian_parser import PedestrianParser
from models.chunk import Chunk

# 3단계 계층 마커 (편/부 → 장 → 사례)
LEVEL1_RE = re.compile(r'제\s*\d+\s*(?:편|부)\s+(.+?)(?:\n|$)')
LEVEL2_RE = re.compile(r'제\s*\d+\s*장\s+(.+?)(?:\n|$)')


class StandardsParser(PedestrianParser):
    """
    2023 과실비율 인정기준서 파서.
    PedestrianParser를 확장해 3단계 계층(level1 > level2 > case_id)을 추적한다.
    document_type = 'standards'
    """

    document_type = "standards"

    def __init__(self):
        super().__init__()
        self._hierarchy_map: Dict[str, Dict] = {}

    # ------------------------------------------------------------------ #
    # 계층 구조 빌드                                                        #
    # ------------------------------------------------------------------ #

    def _build_hierarchy_map(self, pages: List[str]) -> Dict[str, Dict]:
        """페이지를 순서대로 스캔해 case_id → {level1, level2, level3} 매핑을 생성한다."""
        hierarchy: Dict[str, Dict] = {}
        current_level1 = ""
        current_level2 = ""

        for page in pages:
            if self.is_skippable_page(page):
                continue
            for line in page.split("\n"):
                line = line.strip()
                m1 = LEVEL1_RE.match(line)
                if m1:
                    current_level1 = m1.group(1).strip()
                    current_level2 = ""
                    continue
                m2 = LEVEL2_RE.match(line)
                if m2:
                    current_level2 = m2.group(1).strip()
                    continue
                # 해당 줄에 등장하는 case ID에 현재 계층 할당
                for m in re.finditer(r'보\s*(\d+)', line):
                    cid = f"보{m.group(1)}"
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
        self._hierarchy_map = self._build_hierarchy_map(pages)
        chunks = self._extract_from_pages(pages)
        self._attach_hierarchy(chunks)
        return chunks

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                             #
    # ------------------------------------------------------------------ #

    def _attach_hierarchy(self, chunks: List[Chunk]) -> None:
        """각 Chunk의 metadata에 hierarchy 딕셔너리를 주입한다."""
        for chunk in chunks:
            cid = chunk.metadata.case_id
            chunk.metadata.hierarchy = self._hierarchy_map.get(
                cid,
                {"level1": "", "level2": "", "level3": cid},
            )
