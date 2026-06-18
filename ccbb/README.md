# rag_v4 — BGE-M3 + Chroma + Gemini 텍스트·표·이미지 RAG

> 교통사고 과실비율 PDF 및 도로교통법 PDF를 텍스트·표 Document로 추출·색인하고,  
> PDF 내 이미지를 페이지별로 추출·저장하여 답변 시 참조 이미지 파일명을 함께 제공합니다.  
> BGE-M3 임베딩 + ChromaDB + Gemini LLM으로 질의응답하는 RAG 패키지입니다.

---

## 환경 설정

의존성은 `pyproject.toml`에 정의되어 있습니다. `uv`로 설치합니다.

```bash
uv sync

cp .env.example .env
```

`.env` 파일:

```
GOOGLE_API_KEY=your_gemini_api_key
```

| 환경변수 | 사용처 |
|---|---|
| `GOOGLE_API_KEY` | Gemini LLM 답변 생성 |

CUDA가 설치되어 있으면 BGE-M3 임베딩이 자동으로 GPU를 사용합니다.  
감지에 실패하거나 `torch`가 없으면 CPU로 폴백합니다.

CUDA 인식 확인:

```bash
uv run python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
```

---

## 실행

```bash
# DB 빌드 + CLI 질의응답 (./source 폴더 PDF 자동 로드)
uv run python -m rag_v4.rag_runner_v4

# 소스 디렉토리 직접 지정
uv run python -m rag_v4.rag_runner_v4 --source ./my_docs
```

CLI 안에서 `q` 입력 시 종료합니다.

---

## 디렉토리 구조 및 파일별 역할

```
rag_v4/
├── __init__.py            패키지 선언 — 상대 import 및 python -m 실행 활성화
├── config_v4.py           전역 상수 — 경로, 청킹 패턴, DB 설정
├── pdf_loader_v4.py       PDF 로딩·청킹 Mixin — PdfLoaderMixin
├── vectorstore_v4.py      임베딩·VectorStore·검색 Mixin — VectorstoreMixin
├── rag_chain_v4_1.py      LLM·프롬프트·RAG 체인 Mixin — RagChainMixin
├── rag_core_v4.py         메인 클래스 — RagBgeM3 (Mixin 조합)
└── rag_runner_v4.py       CLI 실행 스크립트 (--source 옵션 지원)
```

`rag_core_v4.py`는 `rag_chain_v4_1.py`의 `RagChainMixin`을 import해 사용합니다.

---

## 파일별 상세 설명

### `config_v4.py`

경로·청킹 관련 전역 상수를 정의합니다. 모든 Mixin이 이 파일의 값을 공유합니다.

| 상수 | 설명 |
|---|---|
| `SOURCE_DIR` | 전체 PDF 자동 로드 대상 디렉토리 (`./source`) |
| `DB_PATH` | ChromaDB 저장 경로 (`./chroma_bge_m3_v4`) |
| `COLLECTION_NAME` | Chroma 컬렉션 이름 |
| `IMAGE_OUTPUT_DIR` | 추출 이미지 저장 경로 (`./data/extracted_images`) |
| `CASE_PATTERN` | 과실비율 사례 청킹 정규식 — 줄 단독으로 나타나는 `차N-N` / `회전-N` 패턴만 경계로 인식 |
| `MAX_CASE_CHARS` | 사례 블록 최대 길이 (초과 시 추가 분할, 기본 2000자) |
| `LEGAL_ARTICLE_PATTERN` | 법률 조항 청킹 정규식 (`제N조(제목)` 형식) |
| `LEGAL_ADDENDUM_PATTERN` | 부칙 청킹 정규식 (`부칙 <공포일자>` 형식) |

---

### `pdf_loader_v4.py` — `PdfLoaderMixin`

`SOURCE_DIR` 내의 모든 PDF를 순회하며, 문서 유형을 자동 감지해 청킹 전략을 분기합니다.

| 메서드 | 역할 |
|---|---|
| `load_docs()` | PDF 목록 순회 → 유형 감지 → 청킹 전략 분기 → Document 리스트 반환 |
| `_extract_text_and_images_from_pdf()` | PyMuPDF로 페이지별 텍스트 추출, 이미지를 파일로 저장 |
| `_build_case_title_map_from_tables()` | pdfplumber 표 셀에서 `case_id → case_title` 매핑 생성 (1순위) |
| `_extract_case_title_from_block()` | 텍스트 줄 기반 사례명 추출 (table 매핑 실패 시 2순위 fallback) |
| `_split_by_case()` | 과실비율 문서 — 사례번호 단위 청킹 + title-summary chunk 추가 생성 |
| `_split_by_article()` | 법률 문서 — 조항 단위 청킹 |
| `_split_addendum()` | 법률 문서 — 부칙 단위 청킹 |
| `_extract_table_docs()` | pdfplumber로 표 추출 → Markdown 변환 → `doc_type="table"` Document 생성 |

**이미지 처리 방식**  
PyMuPDF로 이미지를 `./data/extracted_images/page_N_img_M.ext` 형태로 저장합니다.  
VL 모델 해석은 없으며, 파일명만 해당 페이지 Document의 `image_refs` 메타데이터에 기록합니다.

