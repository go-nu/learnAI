import threading
import time

from django.conf import settings
from django.db import connection
from django.db.models import Count, Prefetch
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Product, Review, ReviewTag
from .serializers import (
    ProductDetailSerializer,
    ProductSerializer,
    ReviewCreateSerializer,
    ReviewDetailSerializer,
    ReviewSerializer,
)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


def _run_pipeline(review_id: int):
    delay = getattr(settings, "REPLY_DELAY_MINUTES", 10) * 60
    time.sleep(delay)
    try:
        from pipeline.graph import build_graph
        graph = build_graph()
        graph.invoke({
            "review_id": review_id,
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
    finally:
        connection.close()


# 상품 목록
class ProductListView(ListAPIView):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


# 상품 상세 + 리뷰 목록
class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        reviews_qs = Review.objects.select_related("user", "reply").order_by("-created_at")
        return Product.objects.prefetch_related(Prefetch("reviews", queryset=reviews_qs))


# 리뷰 등록 (고객)
class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(f"[ReviewCreate] user={request.user} data={request.data}")
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"[ReviewCreate] validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        review = serializer.save(user=request.user)
        print(f"[ReviewCreate] saved id={review.id} product_id={review.product_id} user_id={review.user_id}")

        thread = threading.Thread(target=_run_pipeline, args=(review.id,), daemon=True)
        thread.start()

        return Response({"message": "리뷰가 등록되었습니다.", "id": review.id}, status=status.HTTP_201_CREATED)


# 리뷰 목록 (관리자)
class ReviewListView(ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = Review.objects.select_related("user", "reply").order_by("-created_at")
        emotion = self.request.query_params.get("emotion")
        status_filter = self.request.query_params.get("status")
        if emotion:
            qs = qs.filter(emotion_label=emotion)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# 리뷰 상세 (관리자)
class ReviewDetailView(RetrieveAPIView):
    queryset = Review.objects.select_related("user", "reply").prefetch_related("tags")
    serializer_class = ReviewDetailSerializer
    permission_classes = [IsAdminRole]


# 대시보드 (관리자)
class DashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        emotion_stats = (
            Review.objects.exclude(emotion_label=None)
            .values("emotion_label")
            .annotate(count=Count("id"))
        )
        status_stats = Review.objects.values("status").annotate(count=Count("id"))
        recent_reviews = ReviewSerializer(
            Review.objects.select_related("user", "reply").order_by("-created_at")[:10],
            many=True,
        ).data

        return Response({
            "emotion_stats": list(emotion_stats),
            "status_stats": list(status_stats),
            "recent_reviews": recent_reviews,
        })


# 키워드 TOP N (관리자)
class InsightTagsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        tags = (
            ReviewTag.objects.values("tag")
            .annotate(count=Count("id"))
            .order_by("-count")[:limit]
        )
        return Response(list(tags))


# 구글 OAuth 완료 후 JWT 발급 → 프론트엔드로 리디렉트
class GoogleLoginCompleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect(f"{settings.FRONTEND_URL}/login?error=auth_failed")

        refresh = RefreshToken.for_user(request.user)
        refresh["role"] = request.user.role
        refresh["name"] = request.user.name

        params = f"access={str(refresh.access_token)}&refresh={str(refresh)}"
        return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")
