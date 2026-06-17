# rag_v4 — BGE-M3 + Chroma + Gemini 텍스트·표 RAG

교통사고 과실비율 PDF 및 도로교통법 PDF를 **텍스트·표** Document로 추출·색인하고,  
BGE-M3 임베딩 + ChromaDB + Gemini LLM으로 질의응답하는 RAG 패키지입니다.

---

## 환경 설정

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

## 다른 모듈에서 임포트해서 사용하기

```python
from rag_v4 import RagBgeM3v4

rag = RagBgeM3v4()                          # 기본값 (./source, CUDA 자동 감지)
rag = RagBgeM3v4(source_dir="./my_docs")   # 소스 디렉토리 지정
rag = RagBgeM3v4(embedding_device="cpu")   # 디바이스 수동 지정

retriever = rag.build_rag_components()     # DB 없으면 자동 빌드
llm       = rag.get_llm()
answer    = rag.basic_rag_chain(retriever, llm, "차1-1 사고의 과실비율은?")
```

**`RagBgeM3v4` 생성자 파라미터:**

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `source_dir` | `./source` | PDF가 담긴 디렉토리 경로 |
| `db_path` | `./chroma_bge_m3_v4` | ChromaDB 저장 경로 |
| `collection_name` | `pdf_text_table_rag` | Chroma 컬렉션 이름 |
| `image_output_dir` | `./data/extracted_images` | 추출 이미지 저장 경로 |
| `llm_model` | `gemini-3.1-flash-lite` | Gemini 모델 ID |
| `temperature` | `0.0` | LLM 출력 온도 |
| `embedding_device` | `auto` | `"auto"` / `"cuda"` / `"cpu"` |
| `search_k` | `3` | 검색 결과 상위 K개 |

---

## 디렉토리 구조 및 파일별 역할

```
rag_v4/
├── __init__.py          패키지 진입점 — RagBgeM3v4 및 상수 외부 공개
├── config_v4.py         전역 상수 — 경로, 청킹 패턴, DB 설정
├── pdf_loader_v4.py     PDF 로딩·청킹 Mixin — PdfLoaderMixin
├── vectorstore_v4.py    임베딩·VectorStore·검색 Mixin — VectorstoreMixin
├── rag_chain_v4.py      LLM·프롬프트·RAG 체인 Mixin — RagChainMixin
├── rag_core_v4.py       메인 클래스 — RagBgeM3v4 (Mixin 조합)
└── rag_runner_v4.py     CLI 실행 스크립트 (--source 옵션 지원)
```

---

## 파일별 상세 설명

### `config_v4.py`

경로·청킹 관련 전역 상수를 정의합니다.

| 상수 | 값 | 설명 |
|---|---|---|
| `SOURCE_DIR` | `./source` | 전체 PDF 자동 로드 대상 디렉토리 |
| `DB_PATH` | `./chroma_bge_m3_v4` | ChromaDB 저장 경로 |
| `COLLECTION_NAME` | `pdf_text_table_rag` | Chroma 컬렉션 이름 |
| `IMAGE_OUTPUT_DIR` | `./data/extracted_images` | 추출 이미지 저장 경로 |
| `CASE_PATTERN` | `차N-N / 회전-N` | 과실비율 사례 청킹 정규식 (줄 단독 매칭) |
| `MAX_CASE_CHARS` | `2000` | 사례 블록 최대 길이 (초과 시 추가 분할) |
| `LEGAL_ARTICLE_PATTERN` | `제N조(제목)` | 법률 조항 청킹 정규식 |
| `LEGAL_ADDENDUM_PATTERN` | `부칙 <공포일자>` | 부칙 청킹 정규식 |

---

### `pdf_loader_v4.py` — `PdfLoaderMixin`

`SOURCE_DIR` 내의 모든 PDF를 자동으로 로드하고, 문서 유형을 감지해 청킹 전략을 분기합니다.

| 메서드 | 역할 |
|---|---|
| `load_docs()` | PDF 목록 순회 → 유형 감지 → 청킹 전략 분기 → Document 리스트 반환 |
| `_extract_text_and_images_from_pdf()` | PyMuPDF로 페이지별 텍스트 추출, 이미지 파일 저장 (VL 해석 없음) |
| `_build_case_title_map_from_tables()` | pdfplumber 표 셀에서 `case_id → case_title` 매핑 생성 (1순위) |
| `_extract_case_title_from_block()` | 텍스트 줄 기반 사례명 추출 (table 매핑 실패 시 fallback) |
| `_split_by_case()` | 과실비율 문서용 — 사례번호 단위 청킹 + title-summary chunk 추가 생성 |
| `_split_by_article()` | 법률 문서용 — 조항 단위 청킹 |
| `_split_addendum()` | 법률 문서용 — 부칙 단위 청킹 |
| `_extract_table_docs()` | pdfplumber로 표 추출 → Markdown 변환 → `doc_type="table"` Document |

**청킹 전략 자동 감지 흐름 (PDF 1개당):**

```
PDF 읽기
  │
  ├─ CASE_PATTERN 감지 (전체 텍스트 기준)
  │    └─→ 사례별 청킹 (_split_by_case)
  │         table 셀 기반 case_title 매핑 (1순위) + line fallback (2순위)
  │         title-summary chunk 추가 생성
  │
  ├─ LEGAL_ARTICLE_PATTERN 감지 (앞 3페이지 기준)
  │    ├─ LEGAL_ADDENDUM_PATTERN도 감지
  │    │    └─→ 본문(_split_by_article) + 부칙(_split_addendum) 분리 청킹
  │    └─ 부칙 없음
  │         └─→ 전체 조항별 청킹 (_split_by_article)
  │
  └─ 패턴 미감지
       └─→ RecursiveCharacterTextSplitter (chunk_size=800, overlap=100) 폴백
```

