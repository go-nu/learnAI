"""
벤치마크 평가 스크립트
benchmark_data_modified.json의 20개 질문을 baseline / baseline_v4에 묻고
최종 과실비율을 파싱하여 정답(1) / 오답(0)으로 채점한다.

실행:
  uv run evaluate.py
  uv run evaluate.py --save   # 결과를 evaluate_results.json 에도 저장
"""

import argparse
import json
import re
import sys
import time

BENCHMARK_FILE = "./benchmark_data_modified.json"
RESULT_FILE    = "./evaluate_results.json"


# ── 파싱 ────────────────────────────────────────────────────────────────
_RATIO_RE = re.compile(
    r'최종\s*과실비율\s*:\s*A\s*(\d+)\s*%\s*:\s*B\s*(\d+)\s*%'
)

def parse_ratio(text: str) -> tuple[int, int] | None:
    m = _RATIO_RE.search(text)
    return (int(m.group(1)), int(m.group(2))) if m else None

def score(pred: tuple[int, int] | None, gt_a: int, gt_b: int) -> int:
    return 1 if pred == (gt_a, gt_b) else 0


# ── 메인 ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="결과를 JSON 파일로 저장")
    args = parser.parse_args()

    print("baseline / baseline_v4 모듈 로드 중...")
    from baseline    import ask as baseline_ask
    from baseline_v4 import ask as v4_ask

    with open(BENCHMARK_FILE, encoding="utf-8") as f:
        data = json.load(f)

    col_w = {"id": 10, "ans": 16, "b_ratio": 18, "b_sc": 4, "v_ratio": 18, "v_sc": 4}
    header = (
        f"{'ID':<{col_w['id']}} "
        f"{'정답':^{col_w['ans']}} "
        f"{'Baseline 비율':^{col_w['b_ratio']}} {'점':^{col_w['b_sc']}} "
        f"{'V4 비율':^{col_w['v_ratio']}} {'점':^{col_w['v_sc']}}"
    )
    sep = "─" * len(header)

    print()
    print(header)
    print(sep)

    records = []
    baseline_total = v4_total = 0

    for item in data:
        id_   = item["id"]
        query = item["query"]
        gt_a  = item["gt_final_ratio_a"]
        gt_b  = item["gt_final_ratio_b"]
        gt_str = f"A {gt_a}% : B {gt_b}%"

        # ── Baseline ──
        try:
            b_resp  = baseline_ask(query)
            b_ratio = parse_ratio(b_resp)
            b_sc    = score(b_ratio, gt_a, gt_b)
            b_str   = f"A {b_ratio[0]}% : B {b_ratio[1]}%" if b_ratio else "파싱 실패"
        except Exception as e:
            b_resp = b_ratio = None
            b_sc   = 0
            b_str  = f"오류({type(e).__name__})"
            print(f"\n  [Baseline 오류] {e}", file=sys.stderr)

        time.sleep(1)

        # ── V4 ──
        try:
            v4_resp  = v4_ask(query)
            v4_ratio = parse_ratio(v4_resp)
            v4_sc    = score(v4_ratio, gt_a, gt_b)
            v4_str   = f"A {v4_ratio[0]}% : B {v4_ratio[1]}%" if v4_ratio else "파싱 실패"
        except Exception as e:
            v4_resp = v4_ratio = None
            v4_sc   = 0
            v4_str  = f"오류({type(e).__name__})"
            print(f"\n  [V4 오류] {e}", file=sys.stderr)

        time.sleep(1)

        baseline_total += b_sc
        v4_total       += v4_sc

        row = (
            f"{id_:<{col_w['id']}} "
            f"{gt_str:^{col_w['ans']}} "
            f"{b_str:^{col_w['b_ratio']}} {b_sc:^{col_w['b_sc']}} "
            f"{v4_str:^{col_w['v_ratio']}} {v4_sc:^{col_w['v_sc']}}"
        )
        print(row)

        records.append({
            "id":            id_,
            "gt_ratio":      gt_str,
            "baseline_ratio": b_str,
            "baseline_score": b_sc,
            "v4_ratio":      v4_str,
            "v4_score":      v4_sc,
            "baseline_response": b_resp,
            "v4_response":   v4_resp,
        })

    n = len(data)
    print(sep)
    summary_b  = f"{baseline_total}/{n} ({baseline_total/n:.0%})"
    summary_v4 = f"{v4_total}/{n} ({v4_total/n:.0%})"
    print(
        f"{'합계':<{col_w['id']}} "
        f"{'':<{col_w['ans']}} "
        f"{summary_b:^{col_w['b_ratio']}} {' ':^{col_w['b_sc']}} "
        f"{summary_v4:^{col_w['v_ratio']}}"
    )

    if args.save:
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장 → {RESULT_FILE}")


if __name__ == "__main__":
    main()
