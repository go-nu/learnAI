from django.urls import path
from . import views

urlpatterns = [
    path('',            views.index,      name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('status/',     views.status,     name='cctv_status'),
    path('full_log/',   views.full_log,   name='cctv_full_log'),
]
