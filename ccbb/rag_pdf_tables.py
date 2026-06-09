"""
=======================================================================
 PDF Table-Aware RAG Pipeline  (Multi-PDF + Parser Registry)
 source/ 디렉토리의 모든 PDF → BGE-M3 Embedding → ChromaDB (단일 DB)

 파서 레지스트리 (fault_ratio_rag/parsers/registry.py) 자동 선택:
   roundabout_fault_ratio_standards_2025.pdf → RoundaboutParser
   fault_ratio_standards_2023.pdf            → StandardsParser
   fault_ratio_review_cases.pdf              → ReviewCasesParser
   road_traffic_law.pdf                      → LawParser
   그 외 PDF                                 → 레거시 PDFPlumber 청킹

 GPU/CPU 자동 탐지: torch.cuda.is_available() 기반
=======================================================================
"""

import os
import re
import sys
import glob
import shutil
import pdfplumber
from typing import List, Tuple, Optional

# fault_ratio_rag 패키지 경로 추가 (내부 임포트가 패키지 루트 기준)
_PKG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fault_ratio_rag")
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ══════════════════════════════════════════════════════════════════════
# 설정값
# ══════════════════════════════════════════════════════════════════════
SOURCE_DIR  = "./source"
CHROMA_DIR  = "./chroma_db_bge_m3"
EMBED_MODEL = "BAAI/bge-m3"

# CUDA 자동 탐지
try:
    import torch
    _CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    _CUDA_AVAILABLE = False

DEVICE     = "cuda" if _CUDA_AVAILABLE else "cpu"
BATCH_SIZE = 32 if DEVICE == "cuda" else 8   # GPU는 배치 크기 확대

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

# 레거시 사례 단위 청킹 대상 (파서 실패 시 폴백에만 사용)
CASE_CHUNKED_PDFS = {
    "roundabout_fault_ratio_standards_2025.pdf",
    "fault_ratio_standards_2023.pdf",
    "fault_ratio_review_cases.pdf",
}

CASE_SPLIT_PATTERNS = [
    r'\n(?=도표\s*\d+)',
    r'\n(?=사례\s*\d+)',
    r'\n(?=제\s*\d+\s*[조절항호절])',
    r'\n(?=[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])',
    r'\n(?=\d+\.\s+[가-힣A-Z][가-힣A-Za-z\s]{4,})',
    r'\n(?=\[[가-힣\s]{2,20}\]\s*\n)',
]


# ══════════════════════════════════════════════════════════════════════
# 1. 파서 레지스트리 기반 청킹  (신규)
# ══════════════════════════════════════════════════════════════════════
def _chunk_meta_to_dict(m, pdf_path: str) -> dict:
    """ChunkMetadata → ChromaDB 호환 메타데이터 딕셔너리 변환."""
    meta = {
        "source":              pdf_path,
        "file_name":           os.path.basename(pdf_path),
        "doc_type":            "case",          # 검색 필터 하위 호환
        "case_id":             m.case_id,
        "chunk_type":          m.chunk_type,    # core / legal / precedent
        "document_type":       m.document_type, # standards / law / review_cases / roundabout
        "chapter":             m.chapter,
        "layout_pattern":      m.layout_pattern,
        "group_id":            m.group_id,
        "court":               m.court,
        "case_number":         m.case_number,
        "outcome_fault_ratio": m.outcome_fault_ratio,
        "article_number":      m.article_number,
        "law_name":            m.law_name,
        # dict/list → 문자열 (ChromaDB는 str/int/float/bool 만 허용)
        "basic_fault_ratio":   str(m.basic_fault_ratio) if m.basic_fault_ratio else "",
        "laws_included":       ", ".join(m.laws_included) if m.laws_included else "",
    }
    # hierarchy: level1/level2/level3 개별 키로 펼치기
    if m.hierarchy:
        meta["hier_level1"] = m.hierarchy.get("level1", "")
        meta["hier_level2"] = m.hierarchy.get("level2", "")
        meta["hier_level3"] = m.hierarchy.get("level3", "")
    return meta


