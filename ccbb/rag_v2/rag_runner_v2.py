"""
rag_runner_v2.py — 텍스트·표 RAG CLI 실행 스크립트
chroma_text_table DB를 로드 또는 자동 빌드해 질의응답을 실행합니다.

실행 예시
    python -m rag_v2.rag_runner_v2
"""

import sys

from dotenv import load_dotenv

from . import RagBgeM3v2


def main():
    load_dotenv()
    rag = RagBgeM3v2()

    print("=" * 55)
    print("  RAG 컴포넌트 초기화 중 (DB 없으면 자동 빌드)...")
    try:
        retriever = rag.build_rag_components()
    except RuntimeError as e:
        print(f"[오류] {e}")
        sys.exit(1)

    print("  Gemini LLM 초기화 중...")
    try:
        llm = rag.get_llm()
    except EnvironmentError as e:
        print(f"[오류] {e}")
        sys.exit(1)

    print("=" * 55)
    print("  교통사고 과실비율 RAG 질의응답  (q: 종료)")
    print("  * 이미지 원본은 ./data/extracted_images 에서 확인 가능합니다.")
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
