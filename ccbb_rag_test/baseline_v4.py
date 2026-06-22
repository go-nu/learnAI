"""
베이스라인 RAG v4
rag_v4 모듈(RagBgeM3) 사용 — 사례별/조항별 청킹 + ChromaDB + Gemini
에이전트·지식 그래프 없이 retrieve-then-generate만 수행한다.

실행:
  uv run baseline_v4.py build   # DB 구축 (최초 1회)
  uv run baseline_v4.py         # 대화형 검색
"""

import sys

from dotenv import load_dotenv

from rag_v4.rag_core_v4 import RagBgeM3

load_dotenv()

# ── 전역 캐시 (대화 루프 중 재초기화 방지) ──────────────────────────────
_rag: RagBgeM3 | None = None
_retriever = None
_llm = None


def _get_rag_components():
    global _rag, _retriever, _llm
    if _rag is None:
        _rag = RagBgeM3()
        _retriever = _rag.build_rag_components()
        _llm = _rag.get_llm()
    return _rag, _retriever, _llm


# ── DB 구축 ──────────────────────────────────────────────────────────
def build():
    RagBgeM3().create_vectorstore()


# ── 검색 + 생성 ──────────────────────────────────────────────────────
def ask(query: str) -> str:
    rag, retriever, llm = _get_rag_components()
    return rag.basic_rag_chain(retriever, llm, query)


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    print("베이스라인 RAG v4 (종료: q)")
    print("=" * 70)
    while True:
        try:
            query = input("\n질문: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break
        if query.lower() == "q":
            break
        if not query:
            continue
        print("[검색 중...]\n")
        print("[답변]")
        print(ask(query))
        print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
    else:
        main()
