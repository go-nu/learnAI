from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_search, name='index'),
    path('api/generate/', views.api_generate, name='api_generate'),
    path('api/images/', views.api_images, name='api_images'),
]