def parse_with_registry(pdf_path: str) -> Optional[List[Document]]:
    """
    레지스트리로 파서를 자동 선택해 Chunk → Document 변환 후 반환.
    지원하지 않는 형식이면 None 반환 (레거시 폴백 신호).
    """
    try:
        from parsers.registry import get_parser
        parser = get_parser(pdf_path)
        parser_name = type(parser).__name__
        print(f"  → 파서: {parser_name}")
        chunks = parser.extract_chunks(pdf_path)
        docs = [
            Document(page_content=c.text, metadata=_chunk_meta_to_dict(c.metadata, pdf_path))
            for c in chunks
        ]
        print(f"  ✅ 파서 청킹 완료: {len(docs)}개 청크")
        return docs
    except ValueError as e:
        print(f"  ⚠️  파서 미지원 ({e}) → 레거시 청킹으로 폴백")
        return None
    except Exception as e:
        print(f"  ⚠️  파서 오류: {e} → 레거시 청킹으로 폴백")
        return None


# ══════════════════════════════════════════════════════════════════════
# 2. 레거시: 표 포함 PDF 로더
# ══════════════════════════════════════════════════════════════════════
def table_to_markdown(table: List[List], page_num: int, table_idx: int) -> str:
    if not table or not table[0]:
        return ""
    md = f"\n[TABLE {table_idx} - Page {page_num}]\n"
    for row_idx, row in enumerate(table):
        clean_row = [str(cell).strip().replace("\n", " ") if cell else "" for cell in row]
        md += "| " + " | ".join(clean_row) + " |\n"
        if row_idx == 0:
            md += "| " + " | ".join(["---"] * len(clean_row)) + " |\n"
    return md


def load_pdf_with_tables(pdf_path: str) -> Tuple[List[Document], List[Document]]:
    file_name  = os.path.basename(pdf_path)
    text_docs  = []
    table_docs = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text() or ""
            tables   = page.extract_tables()

            page_table_texts = []
            for t_idx, table in enumerate(tables, start=1):
                if not table:
                    continue
                md_table = table_to_markdown(table, page_num, t_idx)
                table_docs.append(Document(
                    page_content=md_table,
                    metadata={
                        "source":      pdf_path,
                        "file_name":   file_name,
                        "page":        page_num,
                        "doc_type":    "table",
                        "table_index": t_idx,
                        "row_count":   len(table),
                        "col_count":   len(table[0]) if table else 0,
                    }
                ))
                page_table_texts.append(md_table)

            full_content = raw_text
            if page_table_texts:
                full_content += "\n\n" + "\n".join(page_table_texts)

            if full_content.strip():
                text_docs.append(Document(
                    page_content=full_content,
                    metadata={
                        "source":    pdf_path,
                        "file_name": file_name,
                        "page":      page_num,
                        "doc_type":  "text",
                    }
                ))

    print(f"  ✅ PDFPlumber 로딩 완료: 텍스트 {len(text_docs)}페이지 / 표 {len(table_docs)}개")
    return text_docs, table_docs


