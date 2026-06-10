"""
=======================================================================
 PDF Table-Aware RAG — 채팅 전용 (기존 ChromaDB 로드 후 검색)
 rag_pdf_tables.py 로 구축된 chroma_db_bge_m3 를 그대로 사용합니다.
=======================================================================
"""

import os
import sys
from typing import List, Tuple, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ══════════════════════════════════════════════════════════════════════
# 설정값 (rag_pdf_tables.py 와 동일하게 유지)
# ══════════════════════════════════════════════════════════════════════
CHROMA_DIR  = "./chroma_db_bge_m3"
EMBED_MODEL = "BAAI/bge-m3"

try:
    import torch
    _CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    _CUDA_AVAILABLE = False

DEVICE     = "cuda" if _CUDA_AVAILABLE else "cpu"
BATCH_SIZE = 32 if DEVICE == "cuda" else 8


# ══════════════════════════════════════════════════════════════════════
# 1. BGE-M3 임베딩 로드
# ══════════════════════════════════════════════════════════════════════
def get_bge_m3_embeddings() -> HuggingFaceEmbeddings:
    print(f"  BGE-M3 모델 로딩 중: {EMBED_MODEL}")
    print(f"  Device: {DEVICE.upper()}  |  Batch size: {BATCH_SIZE}")
    if not _CUDA_AVAILABLE:
        print(f"  (CUDA 미감지 — CPU로 실행)")

    model_kwargs: dict = {"device": DEVICE}
    if DEVICE == "cuda":
        model_kwargs["torch_dtype"] = torch.float16

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": True, "batch_size": BATCH_SIZE},
    )
    print(f"  ✅ BGE-M3 로드 완료")
    return embeddings


# ══════════════════════════════════════════════════════════════════════
# 2. 기존 ChromaDB 로드
# ══════════════════════════════════════════════════════════════════════
def load_vectordb(
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"ChromaDB 디렉토리가 없습니다: {persist_dir}\n"
            "먼저 rag_pdf_tables.py 를 실행해 DB를 구축하세요."
        )
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="pdf_table_rag",
    )
    print(f"  ✅ 기존 ChromaDB 로드: {vectordb._collection.count()}개 벡터")
    return vectordb


# ══════════════════════════════════════════════════════════════════════
# 3. 유사도 검색
# ══════════════════════════════════════════════════════════════════════
def search(
    vectordb: Chroma,
    query: str,
    k: int = 3,
    filter_type: Optional[str] = None,
    file_name: Optional[str] = None,
    chunk_type: Optional[str] = None,
    document_type: Optional[str] = None,
) -> List[Tuple[Document, float]]:
    """
    Args:
        filter_type   : doc_type 필터 — "table" / "text" / "case" / None
        chunk_type    : chunk_type 필터 — "core" / "legal" / "precedent" / None
        document_type : document_type 필터 — "standards" / "law" / "review_cases" / "roundabout" / None
        file_name     : 특정 파일로 검색 범위 제한
    """
    conditions = []
    if filter_type:
        conditions.append({"doc_type": {"$eq": filter_type}})
    if file_name:
        conditions.append({"file_name": {"$eq": file_name}})
    if chunk_type:
        conditions.append({"chunk_type": {"$eq": chunk_type}})
    if document_type:
        conditions.append({"document_type": {"$eq": document_type}})

    if len(conditions) == 0:
        where_filter = None
    elif len(conditions) == 1:
        where_filter = conditions[0]
    else:
        where_filter = {"$and": conditions}

    return vectordb.similarity_search_with_relevance_scores(
        query=query,
        k=k,
        filter=where_filter,
    )


# ══════════════════════════════════════════════════════════════════════
# 4. 검색 결과 출력
# ══════════════════════════════════════════════════════════════════════
def _clean(value) -> str:
    """metadata 값의 줄바꿈을 공백으로 정리."""
    return str(value).replace("\n", " ").strip()


