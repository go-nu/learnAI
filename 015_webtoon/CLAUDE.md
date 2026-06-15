# 웹툰 모바일 서비스

네이버 웹툰 Unofficial API를 활용한 Spring Boot + Thymeleaf 기반 웹 서비스.
오늘의 웹툰 목록 조회, 웹툰 상세·화별 리스트 보기 기능을 제공한다.

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| Language | Java 21 |
| Framework | Spring Boot 4.1.0 |
| View | Thymeleaf + Tailwind CSS (CDN) |
| CSS | Tailwind CSS v3 (커스텀 테마, Be Vietnam Pro 폰트, Material Symbols 아이콘) |
| ORM | Spring Data JPA (Hibernate) |
| DB | MariaDB 10.x |
| HTTP Client | RestTemplate (`SecurityConfig`에서 `@Bean` 등록) |
| 보안 | Spring Security OAuth2 Client (현재 전체 허용, CSRF 비활성화) |
| Boilerplate | Lombok (`@Data`, `@RequiredArgsConstructor`) |
| 빌드 | Gradle |

---

## 외부 API

**베이스 URL**: `https://webtoon-crawler.nomadcoders.workers.dev`

| 엔드포인트 | 응답 타입 | 매핑 DTO | 비고 |
|---|---|---|---|
| `GET /today` | `WebtoonItem[]` | `WebtoonItem` | id, title, thumb |
| `GET /{id}` | `WebtoonItem` | `WebtoonItem` | **응답 JSON에 id 필드 없음** → PathVariable로 보완 |
| `GET /{id}/episodes` | `EpisodeItem[]` | `EpisodeItem` | id, title, thumb, date |

- IMPORTANT: `GET /{id}` 응답에는 `id` 필드가 포함되지 않는다. 컨트롤러에서 PathVariable `id`를 `webtoonId`로 모델에 직접 추가해 템플릿에 전달한다.
- `@JsonIgnoreProperties(ignoreUnknown = true)` 가 두 DTO 모두에 적용되어 있어 API에 추가 필드가 생겨도 에러가 발생하지 않는다.
- 에피소드 링크: `https://m.comic.naver.com/webtoon/detail?titleId={webtoonId}&no={ep.id}`

---

## 주요 명령어

```bash
# 개발 서버 실행
./gradlew bootRun

# 빌드 (테스트 제외)
./gradlew build -x test

# 전체 빌드 (테스트 포함)
./gradlew build

# 테스트 전체 실행
./gradlew test

# 단일 테스트 클래스 실행
./gradlew test --tests "com.matalcross.webtoon.<패키지>.<클래스명>"

# 의존성 확인
./gradlew dependencies

# JAR 패키징
./gradlew bootJar
```

---

## 프로젝트 구조

```
/
├── src/
│   ├── main/
│   │   ├── java/com/matalcross/webtoon/
│   │   │   ├── WebtoonApplication.java
│   │   │   ├── config/
│   │   │   │   ├── SecurityConfig.java        # RestTemplate Bean, Spring Security + OAuth2 설정
│   │   │   │   ├── WebMvcConfig.java          # Interceptor 등록
│   │   │   │   └── CurrentUriInterceptor.java # 모든 뷰에 currentUri 자동 주입
│   │   │   ├── controller/
│   │   │   │   └── WebtoonController.java
│   │   │   ├── service/
│   │   │   │   ├── WebtoonService.java        # 외부 API 호출 + DB 저장
│   │   │   │   └── UserService.java           # 회원 조회 (getUserByEmail, getOAuthAccounts)
│   │   │   ├── oauth/
│   │   │   │   └── CustomOAuth2UserService.java # Google OAuth2 처리 + users/user_oauth_accounts 저장
│   │   │   ├── repository/
│   │   │   │   ├── WebtoonRepository.java     # JpaRepository<Webtoon, Long>
│   │   │   │   ├── EpisodeRepository.java     # JpaRepository<Episode, Long>
│   │   │   │   ├── UserRepository.java        # JpaRepository<User, Long>
│   │   │   │   └── UserOAuthAccountRepository.java
│   │   │   ├── entity/
│   │   │   │   ├── Webtoon.java               # webtoons 테이블 매핑
│   │   │   │   ├── Episode.java               # episodes 테이블 매핑
│   │   │   │   ├── User.java                  # users 테이블 매핑
│   │   │   │   └── UserOAuthAccount.java      # user_oauth_accounts 테이블 매핑
│   │   │   └── dto/
│   │   │       ├── WebtoonItem.java           # id, title, thumb
│   │   │       └── EpisodeItem.java           # id, title, thumb, date, rating
│   │   └── resources/
│   │       ├── application.properties
│   │       └── templates/webtoon/
│   │           ├── inc_head.html              # 공통 헤더 fragment (로그인/로그아웃 포함)
│   │           ├── inc_foot.html              # 공통 하단 내비 fragment
│   │           ├── home.html                  # 홈 (오늘의 웹툰, Hero, 랭킹)
│   │           ├── webtoon_list.html          # 웹툰 상세 + 화별 리스트
│   │           ├── weekly.html                # 요일별 웹툰 (DB createdAt 요일 기준)
│   │           ├── login.html                 # 구글 로그인 페이지
│   │           ├── search.html                # 검색
│   │           ├── storage.html               # 보관함
│   │           └── mypage.html                # 마이페이지 (회원 정보)
│   └── test/
│       └── java/com/matalcross/webtoon/
├── build.gradle
├── settings.gradle
└── CLAUDE.md
```

