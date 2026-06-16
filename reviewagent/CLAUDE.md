# CLAUDE.md — 고객 리뷰 자동 답변 서비스

> 이 파일은 프로젝트의 전체 맥락을 담은 기준 문서입니다.
> 코드 작성 전 반드시 이 문서를 먼저 읽고 시작하세요.

---

## 1. 프로젝트 개요

### 서비스 한 줄 설명
고객이 상품에 리뷰를 남기면, LangGraph 파이프라인이 자동으로 감성을 분석하고
모든 리뷰에 대한 답변 초안을 생성해 관리자가 승인만으로 발행할 수 있는 **리뷰 자동 답변 자동화 서비스**

### 핵심 가치
- 고객 리뷰를 긍정 / 중립 / 부정으로 자동 분류
- 모든 리뷰에 대해 LLM이 감성에 맞는 답변 초안 생성 (temperature = 0.7)
  - 부정: 공감·사과·해결책 구조
  - 중립: 감사 인사 + 개선 약속 구조
  - 긍정: 감사 인사 + 재구매 유도 구조
- 관리자는 초안을 검토 후 수정 또는 그대로 승인
- 전체 리뷰에서 키워드 태그를 추출해 인사이트로 활용
  - 인사이트 = 전체 리뷰에서 자주 언급되는 키워드 TOP N 집계
  - 예) "배송 빠름", "포장 꼼꼼", "가성비" 같은 공통 키워드를 대시보드에 표시

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
- **React (TypeScript)**
- **Tailwind CSS** — 스타일링
- **SweetAlert2** — 알림 / 확인 모달

### AI
- **Gemini API (gemini-3.1-flash-lite)** — 감성 분석, 답변 생성, 키워드 추출
- **LangGraph** — 노드·엣지 기반 파이프라인 오케스트레이션

### 실행 방식
- **동기 방식** — Django 뷰에서 LangGraph를 직접 호출
- 리뷰 제출 후 LangGraph 처리가 완료될 때까지 대기 (10~30초)
- 프론트엔드에서 로딩 스피너로 대기 상태 표시

---

## 3. 데이터 소스

### 개발·시연용 더미 데이터
- **출처** : 네이버 쇼핑 리뷰 공개 데이터셋
- **URL** : `https://raw.githubusercontent.com/bab2min/corpus/master/sentiment/naver_shopping.txt`
- **형식** : `평점(1~5)\t리뷰텍스트` (탭 구분)
- **사용 방법** :
  - `rating` → txt 첫 번째 컬럼 그대로 사용
  - `text` → txt 두 번째 컬럼 그대로 사용
  - `product` → 전부 "시험 상품" 하나로 고정 배정
  - `user` → Faker(ko_KR)로 생성한 고객 계정 랜덤 배정
  - `status` → 전부 `pending`으로 시작
- **시딩 볼륨** : 500건 (LLM 호출 비용 고려)

### 시드 상품
```
네이버 쇼핑 리뷰 데이터는 상품 정보가 없으므로 단일 상품으로 고정

id=1  시험 상품  (모든 시딩 리뷰가 이 상품에 연결됨)

실제 서비스 시연용 상품은 관리자가 직접 등록 (카테고리: 주방·생활용품):
  - 스테인리스 보온 텀블러
  - 실리콘 식품 보관 용기 세트
  - 천연 대나무 도마
  - 다기능 스테인리스 주방 가위
  - 세라믹 머그컵 세트
```

---

## 4. 인증 방식

### 구글 소셜 로그인 (Only)
- 이메일/비밀번호 로그인 없음. 구글 OAuth2 만 사용
- **django-allauth** 로 구글 소셜 로그인 처리
- 로그인 성공 후 JWT 토큰 발급 → 프론트에서 LocalStorage 저장
- JWT 토큰 payload에 `role` 포함 → 프론트에서 관리자/고객 화면 분기

### users 테이블 변경
- `password_hash` 컬럼 제거 (소셜 로그인이므로 불필요)
- `google_id` 컬럼 추가 (구글 OAuth 고유 ID)
- 최초 로그인 시 users 테이블에 자동 생성
- `role` 기본값은 `customer`. 관리자는 DB에서 직접 수동 변경

---

## 5. 화면 목록 (총 7개)

