from pipeline.state import ReplyState


def good_reply(state: ReplyState, llm) -> dict:
    # TODO: 프롬프트 구조 — 감사 인사 + 재구매 유도
    # TODO: llm 호출 → reply_text 반환
    pass


def normal_reply(state: ReplyState, llm) -> dict:
    # TODO: 프롬프트 구조 — 감사 인사 + 개선 약속
    # TODO: llm 호출 → reply_text 반환
    pass


def bad_reply(state: ReplyState, llm) -> dict:
    # TODO: 프롬프트 구조 — 공감 + 사과 + 해결책
    # TODO: llm 호출 → reply_text 반환
    # TODO: retry_count를 state에서 읽어 프롬프트에 활용 가능
    pass


def regenerate_reply(state: ReplyState, llm) -> dict:
    # TODO: regenerate_count 1 증가
    # TODO: 기존 reply_text를 참고해 개선된 답변 재생성
    # TODO: llm 호출 → reply_text 반환
    pass
