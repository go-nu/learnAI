# CLAUDE.md — 고객 리뷰 자동 답변 서비스

> 프로젝트 전체 맥락을 담은 기준 문서입니다. 코드 작성 전 반드시 먼저 읽으세요.

---

## 1. 프로젝트 개요

### 서비스 한 줄 설명
고객 리뷰를 LangGraph 파이프라인이 감성 분석 후 자동 답변을 생성하고,
모든 리뷰에 대한 답변을 **관리자 개입 없이 즉시 자동 발행**하는 리뷰 자동 답변 서비스

### 핵심 가치
- 리뷰를 긍정(good) / 중립(normal) / 부정(bad)으로 자동 분류
- 감성별 답변 구조
  - 긍정: 감사 인사 + 재구매 유도 → 즉시 자동 발행
  - 중립: 감사 인사 + 개선 약속 → 즉시 자동 발행
  - 부정: 공감·사과·해결책 구조 → 품질 검토 후 즉시 자동 발행
- 전체 리뷰 키워드 태그 추출 → 인사이트 대시보드 (TOP N 집계)

### 포트폴리오 목적
LangGraph StateGraph 기반 AI 파이프라인을 실제 서비스 형태(프론트 + 백엔드 + DB)로
구현한 풀스택 프로젝트. 기본 구조는 직접 구현하고, 반복적인 UI 작업은 바이브 코딩 활용.

---

## 2. 기술 스택

### 환경
| 항목 | 값 |
|---|---|
| 개발 환경 | localhost |
| DB Host | localhost |
| DB Name | reviewagentdb |
| DB User | reviewagent |
| DB Password | 1234 |
| DB Engine | MySQL |

### 백엔드
- **Django** — REST API 서버 (Django REST Framework)
- **LangGraph** — AI 파이프라인 (StateGraph)
- **mysqlclient** — Django MySQL 연결
- **django-allauth** — 구글 소셜 로그인
- **djangorestframework-simplejwt** — JWT 토큰 인증

### 프론트엔드
- **React (TypeScript)** + **Tailwind CSS** + **SweetAlert2**

### AI
- **Gemini API (gemini-3.1-flash-lite)** — 감성 분석, 답변 생성, 키워드 추출. 모델명 절대 변경 금지
- **LangGraph** — 노드·엣지 기반 파이프라인 오케스트레이션

### 실행 방식
- **비동기 방식** — Django 뷰에서 완료 응답 후, `threading`으로 LangGraph를 백그라운드 실행
- 사용자는 답변 생성 대기 없이 즉시 "리뷰가 등록되었습니다" 확인
- 답변은 백그라운드 처리 완료 후 DB에 저장. 사용자가 리뷰 목록 재방문 시 확인 가능

---

## 3. 데이터 소스

- **출처**: 네이버 쇼핑 리뷰 공개 데이터셋
- **URL**: `https://raw.githubusercontent.com/bab2min/corpus/master/sentiment/naver_shopping.txt`
- **형식**: `평점(1~5)\t리뷰텍스트` (탭 구분)
- **시딩 볼륨**: 300건 (LLM 호출 비용 고려)
- `product` → "시험 상품" 단일 고정 / `user` → Faker(ko_KR) 랜덤 배정 / `status` → 전부 `pending`

실제 서비스 시연용 상품은 관리자가 직접 등록 (카테고리: 주방·생활용품)

---

## 4. 인증 방식

- 구글 OAuth2 소셜 로그인 전용 (이메일/비밀번호 없음)
- JWT payload에 `role` 포함 → 프론트에서 관리자/고객 화면 분기
- 최초 로그인 시 users 테이블 자동 INSERT. `role` 기본값 `customer`, 관리자는 DB 직접 수정

---

## 5. 화면 목록 (총 7개)

### 고객 화면
| # | 화면명 | 설명 |
|---|---|---|
| 1 | 로그인 | 구글 소셜 로그인 버튼만 표시 |
| 2 | 상품 목록 | 등록된 상품 카드 목록 |
| 3 | 상품 상세 + 리뷰 목록 | 상품 정보 + 리뷰·답변 목록 + 리뷰 작성 폼 |

