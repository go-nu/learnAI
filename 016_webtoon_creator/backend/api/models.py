"""
ToonCraft 데이터베이스 모델 정의
- User: 사용자 (커스텀 AbstractUser)
- Webtoon: 웹툰 작품
- WebtoonEpisode: 웹툰 에피소드
- WebtoonCut: 웹툰 컷 (개별 패널)
- GeneratedImage: AI 생성 이미지 이력
"""

import os
import uuid as uuid_module
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models


# 날짜 기반 파일 업로드 경로 헬퍼
def upload_to_date_path(instance, filename):
    today = date.today()
    return os.path.join(
        'upload',
        str(today.year),
        f'{today.month:02d}',
        f'{today.day:02d}',
        filename
    )


# 웹툰 커버 이미지 업로드 경로 헬퍼 (/media/webtoon/{uuid}/{filename})
def upload_webtoon_cover(instance, filename):
    return f'webtoon/{uuid_module.uuid4()}/{filename}'


# ────────────────────────────────────────────────
# 사용자 모델 (Django AbstractUser 확장)
# ────────────────────────────────────────────────
class User(AbstractUser):
    """사용자 계정 모델"""

    nickname = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='닉네임'
    )
    profile_image = models.ImageField(
        upload_to=upload_to_date_path,
        blank=True,
        null=True,
        verbose_name='프로필 이미지'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return self.username


# ────────────────────────────────────────────────
# 웹툰 작품 모델
# ────────────────────────────────────────────────
class Webtoon(models.Model):
    """웹툰 작품 모델"""

    GENRE_CHOICES = [
        ('romance', '로맨스'),
        ('action', '액션'),
        ('fantasy', '판타지'),
        ('comedy', '개그'),
        ('horror', '공포'),
        ('drama', '드라마'),
        ('daily', '일상'),
        ('sports', '스포츠'),
        ('etc', '기타'),
    ]

    STATUS_CHOICES = [
        ('draft', '초안'),
        ('ongoing', '연재 중'),
        ('completed', '완결'),
        ('hiatus', '휴재'),
    ]

    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='webtoons',
        verbose_name='작가'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    genre = models.CharField(
        max_length=20,
        choices=GENRE_CHOICES,
        default='etc',
        verbose_name='장르'
    )
    description = models.TextField(blank=True, verbose_name='작품 설명')
    cover_image = models.ImageField(
        upload_to=upload_webtoon_cover,
        blank=True,
        null=True,
        verbose_name='커버 이미지'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='연재 상태'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        db_table = 'webtoons'
        verbose_name = '웹툰'
        verbose_name_plural = '웹툰 목록'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ────────────────────────────────────────────────
# 웹툰 에피소드 모델
# ────────────────────────────────────────────────
class WebtoonEpisode(models.Model):
    """웹툰 에피소드(회차) 모델"""

    webtoon = models.ForeignKey(
        Webtoon,
        on_delete=models.CASCADE,
        related_name='episodes',
        verbose_name='웹툰'
    )
    episode_number = models.PositiveIntegerField(verbose_name='회차 번호')
    title = models.CharField(max_length=200, verbose_name='에피소드 제목')
    thumbnail = models.ImageField(
        upload_to=upload_to_date_path,
        blank=True,
        null=True,
        verbose_name='썸네일'
    )
    is_published = models.BooleanField(default=False, verbose_name='발행 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='발행일'
    )

    class Meta:
        db_table = 'webtoon_episodes'
        verbose_name = '에피소드'
        verbose_name_plural = '에피소드 목록'
        unique_together = [['webtoon', 'episode_number']]
        ordering = ['episode_number']

    def __str__(self):
        return f'{self.webtoon.title} - {self.episode_number}화 {self.title}'


# ────────────────────────────────────────────────
# 웹툰 컷 모델 (에피소드 내 개별 패널)
# ────────────────────────────────────────────────
class WebtoonCut(models.Model):
    """웹툰 컷(패널) 모델"""

    episode = models.ForeignKey(
        WebtoonEpisode,
        on_delete=models.CASCADE,
        related_name='cuts',
        verbose_name='에피소드'
    )
    order = models.PositiveIntegerField(verbose_name='순서')
    image = models.ImageField(
        upload_to=upload_to_date_path,
        verbose_name='컷 이미지'
    )
    caption = models.TextField(blank=True, verbose_name='대사/캡션')
    # 편집기 상태 저장: 레이아웃, 이미지 offset/scale, 말풍선 목록(위치·크기·회전·텍스트)
    metadata = models.JSONField(blank=True, null=True, verbose_name='편집 메타데이터')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        db_table = 'webtoon_cuts'
        verbose_name = '웹툰 컷'
        verbose_name_plural = '웹툰 컷 목록'
        ordering = ['order']

    def __str__(self):
        return f'{self.episode} - {self.order}번 컷'


# ────────────────────────────────────────────────
# AI 생성 이미지 이력 모델
# ────────────────────────────────────────────────
class GeneratedImage(models.Model):
    """AI 이미지 생성 이력 모델 (Gemini + ComfyUI)"""

    RATIO_CHOICES = [
        ('1:1', '1:1 정방형'),
        ('3:4', '3:4 세로형'),
        ('4:3', '4:3 가로형'),
    ]

    STYLE_CHOICES = [
        ('animation', '애니메이션'),
        ('free', '자유롭게'),
        ('short_cut', '짧은컷'),
        ('realistic', '사실적'),
        ('sketch', '스케치'),
    ]

    STATUS_CHOICES = [
        ('pending', '생성 중'),
        ('completed', '완료'),
        ('failed', '실패'),
    ]

    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_images',
        verbose_name='생성 사용자'
    )
    prompt_kr = models.TextField(verbose_name='입력 묘사 (한국어)')
    prompt_en = models.TextField(blank=True, verbose_name='변환 프롬프트 (영문, Gemini 생성)')
    style = models.CharField(
        max_length=20,
        choices=STYLE_CHOICES,
        blank=True,
        verbose_name='스타일'
    )
    ratio = models.CharField(
        max_length=10,
        choices=RATIO_CHOICES,
        default='3:4',
        verbose_name='비율'
    )
    reference_image = models.ImageField(
        upload_to=upload_to_date_path,
        blank=True,
        null=True,
        verbose_name='참조 이미지'
    )
    result_image = models.ImageField(
        upload_to=upload_to_date_path,
        blank=True,
        null=True,
        verbose_name='생성 결과 이미지'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='생성 상태'
    )
    error_message = models.TextField(blank=True, verbose_name='오류 메시지')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 요청일')

    class Meta:
        db_table = 'generated_images'
        verbose_name = 'AI 생성 이미지'
        verbose_name_plural = 'AI 생성 이미지 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.style} ({self.created_at:%Y-%m-%d %H:%M})'