### 고객 화면
| # | 화면명 | 설명 |
|---|---|---|
| 1 | 로그인 | 구글 소셜 로그인 버튼만 표시 |
| 2 | 상품 목록 | 등록된 상품 카드 목록. 클릭하면 상품 상세로 이동 |
| 3 | 상품 상세 + 리뷰 목록 | 상품 정보 + 달린 리뷰·답변 목록 + 리뷰 작성 폼 |

### 관리자 화면
| # | 화면명 | 설명 |
|---|---|---|
| 4 | 대시보드 홈 | 감성 비율 차트, 미처리 답변 건수, 최근 리뷰 요약 |
| 5 | 리뷰 목록 | 전체 리뷰. 감성·상태 필터. 클릭하면 상세로 |
| 6 | 리뷰 상세 + 답변 승인 | 원본 리뷰 + AI 초안 나란히 표시. 수정·승인 |
| 7 | 인사이트 | 전체 리뷰 키워드 TOP N 집계 차트 |

### MVP 우선순위
```
1단계 (핵심 흐름): 로그인 → 상품 상세·리뷰 작성 → 리뷰 상세·답변 승인
2단계 (고도화):   대시보드 홈, 리뷰 목록, 인사이트
```

---

## 6. DB 설계 (MySQL)

### 테이블 구성 — 5개

```
users
  └── reviews (user_id FK)
        ├── review_replies (review_id FK)  1:1
        └── review_tags    (review_id FK)  1:N

products
  └── reviews (product_id FK)
```

---

### users
구글 소셜 로그인 전용. 관리자(admin)와 고객(customer)을 role로 구분.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 기본키 자동증가 |
| email | VARCHAR(255) UNIQUE | 구글 계정 이메일 |
| google_id | VARCHAR(255) UNIQUE | 구글 OAuth 고유 ID |
| name | VARCHAR(100) | 구글 계정 표시 이름 |
| role | VARCHAR(20) | `admin` 또는 `customer`. 기본값 `customer` |
| created_at | DATETIME | 최초 로그인(가입) 일시 |

---

### products
리뷰 대상 상품. 포트폴리오용으로 최소 필드만 유지.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 기본키 자동증가 |
| name | VARCHAR(255) | 상품명 |
| category | VARCHAR(100) | 카테고리 (예: 전자기기, 식품) |
| description | TEXT | 상품 설명 |
| created_at | DATETIME | 등록 일시 |

---

### reviews ★ 핵심 테이블
고객 리뷰 원본 + LangGraph 분석 결과를 함께 저장.
`status`로 처리 단계를 추적. Django 뷰가 리뷰 저장 후 즉시 LangGraph를 동기 호출.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 기본키 자동증가 |
| user_id | BIGINT FK | 리뷰 작성 고객 → users.id |
| product_id | BIGINT FK | 어떤 상품의 리뷰인지 → products.id |
| text | TEXT | 고객이 작성한 리뷰 원문. LangGraph 입력값 |
| rating | SMALLINT | 별점 1~5 |
| sentiment_score | FLOAT | LLM이 분석한 감성 강도. -1.0(매우부정) ~ 1.0(매우긍정). 분석 전 NULL |
| sentiment_label | VARCHAR(10) | 점수를 라벨로 변환. `good` / `normal` / `bad`. 분석 전 NULL |
| category | VARCHAR(100) | LLM이 분류한 유형. 예) "배송불만", "품질우수", "재구매의향". 분석 전 NULL |
| status | VARCHAR(20) | 처리 단계. `pending` → `processing` → `done` |
| created_at | DATETIME | 리뷰 작성 일시 |
| analyzed_at | DATETIME | LangGraph 분석 완료 시각. 처리 속도 측정용. 분석 전 NULL |

**status 흐름**
```
pending     리뷰가 막 등록된 상태. LangGraph 실행 전
processing  LangGraph가 실행 중인 상태
done        분석 완료 + 답변 초안 생성 + 태그 추출 완료
```

**sentiment 설명**
```
status    = "이 리뷰를 처리했느냐" (처리 단계)
sentiment = "처리 결과가 어떤 감성이냐" (분석 결과)

예시:
  리뷰 작성 직후  → status: pending,    sentiment_score: NULL
  LangGraph 완료  → status: done,       sentiment_score: -0.85, sentiment_label: negative
```

---

