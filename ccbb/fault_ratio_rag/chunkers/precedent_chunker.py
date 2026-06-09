import re
from typing import Dict
from models.chunk import Chunk, ChunkMetadata

# ⊙{법원명} {연도}.{월}.{일}. 선고 {사건번호} 판결
COURT_HEADER_RE = re.compile(
    r'⊙([가-힣\s]+법원[가-힣\s]*?)\s+'
    r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*선고\s+'
    r'(\S+)\s*판결'
)

# 과실비율 패턴: "N:M" 또는 "N%"
FAULT_RATIO_RE = re.compile(r'(\d+)\s*:\s*(\d+)|(\d+)\s*%')


class PrecedentChunker:
    """
    개별 법원 판결을 파싱해 청크로 변환한다.
    """

    def create_chunk(
        self,
        case_id: str,
        precedent_text: str,
        metadata_partial: Dict,
    ) -> Chunk:
        court = ""
        case_number = ""
        outcome_fault_ratio = ""

        m = COURT_HEADER_RE.search(precedent_text)
        if m:
            court = m.group(1).strip()
            case_number = m.group(5).strip()

        # 과실비율 추출 시도
        rm = FAULT_RATIO_RE.search(precedent_text)
        if rm:
            if rm.group(1) and rm.group(2):
                outcome_fault_ratio = f"{rm.group(1)}:{rm.group(2)}"
            elif rm.group(3):
                outcome_fault_ratio = f"{rm.group(3)}%"

        text = f"[참고 판례]\n{precedent_text.strip()}"

        metadata = ChunkMetadata(
            case_id=case_id,
            chunk_type="precedent",
            document_type=metadata_partial.get("document_type", ""),
            chapter=metadata_partial.get("chapter", ""),
            court=court,
            case_number=case_number,
            outcome_fault_ratio=outcome_fault_ratio,
        )

        return Chunk(text=text, metadata=metadata)
