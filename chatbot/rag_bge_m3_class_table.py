"""
rag_bge_m3_class.py

두 소스 파일을 하나로 통합한 LangChain RAG 클래스 파일입니다.

포함 기능
- PDF 문서 로드 및 chunk 분리 (PDFPlumberLoader — 표 검출 포함)
- 표(Table) → Markdown 변환 후 독립 Document로 저장 (분할 없음)
- BAAI/bge-m3 로컬 임베딩 생성
- Chroma VectorStore 생성 및 검색
- 기존 Chroma DB 기반 Retriever 생성
- Gemini LLM 초기화
- basic RAG chain 실행 (표/텍스트 출처 구분 표기)
- LCEL RunnableLambda 방식 RAG 실행 (표 컨텍스트 포함)

메타데이터 구조
    doc_type : "text"  — 일반 텍스트 chunk
    doc_type : "table" — 표 Document (page / table_index / row_count / col_count 포함)

실행 예시
    python rag_bge_m3_class.py

사용 예시
    from rag_bge_m3_class import RagBgeM3, get_llm, build_rag_components, runnable_lambda

    rag = RagBgeM3()
    llm = rag.get_llm()
    retriever = rag.build_rag_components()
    answer = rag.runnable_lambda(retriever, llm, "경영책임자의 의무는?")
"""

import os
import shutil
from typing import List, Optional, Tuple

import pdfplumber
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


PDF_PATH = "./source/manual.pdf"
DB_PATH = "./chroma_db_bge_m3_table"
COLLECTION_NAME = "pdf_table_rag"