---

## 라우트 구조

| HTTP | URL | 컨트롤러 메서드 | 템플릿 | 설명 |
|---|---|---|---|---|
| GET | `/` | `home()` | `webtoon/home` | 오늘의 웹툰 목록 |
| GET | `/webtoon/{id}` | `webtoonList()` | `webtoon/webtoon_list` | 웹툰 상세 + 화별 리스트 |
| GET | `/weekly` | `weekly()` | `webtoon/weekly` | 요일별 웹툰 |
| GET | `/search` | `search()` | `webtoon/search` | 검색 |
| GET | `/storage` | `storage()` | `webtoon/storage` | 보관함 |
| GET | `/mypage` | `mypage()` | `webtoon/mypage` | 마이페이지 (회원 정보) |
| GET | `/login` | `login()` | `webtoon/login` | 구글 로그인 페이지 |

### `/webtoon/{id}` 모델 속성

| 속성명 | 타입 | 출처 |
|---|---|---|
| `webtoon` | `WebtoonItem` | `GET /{id}` API |
| `webtoonId` | `String` | PathVariable (id 필드 null 보완용) |
| `episodes` | `List<EpisodeItem>` | `GET /{id}/episodes` API |

### `/weekly` 모델 속성

| 속성명 | 타입 | 설명 |
|---|---|---|
| `weeklyWebtoons` | `Map<String, List<WebtoonItem>>` | 요일(MONDAY…SUNDAY)별 웹툰 목록 (DB createdAt 기준) |
| `dayLabels` | `Map<String, String>` | 요일 한글 레이블 (예: MONDAY → 월) |
| `today` | `String` | 현재 요일 (예: THURSDAY) |

### `/mypage` 모델 속성

| 속성명 | 타입 | 설명 |
|---|---|---|
| `userProfile` | `User` | DB에서 조회한 회원 엔티티 (미로그인 시 null) |
| `oauthAccounts` | `List<UserOAuthAccount>` | 연결된 소셜 계정 목록 |

---

## 데이터베이스

**접속 정보** (`application.properties`):
```
spring.datasource.url=jdbc:mariadb://localhost:3306/webtoondb
spring.datasource.username=webtoon
spring.datasource.password=1234
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MariaDBDialect
```

### 테이블 구조 개요

```
콘텐츠 영역
├── webtoons          웹툰 마스터 (네이버 외부 ID 기반)
├── genres            장르 마스터
├── webtoon_genres    웹툰-장르 N:M
└── episodes          에피소드

회원 영역
├── users             회원 기본 정보 (소프트 삭제)
├── roles             권한 마스터 (USER / ADMIN)
├── user_roles        회원-권한 N:M
├── user_oauth_accounts  소셜 로그인 연동 (naver/kakao/google/apple)
├── refresh_tokens    JWT 리프레시 토큰 (해시값만 저장)
├── email_verifications  이메일 인증 토큰
└── password_resets   비밀번호 재설정 토큰

회원 ↔ 콘텐츠 연결 영역
├── favorites         즐겨찾기 (users ↔ webtoons)
├── episode_reads     에피소드 열람 기록 (users ↔ episodes)
└── comments          에피소드 댓글 (소프트 삭제)

관리자 영역
└── admin             관리자 계정 (ID/PW 기반)
```

---

### 1. 콘텐츠 영역

