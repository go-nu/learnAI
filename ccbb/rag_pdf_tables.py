"""
=======================================================================
 PDF Table-Aware RAG Pipeline  (Multi-PDF + Case-Based Chunking)
 source/ 디렉토리의 모든 PDF → BGE-M3 Embedding → ChromaDB (단일 DB)

 사고/사례 단위 청킹 적용 PDF:
   - roundabout_fault_ratio_standards_2025.pdf
   - fault_ratio_standards_2023.pdf
   - fault_ratio_review_cases.pdf
=======================================================================

[설치 명령어]
pip install langchain langchain-community langchain-huggingface
pip install pdfplumber chromadb sentence-transformers
"""

import os
import re
import glob
import shutil
import pdfplumber
from typing import List, Tuple, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ══════════════════════════════════════════════════════════════════════
# 설정값
# ══════════════════════════════════════════════════════════════════════
SOURCE_DIR    = "./source"            # PDF 소스 디렉토리
CHROMA_DIR    = "./chroma_db_bge_m3"  # ChromaDB 저장 디렉토리
EMBED_MODEL   = "BAAI/bge-m3"         # BGE-M3 임베딩 모델
DEVICE        = "cpu"                 # GPU 사용 시 "cuda"
CHUNK_SIZE    = 800                   # 일반 텍스트 청크 크기
CHUNK_OVERLAP = 100                   # 청크 겹침 크기

# 사고/사례 단위로 청킹할 PDF 파일 목록
CASE_CHUNKED_PDFS = {
    "roundabout_fault_ratio_standards_2025.pdf",
    "fault_ratio_standards_2023.pdf",
    "fault_ratio_review_cases.pdf",
}

# 사고/사례 경계를 나타내는 패턴 (우선순위 순)
# 각 패턴은 새 사례/사고의 시작 위치를 식별
CASE_SPLIT_PATTERNS = [
    r'\n(?=도표\s*\d+)',                                      # 도표 1, 도표2 ...
    r'\n(?=사례\s*\d+)',                                      # 사례 1, 사례2 ...
    r'\n(?=제\s*\d+\s*[조절항호절])',                         # 제1조, 제2절 ...
    r'\n(?=[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])',             # ①②③ ...
    r'\n(?=\d+\.\s+[가-힣A-Z][가-힣A-Za-z\s]{4,})',          # 1. 교차로 사고 ...
    r'\n(?=\[[가-힣\s]{2,20}\]\s*\n)',                        # [교차로 직진 대 좌회전] ...
]


# ══════════════════════════════════════════════════════════════════════
# 1. 표 포함 PDF 로더 (PDFPlumber 기반)
# ══════════════════════════════════════════════════════════════════════
def table_to_markdown(table: List[List], page_num: int, table_idx: int) -> str:
    """pdfplumber 테이블 → Markdown 포맷 변환"""
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
    """
    PDFPlumber + 표(table) 인식 파서

    Returns:
        text_docs  : 페이지별 텍스트 Document 리스트
        table_docs : 표별 독립 Document 리스트 (구조 보존)
    """
    file_name = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"  PDF 로딩: {file_name}")
    print(f"{'='*60}")

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

            text_preview = raw_text[:60].replace("\n", " ").strip()
            print(f"  Page {page_num:>2} │ 텍스트 {len(raw_text):>5}자 │ 표 {len(tables)}개"
                  + (f" │ {text_preview}..." if text_preview else ""))

    print(f"\n  ✅ 로딩 완료: 텍스트 {len(text_docs)}페이지 / 표 {len(table_docs)}개")
    return text_docs, table_docs