**이미지 처리 방식:**  
PyMuPDF로 이미지를 `./data/extracted_images/page_N_img_M.ext` 형태로 저장합니다.  
VL 모델 해석은 없으며, 파일명만 해당 페이지 Document의 `image_refs` 메타데이터에 기록합니다.

---

### `vectorstore_v4.py` — `VectorstoreMixin`

BGE-M3 임베딩 생성, Chroma VectorStore 빌드·로드, 유사도 검색을 담당합니다.

| 메서드 | 역할 |
|---|---|
| `get_embeddings()` | `BAAI/bge-m3` 로컬 임베딩 반환 (CUDA 자동 감지, batch_size 동적 조정) |
| `create_vectorstore()` | `load_docs()` 호출 → Chroma DB 생성 및 저장 |
| `build_rag_components()` | DB 유효성 확인, 필요 시 자동 재빌드 → retriever 반환 |
| `similarity_search()` | 기본 유사도 검색 |
| `search_with_score()` | 유사도 점수 포함 검색 |
| `search_with_filter()` | 메타데이터 필터(page) 검색 |
| `search_tables_only()` | `doc_type="table"` 전용 검색 |

**CUDA 자동 감지:**  
`embedding_device="auto"` (기본값)일 때 `torch.cuda.is_available()`으로 감지합니다.  
CUDA: `batch_size=32` / CPU: `batch_size=8` (OOM 방지)

**자동 재빌드 조건** (`build_rag_components()`):
- DB 디렉토리가 없는 경우
- 표(`doc_type="table"`) Document가 0개인 경우
- `case_id` / `article_id` 메타데이터가 없는 경우
- title-summary chunk(`doc_type="summary"`)가 없는 경우

---

### `rag_chain_v4.py` — `RagChainMixin`

Gemini LLM 초기화, 시스템 프롬프트 정의, RAG 체인 두 종류를 제공합니다.

| 메서드 | 역할 |
|---|---|
| `get_llm()` | `GOOGLE_API_KEY`로 Gemini LLM 초기화 |
| `basic_rag_chain()` | LCEL 기반 RAG 체인 — 2배 후보 검색 → rerank → 상위 K 선택 → 답변 생성 |
| `runnable_lambda()` | `RunnableLambda` 기반 RAG 체인 — 전처리·생성·후처리 파이프라인 분리 |

**`basic_rag_chain()` 처리 흐름:**

```
질문 입력
  └─→ similarity_search_with_score (k × 2 후보 검색)
        └─→ _rerank_by_case_title() — case_title 기반 재순위화
              └─→ 상위 search_k 선택
                    └─→ Gemini LLM 답변 생성
                          └─→ 답변 + 참조 문서 메타데이터 반환
```

**`_rerank_by_case_title()` 동작 원리:**  
Chroma L2 점수(낮을수록 유사)에서 case_title과 질문의 **Jaccard 유사도 × boost(0.3)** 만큼 차감합니다.  
방향 반전 사례처럼 벡터 거리가 비슷한 경우 사례명 일치도로 순위를 보정합니다.

**시스템 프롬프트 포함 내용:**
- 과실비율 계산 공식 (기본값 + 수정요소 합계 → 최종값)
- 영합(zero-sum) 수정요소 적용 규칙
- 답변 형식 (사고 유형 → 기본 과실비율 → 수정요소 → 근거 → 출처 → 참조 이미지)

---

### `rag_core_v4.py` — `RagBgeM3v4`

`PdfLoaderMixin`, `VectorstoreMixin`, `RagChainMixin`을 다중 상속해 단일 클래스로 조합합니다.  
`_resolve_device()`로 `embedding_device="auto"` 시 CUDA 감지를 처리합니다.

---

### `rag_runner_v4.py`

CLI 진입점입니다. `build_rag_components()` → `get_llm()` 순서로 초기화하고,  
`q` 입력 시까지 질의응답 루프를 실행합니다.

---

## Document 타입 & 메타데이터

| `doc_type` | 생성 위치 | 설명 |
|---|---|---|
| `text` | `_split_by_case()` / `_split_by_article()` / 폴백 | 본문 청크 |
| `summary` | `_split_by_case()` | 사례명 검색 강화용 — `[사례번호] + [사례명]`만 담은 경량 청크 |
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

---

## 데이터 흐름 요약

```
./source/*.pdf
    │
    ├─ PyMuPDF       → 페이지별 텍스트 Document + 이미지 파일 저장
    ├─ pdfplumber    → 표 → Markdown Document (doc_type="table")
    │                → table 셀 기반 case_title 매핑 (과실비율 문서)
    │
    └─ 청킹 분기
         ├─ 과실비율 문서 → 사례별 text chunk + title-summary chunk
         ├─ 법률 문서    → 조항별 text chunk + 부칙별 text chunk
         └─ 기타         → RecursiveCharacterTextSplitter chunk
              │
              └─→ BAAI/bge-m3 임베딩 (CUDA 자동 감지 → CPU fallback)
                    └─→ ChromaDB (./chroma_bge_m3_v4)
                          └─→ 검색 → case_title rerank → Gemini LLM → 답변
```
