from typing import TypedDict


class ReplyState(TypedDict):
    review_id: int
    text: str  # 리뷰
    rating: int  # 평점
    emotion_label: str  # good / normal / bad
    reply_text: str  # 리뷰 답변
    tags: list[str]  # 키워드 리스트

    retry_count: int  # bad_reply 재생성 횟수
    regenerate_count: int  # 최종 답변 재생성 횟수
    bad_reply_quality_pass: bool  # bad_reply 검토
    final_quality_pass: bool      # 최종 답변 검토
