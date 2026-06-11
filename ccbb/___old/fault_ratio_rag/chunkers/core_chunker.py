from typing import Dict, List
from models.chunk import Chunk, ChunkMetadata


class CoreChunker:
    """
    사고 유형 1건의 핵심 정보를 구조화된 텍스트 청크로 변환한다.
    """

    def create_chunk(
        self,
        case_id: str,
        case_title: str,
        accident_situation: str,
        basic_ratio_explanation: str,
        modifier_explanation: str,
        usage_notes: str,
        basic_fault_ratio: Dict,
        metadata_partial: Dict,
    ) -> Chunk:
        # 기본 과실비율 문자열
        ratio_str = (
            ", ".join(f"{k}: {v}" for k, v in basic_fault_ratio.items())
            if isinstance(basic_fault_ratio, dict) and basic_fault_ratio
            else str(basic_fault_ratio)
        )

        # 조정요소 문자열
        factors = metadata_partial.get("adjustment_factors", [])
        if factors:
            factors_str = ", ".join(
                f"{f.get('party', '')} {f.get('factor_name', '')}: {f.get('value', '')}".strip()
                for f in factors
            )
        else:
            factors_str = ""

        text = (
            f"【{case_id}】 {case_title}\n"
            f"기본 과실비율: {ratio_str}\n"
            f"조정요소: {factors_str}\n"
            f"\n"
            f"[사고상황]\n{accident_situation}\n"
            f"\n"
            f"[기본 과실비율 해설]\n{basic_ratio_explanation}\n"
            f"\n"
            f"[수정요소 해설]\n{modifier_explanation}\n"
            f"\n"
            f"[활용시 참고사항]\n{usage_notes}"
        ).strip()

        metadata = ChunkMetadata(
            case_id=case_id,
            chunk_type="core",
            document_type=metadata_partial.get("document_type", ""),
            chapter=metadata_partial.get("chapter", case_title),
            layout_pattern=metadata_partial.get("layout_pattern", "A"),
            group_id=metadata_partial.get("group_id", ""),
            basic_fault_ratio=basic_fault_ratio if isinstance(basic_fault_ratio, dict) else {},
        )

        return Chunk(text=text, metadata=metadata)
