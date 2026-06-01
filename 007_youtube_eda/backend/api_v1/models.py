from django.db import models


class Channel(models.Model):
    """YouTube 채널 정보 — yt-dlp로 수집한 채널 메타데이터"""

    channel_id = models.CharField(max_length=100, primary_key=True, verbose_name='채널 ID')
    channel_url = models.CharField(max_length=300, verbose_name='수집 URL')
    channel_name = models.CharField(max_length=200, verbose_name='채널명')
    subscriber_count = models.BigIntegerField(default=0, verbose_name='구독자 수')
    video_count = models.IntegerField(default=0, verbose_name='수집 영상 수')
    total_view_count = models.BigIntegerField(default=0, verbose_name='채널 전체 조회수')
    description = models.TextField(blank=True, verbose_name='채널 설명')
    thumbnail_url = models.URLField(max_length=500, blank=True, verbose_name='채널 썸네일')
    banner_url    = models.URLField(max_length=1000, blank=True, verbose_name='채널 배너 이미지')
    country = models.CharField(max_length=10, blank=True, verbose_name='국가 코드')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일시')
    fetched_at = models.DateTimeField(auto_now=True, verbose_name='마지막 수집일시')

    class Meta:
        db_table = 'channel'
        verbose_name = '채널'
        verbose_name_plural = '채널 목록'

    def __str__(self):
        return f'{self.channel_name} ({self.channel_id})'


class Video(models.Model):
    """채널에 등록된 영상 메타데이터 — 제목, 게시일, 영상 길이 등 변하지 않는 정보"""

    video_id = models.CharField(max_length=20, primary_key=True, verbose_name='영상 ID')
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE,
        related_name='videos', verbose_name='채널'
    )
    title = models.CharField(max_length=500, verbose_name='영상 제목')
    description = models.TextField(blank=True, verbose_name='영상 설명')
    published_at = models.DateField(null=True, blank=True, verbose_name='게시일')
    duration_seconds = models.IntegerField(default=0, verbose_name='영상 길이(초)')
    # yt-dlp duration은 이미 초 단위 정수 — ISO 8601 파싱 불필요
    is_short = models.BooleanField(default=False, verbose_name='Shorts 여부')
    # duration_seconds <= 60 이면 YouTube Shorts로 분류
    thumbnail_url = models.URLField(max_length=500, blank=True, verbose_name='썸네일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일시')
    fetched_at = models.DateTimeField(auto_now=True, verbose_name='마지막 수집일시')

    class Meta:
        db_table = 'video'
        verbose_name = '영상'
        verbose_name_plural = '영상 목록'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['channel', 'published_at']),
        ]

    def __str__(self):
        return f'{self.title} ({self.video_id})'

    def save(self, *args, **kwargs):
        self.is_short = self.duration_seconds <= 60
        super().save(*args, **kwargs)


class VideoStats(models.Model):
    """영상 통계 — 조회수, 좋아요, 댓글 등 시간에 따라 변하는 수치 (현재값)"""

    video = models.OneToOneField(
        Video, on_delete=models.CASCADE,
        related_name='stats', primary_key=True, verbose_name='영상'
    )
    view_count = models.BigIntegerField(default=0, verbose_name='조회수')
    like_count = models.IntegerField(default=0, verbose_name='좋아요 수')
    comment_count = models.IntegerField(default=0, verbose_name='댓글 수')
    # like_count / comment_count: 채널 운영자가 비공개 시 None → 0으로 저장
    updated_at = models.DateTimeField(auto_now=True, verbose_name='업데이트일시')

    class Meta:
        db_table = 'video_stats'
        verbose_name = '영상 통계'
        verbose_name_plural = '영상 통계 목록'

    def __str__(self):
        return f'{self.video_id} — 조회수 {self.view_count:,}'


# ── EDA 분석용 추가 테이블 ─────────────────────────────────────────────────────

class VideoStatsSnapshot(models.Model):
    """영상 통계 스냅샷 — 수집할 때마다 기록, 시계열 EDA(성장 추이 분석)에 활용"""

    video = models.ForeignKey(
        Video, on_delete=models.CASCADE,
        related_name='snapshots', verbose_name='영상'
    )
    view_count = models.BigIntegerField(default=0, verbose_name='조회수')
    like_count = models.IntegerField(default=0, verbose_name='좋아요 수')
    comment_count = models.IntegerField(default=0, verbose_name='댓글 수')
    snapshot_at = models.DateTimeField(auto_now_add=True, verbose_name='스냅샷 일시')

    class Meta:
        db_table = 'video_stats_snapshot'
        verbose_name = '영상 통계 스냅샷'
        verbose_name_plural = '영상 통계 스냅샷 목록'
        ordering = ['snapshot_at']
        indexes = [
            models.Index(fields=['video', 'snapshot_at']),
        ]

    def __str__(self):
        return f'{self.video_id} @ {self.snapshot_at:%Y-%m-%d %H:%M}'


class Tag(models.Model):
    """영상 태그 — yt-dlp info["tags"] 에서 추출, 태그별 성과 EDA에 활용"""

    name = models.CharField(max_length=100, unique=True, verbose_name='태그명')

    class Meta:
        db_table = 'tag'
        verbose_name = '태그'
        verbose_name_plural = '태그 목록'

    def __str__(self):
        return self.name


class VideoTag(models.Model):
    """영상-태그 매핑 — 어떤 태그가 높은 조회수와 상관관계가 있는지 EDA 분석"""

    video = models.ForeignKey(
        Video, on_delete=models.CASCADE,
        related_name='video_tags', verbose_name='영상'
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,
        related_name='video_tags', verbose_name='태그'
    )

    class Meta:
        db_table = 'video_tag'
        verbose_name = '영상 태그'
        verbose_name_plural = '영상 태그 목록'
        unique_together = ('video', 'tag')

    def __str__(self):
        return f'{self.video_id} — #{self.tag.name}'


class AiAnalysisReport(models.Model):
    """AI 분석 리포트 — Gemini가 생성한 채널 분석 결과를 채널별로 기록"""

    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE,
        related_name='ai_reports', verbose_name='채널'
    )
    summary = models.TextField(verbose_name='AI 종합 요약')
    insights = models.JSONField(verbose_name='AI 인사이트 (JSON)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'ai_analysis_report'
        verbose_name = 'AI 분석 리포트'
        verbose_name_plural = 'AI 분석 리포트 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.channel.channel_name} — AI 분석 {self.created_at:%Y-%m-%d %H:%M}'


class CollectionLog(models.Model):
    """수집 작업 로그 — 채널별 수집 진행 상태 추적, 오류 기록"""

    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        (STATUS_PENDING, '대기'),
        (STATUS_RUNNING, '수집중'),
        (STATUS_DONE, '완료'),
        (STATUS_ERROR, '오류'),
    ]

    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE,
        related_name='collection_logs', verbose_name='채널'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default=STATUS_PENDING, verbose_name='상태'
    )
    total_videos = models.IntegerField(default=0, verbose_name='전체 영상 수')
    collected_videos = models.IntegerField(default=0, verbose_name='수집 완료 수')
    error_message = models.TextField(blank=True, verbose_name='오류 메시지')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='시작일시')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='완료일시')

    class Meta:
        db_table = 'collection_log'
        verbose_name = '수집 로그'
        verbose_name_plural = '수집 로그 목록'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.channel.channel_name} — {self.get_status_display()} ({self.started_at:%Y-%m-%d %H:%M})'