### 관리자 화면
| # | 화면명 | 설명 |
|---|---|---|
| 4 | 대시보드 홈 | 감성 비율 차트, 처리 현황, 최근 리뷰 요약 |
| 5 | 리뷰 목록 | 전체 리뷰. 감성·상태 필터 |
| 6 | 리뷰 상세 | 원본 리뷰 + AI 답변 조회 |
| 7 | 인사이트 | 전체 리뷰 키워드 TOP N 집계 차트 |

### MVP 우선순위
```
1단계: 로그인 → 상품 상세·리뷰 작성 → 자동 답변 생성·발행 확인
2단계: 대시보드 홈, 리뷰 목록, 인사이트
```

---

## 6. DB 설계 (MySQL)

```
users
  └── reviews (user_id FK)
        ├── review_replies (review_id FK)  1:1
        └── review_tags    (review_id FK)  1:N

products
  └── reviews (product_id FK)
```

### users
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 자동증가 |
| email | VARCHAR(255) UNIQUE | 구글 계정 이메일 |
| google_id | VARCHAR(255) UNIQUE | 구글 OAuth 고유 ID |
| name | VARCHAR(100) | 구글 계정 표시 이름 |
| role | VARCHAR(20) | `admin` / `customer`. 기본값 `customer` |
| created_at | DATETIME | 최초 로그인 일시 |

### products
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 자동증가 |
| name | VARCHAR(255) | 상품명 |
| category | VARCHAR(100) | 카테고리 |
| description | TEXT | 상품 설명 |
| created_at | DATETIME | 등록 일시 |

### reviews ★ 핵심 테이블
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 자동증가 |
| user_id | BIGINT FK | → users.id |
| product_id | BIGINT FK | → products.id |
| text | TEXT | 리뷰 원문. LangGraph 입력값 |
| rating | SMALLINT | 별점 1~5 |
| emotion_label | VARCHAR(10) | `good` / `normal` / `bad`. 분석 전 NULL |
| status | VARCHAR(20) | `pending` → `processing` → `done` |
| created_at | DATETIME | 리뷰 작성 일시 |

**status 흐름**
```
pending     리뷰 등록 직후, LangGraph 실행 전
processing  LangGraph 실행 중
done        분석 + 답변 생성 + 발행 완료
```

### review_replies
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 자동증가 |
| review_id | BIGINT FK UNIQUE | → reviews.id (1:1) |
| reply_text | TEXT | LangGraph 생성 답변 |
| created_at | DATETIME | 답변 생성 일시 |

### review_tags
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 자동증가 |
| review_id | BIGINT FK | → reviews.id |
| tag | VARCHAR(100) | 추출 키워드. 예) "배송", "포장", "가성비" |

---

## 7. LangGraph 파이프라인

### LangGraph 그래프 구조

```
__start__
    │
    ▼
read_review        DB에서 review_id로 리뷰 로드 → State 초기화
    │
    ▼
decide_emotion     LLM 호출 → emotion_label 분류 (good / normal / bad)
    │              [conditional edge] 3-way 분기
    │
    ├── 긍정 ──▶ good_reply    감사 인사 + 재구매 유도 ──────────────┐
    │                                                                  │
    ├── 중립 ──▶ normal_reply  감사 인사 + 개선 약속 ────────────────┤
    │                                                                  ▼
    └── 부정 ──▶ bad_reply     공감·사과·해결책 구조 생성        check_result   최종 품질 검사
                    │              ▲                                   │
                    ▼              │ 미달 시 재생성 (최대 1회)         ├── 통과 ──▶ save_result ──▶ __end__
               review_reply ───────┘                                   │
                    │         통과 시 check_result로 진행              └── 미달 ──▶ regenerate_reply
                    └──────────────────────────────────────────────────┘              │ (최대 2회)
                                                                                      └──▶ check_result
```

### State 구성
노드 간 공유되는 상태값:

| 필드 | 타입 | 설명 |
|---|---|---|
| `review_id` | int | 처리할 리뷰 PK |
| `text` | str | 리뷰 원문 |
| `rating` | int | 별점 1~5 |
| `emotion_label` | str | `good` / `normal` / `bad`. 분류 전 미설정 |
| `reply_text` | str | LLM이 생성한 답변 |
| `tags` | list[str] | 추출 키워드 리스트 |
| `retry_count` | int | `review_reply` ↔ `bad_reply` 루프 재시도 횟수 (최대 1회) |
| `regenerate_count` | int | `check_result` ↔ `regenerate_reply` 루프 재시도 횟수 (최대 2회) |

### 노드별 역할
| 노드 | 역할 |
|---|---|
| `read_review` | DB에서 리뷰 로드 → State 초기화 |
| `decide_emotion` | LLM으로 감성 분류 → `emotion_label` 결정 (good / normal / bad) |
| `good_reply` | 감사 인사 + 재구매 유도 구조 답변 생성 |
| `normal_reply` | 감사 인사 + 개선 약속 구조 답변 생성 |
| `bad_reply` | 공감·사과·해결책 구조 답변 생성 |
| `review_reply` | 부정 답변 품질 검사. 미달 시 `bad_reply`로 재생성 (최대 1회), 통과 시 `check_result`로 전달 |
| `check_result` | 최종 답변 품질 검사. 통과 시 `save_result`, 미달 시 `regenerate_reply`로 전달 |
| `regenerate_reply` | 답변 재생성 후 `check_result`로 재전달 (최대 2회) |
| `save_result` | 답변·태그 DB 저장 및 발행 처리 |

### 라우터 함수
| 함수 | 분기 조건 |
|---|---|
| `route_by_analysis` | `emotion_label` 값에 따라 `good_reply` / `normal_reply` / `bad_reply` 분기 |
| `check_bad_reply` | 부정 답변 품질 검사. `retry_count` 초과 또는 통과 시 `check_result`, 미달 시 `bad_reply` |
| `last_check` | 최종 품질 검사. `regenerate_count` 초과 또는 통과 시 `save_result`, 미달 시 `regenerate_reply` |

---

## 8. 시스템 데이터 플로우

```
고객: 리뷰 작성 + 제출
  │
  ▼
React: POST /api/reviews/ { product_id, text, rating }
  │
  ▼
Django: Review 생성(status=pending) → 즉시 완료 응답
  │                                        │
  │                                        ▼
  │                               React: SweetAlert2 "리뷰가 등록되었습니다"
  │
  └── [백그라운드 threading]
        REPLY_DELAY_MINUTES 대기 (기본값: 10분, .env에서 조정 가능)
          │
          ▼
        LangGraph 실행 (10~30초)
          │
          ├── 긍정·중립: good/normal_reply → save_result → status=done
          │
          └── 부정: bad_reply → review_reply (품질 검사, 최대 1회 재생성)
                        → check_result (최종 품질 검사, 최대 2회 재생성)
                        → save_result → status=done

고객: 리뷰 목록 재방문 시 답변 확인 (답변은 리뷰 등록 후 약 10분 뒤 생성)
```

---

## 9. 주요 주의사항

- **LangGraph 비동기 실행** — `threading`으로 백그라운드 처리. Django 뷰는 즉시 완료 응답 반환. 답변은 `REPLY_DELAY_MINUTES` 대기 후 생성
- **MySQL ENUM 사용 금지** — VARCHAR + Django choices 사용
- **NULL 컬럼 주의** — `emotion_label`은 LangGraph 실행 전 NULL. 프론트 NULL 처리 필수
- **JWT payload에 role 포함** — 프론트에서 관리자/고객 화면 분기
- **시딩 후 LangGraph 수동 트리거 필요** — seed_data.py는 `pending` 상태로만 적재. 별도 스크립트로 LangGraph 실행
- **LLM 모델** — `gemini-3.1-flash-lite` 고정. 절대 변경하지 말 것. API 키는 `.env`의 `GEMINI_API_KEY`로 관리
- **답변 지연 설정** — `.env`의 `REPLY_DELAY_MINUTES`로 조정 (기본값: 10). 미설정 시 10분 적용