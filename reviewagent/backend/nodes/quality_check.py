from pipeline.state import ReplyState
from nodes.utils import get_text

# bad_reply 검토 -> pass, fail
def review_reply(state: ReplyState, llm) -> dict:
    prompt = f"""아래 쇼핑몰 부정 리뷰에 대한 판매자 답변을 평가하세요.

리뷰: {state["text"]}
답변: {state["reply_text"]}

평가 기준 (3가지 모두 충족해야 통과):
1. 공감: 고객의 불만을 이해하고 있는가
2. 사과: 진심 어린 사과가 담겨 있는가
3. 해결책: 구체적인 해결 의지나 방안이 있는가

"pass" 또는 "fail" 중 하나만 답하세요."""

    response = llm.invoke(prompt)
    raw = get_text(response).strip().lower()
    print(f"[review_reply] LLM 원문: {raw!r} → {'PASS' if raw == 'pass' else 'FAIL'}")
    quality_pass = raw == "pass"

    return {
        "bad_reply_quality_pass": quality_pass,
        "retry_count": state["retry_count"] + 1,
    }


# 무한 루프 방지
def check_bad_reply(state: ReplyState) -> str:
    if state["retry_count"] >= 2:
        return "check_result"
    if state["bad_reply_quality_pass"]:
        return "check_result"
    return "bad_reply"

# 최종 답변 검토
def check_result(state: ReplyState, llm) -> dict:
    prompt = f"""아래 쇼핑몰 리뷰에 대한 판매자 답변을 평가하세요.

리뷰: {state["text"]}
답변: {state["reply_text"]}

평가 기준 (모두 충족해야 통과):
1. 자연스러운 문장인가
2. 리뷰 내용과 연관된 답변인가
3. 고객에게 도움이 되는가

"pass" 또는 "fail" 중 하나만 답하세요."""

    response = llm.invoke(prompt)
    raw = get_text(response).strip().lower()
    print(f"[check_result] LLM 원문: {raw!r} → {'PASS' if raw == 'pass' else 'FAIL'}")
    quality_pass = raw == "pass"

    return {"final_quality_pass": quality_pass}


# 무한 루프 방지
def last_check(state: ReplyState) -> str:
    if state["regenerate_count"] >= 2:
        return "save_result"
    if state["final_quality_pass"]:
        return "save_result"
    return "regenerate_reply"