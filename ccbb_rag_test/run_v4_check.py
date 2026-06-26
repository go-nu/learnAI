"""
baseline_v4.py 단독 실행 — 수정요소 섹션 확인용
각 질문에 대해 id와 "3. 수정요소 적용" 섹션만 출력한다.

실행:
  uv run run_v4_check.py
"""

import json
import re
import sys
import time

BENCHMARK_FILE = "./benchmark_data_modified.json"

_SECTION_RE = re.compile(
    r'(?:##\s*)?3\.\s*수정요소\s*적용.*?(?=(?:##\s*)?4\.|$)',
    re.DOTALL,
)


def extract_section3(text: str) -> str:
    m = _SECTION_RE.search(text)
    return m.group(0).strip() if m else "(섹션 없음)"


def main():
    print("baseline_v4 모듈 로드 중...")
    from baseline_v4 import ask

    with open(BENCHMARK_FILE, encoding="utf-8") as f:
        data = json.load(f)

    sep = "=" * 70

    for item in data:
        id_   = item["id"]
        query = item["query"]
        gt_a  = item["gt_final_ratio_a"]
        gt_b  = item["gt_final_ratio_b"]

        print(f"\n{sep}")
        print(f"[{id_}]  정답: A {gt_a}% : B {gt_b}%")
        print(sep)

        try:
            resp    = ask(query)
            section = extract_section3(resp)
            if section == "(섹션 없음)":
                print("[디버그] 원본 응답:")
                print(resp)
            else:
                print(section)
        except Exception as e:
            print(f"오류: {e}", file=sys.stderr)
            print(f"오류 발생 ({type(e).__name__})")

        time.sleep(1)

    print(f"\n{sep}")
    print("완료")


if __name__ == "__main__":
    main()
