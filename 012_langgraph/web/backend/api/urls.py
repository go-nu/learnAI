from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.GenerateView.as_view(), name='generate'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('images/', views.ImagesView.as_view(), name='images'),
]
