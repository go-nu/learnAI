# ToonCraft (툰크래프트) — CLAUDE.md

> AI와 함께, 나만의 웹툰  
> 도메인: tooncraft.co.kr

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 서비스명 | 툰크래프트 (ToonCraft) |
| 슬로건 | AI와 함께, 나만의 웹툰 |
| 도메인 | tooncraft.co.kr |
| 서비스 설명 | 생성형 AI(Gemini API + ComfyUI API)를 활용하여 이미지를 생성하고, 이를 기반으로 웹툰 컷을 제작·편집·발행할 수 있는 웹툰 창작 플랫폼 |

---

## 2. 개발 환경

### 2.1 Frontend

| 항목 | 내용 |
|------|------|
| 런타임 | Node.js v22 |
| 프레임워크 | Next.js (App Router 기반) |
| 스타일 | Tailwind CSS |
| 알림/UI | SweetAlert2 |
| HTTP 클라이언트 | Axios |
| API 통신 방식 | RESTful API |
| API 기본 경로 | `/api` |

**디렉토리 구조 (Frontend)**
```
frontend/
├── app/                   # Next.js App Router
│   ├── layout.tsx
│   ├── page.tsx           # 루트 → 로그인 상태 확인 후 /dashboard 또는 /login 리다이렉트
│   ├── home/              # 홈페이지 (/home)
│   │   └── page.tsx
│   ├── login/             # 사용자 로그인 (/login)
│   │   └── page.tsx
│   ├── dashboard/         # 웹툰 제작 대시보드 (/dashboard)
│   │   └── page.tsx
│   └── api/               # Route Handlers (프록시)
├── components/            # 공통 컴포넌트
├── lib/                   # axios 인스턴스, 유틸리티
├── public/                # 정적 파일
├── styles/                # 전역 CSS
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

---

### 2.2 Backend

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.11 |
| 패키지 관리자 | uv |
| 프레임워크 | Django |
| 스타일 | Tailwind CSS (Django 템플릿용) |
| 알림/UI | SweetAlert2 |
| HTTP 클라이언트 | Axios (프론트 연동) |
| API 통신 방식 | RESTful API (Django REST Framework) |
| API 기본 경로 | `/api` |
| AI 이미지 생성 | Gemini API, ComfyUI API |
| DB 드라이버 | pymysql (`install_as_MySQLdb()` 패치 적용) |

**디렉토리 구조 (Backend)**
```
backend/
├── backend/               # Django 설정 (settings.py, urls.py, wsgi.py, views.py)
├── api/                   # 통합 API 앱 (모델·뷰·시리얼라이저)
│   ├── migrations/        # DB 마이그레이션
│   ├── models.py          # 전체 테이블 정의 (User, Webtoon, WebtoonEpisode, WebtoonCut, GeneratedImage)
│   ├── views.py           # API 뷰
│   ├── admin.py           # Django Admin 등록
│   └── apps.py
├── templates/             # Django 템플릿
│   ├── base.html
│   ├── includes/
│   │   ├── header.html
│   │   └── sidebar.html
│   └── admin/
│       ├── login.html
│       └── dashboard.html
├── media/                 # 업로드 파일 저장소
├── static/
├── pyproject.toml         # uv 패키지 관리
└── manage.py
```

---

### 2.3 Database (MariaDB)

| 항목 | 내용 |
|------|------|
| DBMS | MariaDB |
| Host | localhost |
| ID | tooncraft |
| Password | 1234 |
| Database | tooncraftdb |

**Django settings.py DB 설정 예시**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tooncraftdb',
        'USER': 'tooncraft',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# 커스텀 사용자 모델
AUTH_USER_MODEL = 'api.User'
```

**DB 테이블 목록 (`api/models.py`)**

