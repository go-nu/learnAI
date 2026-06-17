from pipeline.state import ReplyState


def review_reply(state: ReplyState, llm) -> dict:
    # 품질 판단은 check_bad_reply 라우터가 reply_text를 직접 확인
    # 이 노드는 retry_count만 증가시켜 라우터가 횟수 초과를 판단하게 함
    return {"retry_count": state["retry_count"] + 1}


def check_bad_reply(state: ReplyState) -> str:
    # review_reply를 거칠 때마다 retry_count가 +1됨
    # 2회 이상이면 품질 무관하게 check_result로 강제 통과
    if state["retry_count"] >= 2:
        return "check_result"
    if len(state["reply_text"].strip()) >= 50:
        return "check_result"
    return "bad_reply"


def check_result(state: ReplyState) -> dict:
    # 최종 품질 판단은 last_check 라우터가 담당
    return {}


def last_check(state: ReplyState) -> str:
    # regenerate_reply를 거칠 때마다 regenerate_count가 +1됨
    # 2회 이상이면 품질 무관하게 save_result로 강제 통과
    if state["regenerate_count"] >= 2:
        return "save_result"
    if len(state["reply_text"].strip()) >= 30:
        return "save_result"
    return "regenerate_reply"