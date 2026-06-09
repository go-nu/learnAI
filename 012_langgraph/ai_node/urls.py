from django.urls import path
from . import views

urlpatterns = [
    path("",              views.ai_node_view, name="ai_node"),
    path("api/generate/", views.api_generate, name="ai_node_api_generate"),
]
