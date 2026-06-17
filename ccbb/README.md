# rag_v3 — BGE-M3 + Chroma + Gemini 텍스트·표 RAG

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
GOOGLE_API_KEY=gemini_api_key
```

| 환경변수 | 사용처 |
|---|---|
| `GOOGLE_API_KEY` | Gemini LLM 답변 생성 (`gemini-2.5-flash`) |

GPU(CUDA)가 있으면 BGE-M3 임베딩이 자동으로 CUDA로 동작합니다.

---

## 실행

```bash
# DB 빌드 + CLI 질의응답
uv run python -m rag_v3.rag_runner_v3

# 소스 디렉토리 직접 지정
uv run python -m rag_v3.rag_runner_v3 --source ./my_docs
```

---

## 디렉토리 구조 및 파일별 역할

```
rag_v3/
├── __init__.py          패키지 진입점 — RagBgeM3v3 및 상수 외부 공개
├── config_v3.py         전역 상수 — 경로, 청킹 패턴, DB 설정
├── pdf_loader_v3.py     PDF 로딩·청킹 Mixin — PdfLoaderMixin
├── vectorstore_v3.py    임베딩·VectorStore·검색 Mixin — VectorstoreMixin
├── rag_chain_v3.py      LLM·프롬프트·RAG 체인 Mixin — RagChainMixin
├── rag_core_v3.py       메인 클래스 — RagBgeM3v3 (Mixin 조합)
└── rag_runner_v3.py     CLI 실행 스크립트
```

### `config_v3.py`

경로·청킹 관련 전역 상수를 정의합니다.

| 상수 | 값 | 설명 |
|---|---|---|
| `SOURCE_DIR` | `./source` | 전체 PDF 자동 로드 대상 디렉토리 |
| `DB_PATH` | `./chroma_bge_m3_v3` | ChromaDB 저장 경로 |
| `COLLECTION_NAME` | `pdf_text_table_rag` | Chroma 컬렉션 이름 |
| `IMAGE_OUTPUT_DIR` | `./data/extracted_images` | 추출 이미지 저장 경로 |
| `CASE_PATTERN` | `차N-N / 회전N-N` | 과실비율 사례 청킹 정규식 |
| `LEGAL_ARTICLE_PATTERN` | `제N조(제목)` | 법률 조항 청킹 정규식 |
| `LEGAL_ADDENDUM_PATTERN` | `부칙 <공포일자>` | 부칙 청킹 정규식 |

### `pdf_loader_v3.py` — `PdfLoaderMixin`

`SOURCE_DIR` 내의 모든 PDF를 자동으로 로드하고, 문서 유형을 자동 감지해 청킹 전략을 분기합니다.

| 메서드 | 역할 |
|---|---|
| `load_docs()` | PDF 목록 순회, 유형 감지, 청킹 전략 분기 → Document 리스트 반환 |
| `_extract_text_and_images_from_pdf()` | PyMuPDF로 페이지별 텍스트 추출, 이미지 파일 저장 |
| `_extract_table_docs()` | pdfplumber로 표 추출 → Markdown 변환 → `doc_type="table"` Document |
| `_split_by_case()` | 과실비율 문서용 — `차N-N / 회전N-N` 패턴 단위 청킹 |
| `_split_by_article()` | 법률 문서용 — `제N조(...)` 조항 단위 청킹 |
| `_split_addendum()` | 법률 문서용 — `부칙 <...>` 부칙 단위 청킹 |

**청킹 전략 자동 감지:**
- 법률 조항 패턴 감지 → `_split_by_article` + `_split_addendum`
- 과실비율 사례 패턴 감지 → `_split_by_case`
- 해당 없음 → RecursiveCharacterTextSplitter (chunk_size=800, overlap=100) 폴백

### `vectorstore_v3.py` — `VectorstoreMixin`

BGE-M3 임베딩 생성, Chroma VectorStore 빌드·로드, 유사도 검색을 담당합니다.
이미지 Document는 임베딩 대상에서 제외하며 텍스트·표만 색인합니다.

| 메서드 | 역할 |
|---|---|
| `get_embeddings()` | `BAAI/bge-m3` 로컬 임베딩 반환 (CUDA 자동 감지) |
| `create_vectorstore()` | `load_docs()` 호출 → Chroma DB 생성 및 저장 |
| `build_rag_components()` | DB 존재 여부 확인, 없으면 `create_vectorstore()` 자동 실행 → retriever 반환 |

### `rag_chain_v3.py` — `RagChainMixin`

Gemini LLM 초기화, 시스템 프롬프트 정의, RAG 체인 두 종류를 제공합니다.

| 메서드 | 역할 |
|---|---|
| `get_llm()` | `GOOGLE_API_KEY`로 Gemini LLM 초기화 |
| `basic_rag_chain()` | LCEL 기반 단순 RAG 체인 — retriever → prompt → LLM → 메타데이터 합산 |
| `runnable_lambda()` | `RunnableLambda` 기반 RAG 체인 — 전처리(쿼리 정제·컨텍스트 구성)·생성·후처리 분리 |

시스템 프롬프트는 과실비율 계산 공식(기본값·수정요소·최종값)과 법률 조항 인용 형식을 포함합니다.

### `rag_core_v3.py` — `RagBgeM3v3`

`PdfLoaderMixin`, `VectorstoreMixin`, `RagChainMixin`을 다중 상속해 단일 클래스로 조합합니다.

```python
from rag_v3 import RagBgeM3v3

rag = RagBgeM3v3()                        # 기본 (./source 디렉토리)
rag = RagBgeM3v3(source_dir="./my_docs") # 소스 디렉토리 지정

retriever = rag.build_rag_components()
llm       = rag.get_llm()
answer    = rag.basic_rag_chain(retriever, llm, "제44조 음주운전 처벌 기준은?")
```

### `rag_runner_v3.py`

CLI 진입점입니다. `build_rag_components()` → `get_llm()` 순서로 초기화하고, `q` 입력 시까지 질의응답 루프를 실행합니다. `--source` 옵션으로 소스 디렉토리를 지정할 수 있습니다.

---

## Document 타입 & 메타데이터

| doc_type | 생성 위치 | 메타데이터 필드 |
|---|---|---|
| `text` | `_split_by_*` / RecursiveCharacterTextSplitter | `source`, `page`, `doc_type`, `article_id`(조항), `section`(본문/부칙) |
| `table` | `_extract_table_docs` | `source`, `page`, `doc_type`, `table_index`, `row_count`, `col_count` |
