# CLAUDE.md — YouTube 채널 & 영상 분석 웹서비스

## 프로젝트 개요

YouTube 채널 정보(구독자 수, 동영상 수)와 채널에 등록된 영상 데이터(조회수, 영상 시간, 댓글 수 등)를
**API 키 없이** `yt-dlp`로 수집하고, 수집된 데이터를 EDA(탐색적 데이터 분석)하여 시각화 그래프로 제공하는 웹서비스.

---

## 현재 구현 상태 (2026-05-16 기준)

| 항목 | 상태 | 비고 |
|------|------|------|
| DB 모델 설계 | ✅ 완료 | 7개 테이블, MariaDB 적용 |
| Django 마이그레이션 | ✅ 완료 | `0001_initial` 적용됨 |
| 대시보드 UI (디자인) | ✅ 완료 | `/dashboard/main` 페이지 |
| 왼쪽 사이드바 | ✅ 완료 | `Sidebar.tsx` |
| 상단 헤더 | ✅ 완료 | `Header.tsx` (SweetAlert2 팝업 포함) |
| YouTube 데이터 수집 로직 | ⬜ 미구현 | `youtube_service.py` 작성 예정 |
| DRF 시리얼라이저 | ⬜ 미구현 | `serializers.py` 작성 예정 |
| DRF API 뷰 / URL | ⬜ 미구현 | `views.py`, `urls.py` 작성 예정 |
| EDA 분석 로직 | ⬜ 미구현 | `eda_service.py` 작성 예정 |
| 프론트 ↔ 백엔드 연동 | ⬜ 미구현 | 목업 데이터 → 실제 API 교체 예정 |

---

## 실제 기술 스택

### 백엔드
| 역할 | 라이브러리 | 실제 버전 |
|------|-----------|----------|
| 웹 프레임워크 | `Django` + `Django REST Framework` | Django 5.2.12 |
| YouTube 수집 (핵심) | `yt-dlp` | 최신 (API 키 불필요) |
| YouTube 영상 목록 | `scrapetube` | 최신 |
| YouTube InnerTube | `tubescrape` | 최신 |
| 데이터 처리 | `pandas`, `numpy` | 최신 |
| 서버사이드 시각화 | `matplotlib`, `seaborn`, `plotly` | 최신 |
| HTTP 요청 | `requests`, `httpx` | 최신 |
| HTML 파싱 | `beautifulsoup4` | 최신 |
| DB 드라이버 | `pymysql` | 최신 (MySQLdb 호환 패치 적용) |
| 데이터베이스 | `MariaDB` | 192.168.0.12:3306 |

### 프론트엔드
| 역할 | 라이브러리 | 실제 버전 |
|------|-----------|----------|
| UI 프레임워크 | `Next.js` (App Router) | **16.2.6** |
| 런타임 | `React` | **19.2.4** |
| 언어 | `TypeScript` | 5.x |
| 차트/시각화 | `Chart.js` + `react-chartjs-2` | 4.5.1 / 5.3.1 |
| 팝업 | `SweetAlert2` | 11.x |
| 스타일 | `Tailwind CSS` | **v4** (`@tailwindcss/postcss`) |
| 폰트 | `Nanum Gothic` | Google Fonts CDN |

> ⚠️ **주의**: CLAUDE.md 초안의 `Next.js 14`, `Recharts`, `shadcn/ui`, `SWR`, `TanStack Query`는 미설치. 실제로는 Next.js 16 + Chart.js + SweetAlert2.

---

## 실제 디렉터리 구조

