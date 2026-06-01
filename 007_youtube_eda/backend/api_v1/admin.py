from django.contrib import admin

from .models import (
    Channel, Video, VideoStats,
    VideoStatsSnapshot, Tag, VideoTag, CollectionLog,
)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_name', 'channel_id', 'subscriber_count', 'video_count', 'fetched_at')
    search_fields = ('channel_name', 'channel_id')
    readonly_fields = ('created_at', 'fetched_at')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'published_at', 'duration_seconds', 'is_short')
    list_filter = ('channel', 'is_short')
    search_fields = ('title', 'video_id')
    readonly_fields = ('created_at', 'fetched_at')


@admin.register(VideoStats)
class VideoStatsAdmin(admin.ModelAdmin):
    list_display = ('video', 'view_count', 'like_count', 'comment_count', 'updated_at')
    readonly_fields = ('updated_at',)


@admin.register(VideoStatsSnapshot)
class VideoStatsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('video', 'view_count', 'like_count', 'comment_count', 'snapshot_at')
    list_filter = ('snapshot_at',)
    readonly_fields = ('snapshot_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(VideoTag)
class VideoTagAdmin(admin.ModelAdmin):
    list_display = ('video', 'tag')
    list_filter = ('tag',)


@admin.register(CollectionLog)
class CollectionLogAdmin(admin.ModelAdmin):
    list_display = ('channel', 'status', 'total_videos', 'collected_videos', 'started_at', 'finished_at')
    list_filter = ('status', 'channel')
    readonly_fields = ('started_at',)
