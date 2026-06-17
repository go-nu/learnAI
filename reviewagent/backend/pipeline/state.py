from typing import TypedDict


class ReplyState(TypedDict):
    review_id: int
    text: str  # 리뷰
    rating: int  # 평점
    emotion_label: str  # good / normal / bad
    reply_text: str  # 리뷰 답변
    tags: list[str]  # 키워드 리스트

    retry_count: int  # review_reply 노드에서 재생성 횟수
    regenerate_count: int  # regenerate_reply 노드에서 재생성 횟수
