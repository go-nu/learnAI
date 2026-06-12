"""
vectorstore_v1.py — 임베딩·Chroma VectorStore·검색 Mixin
BGE-M3 임베딩 생성, Chroma DB 빌드/로드, 유사도 검색 메서드 모음입니다.
RagBgeM3 클래스에 mixin으로 조합됩니다.
"""

import gc
import os
import shutil
from typing import Optional

from langchain_chroma import Chroma


class VectorstoreMixin:
    """임베딩·VectorStore·검색 관련 메서드 Mixin"""

    def get_embeddings(self):
        """BAAI/bge-m3 로컬 임베딩을 반환합니다. API 키 불필요."""
        from langchain_huggingface import HuggingFaceEmbeddings

        print("  임베딩: BAAI/bge-m3 (로컬)")
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": self.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )

    def create_vectorstore(self):
        """PDF에서 Document를 로드하고 Chroma VectorStore를 생성합니다."""
        print("=" * 50)
        print("[VectorStore 생성]")

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
        n_image = sum(1 for d in docs if d.metadata.get("doc_type") == "image")
        print(f"  → 텍스트 {n_text}개 + 표 {n_table}개 + 이미지 {n_image}개 = 총 {len(docs)}개 "
              f"chunk를 '{self.db_path}'에 저장했습니다.")
        return vectorstore

    def similarity_search(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """VectorStore에서 유사도 검색을 실행합니다."""
        query = query or "경영책임자가 지켜야 할 안전 의무는 무엇인가요?"
        results = vectorstore.similarity_search(query, k=k)
        print(f"  질문: '{query}' → {len(results)}개 결과\n")
        for i, doc in enumerate(results):
            dtype = doc.metadata.get("doc_type", "text")
            print(f"  [결과 {i+1}] [{'표' if dtype=='table' else '이미지' if dtype=='image' else '텍스트'}]")
            print(f"    {doc.page_content[:200]}...")
        return results

    def search_with_score(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """유사도 점수와 함께 검색합니다. (점수 낮을수록 유사)"""
        query = query or "중대재해 발생 시 처벌 수위는?"
        results = vectorstore.similarity_search_with_score(query, k=k)
        print(f"  질문: '{query}'\n")
        for doc, score in results:
            dtype = doc.metadata.get("doc_type", "text")
            print(f"  점수: {score:.4f}  [{dtype.upper()}]  {doc.page_content[:200]}...\n")
        return results

    def search_with_filter(
        self, vectorstore, query: Optional[str] = None, page: int = 0, k: int = 3,
    ):
        """metadata 필터(page)로 검색 범위를 좁혀 검색합니다."""
        query = query or "재해 발생 요건"
        results = vectorstore.similarity_search(query, k=k, filter={"page": page})
        print(f"  질문: '{query}'  (page={page}) → {len(results)}개 결과\n")
        for doc in results:
            dtype = doc.metadata.get("doc_type", "text")
            print(f"  [{dtype.upper()}] p.{doc.metadata.get('page','?')}  "
                  f"{doc.page_content[:200]}...\n")
        return results

    def search_tables_only(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """표(doc_type='table') Document만 대상으로 유사도 검색합니다."""
        query = query or "처벌 기준 및 처벌 수위"
        results = vectorstore.similarity_search(
            query, k=k, filter={"doc_type": "table"}
        )
        print(f"  질문: '{query}'  (표 전용) → {len(results)}개 결과\n")
        for i, doc in enumerate(results):
            meta = doc.metadata
            print(f"  [표 결과 {i+1}] p.{meta.get('page','?')} / "
                  f"표 {meta.get('table_index','?')} / "
                  f"{meta.get('row_count','?')}행×{meta.get('col_count','?')}열")
            print(f"  {doc.page_content}\n")
        return results

    def build_rag_components(self):
        """
        Chroma DB에서 Retriever를 준비합니다.

        아래 조건 중 하나라도 해당하면 자동으로 재빌드합니다.
        - DB 디렉터리가 없는 경우
        - 표(doc_type='table') 또는 이미지(doc_type='image') Document가 0개인 경우
        - case_id 메타데이터가 없는 구버전 DB인 경우

        Windows 파일 락 해제: _client.close() → del → gc.collect() 후 재빌드
        """
        needs_rebuild = False
        vectorstore = None

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
            n_image = sum(1 for m in all_meta if m.get("doc_type") == "image")
            if n_table == 0 or n_image == 0:
                print("  기존 DB에 표 또는 이미지 Document가 없습니다. 재빌드합니다.")
                needs_rebuild = True

            if not needs_rebuild:
                has_case_id = any(
                    m.get("case_id") for m in all_meta if m.get("doc_type") == "text"
                )
                if not has_case_id:
                    print("  기존 DB가 사례별 청킹 이전 버전입니다. 재빌드합니다.")
                    needs_rebuild = True

        if needs_rebuild:
            # Windows 파일 락 해제 후 재빌드
            if vectorstore is not None:
                try:
                    vectorstore._client.close()
                except Exception:
                    pass
                del vectorstore
                gc.collect()
            vectorstore = self.create_vectorstore()
            if vectorstore is None:
                raise RuntimeError("VectorStore 빌드에 실패했습니다.")

        total    = vectorstore._collection.count()
        all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
        n_table  = sum(1 for m in all_meta if m.get("doc_type") == "table")
        n_image  = sum(1 for m in all_meta if m.get("doc_type") == "image")
        n_text   = total - n_table - n_image
        print(f"  VectorStore 로드 완료: 텍스트 {n_text}개 + 표 {n_table}개 "
              f"+ 이미지 {n_image}개 = 총 {total}개 chunk")

        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.search_k},
        )
