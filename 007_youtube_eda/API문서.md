# YouTube EDA 분석 — API 레퍼런스

## 기본 정보

| 항목 | 값 |
|------|-----|
| 베이스 URL | `http://127.0.0.1:8000/api/v1` |
| 인증 | 없음 (개발 환경) |
| 데이터 포맷 | JSON (`Content-Type: application/json`) |
| CSRF | 비활성화 (`@csrf_exempt` — POST/DELETE 엔드포인트) |
| 프론트엔드 프록시 | Next.js rewrites → `/api/*` → `http://127.0.0.1:8000/api/*` |

---

## 공통 응답 구조

### 성공
```json
{ "success": true, ... }
```

### 실패
```json
{ "error": "오류 메시지" }
```

### 상태 코드
| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 누락/형식 오류) |
| 404 | 리소스 없음 |
| 405 | 허용되지 않는 HTTP 메서드 |
| 500 | 서버 오류 |

---

## 1. YouTube 데이터 수집

### 1-1. 채널 정보 수집

```
POST /api/v1/youtube/fetch-channel
```

yt-dlp를 사용해 YouTube 채널 메타데이터를 수집하고 DB에 저장합니다.  
API 키 불필요. 이미 존재하는 채널이면 최신 정보로 업데이트합니다.

**Request Body**
```json
{
  "url": "https://www.youtube.com/@channelname"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `url` | string | ✅ | YouTube 채널 URL (`@handle` 또는 `/channel/UCxxx`) |

**Response (200)**
```json
{
  "success": true,
  "channel": {
    "channel_id":       "UCxxxxxxxxxxxxxxxx",
    "channel_name":     "채널명",
    "channel_url":      "https://www.youtube.com/@channelname",
    "subscriber_count": 150000,
    "video_count":      0,
    "thumbnail_url":    "https://yt3.googleusercontent.com/...",
    "banner_url":       "https://yt3.googleusercontent.com/...",
    "description":      "채널 설명 (최대 300자)",
    "country":          "KR"
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `channel_id` | string | YouTube 내부 채널 ID |
| `channel_name` | string | 채널 표시 이름 |
| `subscriber_count` | number | 구독자 수 (반올림된 표시값) |
| `video_count` | number | 수집 완료된 영상 수 (초기 수집 시 0) |
| `thumbnail_url` | string | 채널 프로필 이미지 URL |
| `banner_url` | string | 채널 배너 이미지 URL (없으면 빈 문자열) |

**Error Response**
```json
{ "error": "채널을 찾을 수 없습니다: ..." }   // 400
{ "error": "URL을 입력해주세요." }              // 400
{ "error": "yt-dlp 미설치. pip install yt-dlp" } // 500
```

---

### 1-2. 영상 수집 시작

```
POST /api/v1/youtube/fetch-videos
```

채널의 일반 영상(`/videos` 탭)과 Shorts(`/shorts` 탭)를 **백그라운드 스레드**로 수집합니다.  
즉시 `log_id`를 반환하며, 수집 진행 상황은 `collection-log` API로 폴링합니다.

**Request Body**
```json
{
  "channel_id": "UCxxxxxxxxxxxxxxxx",
  "max_videos": 50,
  "max_shorts": 50
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `channel_id` | string | ✅ | — | 수집 대상 채널 ID |
| `max_videos` | number | ❌ | 50 | 일반 영상 최대 수집 수 (0~50, 0=수집 안 함) |
| `max_shorts` | number | ❌ | 50 | Shorts 최대 수집 수 (0~50, 0=수집 안 함) |

> `max_videos`와 `max_shorts`가 모두 0이면 400 오류를 반환합니다.  
> 서버에서 0~50 범위로 강제 클램프됩니다.

**Response (200)**
```json
{
  "success":         true,
  "log_id":          42,
  "already_running": false,
  "max_videos":      50,
  "max_shorts":      50
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `log_id` | number | 수집 진행 상황 조회에 사용하는 로그 ID |
| `already_running` | boolean | `true`이면 이미 실행 중인 작업의 `log_id`를 반환 |

**Error Response**
```json
{ "error": "채널을 먼저 수집해주세요." }  // 404 — fetch-channel 먼저 호출 필요
```

---

### 1-3. 수집 진행 상태 조회

```
GET /api/v1/youtube/collection-log/<log_id>
```

백그라운드 수집 작업의 실시간 진행 상황을 반환합니다.  
프론트엔드에서 2초 간격으로 폴링하여 진행률을 표시합니다.

**Path Parameter**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `log_id` | integer | `fetch-videos` 응답의 `log_id` |

**Response (200)**
```json
{
  "success":          true,
  "status":           "running",
  "total_videos":     87,
  "collected_videos": 34,
  "percent":          39,
  "current":          "[34/87] 📹 일반 영상 — 영상 제목...",
  "current_type":     "📹 일반 영상",
  "videos_found":     50,
  "shorts_found":     37,
  "error_message":    null,
  "started_at":       "2025-05-16 10:05:00",
  "finished_at":      null
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `status` | string | `pending` / `running` / `done` / `error` |
| `total_videos` | number | 수집 대상 총 영상 수 (일반+Shorts 합산) |
| `collected_videos` | number | 현재까지 수집 완료된 수 |
| `percent` | number | 진행률 (0~100) |
| `current` | string | 현재 수집 중인 영상 설명 |
| `current_type` | string | `📹 일반 영상` 또는 `🩳 Shorts` |
| `videos_found` | number | `/videos` 탭에서 발견된 영상 수 |
| `shorts_found` | number | `/shorts` 탭에서 발견된 Shorts 수 |
| `error_message` | string\|null | 오류 발생 시 메시지 |
| `started_at` | string\|null | 수집 시작 시각 (`YYYY-MM-DD HH:MM:SS`) |
| `finished_at` | string\|null | 수집 완료 시각 (미완료 시 `null`) |

---

## 2. 채널 관리

### 2-1. 채널 목록 조회

```
GET /api/v1/channel/list
```

수집된 전체 채널 목록과 요약 통계를 반환합니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `sort` | string | `fetched_at` | 정렬 기준: `fetched_at`(최근 수집순) / `subscriber`(구독자순) / `video`(영상순) |
| `q` | string | — | 채널명 검색 키워드 (부분 일치) |

**Response (200)**
```json
{
  "success":      true,
  "total":        3,
  "total_videos": 150,
  "total_views":  4523000,
  "channels": [
    {
      "channel_id":       "UCxxxxxxxxxxxxxxxx",
      "channel_name":     "채널명",
      "channel_url":      "https://www.youtube.com/@channelname",
      "subscriber_count": 150000,
      "video_count":      50,
      "total_view_count": 1234567,
      "thumbnail_url":    "https://...",
      "banner_url":       "https://...",
      "country":          "KR",
      "description":      "채널 설명 (최대 200자)",
      "created_at":       "2025-05-16 09:30",
      "fetched_at":       "2025-05-16 10:00",
      "log": {
        "id":               42,
        "status":           "done",
        "total_videos":     87,
        "collected_videos": 87,
        "started_at":       "2025-05-16 10:05",
        "finished_at":      "2025-05-16 10:48"
      }
    }
  ]
}
```

| 필드 | 설명 |
|------|------|
| `total_views` | 모든 채널 VideoStats 합산 조회수 |
| `total_view_count` | 해당 채널 VideoStats 합산 조회수 |
| `log` | 가장 최근 수집 로그 (없으면 `null`) |

---

### 2-2. 채널 상세 조회

```
GET /api/v1/channel/<channel_id>
```

특정 채널의 상세 정보와 최근 수집 로그 5건을 반환합니다.

**Path Parameter**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `channel_id` | string | YouTube 채널 ID (`UCxxxxxxxxxxxxxxxx`) |

**Response (200)**
```json
{
  "success": true,
  "channel": {
    "channel_id":       "UCxxxxxxxxxxxxxxxx",
    "channel_name":     "채널명",
    "channel_url":      "https://www.youtube.com/@channelname",
    "subscriber_count": 150000,
    "video_count":      50,
    "total_view_count": 1234567,
    "thumbnail_url":    "https://...",
    "country":          "KR",
    "description":      "채널 전체 설명",
    "created_at":       "2025-05-16 09:30",
    "fetched_at":       "2025-05-16 10:00"
  },
  "logs": [
    {
      "id":               42,
      "status":           "done",
      "total_videos":     87,
      "collected_videos": 87,
      "error_message":    "",
      "started_at":       "2025-05-16 10:05",
      "finished_at":      "2025-05-16 10:48"
    }
  ]
}
```

**Error Response**
```json
{ "error": "채널을 찾을 수 없습니다." }  // 404
```

---

### 2-3. 수집 로그 목록 조회

```
GET /api/v1/channel/logs
```

수집 작업 로그 목록을 최신순으로 반환합니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `channel_id` | string | `all` | `all` 또는 특정 채널 ID |
| `limit` | number | 30 | 최대 반환 수 (최대 100) |

**Response (200)**
```json
{
  "success": true,
  "total":   5,
  "logs": [
    {
      "id":               42,
      "channel_id":       "UCxxxxxxxxxxxxxxxx",
      "channel_name":     "채널명",
      "status":           "done",
      "total_videos":     87,
      "collected_videos": 87,
      "percent":          100,
      "error_message":    "",
      "started_at":       "2025-05-16 10:05",
      "finished_at":      "2025-05-16 10:48"
    }
  ]
}
```

| `status` 값 | 의미 |
|------------|------|
| `pending` | 대기 중 (스레드 시작 전) |
| `running` | 수집 진행 중 |
| `done` | 수집 완료 |
| `error` | 오류 발생 |

---

### 2-4. 채널 삭제

```
DELETE /api/v1/channel/<channel_id>/delete
```

채널과 연관된 모든 데이터(영상, 통계, 태그, 수집 로그)를 CASCADE 삭제합니다.

**Path Parameter**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `channel_id` | string | YouTube 채널 ID |

**Response (200)**
```json
{
  "success": true,
  "message": "\"채널명\" 채널이 삭제되었습니다."
}
```

**Error Response**
```json
{ "error": "채널을 찾을 수 없습니다." }  // 404
{ "error": "DELETE만 허용됩니다." }       // 405
```

---

## 3. EDA 분석

### 3-1. EDA 분석 데이터

```
GET /api/v1/eda
```

수집된 영상 데이터를 집계·분석하여 차트용 JSON을 반환합니다.  
`channel_id=all`이면 전체 채널 합산, 특정 ID이면 해당 채널만 분석합니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `channel_id` | string | `all` | `all` 또는 특정 채널 ID |

**Response (200)**
```json
{
  "success":    true,
  "channel_id": "UCxxxxxxxxxxxxxxxx",

  "kpi": {
    "channel_count": 1,
    "total_videos":  87,
    "total_views":   4523000,
    "avg_views":     51986
  },

  "upload_trend": {
    "labels": ["24.06", "24.07", "24.08", "24.09", "24.10", "24.11", "24.12",
               "25.01", "25.02", "25.03", "25.04", "25.05"],
    "data":   [5, 3, 8, 6, 4, 7, 2, 9, 11, 8, 6, 12]
  },

  "views_dist": {
    "labels": ["~1만", "1~5만", "5~10만", "10~50만", "50~100만", "100만+"],
    "data":   [30, 25, 15, 12, 4, 1]
  },

  "shorts_ratio": {
    "regular": 62,
    "shorts":  25
  },

  "weekday": {
    "labels": ["월", "화", "수", "목", "금", "토", "일"],
    "data":   [10, 12, 14, 11, 18, 13, 9]
  },

  "scatter": {
    "regular": [{ "x": 620, "y": 340000 }, "..."],
    "shorts":  [{ "x": 45,  "y": 980000 }, "..."]
  },

  "top10": [
    {
      "rank":     1,
      "title":    "영상 제목",
      "channel":  "채널명",
      "views":    3850000,
      "likes":    142000,
      "comments": 8320,
      "duration": "18:32",
      "is_short": false
    }
  ],

  "engagement": [
    {
      "channel":      "채널명",
      "avg_likes":    4820,
      "avg_comments": 312
    }
  ],

  "engagement_summary": {
    "avg_likes":    4820,
    "avg_comments": 312,
    "like_rate":    13.3
  }
}
```

#### 응답 필드 상세

**`kpi`**
| 필드 | 설명 |
|------|------|
| `channel_count` | 분석 대상 채널 수 |
| `total_videos` | 수집된 총 영상 수 |
| `total_views` | VideoStats 기준 총 조회수 합계 |
| `avg_views` | 영상당 평균 조회수 |

**`upload_trend`**
- 최근 12개월 월별 영상 업로드 수 (게시일 `published_at` 기준)
- `labels`: `YY.MM` 형식 12개 배열
- `data`: 각 월의 업로드 수

**`views_dist`**
- 조회수 구간별 영상 수 분포 히스토그램
- 구간: `~1만`, `1~5만`, `5~10만`, `10~50만`, `50~100만`, `100만+`

**`shorts_ratio`**
- `regular`: 일반 영상 수 (`is_short=false`)
- `shorts`: Shorts 수 (`is_short=true`, `duration_seconds <= 60`)

**`scatter`**
- 영상 길이(초) vs 조회수 산점도 데이터 (최대 150개)
- `regular`: 일반 영상 `[{"x": 길이(초), "y": 조회수}, ...]`
- `shorts`: Shorts `[{"x": 길이(초), "y": 조회수}, ...]`

**`top10`**
- 조회수 기준 상위 10개 영상
- `duration`: `HH:MM:SS` 또는 `MM:SS` 형식 문자열

**`engagement`**
- 채널별 평균 좋아요/댓글 수 (최대 8개 채널)

**`engagement_summary`**
- 전체 분석 대상 영상의 평균 참여도
- `like_rate`: 평균 좋아요 수 / 평균 조회수 × 100 (%)

---

## 4. 데이터 모델 (DB 테이블)

### Channel (`channel` 테이블)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `channel_id` | VARCHAR(100) PK | YouTube 채널 ID |
| `channel_url` | VARCHAR(300) | 수집에 사용한 URL |
| `channel_name` | VARCHAR(200) | 채널명 |
| `subscriber_count` | BIGINT | 구독자 수 |
| `video_count` | INT | 수집 완료된 영상 수 |
| `total_view_count` | BIGINT | 채널 전체 조회수 (미사용, VideoStats 합산 권장) |
| `description` | TEXT | 채널 설명 |
| `thumbnail_url` | VARCHAR(500) | 프로필 이미지 URL |
| `banner_url` | VARCHAR(1000) | 배너 이미지 URL |
| `country` | VARCHAR(10) | 국가 코드 |
| `created_at` | DATETIME | 최초 등록일시 |
| `fetched_at` | DATETIME | 마지막 수집일시 (auto_now) |

### Video (`video` 테이블)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `video_id` | VARCHAR(20) PK | YouTube 영상 ID |
| `channel_id` | FK → Channel | 소속 채널 |
| `title` | VARCHAR(500) | 영상 제목 |
| `description` | TEXT | 영상 설명 (최대 3,000자) |
| `published_at` | DATE | 게시일 |
| `duration_seconds` | INT | 영상 길이 (초 단위) |
| `is_short` | BOOLEAN | Shorts 여부 (`duration_seconds <= 60`이면 자동 설정) |
| `thumbnail_url` | VARCHAR(500) | 썸네일 URL |
| `created_at` / `fetched_at` | DATETIME | 등록/수집 일시 |

### VideoStats (`video_stats` 테이블)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `video_id` | PK / FK → Video | 1:1 관계 |
| `view_count` | BIGINT | 조회수 |
| `like_count` | INT | 좋아요 수 (비공개 채널 = 0) |
| `comment_count` | INT | 댓글 수 (비공개 채널 = 0) |
| `updated_at` | DATETIME | 업데이트 일시 (auto_now) |

### CollectionLog (`collection_log` 테이블)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INT PK AUTO | 로그 ID |
| `channel_id` | FK → Channel | 대상 채널 |
| `status` | VARCHAR(10) | `pending` / `running` / `done` / `error` |
| `total_videos` | INT | 수집 대상 총 수 |
| `collected_videos` | INT | 수집 완료 수 |
| `error_message` | TEXT | 오류 메시지 (최대 1,000자) |
| `started_at` | DATETIME | 시작일시 (auto_now_add) |
| `finished_at` | DATETIME | 완료일시 (null 허용) |

### Tag / VideoTag (`tag`, `video_tag` 테이블)
- `Tag`: 태그명 마스터 (unique)
- `VideoTag`: 영상-태그 M:N 매핑 (unique_together: video + tag)

---

## 5. 수집 흐름 요약

```
① POST /youtube/fetch-channel  →  채널 정보 저장 (Channel 레코드 생성/갱신)
        ↓
② POST /youtube/fetch-videos   →  백그라운드 스레드 시작, log_id 즉시 반환
        ↓
③ GET  /youtube/collection-log/<log_id>  →  2초 간격 폴링, 진행 상황 표시
        ↓  (status: done)
④ GET  /eda?channel_id=<id>    →  분석 결과 조회 (차트 데이터 반환)
```

---

## 6. 서버 실행

```bash
# 백엔드
cd backend
python manage.py runserver 0.0.0.0:8000

# 프론트엔드 (Next.js rewrite → /api/* 자동 프록시)
cd frontend
npm run dev   # http://localhost:3000
```

**DB 접속 정보** (`backend/backend/settings.py`)
| 항목 | 값 |
|------|-----|
| HOST | 192.168.0.12 |
| PORT | 3306 |
| DB | youtubeedadb |
| USER | youtubeeda |

---

## 7. 주요 제약 사항

| 항목 | 제한 |
|------|------|
| 일반 영상 최대 수집 수 | 50개 (`MAX_VIDEOS = 50`) |
| Shorts 최대 수집 수 | 50개 (`MAX_VIDEOS = 50`) |
| 산점도 데이터 | 조회수 상위 150개 |
| EDA TOP 10 | 조회수 기준 상위 10개 |
| 채널별 참여도 분석 | 최대 8개 채널 |
| 로그 최대 반환 | 100개 (`limit` 파라미터) |
| 배너 URL 감지 | 가로/세로 비율 ≥ 2.5 AND 가로 ≥ 480px |
| yt-dlp 수집 방식 | YouTube 내부 InnerTube API 직접 호출 (외부 API 키 불필요) |
