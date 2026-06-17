from pipeline.state import ReplyState
from reviews.models import Review, ReviewReply, ReviewTag


def save_result(state: ReplyState) -> dict:
    # TODO: Review.objects.get(id=state["review_id"])로 리뷰 조회
    # TODO: review.emotion_label = state["emotion_label"] 업데이트
    # TODO: review.status = "done" 업데이트
    # TODO: ReviewReply.objects.create(review=review, reply_text=state["reply_text"])
    # TODO: state["tags"] 순회 → ReviewTag.objects.create(review=review, tag=tag)
    # TODO: review.save()
    pass
