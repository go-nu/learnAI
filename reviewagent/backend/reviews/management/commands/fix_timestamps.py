from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import models

from reviews.models import Review, ReviewReply, User, Product

KST_OFFSET = timedelta(hours=9)


class Command(BaseCommand):
    help = "UTC로 저장된 created_at 값을 KST(+9h)로 일괄 보정합니다."

    def handle(self, *args, **options):
        tables = [
            ("users",          User),
            ("products",       Product),
            ("reviews",        Review),
            ("review_replies", ReviewReply),
        ]
        for label, Model in tables:
            updated = Model.objects.all().update(
                created_at=models.ExpressionWrapper(
                    models.F("created_at") + KST_OFFSET,
                    output_field=models.DateTimeField(),
                )
            )
            self.stdout.write(f"  {label}: {updated}건 보정 완료")

        self.stdout.write(self.style.SUCCESS("모든 타임스탬프가 KST로 보정되었습니다."))