#### webtoons — 웹툰 마스터

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | 내부 PK |
| `source_id` | VARCHAR(50) | NOT NULL, UNIQUE | 네이버 웹툰 외부 ID (예: `790713`) |
| `title` | VARCHAR(255) | NOT NULL | 웹툰 제목 |
| `about` | TEXT | | 줄거리 |
| `age_rating` | VARCHAR(50) | | 연령등급 (예: 전체연령가) |
| `thumb_url` | VARCHAR(500) | | 썸네일 이미지 URL |
| `is_today` | BOOLEAN | NOT NULL, DEFAULT FALSE | 오늘의 웹툰 노출 여부 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | |
| `updated_at` | DATETIME | NOT NULL, ON UPDATE NOW | |

- IMPORTANT: 외부 API의 `id` 값은 `source_id`에 저장. 내부 JOIN은 `id`(PK) 사용

#### genres — 장르 마스터

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE | 장르명 (예: 일상, 에피소드) |

- API `genre` 필드(`"에피소드, 일상"` 형태 쉼표 문자열)를 파싱해 정규화 저장

#### webtoon_genres — 웹툰-장르 N:M

| 컬럼 | 타입 | 제약 |
|---|---|---|
| `webtoon_id` | BIGINT | PK, FK → webtoons.id (CASCADE) |
| `genre_id` | INT | PK, FK → genres.id (CASCADE) |

#### episodes — 에피소드

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | |
| `webtoon_id` | BIGINT | NOT NULL, FK → webtoons.id | |
| `source_id` | VARCHAR(50) | NOT NULL | 외부 에피소드 ID |
| `title` | VARCHAR(255) | NOT NULL | 에피소드 제목 |
| `rating` | DECIMAL(4,2) | | 별점 (예: 9.85, 최대 99.99) |
| `published_date` | VARCHAR(50) | | 게재일 (API `date` 필드) |
| `created_at` | DATETIME | NOT NULL | |

- UNIQUE KEY: `(webtoon_id, source_id)`

---

### 2. 회원 영역

#### users — 회원 기본 정보

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | 로그인 ID |
| `password_hash` | VARCHAR(255) | NULL 허용 | 소셜 전용 계정은 NULL |
| `nickname` | VARCHAR(50) | NOT NULL, UNIQUE | |
| `profile_image_url` | VARCHAR(500) | | |
| `status` | ENUM | NOT NULL, DEFAULT 'active' | `active` / `dormant` / `suspended` / `withdrawn` |
| `email_verified_at` | DATETIME | | 이메일 인증 완료 시각 |
| `last_login_at` | DATETIME | | |
| `created_at` | DATETIME | NOT NULL | |
| `updated_at` | DATETIME | NOT NULL | |
| `deleted_at` | DATETIME | | 탈퇴 시각 (소프트 삭제) |

- IMPORTANT: 소프트 삭제 — 조회 시 `deleted_at IS NULL` 필터 필수
- 소셜 전용 계정은 `password_hash = NULL` → 비밀번호 재설정 엔드포인트 차단 필요

#### roles — 권한 마스터

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INT PK | |
| `name` | VARCHAR(50) UNIQUE | `USER` / `ADMIN` |
| `description` | VARCHAR(255) | 권한 설명 |

- 기초 데이터(Seed): `USER` (일반 회원), `ADMIN` (관리자)

#### user_roles — 회원-권한 N:M

| 컬럼 | 타입 | 제약 |
|---|---|---|
| `user_id` | BIGINT | PK, FK → users.id (CASCADE) |
| `role_id` | INT | PK, FK → roles.id (CASCADE) |
| `granted_at` | DATETIME | NOT NULL, DEFAULT NOW |

#### user_oauth_accounts — 소셜 로그인 연동

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK | → users.id (CASCADE) |
| `provider` | ENUM | `naver` / `kakao` / `google` / `apple` |
| `provider_user_id` | VARCHAR(255) | 제공자 측 고유 ID |
| `created_at` | DATETIME | |

- UNIQUE KEY: `(provider, provider_user_id)`
- 한 회원이 여러 소셜 계정 연결 가능

#### refresh_tokens — JWT 리프레시 토큰

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK | → users.id (CASCADE) |
| `token_hash` | VARCHAR(255) | 토큰 해시값 (원문 저장 금지) |
| `device_info` | VARCHAR(255) | 디바이스/브라우저 정보 |
| `expires_at` | DATETIME | 만료 시각 |
| `revoked_at` | DATETIME | 폐기(로그아웃) 시각 |
| `created_at` | DATETIME | |

#### email_verifications — 이메일 인증

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK | → users.id (CASCADE) |
| `token` | VARCHAR(255) UNIQUE | 인증 토큰 |
| `expires_at` | DATETIME | 만료 시각 |
| `verified_at` | DATETIME | 인증 완료 시각 |
| `created_at` | DATETIME | |

