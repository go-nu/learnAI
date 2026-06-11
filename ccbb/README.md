# multimodal_rag_bge_m3 — RAG 파이프라인 전 과정 설명

교통사고 과실비율 PDF를 **텍스트·표·이미지** 세 종류의 Document로 분리 추출하고,
BGE-M3 임베딩으로 ChromaDB에 색인한 뒤 Gemini LLM으로 질의응답하는 Multimodal RAG 파이프라인입니다.

---

## 환경 설정

```bash
# 의존성 설치 (uv 사용)
uv sync

# .env 파일 생성 후 Gemini API 키 두 개 입력
cp .env.example .env
```

`.env` 파일 내용:

```
GOOGLE_API_KEY=llm용_gemini_api_key
GOOGLE_API_KEY_VISION=vision모델용_별도_gemini_api_key
```

| 환경변수 | 사용처 | 모델 |
|---|---|---|
| `GOOGLE_API_KEY` | RAG 답변 생성 LLM | `gemini-2.5-flash` |
| `GOOGLE_API_KEY_VISION` | 이미지 → 텍스트 요약 비전 모델 | `gemini-2.5-flash` |

GPU(CUDA)가 있으면 BGE-M3 임베딩이 자동으로 CUDA로 동작합니다.
CUDA 없는 환경에서는 경고 메시지 출력 후 CPU로 자동 전환됩니다.

---

## 실행

```bash
# DB 빌드 + CLI 질의응답
python multimodal_rag_bge_m3.py

# 기존 DB 재사용 (빌드 없이 검색만)
python multimodal_rag_test.py

# DB 검증 (청크 분포, 이미지 요약 확인)
python chunk_verify.py
```

---

## RAG 파이프라인 전 과정

파이프라인은 **PHASE 1 문서 추출 → PHASE 2 색인 → PHASE 3 검색·생성** 3단계로 구성됩니다.

---

### PHASE 1 — PDF → Document 변환 (`load_docs`)

`load_docs()`가 내부 메서드를 순서대로 호출하며 세 종류의 Document를 만듭니다.

```
source/*.pdf
    │
    ├─ STEP 1. PyMuPDF 텍스트·이미지 추출  (_extract_text_and_images_from_pdf)
    │           ↓ 페이지별 텍스트 Document + 이미지 파일(.png/.jpg 등) + 이미지 bbox(x0,y0,x1,y1)
    │
    ├─ STEP 2. 텍스트 청크 분할  (RecursiveCharacterTextSplitter)
    │           chunk_size=800 / overlap=100 → doc_type="text" Document 목록
    │
    ├─ STEP 3. 표 추출  (pdfplumber → _extract_table_docs)
    │           각 페이지 표 → Markdown 변환 → doc_type="table" Document
    │           └─ page_table_map 생성: {페이지번호: [pdfplumber Table 객체 목록]}
    │              (STEP 7의 bbox 매칭을 위해 Table 객체를 별도로 보관)
    │
    ├─ STEP 4. 이미지 전처리  (Pillow → _resize_images)
    │           extracted_images/ → filtered_images/
    │           긴 변 > 2240px 또는 비율 > 4.5 이면 리사이즈, PNG로 통일
    │
    ├─ STEP 5. bbox 재구성
    │           filtered 경로 ↔ all_image_infos의 bbox를 basename 키로 매칭
    │           → filtered_image_infos: List[(경로, bbox)]
    │ 
    │           (경로, bbox) 쌍으로 보관 → resize로 확장자 변경 → 파일명(확장자 제외)으로 bbox 재연결
    │
    └─ STEP 6. 이미지 요약 + 표 bbox 매칭  (_summarize_images_with_vision)
                각 이미지를 base64로 Gemini Vision에 전달 → 텍스트 요약 생성
                + _find_nearest_table 로 이미지 bbox가 표 bbox 안에 있는지 비교(margin=5px)
                  → 매칭되면 요약 뒤에 "[관련 표]\n{Markdown표}" 합산
                → doc_type="image" Document
```

---

### STEP 1 상세 — PyMuPDF 텍스트·이미지 추출

`_extract_text_and_images_from_pdf()` 가 반환하는 3개 값:

| 반환값 | 타입 | 내용 |
|---|---|---|
| `documents` | `List[Document]` | 페이지별 텍스트 Document (doc_type="text") |
| `merged_text_path` | `str` | 전체 텍스트를 합친 `.txt` 파일 경로 |
| `all_image_infos` | `List[(str, tuple)]` | 이미지별 `(파일경로, (x0,y0,x1,y1))` 튜플 |

이미지 bbox는 `page.get_image_rects(xref)[0]` 으로 추출합니다.
bbox가 없는 이미지(임베디드 방식 등)는 `None` 으로 저장됩니다.

---

### STEP 6 상세 — 이미지·표 bbox 매칭 (`_find_nearest_table`)

PyMuPDF와 pdfplumber는 **둘 다 좌상단 원점 좌표계**를 사용하므로 별도 변환 없이 직접 비교합니다.

```
표 bbox : (t_x0, t_top, t_x1, t_bottom)
이미지 bbox : (img_x0, img_y0, img_x1, img_y1)

매칭 조건 (margin=5px 오차 허용):
  t_x0 - margin ≤ img_x0  AND  t_top  - margin ≤ img_y0
  img_x1 ≤ t_x1 + margin  AND  img_y1 ≤ t_bottom + margin
```

