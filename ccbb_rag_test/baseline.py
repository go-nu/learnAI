"""
베이스라인 RAG
고정 청킹(1200자/100자 오버랩) + ChromaDB 단일 컬렉션 + 단발 LLM 호출
에이전트·지식 그래프 없이 retrieve-then-generate만 수행한다.

실행:
  uv run baseline.py build   # DB 구축 (최초 1회)
  uv run baseline.py         # 대화형 검색
"""

import os
import sys

import chromadb
import google.generativeai as genai
import pymupdf4llm
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── 설정 ─────────────────────────────────────────────────────────────
BASELINE_DB_PATH = "./baseline_chroma_db"
SOURCE_PDF = "./source/original_document.pdf"
GEMINI_MODEL    = "gemini-2.0-flash-lite"
EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNK_SIZE      = 1200
CHUNK_OVERLAP   = 100
TOP_K           = 3

SYSTEM_PROMPT = """당신은 교통사고 과실비율 전문 AI입니다.
아래 참고 문서를 바탕으로 질문에 답하세요.
문서에 없는 내용은 추측하지 말고, 문서 근거만 사용하세요.
모든 답변은 한국어로 작성하세요.

반드시 답변 마지막에 다음 형식으로 과실비율을 명시하세요 (정보가 불충분해도 문서에서 추론 가능한 가장 근사한 값으로 반드시 기재):
최종 과실비율: A X% : B Y%"""


# ── 임베딩 ───────────────────────────────────────────────────────────
_embed_model: SentenceTransformer | None = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        print(f"[임베딩 모델 로드] {EMBEDDING_MODEL}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


def _embed(texts: list[str]) -> list[list[float]]:
    return _get_embed_model().encode(texts, batch_size=32, show_progress_bar=False).tolist()


# ── DB 구축 ──────────────────────────────────────────────────────────
def build():
    print("[1/3] 문서 로드 중...")
    docs_text = []

    print(f"  PDF 변환: {SOURCE_PDF}")
    docs_text.append(pymupdf4llm.to_markdown(SOURCE_PDF))

    full_text = "\n\n".join(docs_text)
    print(f"  총 텍스트 길이: {len(full_text):,}자")

    print(f"[2/3] 청킹 중... (크기={CHUNK_SIZE}, 오버랩={CHUNK_OVERLAP})")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_text(full_text)
    print(f"  청크 수: {len(chunks)}")

    print("[3/3] ChromaDB 저장 중...")
    client = chromadb.PersistentClient(path=BASELINE_DB_PATH)
    try:
        client.delete_collection("baseline")
    except Exception:
        pass
    col = client.create_collection("baseline")

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embs  = _embed(batch)
        ids   = [f"chunk_{i + j}" for j in range(len(batch))]
        col.add(documents=batch, embeddings=embs, ids=ids)
        print(f"  저장: {i + len(batch)}/{len(chunks)}")

    print(f"\n[완료] {len(chunks)}개 청크 저장 → {BASELINE_DB_PATH}")


# ── 검색 + 생성 ──────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = TOP_K) -> list[str]:
    client = chromadb.PersistentClient(path=BASELINE_DB_PATH)
    col    = client.get_collection("baseline")
    q_emb  = _embed([query])[0]
    res    = col.query(query_embeddings=[q_emb], n_results=top_k)
    return res["documents"][0] if res["documents"] else []


def generate(query: str, contexts: list[str]) -> str:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model   = genai.GenerativeModel(GEMINI_MODEL)
    context = "\n\n---\n\n".join(contexts)
    prompt  = f"{SYSTEM_PROMPT}\n\n[참고 문서]\n{context}\n\n[질문]\n{query}"
    resp    = model.generate_content(prompt)
    return resp.text


def ask(query: str) -> str:
    contexts = retrieve(query)
    return generate(query, contexts)


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    print("베이스라인 RAG (종료: q)")
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
