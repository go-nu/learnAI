from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('role', 'content', 'message_type', 'created_at')
    list_filter = ('role', 'message_type')
