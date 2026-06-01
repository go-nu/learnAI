import uuid
from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    """채팅 세션 - 하나의 대화 흐름을 묶는 단위"""
    session_id  = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='세션 UUID')
    user        = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_sessions',
        verbose_name='사용자',
    )
    username    = models.CharField(max_length=150, blank=True, verbose_name='사용자명')
    chat_model  = models.CharField(max_length=100, default='rag-bge-m3', verbose_name='채팅 모델')
    title       = models.CharField(max_length=200, blank=True, verbose_name='제목')
    client_ip   = models.GenericIPAddressField(null=True, blank=True, verbose_name='접속 IP')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at  = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table            = 'chat_session'
        ordering            = ['-created_at']
        verbose_name        = '채팅 세션'
        verbose_name_plural = '채팅 세션'

    def __str__(self):
        return f"[{self.session_id}] {self.title or '제목 없음'}"

    def get_message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """채팅 메시지 - Q&A 한 쌍"""
    message_id      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='메시지 UUID')
    session         = models.ForeignKey(
        ChatSession, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='messages',
        verbose_name='세션',
    )
    chat_model      = models.CharField(max_length=100, default='rag-bge-m3', verbose_name='채팅 모델(RAG모델)')
    user            = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_messages',
        verbose_name='사용자',
    )
    username        = models.CharField(max_length=150, blank=True, verbose_name='사용자명')  # 계정 삭제 후에도 보존
    question        = models.TextField(verbose_name='사용자 질문')
    answer          = models.TextField(blank=True, verbose_name='AI 답변')
    input_tokens    = models.PositiveIntegerField(default=0, verbose_name='입력 토큰')
    output_tokens   = models.PositiveIntegerField(default=0, verbose_name='출력 토큰')
    total_tokens    = models.PositiveIntegerField(default=0, verbose_name='사용 토큰(합계)')
    response_ms     = models.PositiveIntegerField(default=0, verbose_name='응답 시간(ms)')
    rag_sources     = models.JSONField(default=list, blank=True, verbose_name='RAG 참조 문서')
    is_error        = models.BooleanField(default=False, verbose_name='오류 여부')
    client_ip       = models.GenericIPAddressField(null=True, blank=True, verbose_name='생성 IP')
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table            = 'chat_message'
        ordering            = ['created_at']
        verbose_name        = '채팅 메시지'
        verbose_name_plural = '채팅 메시지'

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '-'
        return f"[{ts}] {self.username}: {self.question[:60]}"


class LoginLog(models.Model):
    """로그인/로그아웃/실패 이력"""
    ACTION_LOGIN  = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_FAIL   = 'fail'
    ACTION_CHOICES = [
        (ACTION_LOGIN,  '로그인'),
        (ACTION_LOGOUT, '로그아웃'),
        (ACTION_FAIL,   '로그인 실패'),
    ]

    user        = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='login_logs',
        verbose_name='사용자',
    )
    username    = models.CharField(max_length=150, blank=True, verbose_name='사용자명')
    email       = models.EmailField(blank=True, verbose_name='이메일')
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='액션')
    client_ip   = models.GenericIPAddressField(null=True, blank=True, verbose_name='접속 IP')
    user_agent  = models.CharField(max_length=300, blank=True, verbose_name='User Agent')
    is_admin    = models.BooleanField(default=False, verbose_name='관리자 여부')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table            = 'login_log'
        ordering            = ['-created_at']
        verbose_name        = '로그인 로그'
        verbose_name_plural = '로그인 로그'

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '-'
        return f"[{ts}] {self.username} - {self.get_action_display()}"