# ══════════════════════════════════════════════════════════════════════
# 3. 레거시: 일반 텍스트 청킹
# ══════════════════════════════════════════════════════════════════════
def split_documents(text_docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(text_docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    print(f"  ✅ 일반 청킹 완료: {len(text_docs)}페이지 → {len(chunks)}개 청크")
    return chunks


# ══════════════════════════════════════════════════════════════════════
# 4. 레거시: 사고/사례 단위 청킹
# ══════════════════════════════════════════════════════════════════════
def split_by_accident_case(
    text_docs: List[Document],
    pdf_path: str,
    min_case_size: int = 100,
) -> List[Document]:
    file_name = os.path.basename(pdf_path)
    full_text = "\n\n".join(
        doc.page_content for doc in text_docs if doc.page_content.strip()
    )

    for pattern in CASE_SPLIT_PATTERNS:
        parts = re.split(pattern, full_text)
        valid_parts = [p.strip() for p in parts if len(p.strip()) >= min_case_size]

        if len(valid_parts) >= 3:
            print(f"  ✅ 사례 분할 패턴 적용: {len(valid_parts)}개 사례")
            docs = []
            for case_idx, case_text in enumerate(valid_parts, start=1):
                first_line = case_text.split("\n")[0].strip()[:60]
                docs.append(Document(
                    page_content=case_text,
                    metadata={
                        "source":      pdf_path,
                        "file_name":   file_name,
                        "doc_type":    "case",
                        "case_id":     str(case_idx),
                        "case_title":  first_line,
                    }
                ))
            return docs

    print(f"  ⚠️  사례 패턴 미감지 → RecursiveCharacterTextSplitter 폴백")
    return split_documents(text_docs)


# ══════════════════════════════════════════════════════════════════════
# 5. BGE-M3 임베딩 (GPU/CPU 자동)
# ══════════════════════════════════════════════════════════════════════
def get_bge_m3_embeddings() -> HuggingFaceEmbeddings:
    print(f"  BGE-M3 모델 로딩 중: {EMBED_MODEL}")
    print(f"  Device: {DEVICE.upper()}  |  Batch size: {BATCH_SIZE}")
    if not _CUDA_AVAILABLE:
        print(f"  (CUDA 미감지 — CPU로 실행. GPU 사용 시 torch+CUDA 설치 필요)")

    model_kwargs: dict = {"device": DEVICE}
    if DEVICE == "cuda":
        model_kwargs["torch_dtype"] = torch.float16  # FP16으로 GPU 메모리/속도 최적화

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": True, "batch_size": BATCH_SIZE},
    )
    print(f"  ✅ BGE-M3 로드 완료")
    return embeddings


# ══════════════════════════════════════════════════════════════════════
# 6. ChromaDB 구축 / 로드
# ══════════════════════════════════════════════════════════════════════
def build_vectordb(
    all_docs: List[Document],
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    print(f"\n  ChromaDB 구축 중 → {persist_dir}")
    print(f"  총 Document 수: {len(all_docs)}개")

    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    vectordb = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="pdf_table_rag",
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"  ✅ ChromaDB 구축 완료: {vectordb._collection.count()}개 벡터 저장")
    return vectordb


def load_vectordb(
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="pdf_table_rag",
    )
    print(f"  ✅ 기존 ChromaDB 로드: {vectordb._collection.count()}개 벡터")
    return vectordb


# ══════════════════════════════════════════════════════════════════════
# 7. 유사도 검색
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
    쿼리로 유사 Document 검색.

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


def print_search_results(query: str, results: List[Tuple[Document, float]]):
    print(f"\n{'━'*65}")
    print(f"  검색 쿼리: \"{query}\"")
    print(f"{'━'*65}")

    for rank, (doc, score) in enumerate(results, 1):
        m          = doc.metadata
        dtype      = m.get("doc_type", "unknown")
        chunk_type = m.get("chunk_type", "")
        doc_type   = m.get("document_type", "")
        fname      = m.get("file_name", "unknown")
        case_id    = m.get("case_id", "-")
        chapter    = m.get("chapter", "")
        law_name   = m.get("law_name", "")
        art_num    = m.get("article_number", "")
        h1         = m.get("hier_level1", "")
        h2         = m.get("hier_level2", "")

        if dtype == "table":
            icon, label = "📊", f"표  │ p.{m.get('page', '-')}"
        elif chunk_type == "legal":
            icon, label = "⚖️ ", f"법규 │ {case_id}"
        elif chunk_type == "precedent":
            icon, label = "🏛️ ", f"판례 │ {case_id} │ {m.get('court','')}"
        elif doc_type == "law":
            icon, label = "📜", f"법률 │ {law_name} {art_num}"
        else:
            icon, label = "📋", f"사례 │ {case_id}"

        type_tag = f"[{doc_type or dtype}]" if doc_type else f"[{dtype}]"
        print(f"\n  [{rank}위] {icon} {type_tag:<14} {fname}")
        print(f"         {label}  │  유사도: {score:.4f}")

        if chapter and chapter != case_id:
            print(f"         제목: {chapter}")
        if h1 or h2:
            print(f"         계층: {h1} > {h2}")

        print(f"  {'─'*60}")
        preview = doc.page_content[:300].replace("\n", " ")
        print(f"  {preview}...")

    print()


# ══════════════════════════════════════════════════════════════════════
# 8. 전체 파이프라인 실행
# ══════════════════════════════════════════════════════════════════════
def build_pipeline(source_dir: str = SOURCE_DIR) -> Tuple[Chroma, HuggingFaceEmbeddings]:
    """source/ 디렉토리의 모든 PDF → 단일 ChromaDB 파이프라인."""

    print("\n" + "█"*65)
    print("  PDF RAG Pipeline  (Parser Registry + Multi-PDF)")
    print(f"  Device: {DEVICE.upper()}  |  Embed batch: {BATCH_SIZE}")
    print("█"*65)

    pdf_files = sorted(glob.glob(os.path.join(source_dir, "*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일이 없습니다: {source_dir}")

    print(f"\n  발견된 PDF: {len(pdf_files)}개")
    for p in pdf_files:
        print(f"  - {os.path.basename(p)}")

    all_docs: List[Document] = []
    stats = []

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        print(f"\n{'═'*65}")
        print(f"  처리 중: {file_name}")
        print(f"{'─'*65}")

        # ① 파서 레지스트리 시도
        parsed_docs = parse_with_registry(pdf_path)

        if parsed_docs is not None:
            all_docs.extend(parsed_docs)
            stats.append({
                "file": file_name, "mode": "parser",
                "chunks": len(parsed_docs), "tables": 0,
            })
        else:
            # ② 레거시 폴백: PDFPlumber + 청킹
            text_docs, table_docs = load_pdf_with_tables(pdf_path)
            is_case_chunked = file_name in CASE_CHUNKED_PDFS

            print(f"\n  [청킹] {'사례 단위' if is_case_chunked else '일반 텍스트'}")
            if is_case_chunked:
                split_docs = split_by_accident_case(text_docs, pdf_path)
            else:
                split_docs = split_documents(text_docs)

            all_docs.extend(split_docs)
            all_docs.extend(table_docs)
            stats.append({
                "file": file_name, "mode": "legacy",
                "chunks": len(split_docs), "tables": len(table_docs),
            })

    # ── 전체 통계 출력 ────────────────────────────────────────────────
    print(f"\n{'═'*65}")
    print(f"  Document 구성 요약")
    print(f"{'═'*65}")
    for s in stats:
        mode_tag = f"[{s['mode']}]"
        tbl = f" / 표:{s['tables']}개" if s["tables"] else ""
        print(f"  {s['file']:<50} {mode_tag:<8} 청크:{s['chunks']:>4}개{tbl}")
    print(f"{'─'*65}")
    print(f"  총 합계: {len(all_docs)}개 Document")

    # Step 3: 임베딩 모델 로드
    print(f"\n{'═'*65}")
    embeddings = get_bge_m3_embeddings()

    # Step 4: ChromaDB 구축
    print(f"\n{'═'*65}")
    vectordb = build_vectordb(all_docs, embeddings)

    return vectordb, embeddings


# ══════════════════════════════════════════════════════════════════════
# 9. 메인 실행
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    vectordb, embeddings = build_pipeline(SOURCE_DIR)

    # ── 검색 테스트 ───────────────────────────────────────────────────
    print("\n" + "█"*65)
    print("  검색 테스트")
    print("█"*65)

    test_queries = [
        ("회전교차로에서 발생한 사고의 과실비율 기준은?",               None,   None, None, None),
        ("보행자 횡단 사고에서 보행자의 급진입 과실비율은?",            "case", None, "core", None),
        ("신호등 있는 교차로에서 직진 차량과 좌회전 차량의 과실비율은?", None,  "fault_ratio_standards_2023.pdf", None, None),
        ("도로교통법 보행자 보호 의무 조항 내용은?",                    None,   None, None, "law"),
    ]

    for query, filter_type, fname, chunk_type, doc_type in test_queries:
        label = []
        if filter_type: label.append(f"doc_type={filter_type}")
        if fname:       label.append(f"file={fname}")
        if chunk_type:  label.append(f"chunk_type={chunk_type}")
        if doc_type:    label.append(f"document_type={doc_type}")
        print(f"\n  ({', '.join(label) if label else '전체 검색'})")
        results = search(
            vectordb, query, k=3,
            filter_type=filter_type, file_name=fname,
            chunk_type=chunk_type, document_type=doc_type,
        )
        print_search_results(query, results)

    # ── 인터랙티브 검색 ───────────────────────────────────────────────
    print("\n" + "═"*65)
    print("  인터랙티브 검색 모드 (종료: 'quit')")
    print("  doc_type    : table / text / case / (Enter=전체)")
    print("  chunk_type  : core / legal / precedent / (Enter=전체)")
    print("  document_type: standards / law / review_cases / roundabout / (Enter=전체)")
    print("  file        : 파일명 / (Enter=전체)")
    print("═"*65)

    while True:
        try:
            query = input("\n  검색어 입력 > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("  종료합니다.")
                break
            if not query:
                continue

            ft  = input("  doc_type     > ").strip().lower() or None
            ct  = input("  chunk_type   > ").strip().lower() or None
            dt  = input("  document_type> ").strip().lower() or None
            fn  = input("  file         > ").strip() or None

            results = search(
                vectordb, query, k=3,
                filter_type=ft, file_name=fn,
                chunk_type=ct, document_type=dt,
            )
            print_search_results(query, results)

        except KeyboardInterrupt:
            print("\n  종료합니다.")
            break