# metadata 표시 순서 및 레이블 정의
_META_DISPLAY_ORDER = [
    ("doc_type",            "doc_type      "),
    ("document_type",       "document_type "),
    ("chunk_type",          "chunk_type    "),
    ("file_name",           "file_name     "),
    ("page",                "page          "),
    ("table_index",         "table_index   "),
    ("row_count",           "row_count     "),
    ("col_count",           "col_count     "),
    ("case_id",             "case_id       "),
    ("case_title",          "case_title    "),
    ("chapter",             "chapter       "),
    ("hier_level1",         "hier_level1   "),
    ("hier_level2",         "hier_level2   "),
    ("hier_level3",         "hier_level3   "),
    ("law_name",            "law_name      "),
    ("article_number",      "article_number"),
    ("court",               "court         "),
    ("case_number",         "case_number   "),
    ("outcome_fault_ratio", "fault_ratio   "),
    ("basic_fault_ratio",   "basic_ratio   "),
    ("laws_included",       "laws_included "),
    ("layout_pattern",      "layout_pattern"),
    ("chunk_id",            "chunk_id      "),
]


def print_search_results(query: str, results: List[Tuple[Document, float]]):
    print(f"\n{'━'*65}")
    print(f"  검색 쿼리: \"{query}\"")
    print(f"{'━'*65}")

    for rank, (doc, score) in enumerate(results, 1):
        m     = doc.metadata
        dtype = m.get("doc_type", "unknown")
        dt    = m.get("document_type", "")

        if dtype == "table":
            icon = "📊"
        elif m.get("chunk_type") == "legal":
            icon = "⚖️ "
        elif m.get("chunk_type") == "precedent":
            icon = "🏛️ "
        elif dt == "law":
            icon = "📜"
        else:
            icon = "📋"

        type_tag = f"[{dt or dtype}]"
        print(f"\n  [{rank}위] {icon} {type_tag:<14}  유사도: {score:.4f}")
        print(f"  {'─'*60}")

        # ── Metadata 블록 ──────────────────────────────────────────────
        print(f"  [Metadata]")
        for key, label in _META_DISPLAY_ORDER:
            val = m.get(key)
            if val is not None and _clean(val) not in ("", "-", "0"):
                print(f"    {label} : {_clean(val)}")
        print(f"  {'─'*60}")

        # ── 내용 미리보기 (100자) ──────────────────────────────────────
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"  [내용] {preview}...")

    print()


# ══════════════════════════════════════════════════════════════════════
# 5. 메인 실행
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    print("\n" + "█"*65)
    print("  RAG 채팅 모드  (기존 ChromaDB 로드)")
    print(f"  Device: {DEVICE.upper()}  |  DB: {CHROMA_DIR}")
    print("█"*65)

    embeddings = get_bge_m3_embeddings()
    vectordb   = load_vectordb(embeddings)

    print("\n" + "═"*65)
    print("  인터랙티브 검색 모드 (종료: 'quit')")
    print("  doc_type     : table / text / case / (Enter=전체)")
    print("  chunk_type   : core / legal / precedent / (Enter=전체)")
    print("  document_type: standards / law / review_cases / roundabout / (Enter=전체)")
    print("  file         : 파일명 / (Enter=전체)")
    print("═"*65)

    while True:
        try:
            query = input("\n  검색어 입력 > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("  종료합니다.")
                break
            if not query:
                continue

            ft = input("  doc_type      > ").strip().lower() or None
            ct = input("  chunk_type    > ").strip().lower() or None
            dt = input("  document_type > ").strip().lower() or None
            fn = input("  file          > ").strip() or None

            results = search(
                vectordb, query, k=3,
                filter_type=ft, file_name=fn,
                chunk_type=ct, document_type=dt,
            )
            print_search_results(query, results)

        except KeyboardInterrupt:
            print("\n  종료합니다.")
            break
