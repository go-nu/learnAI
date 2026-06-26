"""
baseline.py 단독 실행 — 최종 과실비율 확인용
각 질문에 대해 id와 "최종 과실비율" 라인만 출력한다.

실행:
  uv run run_bline_check.py
"""

import json
import re
import sys
import time

BENCHMARK_FILE = "./benchmark_data_modified.json"

_RATIO_RE = re.compile(r'최종\s*과실비율\s*:\s*A\s*\d+\s*%\s*:\s*B\s*\d+\s*%')


def extract_ratio_line(text: str) -> str:
    m = _RATIO_RE.search(text)
    return m.group(0).strip() if m else "(최종 과실비율 없음)"


def main():
    print("baseline 모듈 로드 중...")
    from baseline import ask

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
            resp = ask(query)
            print(extract_ratio_line(resp))
        except Exception as e:
            print(f"오류 발생 ({type(e).__name__})", file=sys.stderr)
            print(f"오류: {e}")

        time.sleep(1)

    print(f"\n{sep}")
    print("완료")


if __name__ == "__main__":
    main()