| 테이블명 | 모델 클래스 | 설명 |
|----------|-------------|------|
| `users` | `User` | 사용자 계정 (AbstractUser 확장) |
| `webtoons` | `Webtoon` | 웹툰 작품 |
| `webtoon_episodes` | `WebtoonEpisode` | 웹툰 에피소드(회차) |
| `webtoon_cuts` | `WebtoonCut` | 웹툰 컷(개별 패널) |
| `generated_images` | `GeneratedImage` | AI 이미지 생성 이력 |

**모델 관계**
```
User ──< Webtoon ──< WebtoonEpisode ──< WebtoonCut
User ──< GeneratedImage
```

**주요 필드 요약**

- `User`: username, email, password, nickname, profile_image, created_at
- `Webtoon`: author(FK), title, genre, description, cover_image, status
- `WebtoonEpisode`: webtoon(FK), episode_number, title, thumbnail, is_published, published_at
- `WebtoonCut`: episode(FK), order, image, caption, metadata(JSON)
- `GeneratedImage`: user(FK), prompt_kr, prompt_en, style, ratio, reference_image, result_image, status

---

### 2.4 RESTful API 연동 규칙

| 항목 | 내용 |
|------|------|
| HTTP 클라이언트 | Axios |
| Frontend API prefix | `/api` |
| Backend API prefix | `/api` |

**Axios 기본 인스턴스 (Frontend)**
```typescript
// lib/axios.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

**인증 API 엔드포인트**
```
GET  /api/auth/csrf/      # CSRF 토큰 발급
GET  /api/auth/me/        # 로그인 여부 확인 및 사용자 정보 반환
POST /api/auth/login/     # 아이디/비밀번호 로그인
POST /api/auth/register/  # 회원가입
POST /api/auth/logout/    # 로그아웃

GET  /auth/login/google-oauth2/    # Google OAuth2 시작 (social-auth-app-django)
GET  /auth/complete/google-oauth2/ # Google OAuth2 콜백
```

**API URL 네이밍 규칙**
```
GET    /api/webtoons/           # 목록 조회
POST   /api/webtoons/           # 생성
GET    /api/webtoons/{id}/      # 단건 조회
PUT    /api/webtoons/{id}/      # 전체 수정
PATCH  /api/webtoons/{id}/      # 부분 수정
DELETE /api/webtoons/{id}/      # 삭제

POST   /api/image/generate/     # AI 이미지 생성
POST   /api/image/upload/       # 이미지 업로드
```

---

### 2.5 파일 처리 방식

업로드된 파일은 날짜 기반 경로로 자동 분류 저장합니다.

**저장 경로 형식**
```
/media/upload/{년}/{월}/{일}/{파일명}
예: /media/upload/2025/06/26/abc123.png
```

**Django 파일 경로 헬퍼**
```python
# apps/common/utils.py
import os
from datetime import date

def upload_to_date_path(instance, filename):
    today = date.today()
    return os.path.join(
        'upload',
        str(today.year),
        f'{today.month:02d}',
        f'{today.day:02d}',
        filename
    )
```

**Django settings.py 미디어 설정**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

## 3. 디자인 컨셉

참조 사이트: [네이버 웹툰](https://comic.naver.com/index)

### 3.1 전체 디자인 방향

네이버 웹툰의 깔끔하고 콘텐츠 중심적인 UI를 참조하여, 아래 원칙을 따릅니다.

- **콘텐츠 우선**: 썸네일·커버 이미지가 중심이 되는 레이아웃
- **포스터형 카드**: 세로형 썸네일 + 작품명 오버레이 형태
- **요일별 탭 네비게이션**: 상단 GNB + 요일/카테고리 SNB 구성
- **깔끔한 화이트 베이스**: 콘텐츠 가독성 최우선
- **모바일 퍼스트 반응형**: 스마트폰 기준으로 설계 후 데스크탑 확장

---

### 3.2 컬러 시스템

```css
/* 메인 색상 */
--color-primary:     #00C73C;   /* 네이버 그린 계열 (포인트) */
--color-primary-hover: #00A832; /* hover 상태 */

/* 배경 */
--color-bg-page:     #FFFFFF;   /* 페이지 배경 */
--color-bg-section:  #F8F8F8;   /* 섹션 카드 배경 */
--color-bg-card:     #FFFFFF;   /* 콘텐츠 카드 */

