import pdfplumber
from parsers.base_parser import BaseParser
from parsers.roundabout_parser import RoundaboutParser
from parsers.law_parser import LawParser
from parsers.standards_parser import StandardsParser
from parsers.review_cases_parser import ReviewCasesParser

# 법률 문서 표지에서 탐지할 법률명 목록
_LAW_NAME_LIST = [
    "도로교통법",
    "교통사고처리특례법",
    "자동차손해배상보장법",
    "도로법",
]


def _read_page(pdf_path: str, page_index: int = 0) -> str:
    """지정 인덱스(0-based)의 단일 페이지 텍스트를 반환한다."""
    with pdfplumber.open(pdf_path) as pdf:
        if page_index < len(pdf.pages):
            return pdf.pages[page_index].extract_text() or ""
    return ""


def _read_sample_text(pdf_path: str, n: int = 5) -> str:
    """PDF 앞쪽 n 페이지의 텍스트를 합쳐 반환한다."""
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:n]:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def get_parser(pdf_path: str) -> BaseParser:
    """
    PDF 표지(1페이지) + 앞 5페이지 샘플을 검사해 적절한 파서를 반환한다.

    탐지 전략:
      - 표지 단독 사용 (1·2번): TOC에 모든 유형 키워드가 등장해
        5페이지 샘플로는 오탐이 발생하기 때문.
      - 법률 문서 표지는 법률명이 2회 이상 중복 기재되는 관행을 이용.
      - 회전교차로 문서 표지에는 "회전교차로"가 제목에 등장.

    탐지 순서:
      1. 표지 첫 300자에 법률명이 2회 이상 등장 → LawParser
      2. 표지에 "회전교차로" 존재 → RoundaboutParser
      3. 5페이지 샘플에 "횡단보도" 또는 "보행자" → StandardsParser
      4. 5페이지 샘플에 "과실비율" (fallback) → ReviewCasesParser
    """
    cover = _read_page(pdf_path, 0)        # 표지(1페이지)만
    sample = _read_sample_text(pdf_path, n=5)  # 넓은 샘플(3·4번용)

    # 1. 법률 문서: 표지 첫 300자에 법률명 2회 이상 (예: "도로교통법\n도로교통법\n...")
    cover_head = cover[:300]
    if any(cover_head.count(name) >= 2 for name in _LAW_NAME_LIST):
        return LawParser()

    # 2. 회전교차로: 표지(제목 페이지)에 "회전교차로" 직접 등장
    if "회전교차로" in cover:
        return RoundaboutParser()

    # 3. 기준서(보행자·횡단보도 유형): 5페이지 샘플 기준
    if "횡단보도" in sample or "보행자" in sample:
        return StandardsParser()

    # 4. 심의사례 fallback
    if "과실비율" in sample:
        return ReviewCasesParser()

    raise ValueError(
        f"지원하지 않는 문서 형식입니다: {pdf_path}\n"
        "표지 또는 앞 5페이지에서 문서 유형을 판별할 수 없습니다."
    )