class ChatFeedback(models.Model):
    """AI 응답에 대한 사용자 피드백 (좋아요/나빠요·코멘트)"""
    RATING_GOOD = 'good'
    RATING_BAD  = 'bad'
    RATING_CHOICES = [
        (RATING_GOOD, '좋아요'),
        (RATING_BAD,  '나빠요'),
    ]

    message     = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name='메시지',
    )
    rating      = models.CharField(max_length=10, choices=RATING_CHOICES, verbose_name='평점')
    comment     = models.TextField(blank=True, verbose_name='코멘트')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table            = 'chat_feedback'
        verbose_name        = '채팅 피드백'
        verbose_name_plural = '채팅 피드백'

    def __str__(self):
        return f"[{self.rating}] {self.message_id}"


class RagConfig(models.Model):
    """RAG 설정 - 문서 인덱스 빌드 단위"""
    STATUS_PENDING    = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_READY      = 'ready'
    STATUS_ERROR      = 'error'
    STATUS_DISABLED   = 'disabled'
    STATUS_CHOICES = [
        (STATUS_PENDING,    '대기 중'),
        (STATUS_PROCESSING, '처리 중'),
        (STATUS_READY,      '준비 완료'),
        (STATUS_ERROR,      '오류'),
        (STATUS_DISABLED,   '비활성'),
    ]

    FILE_TYPE_CHOICES = [
        ('pdf',  'PDF'),
        ('docx', 'Word(docx)'),
        ('txt',  'Text'),
        ('md',   'Markdown'),
        ('csv',  'CSV'),
        ('xlsx', 'Excel'),
        ('html', 'HTML'),
        ('other','기타'),
    ]

    # ── 기본 정보 ──────────────────────────────
    rag_id          = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='RAG UUID')
    name            = models.CharField(max_length=200, verbose_name='RAG명')
    description     = models.TextField(blank=True, verbose_name='설명')
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=STATUS_PENDING, verbose_name='상태',
    )

    # ── 파일 ───────────────────────────────────
    source_file_path = models.CharField(max_length=1000, verbose_name='원본 파일 경로')
    source_file_name = models.CharField(max_length=255, blank=True, verbose_name='원본 파일명')
    source_file_size = models.PositiveBigIntegerField(default=0, verbose_name='파일 크기(bytes)')
    source_file_type = models.CharField(
        max_length=10, choices=FILE_TYPE_CHOICES,
        default='other', verbose_name='파일 유형',
    )
    result_file_path = models.CharField(max_length=1000, blank=True, verbose_name='RAG 결과 파일 경로')

    # ── 임베딩 / 모델 설정 ─────────────────────
    embedding_model = models.CharField(max_length=100, default='BAAI/bge-m3', verbose_name='임베딩 모델')
    llm_model       = models.CharField(max_length=100, default='gemini-2.5-flash', verbose_name='LLM 모델')
    chunk_size      = models.PositiveIntegerField(default=512, verbose_name='청크 크기')
    chunk_overlap   = models.PositiveIntegerField(default=50,  verbose_name='청크 오버랩')
    top_k           = models.PositiveIntegerField(default=5,   verbose_name='검색 Top-K')

    # ── 빌드 결과 통계 ──────────────────────────
    chunk_count     = models.PositiveIntegerField(default=0, verbose_name='청크 수')
    total_tokens    = models.PositiveBigIntegerField(default=0, verbose_name='총 토큰 수')
    build_time_ms   = models.PositiveIntegerField(default=0, verbose_name='빌드 소요 시간(ms)')
    error_message   = models.TextField(blank=True, verbose_name='오류 메시지')

    # ── 관리 ───────────────────────────────────
    created_by      = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='rag_configs',
        verbose_name='생성자',
    )
    client_ip       = models.GenericIPAddressField(null=True, blank=True, verbose_name='생성 IP')
    is_active       = models.BooleanField(default=True, verbose_name='활성 여부')
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at      = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table            = 'rag_config'
        ordering            = ['-created_at']
        verbose_name        = 'RAG 설정'
        verbose_name_plural = 'RAG 설정'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.name}"

    def source_file_size_display(self):
        size = self.source_file_size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
