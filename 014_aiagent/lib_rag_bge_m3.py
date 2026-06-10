"""
lib_rag_bge_m3.py

rag_data/source/ 폴더의 MD 파일을 벡터DB(Chroma)로 만들고
LangChain RAG 검색을 제공하는 라이브러리.

주요 기능:
  - source_dir 내 모든 .md 파일 자동 로드
  - MarkdownHeaderTextSplitter로 헤더(#/##/###) 기준 청킹
  - BAAI/bge-m3 로컬 임베딩 (API 키 불필요)
  - Chroma 벡터스토어 생성 및 로드
  - 유사도 검색 (기본 / 점수 포함 / 메타데이터 필터)
  - Gemini LLM 기반 RAG 답변 체인
  - 대화형 CLI

사용 예시:
    from lib_rag_bge_m3 import RagBgeM3

    rag = RagBgeM3()
    rag.build()                                        # 벡터DB 생성
    results = rag.search("환불 정책은?")               # 유사도 검색
    results = rag.search_with_score("반품 기간")       # 점수 포함 검색
    results = rag.search_with_filter(                  # 파일 필터 검색
        "제3조", filter_dict={"source": "이용약관"}
    )
    answer  = rag.ask("환불 조건은 무엇인가요?")       # RAG 답변
    rag.run_cli()                                      # 대화형 CLI
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import MarkdownHeaderTextSplitter


SOURCE_DIR      = "rag_data/source"
DB_PATH         = "rag_data/cs"
COLLECTION_NAME = "terms_of_service"

_HEADERS_TO_SPLIT = [
    ("#",   "H1"),
    ("##",  "H2"),
    ("###", "H3"),
]


class RagBgeM3:
    """BAAI/bge-m3 + Chroma + Gemini 기반 LangChain RAG 클래스 (MD 전용)"""

    def __init__(
        self,
        source_dir: str = SOURCE_DIR,
        db_path: str = DB_PATH,
        collection_name: str = COLLECTION_NAME,
        search_k: int = 3,
        embedding_device: str = "cpu",
        llm_model: str = "gemini-2.5-flash",
        temperature: float = 0,
    ):
        load_dotenv()
        self.source_dir = source_dir
        self.db_path = db_path
        self.collection_name = collection_name
        self.search_k = search_k
        self.embedding_device = embedding_device
        self.llm_model = llm_model
        self.temperature = temperature

    # ── 1. MD 로드 & 청킹 ────────────────────────────────────────────

    def load_docs(self) -> list:
        """source_dir 내 모든 .md 파일을 로드하고 헤더 기준으로 청킹합니다.

        각 청크의 metadata에 source(파일명 stem)와 file(파일명)을 추가합니다.
        """
        source_path = Path(self.source_dir)
        md_files = sorted(source_path.glob("*.md"))
        if not md_files:
            raise FileNotFoundError(f"'{self.source_dir}'에 .md 파일이 없습니다.")

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=_HEADERS_TO_SPLIT,
            strip_headers=False,
        )

        all_docs = []
        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            chunks = splitter.split_text(text)
            for chunk in chunks:
                chunk.metadata["source"] = md_file.stem
                chunk.metadata["file"] = md_file.name
            valid = [c for c in chunks if c.page_content.strip()]
            all_docs.extend(valid)
            print(f"  {md_file.name}: {len(valid)}개 chunk")

        print(f"  → 총 {len(all_docs)}개 chunk 준비 완료")
        return all_docs

    # ── 2. 임베딩 ────────────────────────────────────────────────────

    def get_embeddings(self):
        """BAAI/bge-m3 로컬 임베딩을 반환합니다. (API 키 불필요)"""
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": self.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )

    # ── 3. 벡터스토어 생성 / 로드 ────────────────────────────────────

    def build(self) -> Chroma:
        """MD 파일로부터 Chroma 벡터스토어를 새로 빌드합니다.

        기존 DB가 있으면 삭제 후 재생성합니다.
        """
        print("=" * 50)
        print("[벡터DB 빌드] 시작")

        docs = self.load_docs()

        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
            print(f"  기존 DB '{self.db_path}' 삭제")

        print("  임베딩 생성 중... (BAAI/bge-m3, 첫 실행 시 모델 다운로드)")
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.get_embeddings(),
            collection_name=self.collection_name,
            persist_directory=self.db_path,
        )

        print(f"  → '{self.db_path}'에 {len(docs)}개 chunk 저장 완료")
        print("=" * 50)
        return vectorstore

    def load_vectorstore(self) -> Chroma:
        """저장된 Chroma 벡터스토어를 로드합니다."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"'{self.db_path}' DB가 없습니다. build()를 먼저 실행하세요."
            )
        vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.get_embeddings(),
            persist_directory=self.db_path,
        )
        count = vectorstore._collection.count()
        print(f"  벡터스토어 로드 완료: {count}개 chunk ({self.db_path})")
        return vectorstore

    # ── 4. 검색 ──────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        k: Optional[int] = None,
        vectorstore: Optional[Chroma] = None,
    ) -> list:
        """유사도 검색.

        Args:
            query: 검색 쿼리
            k: 반환할 결과 수 (기본값: self.search_k)
            vectorstore: 재사용할 벡터스토어 (없으면 자동 로드)

        Returns:
            Document 리스트
        """
        vs = vectorstore or self.load_vectorstore()
        results = vs.similarity_search(query, k=k or self.search_k)

        print(f"\n[검색] '{query}' → {len(results)}개 결과")
        for i, doc in enumerate(results):
            header = doc.metadata.get("H2") or doc.metadata.get("H1") or ""
            source = doc.metadata.get("source", "?")
            print(f"  [{i + 1}] [{source}] {header}")
            print(f"       {doc.page_content[:100]}...")
        return results

    def search_with_score(
        self,
        query: str,
        k: Optional[int] = None,
        vectorstore: Optional[Chroma] = None,
    ) -> list:
        """유사도 점수 포함 검색. 점수가 낮을수록 유사도가 높습니다(거리 기준).

        Returns:
            (Document, float) 튜플 리스트
        """
        vs = vectorstore or self.load_vectorstore()
        results = vs.similarity_search_with_score(query, k=k or self.search_k)

        print(f"\n[점수 검색] '{query}'")
        for doc, score in results:
            header = doc.metadata.get("H2") or doc.metadata.get("H1") or ""
            source = doc.metadata.get("source", "?")
            print(f"  점수: {score:.4f}  [{source}] {header}")
            print(f"       {doc.page_content[:100]}...")
        return results

    def search_with_filter(
        self,
        query: str,
        filter_dict: dict,
        k: Optional[int] = None,
        vectorstore: Optional[Chroma] = None,
    ) -> list:
        """메타데이터 필터로 검색 범위를 좁혀 유사도 검색합니다.

        Args:
            filter_dict: Chroma 메타데이터 필터
                예) {"source": "이용약관"}
                    {"H2": "제3조 (약관의 명시와 개정)"}

        Returns:
            Document 리스트
        """
        vs = vectorstore or self.load_vectorstore()
        results = vs.similarity_search(
            query, k=k or self.search_k, filter=filter_dict
        )

        print(f"\n[필터 검색] '{query}'  filter={filter_dict} → {len(results)}개 결과")
        for i, doc in enumerate(results):
            print(f"  [{i + 1}] {doc.metadata}")
            print(f"       {doc.page_content[:100]}...")
        return results

    # ── 5. Retriever ─────────────────────────────────────────────────

    def get_retriever(
        self,
        vectorstore: Optional[Chroma] = None,
        k: Optional[int] = None,
    ):
        """LangChain Retriever를 반환합니다."""
        vs = vectorstore or self.load_vectorstore()
        return vs.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k or self.search_k},
        )

    # ── 6. LLM ───────────────────────────────────────────────────────

    def get_llm(self):
        """Gemini LLM을 초기화합니다. (GOOGLE_API_KEY 필요)"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY 환경 변수를 설정해주세요.")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=api_key,
            temperature=self.temperature,
        )

    # ── 7. RAG 답변 체인 ─────────────────────────────────────────────

    @staticmethod
    def _format_docs(docs: list) -> str:
        """Document 리스트를 출처 포함 텍스트 블록으로 변환합니다."""
        return "\n\n".join(
            "[{src} / {section}]\n{content}".format(
                src=d.metadata.get("source", "?"),
                section=d.metadata.get("H2") or d.metadata.get("H1") or "본문",
                content=d.page_content,
            )
            for d in docs
        )

    def ask(
        self,
        question: str,
        retriever=None,
        llm=None,
    ) -> str:
        """RAG 체인으로 질문에 답변합니다.

        Args:
            question: 사용자 질문
            retriever: 재사용할 Retriever (없으면 자동 생성)
            llm: 재사용할 LLM (없으면 자동 생성)

        Returns:
            답변 문자열
        """
        _retriever = retriever or self.get_retriever()
        _llm = llm or self.get_llm()

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 쇼핑몰 이용약관 전문 어시스턴트입니다.\n"
                "아래 참고 문서만을 근거로 답하고, 관련 조항을 함께 안내하세요.\n"
                "문서에 답이 없으면 '문서에서 찾을 수 없습니다'라고 답하세요.\n"
                "한국어로 친근하게 답합니다.",
            ),
            ("human", "### 참고 문서\n{context}\n\n### 질문\n{question}"),
        ])

        chain = (
            {
                "context": _retriever | RunnableLambda(self._format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | _llm
            | StrOutputParser()
        )
        return chain.invoke(question)

    # ── 8. 대화형 CLI ────────────────────────────────────────────────

    def run_cli(self):
        """대화형 CLI를 실행합니다. 종료: q"""
        try:
            llm = self.get_llm()
            retriever = self.get_retriever()
        except Exception as exc:
            print(f"[초기화 실패] {exc}")
            return

        print("질문을 입력하세요. 종료: q\n")
        while True:
            question = input("[질문] ").strip()
            if question.lower() == "q":
                break
            if not question:
                continue
            answer = self.ask(question, retriever=retriever, llm=llm)
            print(f"\n[AI] {answer}\n")

    # ── 하위 호환 메서드 (기존 코드와 연동) ──────────────────────────

    def create_vectorstore(self) -> Chroma:
        """build()의 별칭입니다."""
        return self.build()

    def build_rag_components(self):
        """get_retriever()의 별칭입니다."""
        return self.get_retriever()

    def basic_rag_chain(self, retriever, llm, human_message: str) -> str:
        """ask()의 별칭입니다."""
        return self.ask(human_message, retriever=retriever, llm=llm)

    def runnable_lambda(self, retriever, llm, human_message: str) -> str:
        """ask()의 별칭입니다."""
        return self.ask(human_message, retriever=retriever, llm=llm)


# ── 모듈 레벨 함수 (하위 호환) ────────────────────────────────────────

def build_vectordb() -> Chroma:
    return RagBgeM3().build()

def load_docs() -> list:
    return RagBgeM3().load_docs()

def get_embeddings():
    return RagBgeM3().get_embeddings()

def build_rag_components():
    return RagBgeM3().get_retriever()

def get_llm():
    return RagBgeM3().get_llm()

def create_vectorstore() -> Chroma:
    return RagBgeM3().build()


if __name__ == "__main__":
    rag = RagBgeM3()
    rag.build()     # 벡터DB 빌드
    RagBgeM3().run_cli()
