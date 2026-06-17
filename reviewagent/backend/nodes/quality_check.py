from pipeline.state import ReplyState


def review_reply(state: ReplyState, llm) -> dict:
    # TODO: bad_reply 결과물(reply_text) 품질 검사
    # TODO: 통과 기준 예시 — 50자 이상, 공감/사과/해결책 포함 여부
    # TODO: retry_count 1 증가 후 반환 (라우터가 횟수 판단)
    pass


def check_bad_reply(state: ReplyState) -> str:
    # TODO: retry_count >= 1 이면 → "check_result" (횟수 초과, 그냥 통과)
    # TODO: 품질 통과 시                → "check_result"
    # TODO: 품질 미달 시                → "bad_reply"
    pass