```
youtubeeda/
├── CLAUDE.md
│
├── backend/                              # Django 백엔드
│   ├── manage.py
│   ├── backend/                          # Django 설정 패키지
│   │   ├── settings.py                   # DB: youtubeedadb @ 192.168.0.12 (pymysql 패치 포함)
│   │   ├── urls.py                       # 루트 URL (api_v1 포함 예정)
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── api_v1/                           # 메인 앱 (단일 앱 구조)
│       ├── models.py                     # ✅ 7개 모델 구현됨
│       ├── admin.py                      # ✅ 전체 모델 Admin 등록됨
│       ├── views.py                      # ⬜ 미구현
│       ├── serializers.py                # ⬜ 미구현
│       ├── urls.py                       # ⬜ 미구현
│       ├── youtube_service.py            # ⬜ 미구현 (yt-dlp 수집 로직)
│       ├── eda_service.py                # ⬜ 미구현 (pandas EDA 분석)
│       ├── apps.py
│       ├── tests.py
│       └── migrations/
│           └── 0001_initial.py           # ✅ MariaDB 적용 완료
│
└── frontend/                             # Next.js 16 프론트엔드
    ├── package.json
    ├── next.config.ts
    ├── postcss.config.mjs                # @tailwindcss/postcss
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── globals.css               # ✅ Nanum Gothic 변수, 스크롤바
        │   ├── layout.tsx                # ✅ 루트 레이아웃 (Google Fonts 링크)
        │   ├── page.tsx                  # Next.js 기본 홈 (미수정)
        │   └── dashboard/
        │       ├── layout.tsx            # ✅ Sidebar + Header 래퍼
        │       └── main/
        │           └── page.tsx          # ✅ 대시보드 메인 (Chart.js 6종 + 테이블 2종)
        └── components/
            ├── Sidebar.tsx               # ✅ 왼쪽 메뉴바 (usePathname 활성 하이라이트)
            └── Header.tsx                # ✅ 상단 헤더 (SweetAlert2 팝업)
```

---

## DB 설정 (backend/backend/settings.py 실제값)

```python
import pymysql
pymysql.version_info = (2, 2, 1, "final", 0)  # Django 5.x 버전 체크 우회
pymysql.install_as_MySQLdb()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'youtubeedadb',
        'USER': 'youtubeeda',
        'PASSWORD': '1234',
        'HOST': '192.168.0.12',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
```

---

## DB 모델 (api_v1/models.py — 실제 구현)

### ✅ 생성된 테이블 7개

| 테이블 | 클래스 | 용도 |
|--------|--------|------|
| `channel` | `Channel` | 채널 기본 정보 (구독자, 영상수) |
| `video` | `Video` | 영상 메타데이터 (제목, 게시일, 길이, Shorts 여부) |
| `video_stats` | `VideoStats` | 현재 통계 (조회수, 좋아요, 댓글) |
| `video_stats_snapshot` | `VideoStatsSnapshot` | 시계열 스냅샷 (수집 시마다 기록) |
| `tag` | `Tag` | 태그 마스터 |
| `video_tag` | `VideoTag` | 영상-태그 M:N 매핑 |
| `collection_log` | `CollectionLog` | 수집 작업 상태 추적 |

### 핵심 필드 요약

**Channel**: `channel_id(PK)`, `channel_url`, `channel_name`, `subscriber_count`, `video_count`, `total_view_count`, `description`, `thumbnail_url`, `country`, `created_at`, `fetched_at`

**Video**: `video_id(PK)`, `channel(FK)`, `title`, `description`, `published_at`, `duration_seconds`, `is_short(auto)`, `thumbnail_url`
- `save()` 오버라이드: `duration_seconds <= 60` → `is_short = True` 자동 설정

**VideoStats**: `video(PK/OneToOne)`, `view_count`, `like_count`, `comment_count`, `updated_at`
- `like_count`, `comment_count`: 비공개 채널 시 `None` → `default=0` 처리

**CollectionLog**: `channel(FK)`, `status(pending/running/done/error)`, `total_videos`, `collected_videos`, `error_message`, `started_at`, `finished_at`

---

## yt-dlp 수집 흐름 (구현 예정: youtube_service.py)

### API 키 불필요 — yt-dlp 3단계