---

### `vectorstore_v4.py` — `VectorstoreMixin`

BGE-M3 임베딩 생성, Chroma VectorStore 빌드·로드, 유사도 검색을 담당합니다.

| 메서드 | 역할 |
|---|---|
| `get_embeddings()` | `BAAI/bge-m3` 로컬 임베딩 반환 (CUDA 자동 감지, batch_size 동적 조정) |
| `create_vectorstore()` | `load_docs()` 호출 → Chroma DB 생성 및 저장 |
| `build_rag_components()` | DB 유효성 확인, 조건 불충족 시 자동 재빌드 → retriever 반환 |
| `similarity_search()` | 기본 유사도 검색 |
| `search_with_score()` | 유사도 점수 포함 검색 |
| `search_with_filter()` | 메타데이터 필터(page) 검색 |
| `search_tables_only()` | `doc_type="table"` 전용 검색 |

**CUDA 자동 감지**  
`embedding_device="auto"` (기본값)일 때 `torch.cuda.is_available()`으로 감지합니다.  
CUDA: `batch_size=32` / CPU: `batch_size=8` (OOM 방지)

**자동 재빌드 조건** (`build_rag_components()` 내부 판단):
- DB 디렉토리가 없는 경우
- 표(`doc_type="table"`) Document가 0개인 경우
- `case_id` / `article_id` 메타데이터가 없는 경우
- title-summary chunk(`doc_type="summary"`)가 없는 경우

---

### `rag_chain_v4_1.py` — `RagChainMixin`

Gemini LLM 초기화, 시스템 프롬프트 정의, RAG 체인을 제공합니다.

| 메서드 / 함수 | 역할 |
|---|---|
| `get_llm()` | `GOOGLE_API_KEY`로 Gemini LLM 초기화 |
| `basic_rag_chain()` | LCEL 기반 RAG 체인 — 2배 후보 검색 → rerank → 표 사후 fetch → 답변 생성 |
| `runnable_lambda()` | `RunnableLambda` 기반 RAG 체인 — 전처리·생성·후처리 파이프라인 분리 |
| `_rerank_by_case_title()` | case_title과 질문의 Jaccard 유사도로 검색 결과 순위 재조정 |
| `_fetch_missing_tables()` | rerank 결과에 누락된 표를 인접 페이지 기반으로 사후 fetch |
| `_format_docs_to_context()` | Document 리스트를 출처·doc_type 레이블 포함 텍스트 블록으로 변환 |
| `_build_meta_lines()` | 참조 문서 메타데이터(사례번호, 유사도 등)를 답변 말미에 표시 |

**① 시스템 프롬프트 — 동치 판단 기준 추가**  
검색된 문서가 질문과 동일한 사고 유형인지 판단할 때, 단어 일치가 아닌 아래 핵심 요소의 **의미적 일치**를 기준으로 판단하도록 명시되어 있습니다.

| 핵심 요소 | 내용 |
|---|---|
| (a) | 각 차량의 출발 위치 관계 (동일 도로/교차 도로, 좌측/우측) |
| (b) | 각 차량의 진행 동작 (직진/좌회전/우회전/차로변경 등) |
| (c) | 교차로의 신호 유무 및 도로폭 동일 여부 |
| (d) | 사고의 구조적 원인 (회전반경 차이, 진입 순서, 우선권 등) |

"찾을 수 없다"는 결론은 모든 검색 문서를 검토한 이후에만 내리도록, 먼저 (a)~(d) 대조를 자문하는 단계가 강제되어 있습니다.

**② 시스템 프롬프트 — few-shot 예시 추가**  
질문 표현과 문서 표현이 다르더라도 동일 유형으로 매핑되는 구체 예시 2개가 프롬프트에 포함되어 있습니다. 예) `"동일 방향으로 진행하다 회전반경 차이로 충돌"` = `"크게 또는 작게 좌회전하다 충돌"` (차17-1 동일 유형).

**③ `_fetch_missing_tables()` — 표 사후 fetch**  
벡터 검색만으로는 자연어 설명과 임베딩 거리가 먼 표(TABLE) 문서가 누락될 수 있습니다.  
이를 보완하기 위해 rerank 직후 아래 절차로 표를 추가 수집합니다.

1. rerank 결과(`final`)에서 `case_id`가 있으나 TABLE이 없는 문서를 추출
2. 해당 문서의 page ±1 범위에서 Chroma 메타데이터 필터(`source`, `page`, `doc_type=table`)로 직접 조회
3. 중복 없이 `final`에 추가 → LLM 컨텍스트에 포함

표 사후 fetch로 추가된 문서는 벡터 유사도 점수가 없으므로 메타데이터 출력에서 `유사도: N/A`로 표시됩니다.

---

### `rag_core_v4.py` — `RagBgeM3`

`PdfLoaderMixin`, `VectorstoreMixin`, `RagChainMixin`을 다중 상속해 단일 클래스로 조합합니다.  
직접 기능 로직은 없으며, 생성자에서 파라미터를 받아 각 Mixin에 전달하고 `embedding_device="auto"` 시 CUDA 감지를 처리합니다.

