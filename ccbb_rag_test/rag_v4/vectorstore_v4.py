import gc
import os
import shutil
from typing import Optional

from langchain_chroma import Chroma


class VectorstoreMixin:

    # BAAI/bge-m3 로컬 임베딩 반환 (CUDA 자동 감지, batch_size 동적 조정)
    def get_embeddings(self):
        from langchain_huggingface import HuggingFaceEmbeddings

        is_cuda    = self.embedding_device == "cuda"
        batch_size = 32 if is_cuda else 8   # CPU: OOM 방지, CUDA: 기본값 활용

        print(f"  임베딩: BAAI/bge-m3 (로컬, device={self.embedding_device}, batch_size={batch_size})")
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": self.embedding_device},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": batch_size,
            },
        )
        # BGE-M3 기본 max_seq_length=8192 → CPU에서 32×8192×1024×4B=1GB 할당 시도로 OOM
        # 청크 최대 길이(MAX_CASE_CHARS=2000자 ≈ 500~700토큰) 대비 충분한 1024로 제한
        embeddings._client.max_seq_length = 1024
        return embeddings

    # load_docs() 호출 후 Chroma VectorStore 생성 및 저장
    def create_vectorstore(self):
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
        print(f"  → 텍스트 {n_text}개 + 표 {n_table}개 = 총 {len(docs)}개 "
              f"chunk를 '{self.db_path}'에 저장했습니다.")
        return vectorstore

    # 기본 유사도 검색
    def similarity_search(self, vectorstore, query: Optional[str] = None, k: int = 3):
        query = query or "교차로에서 신호위반 사고의 과실비율은?"
        results = vectorstore.similarity_search(query, k=k)
        print(f"  질문: '{query}' → {len(results)}개 결과\n")
        for i, doc in enumerate(results):
            dtype  = doc.metadata.get("doc_type", "text")
            refs   = doc.metadata.get("image_refs", "")
            label  = "표" if dtype == "table" else "텍스트"
            print(f"  [결과 {i+1}] [{label}]  {doc.page_content[:200]}...")
            if refs:
                print(f"    [참조 이미지] {refs}")
        return results

    # 유사도 점수 포함 검색 (점수 낮을수록 유사)
    def search_with_score(self, vectorstore, query: Optional[str] = None, k: int = 3):
        query = query or "중대재해 발생 시 처벌 수위는?"
        results = vectorstore.similarity_search_with_score(query, k=k)
        print(f"  질문: '{query}'\n")
        for doc, score in results:
            dtype = doc.metadata.get("doc_type", "text")
            refs  = doc.metadata.get("image_refs", "")
            print(f"  점수: {score:.4f}  [{dtype.upper()}]  {doc.page_content[:200]}...")
            if refs:
                print(f"  [참조 이미지] {refs}")
            print()
        return results

    # metadata 필터(page)로 검색 범위를 좁혀 검색
    def search_with_filter(
        self, vectorstore, query: Optional[str] = None, page: int = 0, k: int = 3,
    ):
        query = query or "재해 발생 요건"
        results = vectorstore.similarity_search(query, k=k, filter={"page": page})
        print(f"  질문: '{query}'  (page={page}) → {len(results)}개 결과\n")
        for doc in results:
            dtype = doc.metadata.get("doc_type", "text")
            refs  = doc.metadata.get("image_refs", "")
            print(f"  [{dtype.upper()}] p.{doc.metadata.get('page','?')}  "
                  f"{doc.page_content[:200]}...")
            if refs:
                print(f"  [참조 이미지] {refs}")
            print()
        return results

    # doc_type='table' Document만 대상으로 유사도 검색
    def search_tables_only(self, vectorstore, query: Optional[str] = None, k: int = 3):
        query = query or "처벌 기준 및 처벌 수위"
        results = vectorstore.similarity_search(
            query, k=k, filter={"doc_type": "table"}
        )
        print(f"  질문: '{query}'  (표 전용) → {len(results)}개 결과\n")
        for i, doc in enumerate(results):
            meta = doc.metadata
            refs = meta.get("image_refs", "")
            print(f"  [표 결과 {i+1}] p.{meta.get('page','?')} / "
                  f"표 {meta.get('table_index','?')} / "
                  f"{meta.get('row_count','?')}행×{meta.get('col_count','?')}열")
            print(f"  {doc.page_content}\n")
            if refs:
                print(f"  [참조 이미지] {refs}\n")
        return results

    # DB 유효성 확인 및 자동 재빌드 후 retriever 반환
    def build_rag_components(self):
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
            if n_table == 0:
                print("  기존 DB에 표 Document가 없습니다. 재빌드합니다.")
                needs_rebuild = True

            if not needs_rebuild:
                has_chunk_id = any(
                    m.get("case_id") or m.get("article_id")
                    for m in all_meta
                    if m.get("doc_type") == "text"
                )
                if not has_chunk_id:
                    print("  기존 DB가 청킹 이전 버전입니다. 재빌드합니다.")
                    needs_rebuild = True

            if not needs_rebuild:
                # v4: title-summary chunk 존재 여부 확인 (없으면 v3 이하 DB)
                has_case_docs = any(m.get("case_id") for m in all_meta)
                has_summary   = any(m.get("doc_type") == "summary" for m in all_meta)
                if has_case_docs and not has_summary:
                    print("  기존 DB에 title-summary chunk가 없습니다. 재빌드합니다.")
                    needs_rebuild = True

        if needs_rebuild:
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
        n_text    = sum(1 for m in all_meta if m.get("doc_type") == "text")
        n_table   = sum(1 for m in all_meta if m.get("doc_type") == "table")
        n_summary = sum(1 for m in all_meta if m.get("doc_type") == "summary")
        print(f"  VectorStore 로드 완료: 텍스트 {n_text}개 + 표 {n_table}개 + 요약 {n_summary}개 = 총 {total}개 chunk")

        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.search_k},
        )
