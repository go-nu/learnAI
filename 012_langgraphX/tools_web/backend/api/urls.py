from django.urls import path
from . import views

urlpatterns = [
    path('text2img/', views.Text2ImgView.as_view(), name='text2img'),
    path('img2img/', views.Img2ImgView.as_view(), name='img2img'),
    path('images/', views.ImagesView.as_view(), name='images'),
]