이미지가 표 영역 안에 완전히 포함될 때만 매칭됩니다.
매칭된 표는 Markdown으로 변환해 이미지 요약 뒤에 합산합니다.

```
[이미지 Document page_content 예시]
이 이미지는 신호 없는 교차로에서 직진 A차량과 좌회전 B차량의 충돌 상황을 나타냅니다...

[관련 표]
[TABLE 0 - Page 5]
| 사고 유형 | A 과실 | B 과실 |
| --- | --- | --- |
| 차16 직진 vs 좌회전 | 30% | 70% |
```

---

### PHASE 2 — 임베딩 & 색인 (`create_vectorstore`)

```
text_chunks + table_docs + image_docs
    ↓
BAAI/bge-m3  (로컬 임베딩, CUDA 자동 감지)
    ↓
ChromaDB  →  chroma_multimodal/
    collection: "pdf_table_rag"
    메타데이터 필드: doc_type / source / page / images / table_index / row_count / col_count
```

BGE-M3는 한국어·영어 혼용 문서에 최적화된 다국어 임베딩 모델입니다.
API 키 없이 로컬에서 동작하며, GPU가 있으면 자동으로 CUDA 모드로 로드됩니다.

---

### PHASE 3 — 검색 & 생성

#### DB 로드 (`build_rag_components`)

```
chroma_multimodal/ 존재 여부 확인
    ├─ 없음 또는 table/image Document가 0개 → create_vectorstore() 자동 재빌드
    └─ 있음 → Chroma 로드 → as_retriever(k=3) 반환
```

#### 질의응답 — `runnable_lambda`

```
human_message
    │
    ├─ preprocess(query)
    │   cleaned = query.strip().rstrip("?!.")
    │   docs = retriever.invoke(cleaned)  ← ChromaDB k=3 검색
    │   컨텍스트 블록 구성:
    │     [텍스트 — p.N]  본문 텍스트
    │     [표 — p.N, 표M]  Markdown 표
    │     [이미지 — p.N, filename]  이미지 요약 + [동일 페이지 텍스트 참고]
    │   → {"context": ..., "question": ..., "retrieved_docs": docs}
    │
    ├─ RunnablePassthrough.assign(answer=...)
    │   (context + question) → ChatPromptTemplate → Gemini LLM → StrOutputParser
    │
    ├─ merge_llm_output
    │   → {"answer": ..., "retrieved_docs": docs}
    │
    └─ postprocess(inputs)
        "[교통사고 과실비율 기반 답변]\n{answer}"
        "─" * 50
        "[참조 문서 메타데이터]"
          [1] doc_type: image  │ source: ...  │ page: 5
               이미지 파일: page_5_img_1.png
          [2] doc_type: table  │ source: ...  │ page: 5
               표 인덱스: 1 / 행: 3 × 열: 4
          ...
```

#### 질의응답 — `basic_rag_chain`

`runnable_lambda`보다 단순한 LCEL 구조입니다.
`format_docs` 클로저 변수 `_retrieved`로 검색된 docs를 보관하고,
chain 실행 후 동일한 메타데이터 블록을 반환값에 합산합니다.

---

## Document 타입 & 메타데이터

| doc_type | 생성 단계 | 메타데이터 필드 |
|---|---|---|
| `text` | STEP 2 (텍스트 청크 분할) | `source`, `page`, `doc_type` |
| `table` | STEP 3 (pdfplumber 표 추출) | `source`, `page`, `doc_type`, `table_index`, `row_count`, `col_count` |
| `image` | STEP 6 (Gemini Vision 요약) | `source`, `page`, `doc_type`, `images` |

이미지 Document의 `page_content`에는 Gemini 요약과 매칭된 표(있을 경우)가 함께 포함됩니다.

---

## 이미지 전처리 규격

| 항목 | 값 | 설명 |
|---|---|---|
| `MAX_IMG_PX` | 2240px | 긴 변 최대 픽셀 |
| `MAX_IMG_RATIO` | 4.5 | 가로:세로 최대 비율 |
| `MAX_IMG_BYTES` | 20MB | 최대 파일 크기 (초과 시 건너뜀) |
| 저장 포맷 | PNG | LANCZOS 리샘플링, 확장자 통일 |
| 지원 포맷 | PNG·JPEG·WEBP·BMP | 그 외 포맷은 건너뜀 |

---

## 주요 상수

```python
PDF_PATH         = "./source/fault_ratio_standards_carvcar.pdf"
DB_PATH          = "./chroma_multimodal"
COLLECTION_NAME  = "pdf_table_rag"
IMAGE_OUTPUT_DIR = "./data/extracted_images"
FILTERED_IMG_DIR = "./data/filtered_images"
VISION_MODEL     = "gemini-2.5-flash"   # GOOGLE_API_KEY_VISION 사용
```

`RagBgeM3()` 생성 시 모든 상수를 파라미터로 오버라이드할 수 있습니다.

```python
rag = RagBgeM3(
    pdf_path="./source/other.pdf",
    db_path="./chroma_other",
    search_k=5,
    embedding_device="cuda",   # 또는 "cpu"
)
```
