from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ChunkMetadata:
    case_id: str                     # e.g. "보1", "회전-1"
    chunk_type: str                  # "core" | "legal" | "precedent"
    document_type: str               # "pedestrian" | "roundabout" | "standards" | "review_cases" | "law"
    chapter: str                     # case title string

    layout_pattern: str = ""         # "A" | "B"
    group_id: str = ""               # e.g. "보3-보4"

    basic_fault_ratio: Dict = field(default_factory=dict)
    # {"보행자": 30}  or  {"레드(A)": 20, "블루(B)": 80}

    laws_included: List = field(default_factory=list)
    # list of article name strings

    court: str = ""                  # for precedent chunks
    case_number: str = ""            # for precedent chunks
    outcome_fault_ratio: str = ""    # "N:M" or "N%"

    hierarchy: Optional[Dict] = None
    # {"level1": "...", "level2": "...", "level3": "..."}
    # for standards documents with 3-level structure

    article_number: str = ""         # for law document chunks only
    law_name: str = ""               # for law document chunks only


@dataclass
class Chunk:
    text: str
    metadata: ChunkMetadata
