from pipeline.state import ReplyState
from reviews.models import Review


def read_review(state: ReplyState) -> dict:
    review = Review.objects.get(id=state["review_id"])

    review.status = "processing"
    review.save()

    return {
        "text": review.text,
        "rating": review.rating,
    }