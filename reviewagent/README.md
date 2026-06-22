# 리뷰 에이전트 (Review Agent)

고객 리뷰를 LangGraph AI 파이프라인이 자동으로 분석하고, 감성에 맞는 답변을 생성·발행하는 풀스택 서비스입니다.

---

## 주요 기능

- **감성 자동 분류** — 리뷰를 긍정(good) / 중립(normal) / 부정(bad) 으로 분류
- **자동 답변 생성** — 감성별 맞춤 구조로 답변 생성 후 즉시 발행
  - 긍정: 감사 인사 + 재구매 유도
  - 중립: 감사 인사 + 개선 약속
  - 부정: 공감 · 사과 · 해결책 (품질 검사 포함, 최대 2회 재생성)
- **비동기 처리** — 리뷰 등록 즉시 완료 응답, 답변은 백그라운드에서 생성
- **키워드 인사이트** — 전체 리뷰 키워드 TOP N 집계 차트
- **구글 소셜 로그인** — OAuth2 + JWT 인증

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 프론트엔드 | React 19 · TypeScript · Tailwind CSS · Vite |
| 백엔드 | Django 5 · Django REST Framework · SimpleJWT |
| AI 파이프라인 | LangGraph · Gemini API (`gemini-3.1-flash-lite`) |
| 인증 | Google OAuth2 (django-allauth) |
| DB | MySQL 8 |
| 비동기 | Python threading |

---

## LangGraph 파이프라인

![LangGraph Pipeline](assets/pipeline.png)

---

## 화면 구성

### 로그인

![로그인](assets/screenshots/login.png)

### 상품 목록

![상품 목록](assets/screenshots/products.png)

### 상품 상세 / 리뷰 작성

![상품 상세](assets/screenshots/product-detail.png)

### 관리자 대시보드

![대시보드](assets/screenshots/admin-dashboard.png)

### 관리자 리뷰 목록

![리뷰 목록](assets/screenshots/admin-reviews.png)

### 인사이트

![인사이트](assets/screenshots/admin-insights.png)

---

## 프로젝트 구조

```
reviewagent/
├── assets/
│   ├── pipeline.png              # LangGraph 파이프라인 다이어그램
│   └── screenshots/              # UI 화면 캡처
├── backend/
│   ├── config/                   # Django 설정, URL 라우팅
│   ├── reviews/                  # 모델, 뷰, 시리얼라이저
│   ├── pipeline/                 # LangGraph 그래프, State 정의, 시드 데이터
│   ├── nodes/                    # 파이프라인 노드 (분류, 답변 생성, 품질 검사, 저장)
│   ├── .env.example
│   └── manage.py
└── frontend/
    └── src/
        ├── pages/                # 고객 화면, 관리자 화면
        ├── components/           # 공통 레이아웃, UI 컴포넌트
        ├── context/              # AuthContext (JWT)
        └── api/                  # axios 클라이언트
```

---

## 시작하기

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- MySQL 8
- [uv](https://github.com/astral-sh/uv) (Python 패키지 매니저)
- Google Cloud 프로젝트 및 OAuth2 클라이언트 ID
- Gemini API 키

### 1. MySQL 데이터베이스 생성

```sql
CREATE DATABASE reviewagentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'reviewagent'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON reviewagentdb.* TO 'reviewagent'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 백엔드 설정

```bash
cd backend

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 아래 값 입력
```

`.env` 파일:

```env
GEMINI_API_KEY=your_gemini_api_key

DJANGO_SECRET_KEY=your_django_secret_key

DB_NAME=reviewagentdb
DB_USER=reviewagent
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

REPLY_DELAY_MINUTES=10
```

```bash
# 패키지 설치
uv sync

# DB 마이그레이션
uv run python manage.py migrate

# 개발 서버 실행
uv run python manage.py runserver
```

### 3. 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev
```

프론트엔드: `http://localhost:5173`  
백엔드 API: `http://localhost:8000`

### 4. 시드 데이터 적재 (선택)

네이버 쇼핑 공개 데이터셋 300건을 DB에 적재합니다.

```bash
cd backend
uv run python pipeline/seed_data.py
```

> 시드 데이터는 `pending` 상태로만 저장됩니다. 아래 스크립트로 파이프라인을 수동 실행하세요.

```bash
uv run python pipeline/reply_workflow.py
```

---

## API 엔드포인트

| 메서드 | URL | 설명 | 권한 |
|---|---|---|---|
| GET | `/api/products/` | 상품 목록 | 인증 |
| GET | `/api/products/:id/` | 상품 상세 + 리뷰 | 인증 |
| POST | `/api/reviews/create/` | 리뷰 등록 | 인증 |
| GET | `/api/reviews/` | 전체 리뷰 목록 | 관리자 |
| GET | `/api/reviews/:id/` | 리뷰 상세 | 관리자 |
| GET | `/api/dashboard/` | 대시보드 통계 | 관리자 |
| GET | `/api/insights/tags/` | 키워드 TOP N | 관리자 |

---

## 인증 흐름

```
고객 → 구글 로그인 → django-allauth OAuth2 처리
      → JWT 발급 (payload에 role, name 포함)
      → 프론트엔드 /auth/callback 으로 리디렉트
      → localStorage에 access/refresh 토큰 저장
      → role 값으로 고객/관리자 화면 분기
```

> 최초 로그인 시 `users` 테이블에 자동 등록됩니다.  
> 관리자 권한 부여: DB에서 `role` 컬럼을 `admin`으로 직접 수정하세요.

---

## 환경 변수 목록

| 변수명 | 설명 | 기본값 |
|---|---|---|
| `GEMINI_API_KEY` | Gemini API 키 | — |
| `DJANGO_SECRET_KEY` | Django 시크릿 키 | — |
| `DB_NAME` | MySQL 데이터베이스명 | `reviewagentdb` |
| `DB_USER` | MySQL 사용자 | `reviewagent` |
| `DB_PASSWORD` | MySQL 비밀번호 | — |
| `DB_HOST` | MySQL 호스트 | `localhost` |
| `DB_PORT` | MySQL 포트 | `3306` |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 | — |
| `REPLY_DELAY_MINUTES` | 리뷰 등록 후 답변 생성까지 대기 시간(분) | `10` |
