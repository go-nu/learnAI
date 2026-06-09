from django.contrib import admin
from .models import GenerationRecord


@admin.register(GenerationRecord)
class GenerationRecordAdmin(admin.ModelAdmin):
    list_display = ('mode', 'prompt', 'denoise', 'created_at')
    list_filter = ('mode',)
    search_fields = ('prompt',)