# ══════════════════════════════════════════════════════════════════════
# 2. 일반 텍스트 청킹 (일반 PDF용)
# ══════════════════════════════════════════════════════════════════════
def split_documents(text_docs: List[Document]) -> List[Document]:
    """페이지 텍스트를 고정 크기 청크로 분할"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(text_docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i

    print(f"  ✅ 청킹 완료: {len(text_docs)}페이지 → {len(chunks)}개 청크")
    return chunks


# ══════════════════════════════════════════════════════════════════════
# 3. 사고/사례 단위 청킹 (특수 PDF용)
# ══════════════════════════════════════════════════════════════════════
def split_by_accident_case(
    text_docs: List[Document],
    pdf_path: str,
    min_case_size: int = 100,
) -> List[Document]:
    """
    과실비율·사례 PDF를 사고/사례 단위로 분할.

    전체 텍스트를 하나로 합친 후 사례 경계 패턴으로 분할.
    유효한 패턴이 없으면 RecursiveCharacterTextSplitter로 폴백.

    Args:
        text_docs     : load_pdf_with_tables()에서 반환된 페이지별 Document
        pdf_path      : 원본 PDF 경로 (메타데이터용)
        min_case_size : 유효 사례로 인정할 최소 문자 수
    Returns:
        doc_type="case" 인 Document 리스트
    """
    file_name = os.path.basename(pdf_path)

    # 전체 텍스트 합치기 (페이지 구분 보존)
    full_text = "\n\n".join(
        doc.page_content for doc in text_docs if doc.page_content.strip()
    )

    # 사례 분할 패턴 순서대로 시도
    for pattern in CASE_SPLIT_PATTERNS:
        parts = re.split(pattern, full_text)
        valid_parts = [p.strip() for p in parts if len(p.strip()) >= min_case_size]

        if len(valid_parts) >= 3:
            print(f"  ✅ 사례 분할 패턴 적용: {len(valid_parts)}개 사례 추출")
            print(f"     패턴: {pattern}")

            docs = []
            for case_idx, case_text in enumerate(valid_parts, start=1):
                # 사례 제목 추출 (첫 줄 또는 첫 40자)
                first_line = case_text.split("\n")[0].strip()[:60]

                docs.append(Document(
                    page_content=case_text,
                    metadata={
                        "source":        pdf_path,
                        "file_name":     file_name,
                        "doc_type":      "case",
                        "case_id":       case_idx,
                        "case_title":    first_line,
                    }
                ))
            return docs

    # 폴백: 일반 텍스트 청킹
    print(f"  ⚠️  사례 패턴 미감지 → RecursiveCharacterTextSplitter 폴백")
    return split_documents(text_docs)


# ══════════════════════════════════════════════════════════════════════
# 4. BGE-M3 임베딩 모델 초기화
# ══════════════════════════════════════════════════════════════════════
def get_bge_m3_embeddings() -> HuggingFaceEmbeddings:
    """
    BAAI/bge-m3 임베딩 모델 로드.
    최초 실행 시 모델 자동 다운로드 (~570MB)
    """
    print(f"  BGE-M3 모델 로딩 중: {EMBED_MODEL} / Device: {DEVICE}")
    print(f"  (최초 실행 시 모델 다운로드 필요, 약 570MB)")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": DEVICE},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 8},
    )

    print(f"  ✅ BGE-M3 임베딩 모델 로드 완료")
    return embeddings


# ══════════════════════════════════════════════════════════════════════
# 5. ChromaDB 벡터 저장소 구축
# ══════════════════════════════════════════════════════════════════════
def build_vectordb(
    all_docs: List[Document],
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    """Document 리스트 → BGE-M3 임베딩 → ChromaDB 저장"""
    print(f"\n  ChromaDB 구축 중... 저장 경로: {persist_dir}")
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


# ══════════════════════════════════════════════════════════════════════
# 6. 기존 ChromaDB 불러오기
# ══════════════════════════════════════════════════════════════════════
def load_vectordb(
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    """저장된 ChromaDB 로드 (재사용)"""
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
) -> List[Tuple[Document, float]]:
    """
    쿼리로 유사 Document 검색.

    Args:
        query       : 검색 쿼리 문자열
        k           : 반환할 결과 수
        filter_type : "table" / "text" / "case" / None(전체)
        file_name   : 특정 파일로 검색 범위 제한 (None=전체)
    """
    conditions = []
    if filter_type:
        conditions.append({"doc_type": {"$eq": filter_type}})
    if file_name:
        conditions.append({"file_name": {"$eq": file_name}})

    if len(conditions) == 0:
        where_filter = None
    elif len(conditions) == 1:
        where_filter = conditions[0]
    else:
        where_filter = {"$and": conditions}

    results = vectordb.similarity_search_with_relevance_scores(
        query=query,
        k=k,
        filter=where_filter,
    )
    return results


def print_search_results(query: str, results: List[Tuple[Document, float]]):
    """검색 결과를 보기 좋게 출력"""
    print(f"\n{'━'*65}")
    print(f"  검색 쿼리: \"{query}\"")
    print(f"{'━'*65}")

    for rank, (doc, score) in enumerate(results, 1):
        dtype     = doc.metadata.get("doc_type", "unknown")
        page      = doc.metadata.get("page", "-")
        case_id   = doc.metadata.get("case_id", "-")
        case_title= doc.metadata.get("case_title", "")
        fname     = doc.metadata.get("file_name", "unknown")
        icon      = "📊" if dtype == "table" else ("⚖️ " if dtype == "case" else "📄")

        print(f"\n  [{rank}위] {icon} {dtype:5s} │ {fname} │ "
              + (f"사례 {case_id}" if case_id != "-" else f"p.{page}")
              + f" │ 유사도: {score:.4f}")
        if case_title and dtype == "case":
            print(f"          제목: {case_title}")
        print(f"  {'─'*60}")
        preview = doc.page_content[:300].replace("\n", " ")
        print(f"  {preview}...")

    print()


# ══════════════════════════════════════════════════════════════════════
# 8. 전체 파이프라인 실행
# ══════════════════════════════════════════════════════════════════════
def build_pipeline(source_dir: str = SOURCE_DIR) -> Tuple[Chroma, HuggingFaceEmbeddings]:
    """source/ 디렉토리의 모든 PDF → 단일 ChromaDB 파이프라인"""

    print("\n" + "█"*65)
    print("  PDF Table-Aware RAG Pipeline  (Multi-PDF)")
    print("  source/*.pdf → PDFPlumber → BGE-M3 → ChromaDB")
    print("█"*65)

    # PDF 파일 목록 수집
    pdf_files = sorted(glob.glob(os.path.join(source_dir, "*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일이 없습니다: {source_dir}")

    print(f"\n  발견된 PDF: {len(pdf_files)}개")
    for p in pdf_files:
        mode = "사례단위청킹" if os.path.basename(p) in CASE_CHUNKED_PDFS else "일반청킹"
        print(f"  - {os.path.basename(p)}  [{mode}]")

    all_docs: List[Document] = []
    stats = []

    # ── PDF별 처리 ────────────────────────────────────────────────────
    for pdf_path in pdf_files:
        file_name       = os.path.basename(pdf_path)
        is_case_chunked = file_name in CASE_CHUNKED_PDFS

        # Step 1: PDF 로드 (텍스트 + 표)
        text_docs, table_docs = load_pdf_with_tables(pdf_path)

        # Step 2: 청킹 전략 분기
        print(f"\n[청킹] {file_name}")
        print(f"{'─'*40}")

        if is_case_chunked:
            print(f"  → 사고/사례 단위 청킹")
            split_docs = split_by_accident_case(text_docs, pdf_path)
        else:
            print(f"  → 일반 텍스트 청킹 (chunk_size={CHUNK_SIZE})")
            split_docs = split_documents(text_docs)

        all_docs.extend(split_docs)
        all_docs.extend(table_docs)

        stats.append({
            "file":   file_name,
            "chunks": len(split_docs),
            "tables": len(table_docs),
        })

    # ── 전체 통계 출력 ────────────────────────────────────────────────
    print(f"\n{'═'*65}")
    print(f"  📦 전체 Document 구성 요약")
    print(f"{'═'*65}")
    for s in stats:
        mode = "사례" if s["file"] in CASE_CHUNKED_PDFS else "청크"
        print(f"  {s['file']:<52} {mode}:{s['chunks']:>4}개  표:{s['tables']:>3}개")
    print(f"{'─'*65}")
    print(f"  총 합계: {len(all_docs)}개 Document")

    # Step 3: BGE-M3 임베딩 모델 로드
    print(f"\n{'═'*65}")
    print("  BGE-M3 임베딩 모델 초기화")
    print(f"{'─'*65}")
    embeddings = get_bge_m3_embeddings()

    # Step 4: ChromaDB 구축
    print(f"\n{'═'*65}")
    print("  ChromaDB 벡터 저장소 구축")
    print(f"{'─'*65}")
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
        ("회전교차로에서 발생한 사고의 과실비율 기준은?",              None,   None),
        ("보행자 횡단 사고에서 보행자의 급진입 과실비율은?",           "case", None),
        ("신호등 있는 교차로에서 직진 차량과 좌회전 차량의 과실비율은?", None,  "fault_ratio_standards_2023.pdf"),
    ]

    for query, filter_type, fname in test_queries:
        label = []
        if filter_type: label.append(f"doc_type={filter_type}")
        if fname:       label.append(f"file={fname}")
        print(f"\n  ({', '.join(label) if label else '전체 검색'})")
        results = search(vectordb, query, k=3, filter_type=filter_type, file_name=fname)
        print_search_results(query, results)

    # ── 인터랙티브 검색 ───────────────────────────────────────────────
    print("\n" + "═"*65)
    print("  인터랙티브 검색 모드 (종료: 'quit' 입력)")
    print("  필터: doc_type = table / text / case / (Enter=전체)")
    print("  파일: 파일명 입력 / (Enter=전체)")
    print("═"*65)

    while True:
        try:
            query = input("\n  검색어 입력 > ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("  종료합니다.")
                break
            if not query:
                continue

            filter_input = input("  doc_type 필터 (table/text/case/Enter=전체) > ").strip().lower()
            filter_type  = filter_input if filter_input in ("table", "text", "case") else None

            file_input   = input("  파일 필터 (파일명/Enter=전체) > ").strip()
            file_name    = file_input if file_input else None

            results = search(vectordb, query, k=3, filter_type=filter_type, file_name=file_name)
            print_search_results(query, results)

        except KeyboardInterrupt:
            print("\n  종료합니다.")
            break