```python
import yt_dlp

# 1단계: 채널 정보 (구독자수, 채널명)
def fetch_channel_info(channel_url: str) -> dict:
    opts = {'extract_flat': True, 'skip_download': True,
            'quiet': True, 'playlist_items': '1'}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    return {
        'channel_id':       info.get('channel_id'),
        'channel_name':     info.get('channel'),
        'subscriber_count': info.get('channel_follower_count', 0),
        'description':      info.get('description', ''),
        'thumbnail_url':    info.get('thumbnail', ''),
    }

# 2단계: 전체 영상 ID 목록 (빠른 플랫 수집)
def fetch_video_ids(channel_url: str) -> list[str]:
    opts = {'extract_flat': True, 'skip_download': True, 'quiet': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url + '/videos', download=False)
    return [e['id'] for e in info.get('entries', [])]

# 3단계: 영상 상세 (조회수, 좋아요, 댓글, 길이)
def fetch_video_detail(video_id: str) -> dict:
    url = f'https://www.youtube.com/watch?v={video_id}'
    opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        'video_id':         info.get('id'),
        'title':            info.get('title'),
        'upload_date':      info.get('upload_date'),   # 'YYYYMMDD' → strptime 필요
        'duration_seconds': info.get('duration', 0),   # 이미 초 단위
        'view_count':       info.get('view_count', 0),
        'like_count':       info.get('like_count') or 0,
        'comment_count':    info.get('comment_count') or 0,
        'thumbnail_url':    info.get('thumbnail', ''),
        'tags':             info.get('tags', []),
    }
```

> 성능 팁: 영상 수 많을 때 `concurrent.futures.ThreadPoolExecutor` 병렬 수집, 요청 간 0.5~1초 딜레이 권장.

---

## 대시보드 UI (frontend — 실제 구현)

### 접속 URL: `http://localhost:3000/dashboard/main`

### 구현된 화면 구성

**왼쪽 사이드바** (`#212121` 다크)
- YouTube 빨간 로고 + "EDA 분석" 텍스트
- 메뉴: `데이터 수집` / `채널 리스트` / `채널 분석`
- `usePathname()`으로 현재 경로 활성화 (`#FF0000` 좌측 보더)
- 하단 관리자 계정 표시

**상단 헤더** (흰색)
- 왼쪽: 로고 + BETA 뱃지
- 오른쪽: 로그인 / 로그아웃 / 개인정보수정 버튼
- SweetAlert2 팝업: 로그아웃 확인, 개인정보수정 안내

**메인 대시보드** (`/dashboard/main/page.tsx`)

| 섹션 | 구현 내용 |
|------|---------|
| 페이지 헤더 | 채널 필터 셀렉트 + 기간 필터 + 데이터 수집 버튼(SweetAlert2 URL 입력 팝업) |
| KPI 카드 4개 | 수집 채널 수 / 총 영상 수 / 총 조회수 / 평균 조회수 (증감 표시) |
| Line 차트 | 월별 업로드 추이 (Chart.js) |
| Bar 차트 | 조회수 구간별 분포 히스토그램 (Chart.js) |
| Scatter 차트 | 영상 길이 vs 조회수 — 일반/Shorts 구분 (Chart.js) |
| Doughnut 차트 | Shorts vs 일반 영상 비율 (Chart.js) |
| Bar 차트 | 요일별 업로드 패턴 (Chart.js) |
| Progress bar | 참여도 지표 (좋아요율, 댓글률) |
| 테이블 | TOP 10 영상 (조회수 순위, Shorts 뱃지) |
| 테이블 | 최근 수집 로그 (진행률 바 + 상태 뱃지) |

> 현재 모든 차트는 **목업 데이터**로 동작. 백엔드 API 완성 후 실제 데이터로 교체 예정.

---

## API 엔드포인트 설계 (구현 예정: api_v1/)

```
POST /api/v1/channels/fetch/
     Body: {"url": "https://www.youtube.com/@channelname"}
     → 채널 정보 수집 후 DB 저장

GET  /api/v1/channels/
     → 저장된 채널 목록

GET  /api/v1/channels/<channel_id>/
     → 채널 상세 정보

POST /api/v1/channels/<channel_id>/fetch-videos/
     → 전체 영상 수집 후 DB 저장 (CollectionLog 생성)

GET  /api/v1/channels/<channel_id>/videos/
     → 채널 영상 목록 (VideoStats 포함)

GET  /api/v1/channels/<channel_id>/eda/
     → EDA 분석 결과 JSON (차트 데이터)
```

