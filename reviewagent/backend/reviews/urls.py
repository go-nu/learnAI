from django.urls import path

from . import views

urlpatterns = [
    path("auth/complete/", views.GoogleLoginCompleteView.as_view()),
    path("products/", views.ProductListView.as_view()),
    path("products/<int:pk>/", views.ProductDetailView.as_view()),
    path("reviews/", views.ReviewListView.as_view()),
    path("reviews/create/", views.ReviewCreateView.as_view()),
    path("reviews/<int:pk>/", views.ReviewDetailView.as_view()),
    path("dashboard/", views.DashboardView.as_view()),
    path("insights/tags/", views.InsightTagsView.as_view()),
]
