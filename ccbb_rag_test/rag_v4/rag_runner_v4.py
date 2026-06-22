import sys

from dotenv import load_dotenv

from .rag_core_v4 import RagBgeM3


# CLI 진입점 — DB 로드 또는 자동 빌드 후 질의응답 루프 실행
def main():
    load_dotenv()

    # --source 옵션으로 소스 디렉토리 오버라이드
    source_dir = None
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        if idx + 1 < len(sys.argv):
            source_dir = sys.argv[idx + 1]

    rag = RagBgeM3(source_dir=source_dir) if source_dir else RagBgeM3()

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
    print("  교통사고 과실비율 / 도로교통법 RAG 질의응답  (q: 종료)")
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