### review_replies
LangGraph가 생성한 AI 답변 초안 + 관리자의 승인 이력.
모든 리뷰(긍정·중립·부정)에 답변 초안이 생성됨.
리뷰 1개에 답변은 반드시 1개 (1:1 관계, review_id UNIQUE).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 기본키 자동증가 |
| review_id | BIGINT FK UNIQUE | 어떤 리뷰의 답변인지 → reviews.id |
| draft_text | TEXT | LangGraph가 생성한 최초 답변 초안. 관리자가 검토하는 원본 |
| final_text | TEXT | 관리자가 수정한 내용. NULL이면 draft_text를 그대로 발행 |
| revision_count | SMALLINT | LangGraph 품질검토 루프 반복 횟수. 0이면 첫 초안 통과 |
| status | VARCHAR(20) | `draft`(승인대기) / `approved`(승인) |
| created_at | DATETIME | 초안 생성 일시 |
| approved_at | DATETIME | 관리자 승인 시각. 승인 전 NULL |

**draft vs final 설명**
```
draft_text   LLM이 생성한 원본 초안. 항상 존재.
final_text   관리자가 수정했을 때만 값이 있음.
발행 텍스트  final_text가 있으면 final_text, 없으면 draft_text 사용.
```

**revision_count 설명**
```
LangGraph의 review_draft 품질검토 루프가 몇 번 돌았는지 기록.
0 = 첫 초안이 품질 기준 통과
1 = 한 번 재생성 후 통과
포트폴리오에서 "평균 재생성 횟수 1.2회" 같은 수치 지표로 활용 가능
```

---

### review_tags
LangGraph가 리뷰에서 추출한 키워드 태그.
감성 구분 없이 전체 리뷰에 적용. 리뷰 1개에 태그 여러 개 (1:N 관계).
태그를 집계해 인사이트 화면의 "자주 언급된 키워드 TOP N" 차트를 만든다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | BIGINT PK | 기본키 자동증가 |
| review_id | BIGINT FK | 어떤 리뷰에서 추출됐는지 → reviews.id |
| tag | VARCHAR(100) | 추출된 키워드. 예) "배송", "포장", "가격", "품질", "재구매" |
| created_at | DATETIME | 태그 생성 일시 |

---

## 7. LangGraph 파이프라인

### ReviewState (공유 상태)
```python
class ReviewState(TypedDict):
    review_id       : int
    text            : str           # 리뷰 원문
    rating          : int           # 별점 1~5
    sentiment_score : float         # LLM 분석 결과 (-1.0 ~ 1.0)
    sentiment_label : str           # positive / neutral / negative
    category        : str           # LLM 분류 유형
    route           : str           # 분기 경로 (decide_route 결과)
    draft_text      : str           # AI 답변 초안
    revision_count  : int           # 재생성 횟수 (최대 2)
    tags            : list[str]     # 추출된 키워드 리스트
```

### 노드 구성 (Depth 5)

```
__start__
    │
    ▼
① fetch_review          DB에서 review_id로 리뷰 텍스트·별점 로드 → State 초기화
    │
    ▼
② analyze_sentiment     LLM 호출 → sentiment_score, sentiment_label, category 추출
    │                   결과를 reviews 테이블에 업데이트 (status: processing)
    ▼
③ decide_route          [conditional edge] 감성 기준으로 3-way 분기
    │
    ├─── negative ────▶ ④-A gen_reply (부정형)   공감·사과·해결책 구조 초안 생성
    │                         │
    │                         ▼
    │                    review_draft              품질 검토. 미달이면 gen_reply로 루프
    │                         │ 통과
    │                         ▼
    │                    (⑤로 합류)
    │
    ├─── neutral  ────▶ ④-B gen_reply (중립형)   감사 인사 + 개선 약속 구조 초안 생성
    │                         │
    │                         ▼
    │                    review_draft              품질 검토. 미달이면 gen_reply로 루프
    │                         │ 통과
    │                         ▼
    │                    (⑤로 합류)
    │
    └─── positive ────▶ ④-C gen_reply (긍정형)   감사 인사 + 재구매 유도 구조 초안 생성
                              │
                              ▼
                         review_draft              품질 검토. 미달이면 gen_reply로 루프
                              │ 통과
                              ▼
                         (⑤로 합류)
    │
    ▼
⑤ save_result           처리 결과를 DB에 저장
                         - 전체: review_replies 테이블에 초안 INSERT
                         - 전체: review_tags 테이블에 키워드 태그 INSERT
                         - reviews.status = done, analyzed_at 업데이트
    │
    ▼
__end__
```