class RagBgeM3:
    """BGE-M3 + Chroma + Gemini 기반 LangChain RAG 클래스"""

    def __init__(
        self,
        pdf_path: str = PDF_PATH,
        db_path: str = DB_PATH,
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        search_k: int = 3,
        embedding_device: str = "cpu",
        llm_model: str = "gemini-2.5-flash",
        temperature: float = 0,
    ):
        load_dotenv()
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.search_k = search_k
        self.embedding_device = embedding_device
        self.llm_model = llm_model
        self.temperature = temperature

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — 표(Table) → Markdown 변환                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _table_to_markdown(table: List[List], page_num: int, table_idx: int) -> str:
        """
        pdfplumber가 반환한 2D 리스트를 Markdown 표 문자열로 변환합니다.

        변환 예시
        ---------
        [TABLE 2 - Page 3]
        | 구분 | 의무 내용 | 위반 시 처벌 |
        | --- | --- | --- |
        | 경영책임자 | 안전보건관리체계 구축 | 1년 이상 징역 |
        """
        if not table or not table[0]:
            return ""

        header = f"[TABLE {table_idx} - Page {page_num}]\n"
        rows = []
        for row_idx, row in enumerate(table):
            clean = [str(cell).strip().replace("\n", " ") if cell else "" for cell in row]
            rows.append("| " + " | ".join(clean) + " |")
            if row_idx == 0:                          # 헤더 구분선
                rows.append("| " + " | ".join(["---"] * len(clean)) + " |")
        return header + "\n".join(rows)

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — 페이지 단위 표 Document 생성                           #
    # ------------------------------------------------------------------ #
    def _extract_table_docs(self, pdf_path: str) -> List[Document]:
        """
        pdfplumber로 각 페이지의 표를 추출해 독립 Document 목록을 반환합니다.

        메타데이터 필드
        ---------------
        source      : PDF 파일 경로
        page        : 0-based 페이지 번호  (PyPDFLoader 기준과 일치)
        doc_type    : "table"
        table_index : 해당 페이지 내 표 순서 (1-based)
        row_count   : 행 수
        col_count   : 열 수
        """
        table_docs: List[Document] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):   # 0-based
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables, start=1):
                    if not table:
                        continue
                    md = self._table_to_markdown(table, page_num + 1, t_idx)
                    if not md.strip():
                        continue
                    table_docs.append(Document(
                        page_content=md,
                        metadata={
                            "source":      pdf_path,
                            "page":        page_num,      # 0-based (PyPDF 호환)
                            "doc_type":    "table",
                            "table_index": t_idx,
                            "row_count":   len(table),
                            "col_count":   len(table[0]) if table else 0,
                        },
                    ))
        return table_docs

    # ------------------------------------------------------------------ #
    #  load_docs — 텍스트 chunk + 표 Document 통합 반환                   #
    # ------------------------------------------------------------------ #
    def load_docs(self) -> Optional[List[Document]]:
        """
        PDFPlumberLoader로 PDF를 로드하고 LangChain Document 목록을 반환합니다.

        처리 흐름
        ---------
        1. PDFPlumberLoader → 페이지 텍스트 추출
        2. RecursiveCharacterTextSplitter → 텍스트를 chunk 분할
           · 각 chunk에 doc_type="text" 메타데이터 부여
        3. pdfplumber → 표 전용 추출
           · 표 Document는 분할하지 않고 원형 보존 (doc_type="table")
        4. 텍스트 chunk + 표 Document 합산 반환
        """
        if not os.path.exists(self.pdf_path):
            print(f"[오류] '{self.pdf_path}' 파일이 없습니다.")
            print("      → python create_manual_pdf.py 를 먼저 실행하세요!")
            return None

        # ── 1. 텍스트 추출 (PDFPlumberLoader) ──────────────────────────
        loader = PDFPlumberLoader(self.pdf_path)
        pages  = loader.load()

        # ── 2. 텍스트 chunk 분할 ────────────────────────────────────────
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        text_chunks = splitter.split_documents(pages)
        text_chunks = [d for d in text_chunks if d.page_content.strip()]
        for chunk in text_chunks:
            chunk.metadata["doc_type"] = "text"   # 텍스트 chunk 표시

        # ── 3. 표 추출 (pdfplumber 직접 호출) ──────────────────────────
        table_docs = self._extract_table_docs(self.pdf_path)

        # ── 4. 합산 ─────────────────────────────────────────────────────
        all_docs = text_chunks + table_docs
        all_docs = [d for d in all_docs if d.page_content.strip()]

        print(f"  → 텍스트 chunk {len(text_chunks)}개 + 표 {len(table_docs)}개 "
              f"= 총 {len(all_docs)}개 Document 준비 완료")
        return all_docs

    def get_embeddings(self):
        """BAAI/bge-m3 로컬 임베딩 — 프로세스 수준 캐싱으로 재사용"""
        from langchain_huggingface import HuggingFaceEmbeddings

        cache_key = self.embedding_device
        if cache_key not in _EMBEDDING_CACHE:
            print("  임베딩: BAAI/bge-m3 (로컬, 최초 로드)")
            _EMBEDDING_CACHE[cache_key] = HuggingFaceEmbeddings(
                model_name="BAAI/bge-m3",
                model_kwargs={"device": self.embedding_device},
                encode_kwargs={"normalize_embeddings": True},
            )
        return _EMBEDDING_CACHE[cache_key]

    def create_vectorstore(self):
        """LangChain Chroma VectorStore를 생성하고 PDF chunk(텍스트+표)를 저장합니다."""
        print("=" * 50)
        print("[실습 1] VectorStore 생성 및 문서 저장")

        docs = self.load_docs()
        if docs is None:
            return None

        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)

        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.get_embeddings(),
            collection_name=self.collection_name,
            persist_directory=self.db_path,
        )

        n_text  = sum(1 for d in docs if d.metadata.get("doc_type") == "text")
        n_table = sum(1 for d in docs if d.metadata.get("doc_type") == "table")
        print(f"  → 텍스트 {n_text}개 + 표 {n_table}개 = 총 {len(docs)}개 chunk를 "
              f"'{self.db_path}'에 저장했습니다.")
        return vectorstore

    def similarity_search(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """VectorStore에서 유사도 검색을 실행합니다. (텍스트·표 모두 검색)"""
        print("=" * 50)
        print("[실습 2] 유사도 검색 (similarity_search)")

        query = query or "경영책임자가 지켜야 할 안전 의무는 무엇인가요?"
        results = vectorstore.similarity_search(query, k=k)

        print(f"  질문: '{query}'")
        print(f"  → {len(results)}개 결과 반환\n")
        for i, doc in enumerate(results):
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  [결과 {i + 1}] {icon} [{dtype.upper()}]")
            print(f"    내용: {doc.page_content[:200]}...")
            print(f"    출처: {doc.metadata}")
        print()
        return results

    def search_with_score(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """VectorStore에서 유사도 점수와 함께 검색합니다. (텍스트·표 모두 검색)"""
        print("=" * 50)
        print("[실습 3] 점수 포함 검색 (similarity_search_with_score)")

        query = query or "중대재해 발생 시 처벌 수위는?"
        results = vectorstore.similarity_search_with_score(query, k=k)

        print(f"  질문: '{query}'\n")
        for doc, score in results:
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  점수: {score:.4f}  ← 낮을수록 유사 (Chroma는 거리 기준)  "
                  f"{icon} [{dtype.upper()}]")
            print(f"  내용: {doc.page_content[:200]}...")
            print()
        return results

    def search_with_filter(
        self,
        vectorstore,
        query: Optional[str] = None,
        page: int = 0,
        k: int = 3,
    ):
        """metadata 필터로 검색 범위를 좁혀 검색합니다. (page 기준, 텍스트+표 포함)"""
        print("=" * 50)
        print("[실습 4] metadata 필터 검색")

        query = query or "재해 발생 요건"
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"page": page},
        )

        print(f"  질문: '{query}'  (page={page} chunk만 검색)")
        print(f"  → {len(results)}개 결과\n")
        for doc in results:
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  {icon} [{dtype.upper()}]  "
                  f"p.{doc.metadata.get('page', '?')}  "
                  f"출처: {doc.metadata.get('source', '')}")
            print(f"  내용: {doc.page_content[:200]}...")
            print()
        return results

    def search_tables_only(
        self,
        vectorstore,
        query: Optional[str] = None,
        k: int = 3,
    ):
        """
        표(Table) Document만 대상으로 유사도 검색합니다.

        doc_type="table" 메타데이터 필터를 사용하므로
        텍스트 chunk는 결과에 포함되지 않습니다.
        """
        print("=" * 50)
        print("[실습 5] 표 전용 검색 (search_tables_only)")

        query = query or "처벌 기준 및 처벌 수위"
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"doc_type": "table"},
        )

        print(f"  질문: '{query}'  (표 Document만 검색)")
        print(f"  → {len(results)}개 표 결과\n")
        for i, doc in enumerate(results):
            meta = doc.metadata
            print(f"  📊 [표 결과 {i + 1}]  "
                  f"p.{meta.get('page', '?')} / "
                  f"표 {meta.get('table_index', '?')} / "
                  f"{meta.get('row_count', '?')}행×{meta.get('col_count', '?')}열")
            print(f"  {doc.page_content}")
            print()
        return results

    def build_rag_components(self):
        """기존 chroma_db_bge_m3에서 Retriever를 준비합니다.
        DB가 없거나 표(doc_type='table')가 0개면 자동으로 재빌드합니다."""
        needs_rebuild = False

        if not os.path.exists(self.db_path):
            print(f"  '{self.db_path}' DB가 없어 새로 빌드합니다.")
            needs_rebuild = True
        else:
            embeddings = self.get_embeddings()
            vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.db_path,
            )
            all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
            n_table = sum(1 for m in all_meta if m.get("doc_type") == "table")
            if n_table == 0:
                print(f"  기존 DB에 표(table) Document가 없습니다. 표 포함으로 재빌드합니다.")
                needs_rebuild = True

        if needs_rebuild:
            vectorstore = self.create_vectorstore()
            if vectorstore is None:
                raise RuntimeError("VectorStore 빌드에 실패했습니다.")

        total = vectorstore._collection.count()
        all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
        n_table = sum(1 for m in all_meta if m.get("doc_type") == "table")
        n_text  = total - n_table
        print(f"  VectorStore 로드 완료: 텍스트 {n_text}개 + 표 {n_table}개 = 총 {total}개 chunk")

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.search_k},
        )
        return retriever

    def get_llm(self):
        """LLM 초기화 — Claude(Anthropic)와 Gemini(Google) 모두 지원"""
        if self.llm_model.startswith("claude"):
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수를 설정해주세요.")
            return ChatAnthropic(
                model=self.llm_model,
                anthropic_api_key=api_key,
                temperature=self.temperature,
            )
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise EnvironmentError("GOOGLE_API_KEY 환경 변수를 설정해주세요.")
            return ChatGoogleGenerativeAI(
                model=self.llm_model,
                google_api_key=api_key,
                temperature=self.temperature,
            )

    def load_retriever(self):
        """기존 VectorDB에서 Retriever만 로드합니다 (재빌드 없음)."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"VectorDB가 없습니다: {self.db_path}")
        embeddings = self.get_embeddings()
        vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings,
            persist_directory=self.db_path,
        )
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.search_k},
        )

    def basic_rag_chain(self, retriever, llm, human_message: str):
        """기본 LCEL RAG chain을 실행합니다."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 중소기업 전략기술로드맵 전문 어시스턴트입니다.\n"
                    "아래 컨텍스트만을 근거로 답하고, 출처(source, page)를 함께 적으세요.\n"
                    "컨텍스트에 답이 없으면 '문서에서 찾을 수 없습니다'라고 답하세요.\n"
                    "표([TABLE])가 포함된 경우 표의 수치나 항목을 적극 활용하세요.\n"
                    "한국어로, 친근하게 답합니다.",
                ),
                ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
            ]
        )

        def format_docs(docs: list) -> str:
            """Document 리스트 → 출처 포함 텍스트 블록 (표 여부 표시)"""
            blocks = []
            for d in docs:
                dtype  = d.metadata.get("doc_type", "text")
                source = d.metadata.get("source", "?")
                page   = d.metadata.get("page", "?")
                label  = f"[출처: {source} p.{page}] [{'표' if dtype == 'table' else '텍스트'}]"
                blocks.append(f"{label}\n{d.page_content}")
            return "\n\n".join(blocks)

        rag_chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        return rag_chain.invoke(human_message)

    def runnable_lambda(self, retriever, llm, human_message: str, label: str = "중소기업 전략기술로드맵"):
        """LCEL RunnableLambda 방식으로 전처리/후처리를 포함한 RAG를 실행합니다."""

        def preprocess(query: str) -> dict:
            """질문을 정제하고 chroma_db에서 관련 문서를 검색해 context 구성.
            표 Document는 '[표]' 레이블로 구분해 LLM이 인식하도록 합니다."""
            cleaned = query.strip().rstrip("?!.")
            docs = retriever.invoke(cleaned)
            blocks = []
            for d in docs:
                dtype = d.metadata.get("doc_type", "text")
                page  = d.metadata.get("page", "?")
                if dtype == "table":
                    t_idx = d.metadata.get("table_index", "?")
                    label = f"[표 — p.{page}, 표{t_idx}]"
                else:
                    label = f"[텍스트 — p.{page}]"
                blocks.append(f"{label}\n{d.page_content}")
            context = "\n\n".join(blocks)
            return {"context": context, "question": cleaned}

        def postprocess(text: str) -> str:
            """답변에 출처 안내 문구 추가"""
            return f"[{label} 기반 답변]\n{text.strip()}"

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "주어진 참고 문서만을 근거로 정확하게 답하세요.\n"
                    "[표] 레이블이 붙은 내용은 문서의 표(Table)이므로 수치와 항목을 정확히 인용하세요.",
                ),
                ("human", "참고 문서:\n{context}\n\n질문: {question}"),
            ]
        )

        chain = (
            RunnableLambda(preprocess)
            | prompt
            | llm
            | StrOutputParser()
            | RunnableLambda(postprocess)
        )

        return chain.invoke(human_message)

    def run_cli(self):
        """질문을 입력받아 RAG 답변을 출력하는 CLI 실행 함수입니다."""
        try:
            llm = self.get_llm()
            retriever = self.build_rag_components()
        except Exception as exc:
            print("llm, vectorDB 호출에 실패하였습니다.")
            print(f"[상세 오류] {exc}")
            return

        while True:
            human_message = input("[질문(q:종료)]")
            if human_message == "q":
                return

            ai_message = self.runnable_lambda(retriever, llm, human_message)
            print(f"[AI] {ai_message}")