---

### `rag_runner_v4.py`

CLI 진입점입니다. `build_rag_components()` → `get_llm()` 순서로 초기화하고, `q` 입력 시까지 질의응답 루프를 실행합니다. `--source` 옵션으로 PDF 디렉토리를 런타임에 지정할 수 있습니다.

---

## Document 타입 & 메타데이터

| `doc_type` | 생성 위치 | 설명 |
|---|---|---|
| `text` | `_split_by_case()` / `_split_by_article()` / 폴백 | 본문 청크 |
| `summary` | `_split_by_case()` | 사례명 검색 강화용 — 사례번호 + 사례명만 담은 경량 청크 |
| `table` | `_extract_table_docs()` | pdfplumber 표 → Markdown 변환 청크 |

**과실비율 문서 `text` / `summary` chunk 메타데이터:**

| 필드 | 설명 |
|---|---|
| `case_id` | 사례 번호 (예: `차1-1`, `회전-10`) |
| `case_title` | 사례명 (예: `후진입 차량이 차로변경하여 진출한 사고`) |
| `has_exit` | 진출 관련 사고 여부 (`bool`) |
| `has_lane_change` | 차로변경 관련 사고 여부 (`bool`) |
| `lane_change_actor` | 차로변경 행위 주체 (`"후진입 차량"` / `"선진입 차량"` / `"회전 중 차량"`) |
| `collision_stage` | 충돌 발생 단계 (`"후진입 직후"` / `"진출 과정"` / `"회전 중"`) |
| `image_refs` | 동일 페이지 이미지 파일명 목록 (`,` 구분) |

**법률 문서 `text` chunk 메타데이터:**

| 필드 | 설명 |
|---|---|
| `article_id` | 조항 제목 (예: `제44조(술에 취한 상태에서의 운전 금지)`) 또는 부칙 선언문 |
| `section` | `"본문"` 또는 `"부칙"` |

**`table` chunk 메타데이터:**

| 필드 | 설명 |
|---|---|
| `table_index` | 페이지 내 표 순번 |
| `row_count` | 행 수 |
| `col_count` | 열 수 |
| `image_refs` | 동일 페이지 이미지 파일명 목록 |

> **주의:** 현재 `table` 문서에는 `case_id`가 태깅되어 있지 않습니다.  
> 이로 인해 벡터 검색만으로는 사고 설명 질문 시 표가 누락될 수 있습니다.  
> `rag_chain_v4_1.py`의 `_fetch_missing_tables()`가 이를 인접 페이지 기반으로 보완합니다.

---

## 데이터 흐름 요약

```
./source/*.pdf
    │
    ├─ PyMuPDF       → 페이지별 텍스트 Document + 이미지 파일 저장
    ├─ pdfplumber    → 표 → Markdown Document (doc_type="table")
    │                → table 셀 기반 case_title 매핑 (과실비율 문서)
    │
    └─ 청킹 분기 (load_docs 내 자동 감지)
         ├─ CASE_PATTERN 감지 (전체 텍스트)
         │    └─→ 사례별 청킹 (_split_by_case)
         │         case_title_map 1순위, 줄 기반 추출 2순위
         │         본문 chunk + title-summary chunk 생성
         │
         ├─ LEGAL_ARTICLE_PATTERN 감지 (앞 3페이지)
         │    ├─ LEGAL_ADDENDUM_PATTERN도 감지
         │    │    └─→ 본문(_split_by_article) + 부칙(_split_addendum) 분리 청킹
         │    └─ 부칙 없음
         │         └─→ 전체 조항별 청킹 (_split_by_article)
         │
         └─ 패턴 미감지
              └─→ RecursiveCharacterTextSplitter (chunk_size=800, overlap=100) 폴백

                   └─→ BAAI/bge-m3 임베딩 (CUDA 자동 감지 → CPU fallback)
                         └─→ ChromaDB (./chroma_bge_m3_v4)
                               └─→ 벡터 검색 (search_k × 2 후보)
                                     └─→ case_title Jaccard rerank
                                           └─→ 표 사후 fetch (_fetch_missing_tables)
                                                 └─→ Gemini LLM → 답변
```

---

## 오류 메시지 안내

| 상황 | 출력 메시지 | 해결 방법 |
|---|---|---|
| `GOOGLE_API_KEY` 미설정 | `GOOGLE_API_KEY 환경 변수를 설정해주세요.` | `.env`에 키 추가 후 재실행 |
| `./source`에 PDF 없음 | `'./source' 디렉토리에 PDF 파일이 없습니다.` | PDF를 `./source`에 복사하거나 `--source` 옵션으로 경로 지정 |
| VectorStore 빌드 실패 | `VectorStore 빌드에 실패했습니다.` | PDF 추출 결과가 비어 있는지 확인 |
| CUDA 없음 (정상 동작) | `임베딩 디바이스 자동 감지: CPU` | 오류 아님 — CPU로 자동 폴백 (`batch_size=8`) |
