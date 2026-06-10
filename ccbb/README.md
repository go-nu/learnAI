# ccbb — 교통사고 과실비율 RAG 파이프라인

교통사고 과실비율 관련 PDF를 문서 유형별 파서로 구조화 청킹하고,
BGE-M3 임베딩 + ChromaDB로 유사도 검색을 수행합니다.

---

## 환경 설정

```bash
pip install pdfplumber pyyaml langchain langchain-community \
            langchain-huggingface chromadb sentence-transformers
```

GPU 사용 시 CUDA 버전 `torch` 추가 설치 → 자동으로 CUDA 모드 동작.

---

## 실행

```bash
# DB 구축 + 검색
python rag_pdf_tables.py

# 기존 DB로 검색만
python rag_test.py
```

---

## 데이터 흐름

```
source/*.pdf
    ↓
[registry.py] PDF 표지 기반 파서 자동 선택
    ├─ StandardsParser   → fault_ratio_standards_2023.pdf
    ├─ ReviewCasesParser → fault_ratio_review_cases.pdf
    ├─ LawParser         → road_traffic_law.pdf
    └─ RoundaboutParser  → roundabout_fault_ratio_standards_2025.pdf
    ↓
List[Chunk]  (core / legal / precedent)
    ↓
BGE-M3 임베딩 → ChromaDB (chroma_db_bge_m3/)
```

---

## 청킹 방식

| 파서 | document_type | case 단위 | 계층(hier_level) |
|---|---|---|---|
| StandardsParser | `standards` | `보N` 번호 패턴 | level1~3 추출 |
| ReviewCasesParser | `review_cases` | 페이지 상단 한글 제목 | 없음 |
| LawParser | `law` | `제N조` 조항 | 없음 |
| RoundaboutParser | `roundabout` | `회전-N` 번호 패턴 | 없음 |

모든 파서는 사례 텍스트를 **6개 섹션**(사고상황 / 기본과실비율해설 / 수정요소해설 / 활용참고사항 / 관련법규 / 참고판례)으로 분리한 뒤 3종 청커로 청크를 생성합니다.

| chunk_type | 내용 |
|---|---|
| `core` | 사고상황 · 과실비율 · 수정요소 · 참고사항 |
| `legal` | 관련 법규 조문 (섹션 있을 때만 생성) |
| `precedent` | 법원 판결 (섹션 있을 때만 생성) |

### StandardsParser — hier_level 추출

본문 헤딩 패턴과 pdfplumber 폰트 정보(크기·bold)를 결합해 3단계 계층을 탐지합니다.

| 레벨 | 탐지 조건 | 예시 |
|---|---|---|
| `hier_level1` | `(1)` `(2)` 괄호숫자 or bold/대형 폰트 | `횡단보도 내(內) (신호등 있음)` |
| `hier_level2` | `1)` `2)` 또는 `1.` `2.` 숫자 패턴 | `자동차 녹색신호 교차로 통과 후` |
| `hier_level3` | `보N` `차N` case ID 자체 | `보1` |

---

## 주요 메타데이터

| 필드 | 설명 | 예시 |
|---|---|---|
| `document_type` | 문서 유형 | `standards` / `law` / `review_cases` / `roundabout` |
| `chunk_type` | 청크 유형 | `core` / `legal` / `precedent` |
| `file_name` | PDF 파일명 | `fault_ratio_standards_2023.pdf` |
| `case_id` | 사례 ID | `보1` / `도로교통법_제27조` |
| `chapter` | 사례 제목 | `횡단보도에서 보행자와의 사고` |
| `hier_level1~3` | 계층 (standards 전용) | — |
| `law_name` / `article_number` | 법률명·조항 (law 전용) | `도로교통법` / `제27조` |
| `basic_fault_ratio` | 기본 과실비율 | `{'차량': 70, '보행자': 30}` |

---

## 검색 필터 예시

```python
search(vectordb, "보행자 횡단 사고",   document_type="standards")
search(vectordb, "보행자 보호 의무",   chunk_type="legal")
search(vectordb, "신호위반 교차로",
       file_name="fault_ratio_standards_2023.pdf", chunk_type="core")
```

---

## 폴더 구조

```
ccbb/
├── rag_pdf_tables.py      # DB 구축 + 검색
├── rag_test.py            # 검색 전용 (기존 DB 재사용)
├── source/                # 원본 PDF (.gitignore)
├── chroma_db_bge_m3/      # ChromaDB 벡터 DB (자동 생성)
├── ccbb_html/             # 웹 UI 프로토타입
└── fault_ratio_rag/       # 청킹 패키지
    ├── models/chunk.py
    ├── parsers/           # base / pedestrian / standards / review_cases / law / roundabout / registry
    ├── chunkers/          # core / legal / precedent
    └── config.yaml
```