# -----------------------------------------------------------------------------
# 기존 함수명 호환용 래퍼
# 기존 소스에서 import 하던 함수명을 그대로 사용할 수 있게 유지합니다.
# -----------------------------------------------------------------------------
_EMBEDDING_CACHE: dict = {}

_default_rag = RagBgeM3()


def load_docs():
    return _default_rag.load_docs()


def get_embeddings():
    return _default_rag.get_embeddings()


def create_vectorstore():
    return _default_rag.create_vectorstore()


def similarity_search(vectorstore):
    return _default_rag.similarity_search(vectorstore)


def search_with_score(vectorstore):
    return _default_rag.search_with_score(vectorstore)


def search_with_filter(vectorstore):
    return _default_rag.search_with_filter(vectorstore)


def search_tables_only(vectorstore):
    return _default_rag.search_tables_only(vectorstore)


def build_rag_components():
    return _default_rag.build_rag_components()


def get_llm():
    return _default_rag.get_llm()


def basic_rag_chain(retriever, llm, human_message):
    return _default_rag.basic_rag_chain(retriever, llm, human_message)


def runnable_lambda(retriever, llm, human_message):
    return _default_rag.runnable_lambda(retriever, llm, human_message)


if __name__ == "__main__":
    RagBgeM3().run_cli()
