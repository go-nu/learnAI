from django.db import models
from django.contrib.auth.hashers import make_password, check_password as _check_password


class Manager(models.Model):
    username   = models.CharField(max_length=50, unique=True)
    password   = models.CharField(max_length=255)
    name       = models.CharField(max_length=50)
    name_en    = models.CharField(max_length=100, blank=True)  # CCTV 얼굴 인식용 영문 이름
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    photo      = models.ImageField(upload_to='managers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return _check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.name})"