/* 텍스트 */
--color-text-primary:   #1A1A1A; /* 본문 */
--color-text-secondary: #666666; /* 보조 텍스트 */
--color-text-muted:     #999999; /* 힌트/비활성 */

/* 테두리 */
--color-border:      #E8E8E8;
--color-border-focus:#00C73C;

/* 상태 색상 */
--color-new:         #FF4500;   /* NEW 배지 */
--color-up:          #FF6B35;   /* UP 배지 (업데이트) */
--color-best:        #FFD700;   /* BEST 배지 */
```

**Tailwind 커스텀 설정 (tailwind.config.ts)**
```typescript
extend: {
  colors: {
    primary: {
      DEFAULT: '#00C73C',
      hover:   '#00A832',
    },
    webtoon: {
      bg:       '#F8F8F8',
      card:     '#FFFFFF',
      border:   '#E8E8E8',
      text:     '#1A1A1A',
      sub:      '#666666',
      muted:    '#999999',
      new:      '#FF4500',
      up:       '#FF6B35',
      best:     '#FFD700',
    },
  },
}
```

---

### 3.3 타이포그래피

네이버 웹툰은 **나눔스퀘어(NanumSquare)** 계열 폰트를 사용합니다. 본 서비스도 이를 기본 폰트로 채택합니다.

```css
/* 폰트 임포트 */
@import url('https://cdn.jsdelivr.net/gh/moonspam/NanumSquare@2.0/nanumsquare.css');

/* 또는 Google Fonts Noto Sans KR (대안) */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

:root {
  --font-base: 'NanumSquare', 'Noto Sans KR', 'Apple SD Gothic Neo',
               'Malgun Gothic', sans-serif;
}

body {
  font-family: var(--font-base);
  font-size: 14px;
  line-height: 1.6;
  color: #1A1A1A;
  word-break: keep-all;
}
```

**폰트 사이즈 스케일**
```
xs:   11px  — 뱃지, 태그
sm:   12px  — 캡션, 메타 정보
base: 14px  — 본문 기본
md:   15px  — 서브 타이틀
lg:   18px  — 섹션 타이틀
xl:   22px  — 페이지 타이틀
2xl:  28px  — 메인 헤드라인
```

---

### 3.4 레이아웃 & 그리드

```css
/* 최대 너비 */
.container-main   { max-width: 1080px; margin: 0 auto; padding: 0 16px; }
.container-narrow { max-width: 860px; }

/* 웹툰 카드 그리드 */
.webtoon-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);   /* 데스크탑 */
  gap: 12px;
}

