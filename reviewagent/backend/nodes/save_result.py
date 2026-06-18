from pipeline.state import ReplyState
from reviews.models import Review, ReviewReply, ReviewTag


# 최종 답변 저장
def save_result(state: ReplyState) -> dict:
    review = Review.objects.get(id=state["review_id"])

    review.emotion_label = state["emotion_label"]
    review.status = "done"
    review.save()

    ReviewReply.objects.create(review=review, reply_text=state["reply_text"])

    for tag in state["tags"]:
        ReviewTag.objects.create(review=review, tag=tag)

    return {}
