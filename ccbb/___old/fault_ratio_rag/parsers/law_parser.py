import re
from typing import Dict, List, Optional, Tuple
from parsers.base_parser import BaseParser
from models.chunk import Chunk, ChunkMetadata

# 법률 이름 후보 (우선순위 순)
LAW_NAMES = [
    "도로교통법",
    "교통사고처리특례법",
    "자동차손해배상보장법",
    "도로법",
]

# 조항 헤더: 줄 맨 앞에 "제N조" 또는 "제N조의M" 형식
# re.MULTILINE((?m))으로 ^ 를 줄 시작에 매칭 → 본문 인라인 참조 제외
ARTICLE_HEADER_RE = re.compile(
    r'(?m)^제\s*(\d+)\s*조(?:의\s*\d+)?\s*(?:\([^)]*\))?(?=[\s①②③④⑤\n])'
)

# 법률명 탐지용
LAW_NAME_RE = re.compile(
    r'(도로교통법|교통사고처리특례법|자동차손해배상보장법|도로법)'
)


class LawParser(BaseParser):
    """
    도로교통법 등 법률 문서 파서.
    조항(제N조) 단위로 청크를 생성하고,
    case_id = "{law_name}_제{N}조" 형식을 사용한다.
    document_type = 'law'
    """

    document_type = "law"

    # ------------------------------------------------------------------ #
    # BaseParser 구현                                                       #
    # ------------------------------------------------------------------ #

    def detect_cases(self, pages: List[str]) -> List[str]:
        law_name = self._detect_law_name(pages)
        seen: set = set()
        result: List[str] = []
        for page in pages:
            if self.is_skippable_page(page):
                continue
            for m in ARTICLE_HEADER_RE.finditer(page):
                article_num = f"제{m.group(1)}조"
                cid = f"{law_name}_{article_num}"
                if cid not in seen:
                    seen.add(cid)
                    result.append(cid)
        return result

    def detect_pattern(self, case_id: str, pages: List[str]) -> str:
        # 법률 문서에는 A/B 레이아웃 구분이 적용되지 않는다.
        return ""

    def extract_chunks(self, pdf_path: str) -> List[Chunk]:
        pages = self._load_pages(pdf_path)
        law_name = self._detect_law_name(pages)
        full_text = "\n".join(
            p for p in pages if not self.is_skippable_page(p)
        )
        return self._split_by_article(full_text, law_name)

    # ------------------------------------------------------------------ #
    # 내부 헬퍼                                                             #
    # ------------------------------------------------------------------ #

    def _detect_law_name(self, pages: List[str]) -> str:
        for page in pages[:5]:
            m = LAW_NAME_RE.search(page)
            if m:
                return m.group(1)
        return "법률"

    def _split_by_article(self, full_text: str, law_name: str) -> List[Chunk]:
        """전체 텍스트를 조항 단위로 분리해 Chunk 리스트를 반환한다."""
        # 모든 조항 헤더 위치 탐색
        boundaries: List[Tuple[int, str]] = []
        for m in ARTICLE_HEADER_RE.finditer(full_text):
            article_num = f"제{m.group(1)}조"
            boundaries.append((m.start(), article_num))

        chunks: List[Chunk] = []
        for idx, (start, article_num) in enumerate(boundaries):
            end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(full_text)
            article_text = full_text[start:end].strip()
            if not article_text:
                continue

            article_title = self._extract_article_title(article_text, article_num)
            case_id = f"{law_name}_{article_num}"

            metadata = ChunkMetadata(
                case_id=case_id,
                chunk_type="core",
                document_type=self.document_type,
                chapter=article_title,
                article_number=article_num,
                law_name=law_name,
            )
            chunks.append(Chunk(text=article_text, metadata=metadata))

        return chunks

    def _extract_article_title(self, article_text: str, article_num: str) -> str:
        """조항 제목(괄호 안 내용)을 추출한다. 없으면 article_num을 반환한다."""
        m = re.search(r'제\s*\d+\s*조\s*\(([^)]+)\)', article_text)
        if m:
            return f"{article_num}({m.group(1).strip()})"
        return article_num
