# YouTube EDA 분석 웹서비스

YouTube 채널과 등록 영상 데이터를 **API 키 없이** 수집하고, EDA(탐색적 데이터 분석) 결과를 시각화하는 웹서비스.

---

## 프로젝트 구조

```
youtubeeda/
├── backend/                        # Django 백엔드
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                        # 환경변수 (커밋 금지)
│   ├── backend/                    # Django 설정 패키지
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api_v1/                     # 메인 API 앱
│       ├── models.py               # Channel, Video 모델
│       ├── serializers.py          # DRF 시리얼라이저
│       ├── views.py                # API 뷰
│       ├── urls.py                 # API 라우팅
│       ├── youtube_service.py      # yt-dlp 수집 로직
│       └── eda_service.py          # pandas EDA 분석 로직
└── frontend/                       # React 프론트엔드
    ├── src/
    │   ├── pages/
    │   │   ├── ChannelSearch.jsx   # 채널 URL 입력 + 수집 트리거
    │   │   └── Dashboard.jsx       # EDA 대시보드 (차트)
    │   └── components/
    │       └── charts/             # 개별 차트 컴포넌트
    └── package.json
```

---

## 기술 스택

### 백엔드
| 항목 | 선택 | 이유 |
|------|------|------|
| Framework | Django 5.2 + Django REST Framework | 기존 프로젝트 기반 |
| DB | MariaDB (`youtubeedadb` @ 192.168.0.12:3306) | 기존 설정 |
| DB Driver | pymysql | MySQLdb 호환 |
| **YouTube 수집** | **yt-dlp** | **API 키 불필요, 채널/영상 메타데이터 완전 지원** |
| EDA/통계 | pandas, numpy | 데이터 분석 |
| 환경변수 | python-dotenv | .env 파일 로드 |

### 프론트엔드
| 항목 | 선택 |
|------|------|
| Framework | React (Vite) |
| HTTP 클라이언트 | axios |
| 차트/시각화 | Recharts |
| 스타일 | Tailwind CSS |

---

## 데이터 수집 방식: yt-dlp (API 키 불필요)

### yt-dlp란
- YouTube 공개 페이지를 직접 파싱하는 오픈소스 도구
- **API 키, 인증 불필요** — YouTube URL만 있으면 메타데이터 추출 가능
- 채널 핸들(`@channelname`), 채널 ID(`/channel/UCxxx`) 모두 지원

### 수집 가능한 필드
| 필드 | yt-dlp 키 | 설명 |
|------|-----------|------|
| 채널 이름 | `channel` | 채널 표시 이름 |
| 채널 ID | `channel_id` | YouTube 내부 채널 ID |
| 구독자 수 | `channel_follower_count` | 구독자 수 |
| 영상 제목 | `title` | 영상 제목 |
| 조회수 | `view_count` | 누적 조회수 |
| 좋아요 수 | `like_count` | 좋아요 수 |
| 댓글 수 | `comment_count` | 댓글 수 |
| 영상 길이 | `duration` | **초 단위 정수** (파싱 불필요) |
| 게시일 | `upload_date` | `YYYYMMDD` 문자열 |
| 썸네일 | `thumbnail` | 썸네일 URL |

---

## 수집 흐름 (youtube_service.py)

### 1단계: 채널 정보 수집
입력: YouTube 채널 URL (`https://www.youtube.com/@channelname` 또는 `/channel/UCxxx`)

```python
import yt_dlp

def fetch_channel_info(channel_url: str) -> dict:
    opts = {
        'extract_flat': True,   # 영상 다운로드 없이 메타데이터만
        'skip_download': True,
        'quiet': True,
        'playlist_items': '1',  # 영상 1개만 추출해 채널 정보 빠르게 획득
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    return {
        'channel_id':        info.get('channel_id'),
        'channel_name':      info.get('channel'),
        'subscriber_count':  info.get('channel_follower_count', 0),
        'description':       info.get('description', ''),
        'thumbnail_url':     info.get('thumbnail', ''),
    }
```

### 2단계: 채널 전체 영상 ID 목록 수집 (빠른 플랫 수집)
```python
def fetch_video_ids(channel_url: str) -> list[str]:
    opts = {
        'extract_flat': True,   # 영상 상세정보 없이 ID만 빠르게 수집
        'skip_download': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url + '/videos', download=False)
    return [entry['id'] for entry in info.get('entries', [])]
```

### 3단계: 영상 상세정보 수집 (조회수, 좋아요, 댓글, 길이)
```python
def fetch_video_detail(video_id: str) -> dict:
    url = f'https://www.youtube.com/watch?v={video_id}'
    opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        'video_id':        info.get('id'),
        'title':           info.get('title'),
        'upload_date':     info.get('upload_date'),   # 'YYYYMMDD'
        'duration_seconds': info.get('duration', 0),  # 이미 초 단위
        'view_count':      info.get('view_count', 0),
        'like_count':      info.get('like_count', 0),
        'comment_count':   info.get('comment_count', 0),
        'thumbnail_url':   info.get('thumbnail', ''),
    }
```

> **성능 팁**: 영상 수가 많으면 `concurrent.futures.ThreadPoolExecutor`로 병렬 수집.  
> YouTube 차단 방지를 위해 요청 간 0.5~1초 간격 유지 권장.

---

## 데이터 모델 (models.py)

