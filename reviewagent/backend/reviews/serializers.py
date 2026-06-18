from rest_framework import serializers

from .models import Product, Review, ReviewReply, ReviewTag


class ReviewReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReply
        fields = ["id", "reply_text", "created_at"]


class ReviewTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewTag
        fields = ["tag"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category", "description", "created_at"]


class ReviewSummarySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    reply = ReviewReplySerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_name", "text", "rating", "emotion_label", "status", "created_at", "reply"]


class ProductDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "description", "created_at", "reviews"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    reply = ReviewReplySerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_name", "text", "rating", "emotion_label", "status", "created_at", "reply"]


class ReviewDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    reply = ReviewReplySerializer(read_only=True)
    tags = ReviewTagSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_name", "text", "rating", "emotion_label", "status", "created_at", "reply", "tags"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["product", "text", "rating"]

    def create(self, validated_data):
        return Review.objects.create(status="pending", **validated_data)
