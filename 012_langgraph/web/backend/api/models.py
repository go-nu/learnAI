from django.db import models


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', '사용자'), ('assistant', '어시스턴트')]
    TYPE_CHOICES = [('text', '텍스트'), ('image', '이미지')]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"