@media (max-width: 1024px) {
  .webtoon-grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 768px) {
  .webtoon-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 480px) {
  .webtoon-grid { grid-template-columns: repeat(2, 1fr); }
}
```

---

### 3.5 컴포넌트 스타일 가이드

**GNB (Global Navigation Bar)**
```
- 배경: #FFFFFF / 하단 border: 1px solid #E8E8E8
- 로고 영역 좌측, 검색바 중앙, 로그인/메뉴 우측
- 높이: 56px (모바일) / 64px (데스크탑)
- sticky top-0, z-index: 100
```

**SNB (Sub Navigation Bar — 요일/카테고리 탭)**
```
- 배경: #FFFFFF
- 탭 텍스트: 14px, color #666666
- 활성 탭: color #00C73C, border-bottom: 2px solid #00C73C
- 탭 간격: padding 12px 16px
```

**웹툰 카드 (포스터형)**
```
- 비율: 세로형 3:4 (썸네일)
- border-radius: 6px
- 그림자: box-shadow: 0 2px 8px rgba(0,0,0,0.08)
- hover 시: scale(1.02) + shadow 강화
- 제목: 13px bold, 2줄 말줄임 (line-clamp: 2)
- 작가명: 12px, color #999999
```

**버튼**
```css
/* Primary 버튼 */
.btn-primary {
  background: #00C73C;
  color: #FFFFFF;
  border-radius: 4px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
}
.btn-primary:hover { background: #00A832; }

/* Secondary 버튼 */
.btn-secondary {
  background: #FFFFFF;
  color: #1A1A1A;
  border: 1px solid #E8E8E8;
  border-radius: 4px;
}
```

---

## 4. AI 기능 연동

### 4.1 Gemini API (텍스트 → 이미지 프롬프트 생성)

```python
# apps/image/services/gemini_service.py
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_image_prompt(user_input: str) -> str:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(
        f"웹툰 컷을 위한 이미지 생성 프롬프트를 영어로 작성해줘: {user_input}"
    )
    return response.text
```

### 4.2 ComfyUI API (이미지 생성)

```python
# apps/image/services/comfyui_service.py
import requests

COMFYUI_URL = settings.COMFYUI_API_URL  # 예: http://localhost:8188

def generate_image(prompt: str, workflow: dict) -> bytes:
    payload = {
        "prompt": workflow,
        "client_id": "tooncraft"
    }
    response = requests.post(f"{COMFYUI_URL}/prompt", json=payload)
    response.raise_for_status()
    return response.json()
```

---

## 5. 환경 변수 (.env)

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,tooncraft.co.kr

# Database
DB_NAME=tooncraftdb
DB_USER=tooncraft
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=3306

# AI APIs
GEMINI_API_KEY=your-gemini-api-key
COMFYUI_API_URL=http://localhost:8188

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 6. 코드 작성 규칙

### 6.1 공통 원칙
- 모든 코드는 **한국어 주석** 으로 작성
- 함수/변수명은 **영어 camelCase** (JS/TS) 또는 **snake_case** (Python)
- 컴포넌트명은 **PascalCase**
- API 응답은 항상 아래 형식을 따름:

```json
{
  "success": true,
  "message": "처리 완료",
  "data": { ... }
}
```

```json
{
  "success": false,
  "message": "오류 메시지",
  "errors": { ... }
}
```

### 6.2 Frontend (Next.js)
- App Router 사용 (`app/` 디렉토리)
- 서버 컴포넌트 우선, 상호작용 필요 시 `'use client'` 명시
- Tailwind CSS 유틸리티 클래스 우선 사용
- 전역 스타일은 `styles/globals.css`에 CSS 변수로 관리
- 알림창은 SweetAlert2 사용 (`Swal.fire(...)`)
- API 호출은 반드시 `lib/axios.ts` 인스턴스 사용

### 6.3 Backend (Django)
- Django REST Framework(DRF) 사용
- View는 `APIView` 또는 `ViewSet` 기반
- 시리얼라이저로 입력값 유효성 검사 필수
- 파일 업로드는 `upload_to_date_path` 헬퍼 사용
- 에러 핸들링은 전역 exception handler 사용

---

## 7. 실행 방법

### Frontend 실행
```bash
cd frontend
npm install
npm run dev        # 개발 서버: http://localhost:3000
```

### Backend 실행
```bash
cd backend
uv sync                        # 의존성 설치 (uv.lock 기반)
uv run python manage.py migrate
uv run python manage.py runserver    # 개발 서버: http://localhost:8000
```

**uv 주요 명령어**
```bash
uv init                        # 프로젝트 초기화 (pyproject.toml 생성)
uv add django                  # 패키지 추가
uv add --dev pytest            # 개발용 패키지 추가
uv remove django               # 패키지 제거
uv sync                        # uv.lock 기반 의존성 동기화
uv run <command>               # 가상환경 내에서 명령 실행
uv pip compile requirements.in # requirements.txt 생성 (선택)
```

### MariaDB 초기 설정
```sql
CREATE DATABASE tooncraftdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tooncraft'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON tooncraftdb.* TO 'tooncraft'@'localhost';
FLUSH PRIVILEGES;
```

---

## 8. 관리자 페이지 디자인 컨셉 (Backend)

### 8.1 레이아웃 구조

관리자 페이지는 **상단메뉴 + 왼쪽메뉴 + 오른쪽 콘텐츠** 3단 구조로 구성합니다.

```
┌─────────────────────────────────────────────┐
│                  상단메뉴 (GNB)               │  ← header.html
├──────────────┬──────────────────────────────┤
│              │                              │
│  왼쪽메뉴    │      오른쪽 콘텐츠 영역        │
│  (Sidebar)   │      (각 페이지 본문)          │
│              │                              │
│              │                              │
└──────────────┴──────────────────────────────┘
                        ↑ sidebar.html
```

### 8.2 템플릿 디렉토리 구조

HTML 파일은 `/templates` 디렉토리에 작성합니다.

```
backend/templates/
├── base.html                  # 전체 레이아웃 베이스 (include 조합)
├── includes/
│   ├── header.html            # 상단메뉴 (모든 페이지 공통 include)
│   └── sidebar.html           # 왼쪽메뉴 (모든 페이지 공통 include)
├── admin/
│   ├── login.html             # 관리자 로그인 (/login)
│   └── dashboard.html         # 관리자 대시보드 (/dashboard)
└── errors/
    ├── 404.html
    └── 500.html
```

### 8.3 왼쪽 메뉴 (Sidebar) 구성

| 메뉴명 | 아이콘 | 경로 | 설명 |
|--------|--------|------|------|
| 대시보드 | 📊 | `/dashboard` | 통계 및 현황 |
| 사용자 관리 | 👥 | `/admin/users/` | 회원 목록·수정·삭제 |
| 웹툰 관리 | 🎨 | `/admin/webtoons/` | 웹툰 목록·승인·삭제 |
| 이미지 관리 | 🖼️ | `/admin/images/` | AI 생성 이미지 관리 |
| 통계 | 📈 | `/admin/stats/` | 이용 현황 통계 |
| 설정 | ⚙️ | `/admin/settings/` | 시스템 설정 |

### 8.4 include 사용 규칙

`base.html`에 공통 레이아웃을 정의하고, 각 페이지는 `base.html`을 상속합니다.

```html
<!-- base.html 구조 -->
{% include 'includes/header.html' %}
{% include 'includes/sidebar.html' %}
{% block content %}{% endblock %}
```

```html
<!-- 각 페이지 상속 예시 -->
{% extends 'base.html' %}
{% block content %}
  <!-- 페이지별 콘텐츠 -->
{% endblock %}
```

### 8.5 Django settings.py 템플릿 설정

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # /templates 루트 등록
        'APP_DIRS': True,
        ...
    },
]
```

---

## 9. 페이지 라우트 구성 (Frontend / Backend)

### 9.1 Frontend (Next.js) — http://localhost:3000

| 경로 | 페이지명 | 설명 |
|------|----------|------|
| `/` | 루트 | 로그인 상태 확인 → 로그인O: /dashboard, 로그인X: /login |
| `/home` | 홈페이지 | 서비스 소개, 웹툰 목록, 메인 랜딩 |
| `/login` | 사용자 로그인 | 로그인(아이디/비밀번호) + 회원가입 + Google OAuth 탭 전환 방식 |
| `/dashboard` | 대시보드 개요 | 웹툰만들기·이미지생성 기능 카드, 최근 이미지 (웹툰만들기 CTA → /dashboard/ai_image_generator) |
| `/dashboard/ai_image_generator` | AI 이미지 만들기 | AI 이미지 생성 (사이드바 + 컨트롤 패널 + 프리뷰) |
| `/dashboard/ai_image_generator/generator` | 새 웹툰 만들기 | 웹툰 프로젝트 설정 + AI 컷 생성 + 저장된 컷 목록 |
| `/dashboard/ai_image_generator/episode` | 에피소드 추가 | 에피소드 설정(WebtoonEpisode 모델) + AI 컷 생성 + 에피소드 컷 목록 |
| `/dashboard/ai_image_generator/cut_add` | 웹툰 편집기 | 이미지 라이브러리(좌) + 캔버스 드래그 편집(중) + 말풍선(우1) + 레이아웃 템플릿(우2) 5단 구성; 마우스 휠 줌, 우클릭 드래그 캔버스 이동, 말풍선 드래그 배치·이동·리사이즈·회전 |

### 9.2 Backend (Django) — http://localhost:8000

| 경로 | 페이지명 | 설명 |
|------|----------|------|
| `/login` | 관리자 로그인 | 관리자 전용 로그인 페이지 |
| `/dashboard` | 관리자 대시보드 | 사용자·웹툰·이미지 통합 관리 |
| `/api/...` | REST API | Frontend와 통신하는 API 엔드포인트 |

> **주의**: Frontend `/login`은 일반 사용자용, Backend `/login`은 관리자 전용으로 역할이 다릅니다.

---

## 10. 프론트엔드 대시보드 설계 (/dashboard)

> 참조 디자인: `개발기술문서/미리캠퍼스.webp` (미리캔버스 스타일 AI 이미지 생성 UI)

### 10.1 전체 레이아웃

다크 테마 기반의 **사이드바 메뉴 + 콘텐츠 영역** 3단 구조입니다.

```
┌──────────────────────────────────────────────────────────┐
│                      상단 GNB                             │  ← 로고, 언어 선택, 사용자 아이콘
├───────────────┬──────────────────┬────────────────────────┤
│  사이드바      │  컨트롤 패널      │   프리뷰 영역            │
│  (200px)      │  (346px, AI만)   │   (나머지 전체, AI만)    │
│               │                  │                        │
│  웹툰만들기    │  • 스타일 선택    │  • 경고/안내 배너        │
│  ├ 웹툰 작품   │  • 프롬프트 입력  │  • 생성 이미지 표시      │
│  ├ 에피소드    │  • 비율 선택     │  • 탭 (디자인/애니/기타)  │
│  └ 컷         │  • 이미지 첨부   │  • 복사·재생성 버튼       │
│               │  • 초기화/생성   │  • 다운로드 버튼          │
│  이미지생성    │                  │                        │
│  ├ AI만들기    │  ※ AI 이미지 만들기 선택 시에만 표시         │
│  └ 생성 이력   │  ※ 나머지 메뉴는 전체 너비 콘텐츠 영역 사용  │
└───────────────┴──────────────────┴────────────────────────┘
```

### 10.1-1 사이드바 메뉴 구성

| 그룹 | 메뉴 키 | 메뉴명 | 설명 |
|------|---------|--------|------|
| 웹툰만들기 | `webtoon-works` | 웹툰 작품 | 웹툰 작품 목록·관리 |
| 웹툰만들기 | `webtoon-episodes` | 웹툰 에피소드(회차) | 에피소드 목록·관리 |
| 웹툰만들기 | `webtoon-cuts` | 웹툰 컷(개별 패널) | 컷(패널) 목록·관리 |
| 이미지생성 | `image-create` | AI 이미지 만들기 | AI 이미지 생성 (컨트롤 패널 + 프리뷰) |
| 이미지생성 | `image-history` | AI 이미지 생성 이력 | 생성된 이미지 이력 조회 |

**사이드바 활성 상태 스타일**
- 활성 메뉴: `color: #00C73C`, `background: rgba(0,199,60,0.08)`, `border-left: 2px solid #00C73C`
- 비활성 메뉴: `color: var(--dash-text-sub)`, `border-left: 2px solid transparent`

### 10.2 컬러 시스템 (다크 테마)

```css
/* 대시보드 전용 다크 테마 */
--dash-bg:           #1A1A2E;   /* 전체 배경 */
--dash-panel:        #16213E;   /* 패널/카드 배경 */
--dash-surface:      #0F3460;   /* 강조 서피스 */
--dash-border:       #2A2A4A;   /* 구분선 */

/* 텍스트 */
--dash-text:         #FFFFFF;   /* 기본 텍스트 */
--dash-text-sub:     #A0A0C0;   /* 보조 텍스트 */
--dash-text-muted:   #606080;   /* 비활성 텍스트 */

/* 액션 */
--dash-primary:      #00C73C;   /* 생성 버튼 (기존 primary 유지) */
--dash-warning:      #E6A817;   /* 경고 배너 배경 */
--dash-warning-text: #1A1A00;   /* 경고 배너 텍스트 */
```

### 10.3 왼쪽 컨트롤 패널 구성

| 순서 | 컴포넌트 | 설명 |
|------|----------|------|
| 1 | 뒤로가기 헤더 | `< 바로 시작하기` 형태, 홈으로 이동 |
| 2 | 스타일 선택 | 썸네일 가로 스크롤 카드 (애니메이션·자유롭게·짧은컷 등), 전체보기 링크 |
| 3 | 결과물 묘사 | 텍스트 에리어 (한국어 입력 → Gemini가 영문 프롬프트로 변환), 글자수 표시 |
| 4 | 비율 선택 | 라디오 버튼 그룹 — `1:1` / `3:4` / `4:3` |
| 5 | 이미지 첨부 | 참조 이미지 업로드 (선택) |
| 6 | 크레딧 배너 | 매일 충전 안내 (선택적 표시) |
| 7 | 액션 버튼 | `초기화` (secondary) + `생성` (primary, 전체 너비) |

### 10.4 오른쪽 프리뷰 영역 구성

| 구성 요소 | 설명 |
|-----------|------|
| 경고 배너 | 로그인 유도 또는 안내 메시지 (노란 배경, 상단 고정) |
| 이미지 표시 영역 | 생성된 웹툰 컷 이미지 중앙 표시, 로딩 스피너 포함 |
| 기능 탭 | `디자인` / `애니메이션` / `기타` / `배경 제거(토글)` |
| 상단 액션 버튼 | 복사 아이콘, 재생성 아이콘, `에디터 배우기` 버튼 |
| 이미지 내 다운로드 | 이미지 우하단 오버레이 다운로드 버튼 |

### 10.5 Next.js 컴포넌트 구조

```
app/dashboard/
├── page.tsx                        # 대시보드 개요 페이지 (/dashboard)
│                                   # - GNB + 웰컴 배너 + 기능 카드 2개 + 최근 이미지
│                                   # - FEATURE_GROUPS 정의 (사이드바 메뉴와 동일 구조)
├── ai_image_generator/
│   └── page.tsx                    # AI 이미지 만들기 (/dashboard/ai_image_generator)
│                                   # - DashboardLayout 렌더링
└── components/
    ├── DashboardLayout.tsx         # AI 이미지 만들기 레이아웃 (GNB + 사이드바 + 콘텐츠)
    │                               # - MenuKey 타입 및 MENU_GROUPS 정의
    │                               # - activeMenu 상태로 콘텐츠 조건부 렌더링
    │                               # - "← 바로 시작하기" → /dashboard 링크
    ├── WebtoonWorksContent.tsx     # 웹툰 작품 목록 (Webtoon 모델 기반 테이블)
    │                               # - "새 웹툰 만들기" → /dashboard/ai_image_generator/generator
    ├── WebtoonEpisodesContent.tsx  # 웹툰 에피소드 목록 (WebtoonEpisode 모델 기반 테이블)
    │                               # - "에피소드 추가" → /dashboard/ai_image_generator/episode
    ├── WebtoonCutsContent.tsx      # 웹툰 컷 목록 (WebtoonCut 모델 기반 이미지 그리드)
    │                               # - "컷 추가" → /dashboard/ai_image_generator/cut_add
    │                               # - 컬럼: 커버·제목·장르·연재상태·생성일·관리
    │                               # - STATUS 뱃지: draft/ongoing/completed/hiatus
    ├── WebtoonEpisodesContent.tsx  # 웹툰 에피소드 목록 (WebtoonEpisode 모델 기반 테이블)
    │                               # - 컬럼: 썸네일·회차·제목·발행여부·생성일·발행일·관리
    │                               # - 발행 여부 뱃지: 발행됨(초록)/미발행(회색)
    ├── WebtoonCutsContent.tsx      # 웹툰 컷 목록 (WebtoonCut 모델 기반 이미지 그리드)
    │                               # - 3:4 비율 카드, 순서 뱃지, 대사/캡션 미리보기
    │                               # - 수정/삭제 오버레이 버튼
    ├── ControlPanel/               # AI 이미지 만들기 선택 시 표시
    │   ├── StyleSelector.tsx       # 스타일 썸네일 카드
    │   ├── PromptInput.tsx         # 결과물 묘사 텍스트에리어
    │   ├── RatioSelector.tsx       # 비율 선택 라디오
    │   ├── ImageUpload.tsx         # 이미지 첨부
    │   └── ActionButtons.tsx       # 초기화/생성 버튼
    └── PreviewPanel/               # AI 이미지 만들기 선택 시 표시
        ├── WarningBanner.tsx       # 경고/안내 배너
        ├── ImagePreview.tsx        # 이미지 표시 + 다운로드
        └── FeatureTabs.tsx         # 디자인/애니메이션/기타 탭
```

### 10.5-1 대시보드 개요 페이지 구성 (`/dashboard`)

```
┌──────────────────────────────────────────────────────────┐
│                      상단 GNB                             │
├──────────────────────────────────────────────────────────┤
│  안녕하세요, User님! 👋          [1,000 크레딧 보유]       │  ← 웰컴 배너
│                                                          │
│  ┌─────────────────────────┐  ┌─────────────────────┐   │  ← 기능 카드 2열
│  │  🎨 웹툰만들기           │  │  ✨ 이미지생성       │   │
│  │  ─────────────────────  │  │  ─────────────────  │   │
│  │  [웹툰 작품       0개]   │  │  [AI 이미지 만들기→] │   │
│  │  [에피소드(회차)  0개]   │  │  [AI 이미지 생성이력 0개]│ │
│  │  [컷(개별 패널)  0개]   │  │                     │   │
│  │  [웹툰 만들기 시작 →]    │  │  [이미지 생성하기 →] │   │
│  └─────────────────────────┘  └─────────────────────┘   │
│                                                          │
│  최근 생성 이미지                              [전체보기→] │  ← 최근 이미지 섹션
│  ┌──────────────────────────────────────────────────┐   │
│  │         (빈 상태) 첫 이미지 생성하기               │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

**MenuKey 타입 정의**
```typescript
type MenuKey =
  | 'webtoon-works'     // 웹툰 작품
  | 'webtoon-episodes'  // 웹툰 에피소드(회차)
  | 'webtoon-cuts'      // 웹툰 컷(개별 패널)
  | 'image-create'      // AI 이미지 만들기 (기본값)
  | 'image-history';    // AI 이미지 생성 이력
```

### 10.6 AI 생성 흐름

```
사용자 입력 (한국어 묘사)
        ↓
Gemini API → 영문 이미지 프롬프트 생성
        ↓
ComfyUI API → 웹툰 스타일 이미지 생성
        ↓
오른쪽 프리뷰 영역에 결과 표시
        ↓
다운로드 / 웹툰 컷으로 저장
```

> **주의**: Frontend `/login`은 일반 사용자용, Backend `/login`은 관리자 전용으로 역할이 다릅니다.

---

## 11. 주요 참고 URL

| 항목 | URL |
|------|-----|
| 네이버 웹툰 (디자인 참조) | https://comic.naver.com/index |
| Next.js 공식 문서 | https://nextjs.org/docs |
| Django REST Framework | https://www.django-rest-framework.org |
| Tailwind CSS | https://tailwindcss.com/docs |
| SweetAlert2 | https://sweetalert2.github.io |
| Gemini API | https://ai.google.dev/docs |
| ComfyUI API | https://github.com/comfyanonymous/ComfyUI |
| NanumSquare 폰트 | https://campaign.naver.com/nanumsquare_neo/ |