### Channel
| 필드 | 타입 | 설명 |
|------|------|------|
| channel_id | CharField(PK) | YouTube 채널 ID |
| channel_name | CharField | 채널 이름 |
| channel_url | CharField | 수집에 사용한 원본 URL |
| subscriber_count | BigIntegerField | 구독자 수 |
| video_count | IntegerField | 수집된 영상 수 |
| description | TextField | 채널 설명 |
| thumbnail_url | URLField | 채널 썸네일 |
| fetched_at | DateTimeField | 데이터 수집 시각 (auto) |

### Video
| 필드 | 타입 | 설명 |
|------|------|------|
| video_id | CharField(PK) | YouTube 영상 ID |
| channel | ForeignKey(Channel) | 소속 채널 |
| title | CharField | 영상 제목 |
| published_at | DateField | 게시일 (`upload_date` 파싱) |
| duration_seconds | IntegerField | 영상 길이(초) — yt-dlp 직접 제공 |
| view_count | BigIntegerField | 조회수 |
| like_count | IntegerField | 좋아요 수 |
| comment_count | IntegerField | 댓글 수 |
| thumbnail_url | URLField | 영상 썸네일 |
| fetched_at | DateTimeField | 데이터 수집 시각 (auto) |

---

## API 엔드포인트 (api_v1)

| Method | URL | Body / Param | 설명 |
|--------|-----|------|------|
| POST | `/api/v1/channels/fetch/` | `{"url": "https://youtube.com/@name"}` | 채널 정보 수집 후 저장 |
| GET | `/api/v1/channels/` | — | 저장된 채널 목록 |
| GET | `/api/v1/channels/<channel_id>/` | — | 채널 상세 정보 |
| POST | `/api/v1/channels/<channel_id>/fetch-videos/` | — | 전체 영상 수집 후 저장 |
| GET | `/api/v1/channels/<channel_id>/videos/` | — | 채널 영상 목록 |
| GET | `/api/v1/channels/<channel_id>/eda/` | — | EDA 분석 결과 JSON |

---

## EDA 분석 항목 (eda_service.py)

pandas DataFrame 기반으로 분석 후 프론트엔드에서 바로 사용할 수 있는 JSON 반환.

| # | 분석 항목 | 차트 종류 | 설명 |
|---|-----------|-----------|------|
| 1 | 조회수 분포 | 히스토그램 | 구간별 영상 수 |
| 2 | 조회수 vs 좋아요 | 산점도 | 상관관계 파악 |
| 3 | 조회수 vs 댓글수 | 산점도 | 참여도 분석 |
| 4 | 영상 길이 vs 조회수 | 산점도 | 최적 영상 길이 탐색 |
| 5 | 영상 길이 분포 | 히스토그램 | Shorts(60초 이하) vs 일반 분류 |
| 6 | 월별 업로드 추이 | 라인차트 | 게시일 기준 업로드 빈도 |
| 7 | 요일별 업로드 패턴 | 바차트 | 어느 요일에 많이 올리는지 |
| 8 | 상위 10개 영상 | 수평 바차트 | 조회수 기준 TOP 10 |
| 9 | 기술 통계 요약 | 테이블 | 평균/중앙값/최대값 등 |

---

## 환경 변수 (backend/.env)

API 키 없이 동작하므로 YouTube 관련 키 불필요. DB 접속 정보만 관리.

```
DJANGO_SECRET_KEY=your_secret_key
DB_NAME=youtubeedadb
DB_USER=youtubeeda
DB_PASSWORD=1234
DB_HOST=192.168.0.12
DB_PORT=3306
```

---

## 개발 순서

1. `pip install yt-dlp` 설치 확인 및 `requirements.txt` 작성
2. `api_v1/models.py` — Channel, Video 모델 작성
3. `python manage.py makemigrations && python manage.py migrate`
4. `api_v1/serializers.py` — DRF 시리얼라이저 작성
5. `api_v1/youtube_service.py` — yt-dlp 수집 로직 (채널 정보 → 영상 ID → 영상 상세)
6. `api_v1/eda_service.py` — pandas 기반 EDA 분석 및 JSON 직렬화
7. `api_v1/views.py` + `api_v1/urls.py` — API 뷰 및 라우팅
8. `backend/urls.py` — `/api/v1/` prefix 연결
9. `frontend/` — React + Recharts 차트 컴포넌트 개발

---

## 개발 서버 실행

```bash
# 백엔드
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 프론트엔드
cd frontend
npm install
npm run dev
```

---

## 주요 패키지 (requirements.txt)

```
Django>=5.2
djangorestframework
django-cors-headers
pymysql
yt-dlp
pandas
numpy
python-dotenv
```

---

## 주의사항

- **yt-dlp 요청 속도**: 영상 상세 수집 시 영상당 1회 요청. 채널에 영상이 많으면(500개+) 수집에 수 분 소요. 백그라운드 태스크(Celery 또는 Django Q) 도입 고려.
- **YouTube 차단**: 단시간 대량 요청 시 YouTube가 일시적으로 차단할 수 있음. 요청 간 짧은 딜레이(0.5초) 권장.
- **`upload_date` 파싱**: yt-dlp가 반환하는 `upload_date`는 `'YYYYMMDD'` 문자열 — `datetime.strptime(val, '%Y%m%d').date()`로 변환.
- **`like_count` / `comment_count`**: 채널 운영자가 비공개 설정하면 `None` 반환. 저장 전 `or 0` 처리 필수.
- **CORS**: 프론트엔드(Vite 기본 5173)와 백엔드(8000) 포트 다름 — `django-cors-headers`로 `CORS_ALLOWED_ORIGINS` 설정 필요.
- **settings.py 민감정보**: DB 비밀번호 등은 반드시 `.env` + `python-dotenv`로 관리. 하드코딩 금지.