**품질검토 루프는 모든 리뷰에 적용**
```
모든 감성(긍정·중립·부정)에 대해 동일한 품질 기준을 적용
최대 2회 재생성 후 강제 통과 (무한루프 방지)
```

### 분기 기준 (decide_route)

```python
def decide_route(state: ReviewState) -> str:
    score = state["sentiment_score"]
    if score < -0.3:
        return "negative"   # → gen_reply 부정형
    elif score > 0.3:
        return "positive"   # → gen_reply 긍정형
    else:
        return "neutral"    # → gen_reply 중립형
```

| 구간 | 라벨 | 답변 톤 |
|---|---|---|
| -1.0 ~ -0.3 | negative | 공감 + 사과 + 해결책 |
| -0.3 ~ 0.3 | neutral | 감사 인사 + 개선 약속 |
| 0.3 ~ 1.0 | positive | 감사 인사 + 재구매 유도 |

### review_draft 품질검토 루프 (모든 리뷰 적용)

```python
def review_draft(state: ReviewState) -> str:
    # 최대 2회까지만 재생성 (무한루프 방지)
    if state["revision_count"] >= 2:
        return "save_result"
    # 품질 기준: 100자 이상
    if len(state["draft_text"]) >= 100:
        return "save_result"
    return state["route"]   # → 해당 감성의 gen_reply로 돌아감
```

---

## 8. 시스템 데이터 플로우 (동기 방식)

```
[고객]
  상품 목록 클릭
  → 상품 상세 페이지에서 별점 + 리뷰 텍스트 작성
  → 제출 버튼 클릭

[프론트엔드 React]
  로딩 스피너 표시 ("AI가 분석 중입니다...")
  POST /api/reviews/
  → { product_id, text, rating }

[백엔드 Django — 동기 처리]
  1. Review 객체 생성 (status="pending")
  2. LangGraph 파이프라인 즉시 실행 (10~30초 소요)
     fetch_review → analyze_sentiment → decide_route
       → gen_reply (감성별 톤 다름) → review_draft 루프 (모든 감성)
       → save_result
  3. 처리 완료 후 201 응답 반환

[DB MySQL]
  reviews 업데이트 (sentiment_score, sentiment_label, category, status=done, analyzed_at)
  review_replies INSERT (draft_text, revision_count)
  review_tags INSERT (키워드 태그)

[프론트엔드 React]
  응답 수신 → 로딩 스피너 제거
  SweetAlert2로 "분석 완료" 알림
  상품 상세 페이지 리뷰 목록 갱신

[관리자]
  대시보드에서 미처리 답변(status=draft) 확인
  → 리뷰 상세 페이지: 원본 리뷰 + AI 초안 나란히 표시
  → 수정하거나 그대로 "승인" 클릭
  → review_replies.status = "approved", approved_at 기록
```
---

## 주요 주의사항

- **LangGraph 동기 실행** — 리뷰 POST API가 처리 완료까지 10~30초 블로킹. 프론트 로딩 스피너 필수
- **MySQL에서 ENUM 대신 VARCHAR** + Django choices 사용
- **sentiment_score, sentiment_label, category, analyzed_at** — LangGraph 실행 전 NULL. 프론트 NULL 처리 필수
- **revision_count 최대 2** — 무한 루프 방지 하드코딩. 모든 리뷰에 적용
- **JWT 토큰 payload에 role 포함** — 프론트에서 role로 관리자/고객 화면 분기
- **구글 로그인 최초 시** — users 테이블에 자동 INSERT. role은 customer로 고정. 관리자 지정은 DB 직접 수정
- **시딩 후 LangGraph 수동 트리거 필요** — seed_data.py는 리뷰를 pending 상태로만 적재. 별도 스크립트로 LangGraph 실행
- **LLM 모델** — gemini-3.1-flash-lite 사용. API 키는 환경변수 .env 파일에서 `GEMINI_API_KEY`로 관리
- **인사이트 = 키워드 집계** — 상품 카테고리 구분 없이 전체 리뷰 태그를 단순 집계. "배송", "품질" 같은 공통 키워드 TOP N 표시