---

## EDA 분석 항목 (구현 예정: eda_service.py)

| 차트 | 분석 내용 | Chart.js 타입 |
|------|---------|--------------|
| 조회수 분포 히스토그램 | 구간별 영상 수 | Bar |
| 월별 업로드 추이 | 게시일 기준 월별 업로드 빈도 | Line |
| 영상 길이 vs 조회수 | 상관관계 산점도 | Scatter |
| Shorts vs 일반 비율 | is_short 기준 분류 | Doughnut |
| 요일별 업로드 패턴 | 업로드 요일 분포 | Bar |
| TOP 10 영상 | 조회수 기준 상위 10개 | 테이블 |
| 참여도 지표 | 좋아요율, 댓글률 | Progress |
| 태그 분석 | 태그별 평균 조회수 (VideoTag) | Bar |
| 시계열 성장 추이 | VideoStatsSnapshot 기반 | Line |

---

## 수집 시 주의사항

| 항목 | 내용 |
|------|------|
| 요청 딜레이 | 영상 간 0.5~1초 sleep 권장 (YouTube 차단 방지) |
| 대량 수집 | 배치 단위(50개) 분할 + ThreadPoolExecutor 병렬 처리 |
| `like_count` / `comment_count` | 채널 비공개 설정 시 `None` → `or 0` 처리 필수 |
| `upload_date` | `'YYYYMMDD'` 문자열 → `datetime.strptime(val, '%Y%m%d').date()` 변환 |
| `duration` | yt-dlp가 이미 **초 단위 정수**로 반환 (ISO 8601 파싱 불필요) |
| 구독자 수 | 반올림된 표시값 수집 (정확한 수치 아닐 수 있음) |
| 비공개/멤버십 영상 | 수집 불가 |

---

## 개발 서버 실행

```bash
# 백엔드
cd backend
pip install django djangorestframework django-cors-headers pymysql \
            yt-dlp scrapetube \
            pandas numpy python-dotenv
python manage.py runserver 0.0.0.0:8000

# 프론트엔드
cd frontend
npm install
npm run dev   # http://localhost:3000
# 대시보드: http://localhost:3000/dashboard/main
```

---

## 다음 개발 순서 (Phase 별)

### Phase 2 — 백엔드 API 구현
1. `api_v1/serializers.py` — Channel, Video, VideoStats DRF 시리얼라이저
2. `api_v1/youtube_service.py` — yt-dlp 수집 로직 (채널 정보 → 영상 ID → 영상 상세)
3. `api_v1/eda_service.py` — pandas EDA 분석 로직 (차트별 JSON 반환)
4. `api_v1/views.py` — DRF APIView (수집 트리거, 채널 목록, EDA 결과)
5. `api_v1/urls.py` + `backend/urls.py` — URL 연결
6. `backend/backend/settings.py` — `rest_framework`, `corsheaders` INSTALLED_APPS 추가

### Phase 3 — 프론트 ↔ 백엔드 연동
1. `frontend/src/lib/api.ts` — Django API 호출 함수 모음
2. `frontend/src/types/youtube.ts` — Channel / Video TypeScript 타입 정의
3. `next.config.ts` — `/api/*` → `http://localhost:8000/api/*` rewrites 설정
4. `dashboard/main/page.tsx` — 목업 데이터 → 실제 API fetch 교체

### Phase 4 — 고도화
- 여러 채널 비교 분석
- 데이터 CSV 내보내기
- 태그 워드클라우드 (Python → API 이미지)
- 수집 진행률 실시간 표시 (SSE 또는 WebSocket)

---

## 법적/윤리적 고려

- 수집 데이터는 분석 목적으로만 사용
- YouTube 이용약관(ToS) 확인 후 상업적 활용 여부 판단
- 공개 데이터만 대상, 개인정보 수집 금지