#### password_resets — 비밀번호 재설정

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK | → users.id (CASCADE) |
| `token` | VARCHAR(255) UNIQUE | 재설정 토큰 |
| `expires_at` | DATETIME | 만료 시각 |
| `used_at` | DATETIME | 사용 시각 |
| `created_at` | DATETIME | |

---

### 3. 회원 ↔ 콘텐츠 연결 영역

#### favorites — 즐겨찾기

| 컬럼 | 타입 | 제약 |
|---|---|---|
| `user_id` | BIGINT | PK, FK → users.id (CASCADE) |
| `webtoon_id` | BIGINT | PK, FK → webtoons.id (CASCADE) |
| `created_at` | DATETIME | NOT NULL |

#### episode_reads — 에피소드 열람 기록

| 컬럼 | 타입 | 제약 |
|---|---|---|
| `user_id` | BIGINT | PK, FK → users.id (CASCADE) |
| `episode_id` | BIGINT | PK, FK → episodes.id (CASCADE) |
| `read_at` | DATETIME | NOT NULL |

#### comments — 에피소드 댓글

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | |
| `user_id` | BIGINT FK | → users.id (CASCADE) |
| `episode_id` | BIGINT FK | → episodes.id (CASCADE) |
| `content` | TEXT | 댓글 내용 |
| `created_at` | DATETIME | |
| `deleted_at` | DATETIME | 소프트 삭제 |

---

### 4. 관리자 영역

#### admin — 관리자 계정

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT | |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | 관리자 로그인 ID |
| `password` | VARCHAR(255) | NOT NULL | 비밀번호 (해시 저장 권장) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |

```sql
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

- users 테이블과 별도로 관리되는 독립 관리자 계정 테이블
- IMPORTANT: `password` 컬럼에 평문 저장 금지 — BCrypt 등 해시 알고리즘 사용 필수

---

## 프론트엔드 (Thymeleaf + Tailwind)

- Tailwind CSS는 CDN으로 로드: `https://cdn.tailwindcss.com?plugins=forms,container-queries`
- 커스텀 테마는 각 HTML의 `<script id="tailwind-config">` 인라인 블록에 정의 (새 페이지 추가 시 동일 블록 복사)
- 주요 커스텀 색상: `primary: #006e2e`, `surface: #f8f9fc`, `on-surface: #191c1e`
- 아이콘: Google Material Symbols Outlined (CDN)
- 폰트: Be Vietnam Pro (Google Fonts)
- 공통 헤더: `th:replace="~{webtoon/inc_head :: head}"`
- 공통 하단 내비: `th:replace="~{webtoon/inc_foot :: foot}"`
- `currentUri` 변수는 `CurrentUriInterceptor`가 모든 뷰에 자동 주입 → 하단 내비 활성 탭 표시에 사용

---

## 코드 스타일

- DTO는 Lombok `@Data` 클래스 사용 (record 미사용)
- 외부 API 응답 DTO에 `@JsonIgnoreProperties(ignoreUnknown = true)` 필수
- 서비스 레이어에서 RestTemplate으로 외부 API 호출; API 호출은 `WebtoonService`에만 작성
- `@RequiredArgsConstructor` + `final` 필드로 생성자 주입
- `RestTemplate` Bean은 `SecurityConfig`에 정의
- 네이밍: 클래스 `PascalCase`, 메서드·변수 `camelCase`, Thymeleaf 변수 `camelCase`
- 새 페이지 추가 순서: DTO → Service 메서드 → Controller `@GetMapping` → Thymeleaf 템플릿

---

## 워크플로우 규칙

- 외부 API 호출은 `WebtoonService`에만 작성; 컨트롤러에서 직접 HTTP 호출 금지
- 새 API 응답 필드 매핑 시 DTO에 `@JsonIgnoreProperties(ignoreUnknown = true)` 확인
- Tailwind 커스텀 테마 변경 시 모든 HTML 파일의 `tailwind.config` 블록을 동일하게 유지
- `currentUri` 기반 내비 활성화 로직은 `inc_foot.html`에만 작성

---

## 주의 사항

- IMPORTANT: `GET /{id}` API 응답에 `id` 필드가 없으므로 `webtoon.id` 대신 모델의 `webtoonId`를 사용할 것
- IMPORTANT: 네이버 웹툰 에피소드 URL은 모바일 버전 사용: `https://m.comic.naver.com/webtoon/detail?titleId={webtoonId}&no={ep.id}`
- `application.properties`의 DB 패스워드를 코드에 하드코딩하지 말 것
- Spring Security는 현재 전체 허용(`anyRequest().permitAll()`) 상태 — 인증이 필요한 기능 추가 시 반드시 Security 설정 수정 필요
