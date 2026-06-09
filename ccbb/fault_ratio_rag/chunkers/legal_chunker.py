import re
from typing import Dict, List
from models.chunk import Chunk, ChunkMetadata

# 법조문 경계: "⊙도로교통법 제N조" 또는 "⊙교통사고처리특례법 제N조" 등
ARTICLE_RE = re.compile(
    r'⊙(?:도로교통법|교통사고처리특례법|도로법|자동차손해배상보장법)\s*제\s*\d+조[^\n]*'
)


class LegalChunker:
    """
    관련 법규 텍스트를 파싱해 법조문 목록을 추출하는 청크를 생성한다.
    """

    def create_chunk(
        self,
        case_ids: List[str],
        legal_text: str,
        metadata_partial: Dict,
    ) -> Chunk:
        # 법조문 이름 추출
        laws_included = [m.group().strip() for m in ARTICLE_RE.finditer(legal_text)]

        case_id = case_ids[0] if case_ids else ""
        text = f"[관련 법규]\n{legal_text.strip()}"

        metadata = ChunkMetadata(
            case_id=case_id,
            chunk_type="legal",
            document_type=metadata_partial.get("document_type", ""),
            chapter=metadata_partial.get("chapter", ""),
            layout_pattern=metadata_partial.get("layout_pattern", ""),
            group_id=metadata_partial.get("group_id", ""),
            laws_included=laws_included,
        )

        return Chunk(text=text, metadata=metadata)
