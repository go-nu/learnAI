import traceback

from django.core.management.base import BaseCommand
from reviews.models import Review


class Command(BaseCommand):
    help = "pending 리뷰에 대해 LangGraph 파이프라인을 즉시 실행합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="처리할 리뷰 수 (기본값: 10)",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        reviews = Review.objects.filter(status="pending").order_by("-created_at")[:limit]

        if not reviews:
            self.stdout.write(self.style.WARNING("처리할 pending 리뷰가 없습니다."))
            return

        self.stdout.write(f"총 {reviews.count()}건 파이프라인 실행 시작...")

        from pipeline.graph import build_graph
        graph = build_graph()

        for review in reviews:
            self.stdout.write(f"  ▶ review #{review.id} 처리 중...", ending=" ")
            try:
                graph.invoke({
                    "review_id": review.id,
                    "text": "",
                    "rating": 0,
                    "emotion_label": "",
                    "reply_text": "",
                    "tags": [],
                    "retry_count": 0,
                    "regenerate_count": 0,
                    "bad_reply_quality_pass": False,
                    "final_quality_pass": False,
                })
                self.stdout.write(self.style.SUCCESS("완료"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"실패: {e}"))
                self.stdout.write(traceback.format_exc())

        self.stdout.write(self.style.SUCCESS("파이프라인 실행 완료."))
