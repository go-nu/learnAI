"""
0612_multimodal_rag_test.py  —  이전 버전 대비 변경 사항

- LLM 호출 방식: runnable_lambda → basic_rag_chain 으로 변경
  · 출처 레이블 형식 통일: [출처: {source} p.{page}] [표/이미지/텍스트]
- 0612_multimodal_rag_bge_m3 모듈 사용 (사례별 청킹 + 비례 조정 공식 반영)

실행 예시
    python 0612_multimodal_rag_test.py
"""

import importlib.util
import os
import sys

from dotenv import load_dotenv
from langchain_chroma import Chroma

# 날짜 접두사 파일명은 Python이 직접 import할 수 없으므로 importlib 사용
_spec = importlib.util.spec_from_file_location(
    "rag_module",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "0612_multimodal_rag_bge_m3.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
RagBgeM3 = _mod.RagBgeM3

DB_PATH = "./chroma_multimodal"
COLLECTION_NAME = "pdf_table_rag"


def load_retriever(rag: RagBgeM3):
    """기존 chroma_multimodal DB를 로드해 Retriever를 반환합니다. 재빌드하지 않습니다."""
    if not os.path.exists(DB_PATH):
        print(f"[오류] '{DB_PATH}' DB가 존재하지 않습니다.")
        print("      → 0612_multimodal_rag_bge_m3.py 를 먼저 실행해 DB를 생성하세요.")
        return None

    embeddings = rag.get_embeddings()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=DB_PATH,
    )

    total = vectorstore._collection.count()
    if total == 0:
        print(f"[오류] '{DB_PATH}' DB가 비어 있습니다. 재빌드가 필요합니다.")
        print("      → 0612_multimodal_rag_bge_m3.py 를 실행해 DB를 다시 생성하세요.")
        return None

    all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
    n_table = sum(1 for m in all_meta if m.get("doc_type") == "table")
    n_image = sum(1 for m in all_meta if m.get("doc_type") == "image")
    n_text  = total - n_table - n_image
    print(f"  텍스트 {n_text}개 + 표 {n_table}개 + 이미지 {n_image}개 = 총 {total}개 chunk")

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": rag.search_k},
    )


def main():
    load_dotenv()
    rag = RagBgeM3()

    print("=" * 55)
    print("  chroma_multimodal DB 로드 중...")
    retriever = load_retriever(rag)
    if retriever is None:
        sys.exit(1)

    print("  Gemini LLM 초기화 중...")
    try:
        llm = rag.get_llm()
    except EnvironmentError as e:
        print(f"[오류] {e}")
        sys.exit(1)

    print("=" * 55)
    print("  교통사고 과실비율 RAG 질의응답  (q: 종료)")
    print("=" * 55)

    while True:
        try:
            human_message = input("\n[질문] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not human_message:
            continue
        if human_message.lower() == "q":
            print("종료합니다.")
            break

        try:
            answer = rag.basic_rag_chain(retriever, llm, human_message)
            print(f"\n[AI] {answer}")
        except Exception as e:
            print(f"[오류] {e}")


if __name__ == "__main__":
    main()
