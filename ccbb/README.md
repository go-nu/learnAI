# ccbb — 교통사고 과실비율 RAG 파이프라인

교통사고 과실비율 관련 PDF 문서를 **문서 유형별 전용 파서**로 구조화 청킹하고,
BGE-M3 임베딩 + ChromaDB 벡터 DB에 적재해 유사도 검색을 수행하는 파이프라인입니다.

---

## 환경 설정

**Python 3.11 이상 필요**

```bash
pip install pdfplumber pyyaml langchain langchain-community \
            langchain-huggingface chromadb sentence-transformers
```

> GPU 사용 시 `torch`(CUDA 버전)를 추가 설치하면 자동으로 CUDA 모드로 동작합니다.
> CPU만 있어도 실행 가능합니다.

---

## 실행 방법

```bash
python rag_pdf_tables.py
```

`source/` 폴더 안의 PDF 전체를 자동 처리합니다.

1. 각 PDF에 맞는 파서를 자동 선택해 구조화 청킹
2. BGE-M3 모델로 임베딩 생성 (GPU/CPU 자동 감지)
3. ChromaDB 벡터 DB 구축
4. 테스트 쿼리 실행 후 인터랙티브 검색 모드 진입

---

## 데이터 흐름

```
source/*.pdf
    │
    ▼
[registry.py] — PDF 표지 내용으로 문서 유형 판별
    │
    ├─ StandardsParser   (fault_ratio_standards_2023.pdf)
    ├─ ReviewCasesParser (fault_ratio_review_cases.pdf)
    ├─ LawParser         (road_traffic_law.pdf)
    └─ RoundaboutParser  (roundabout_fault_ratio_standards_2025.pdf)
    │
    ▼
List[Chunk]  ←  core / legal / precedent 청크
    │
    ▼
BGE-M3 임베딩  →  ChromaDB (chroma_db_bge_m3/)
    │
    ▼
유사도 검색 (similarity_search_with_relevance_scores)
```

---

## 폴더 · 파일 역할

```
ccbb/
│
├── rag_pdf_tables.py          # ★ 메인 실행 파일
│                              #   - source/ PDF 전체 처리 → ChromaDB 구축
│                              #   - fault_ratio_rag 패키지 파서를 우선 사용,
│                              #     미지원 포맷은 레거시 PDFPlumber 청킹으로 폴백
│                              #   - GPU/CPU 자동 감지 (torch.cuda.is_available)
│                              #   - 인터랙티브 검색 모드 포함
│
├── source/                    # 원본 PDF 저장 폴더 (.gitignore 등록됨)
│   ├── fault_ratio_standards_2023.pdf          # 과실비율 인정기준서 (보행자편)
│   ├── fault_ratio_review_cases.pdf            # 과실비율 심의사례집
│   ├── road_traffic_law.pdf                    # 도로교통법 (법률 원문)
│   └── roundabout_fault_ratio_standards_2025.pdf  # 회전교차로 과실비율 기준서
│
├── chroma_db_bge_m3/          # ChromaDB 벡터 DB (실행 시 자동 생성/갱신)
│
├── ccbb_html/                 # 웹 UI 프로토타입 (HTML/Tailwind CSS)
│   ├── landing.html           # 메인 화면 (파일 업로드 UI)
│   ├── upload.html            # 업로드 화면
│   ├── analyzing.html         # 처리 중 상태 화면
│   ├── search.html            # 검색 화면
│   └── result.html            # 검색 결과 화면
│
├── fault_ratio_rag/           # 과실비율 문서 전용 구조화 청킹 패키지
│   │
│   ├── models/
│   │   └── chunk.py           # 데이터 모델 정의
│   │                          #   - Chunk: text + metadata 쌍
│   │                          #   - ChunkMetadata: case_id, chunk_type,
│   │                          #     document_type, chapter, hierarchy,
│   │                          #     article_number, law_name 등
│   │
│   ├── parsers/
│   │   ├── base_parser.py         # 추상 베이스 클래스
│   │   │                          #   - is_skippable_page(): 목차·서문 페이지 필터
│   │   │                          #   - _load_pages(): pdfplumber PDF 로드
│   │   │                          #   - detect_cases() / detect_pattern() / extract_chunks() 인터페이스
│   │   │
│   │   ├── pedestrian_parser.py   # 보행자 사고 문서 파서 (StandardsParser 베이스)
│   │   │                          #   - 보N 형식 case ID 탐지
│   │   │                          #   - 사고상황·과실비율·수정요소·법규·판례 섹션 분리
│   │   │                          #   - 레이아웃 패턴 A/B 감지
│   │   │
│   │   ├── standards_parser.py    # 과실비율 인정기준서 파서 (PedestrianParser 확장)
│   │   │                          #   - document_type: "standards"
│   │   │                          #   - 3단계 계층 추적: 편(level1) > 장(level2) > 보N(level3)
│   │   │                          #   - 각 Chunk.metadata.hierarchy 에 계층 정보 첨부
│   │   │
│   │   ├── review_cases_parser.py # 심의사례집 파서
│   │   │                          #   - document_type: "review_cases"
│   │   │                          #   - case_id = 페이지 헤더의 사례 제목 전체 문자열
│   │   │                          #   - 보N 같은 번호 ID 없음
│   │   │
│   │   ├── law_parser.py          # 법률 문서 파서
│   │   │                          #   - document_type: "law"
│   │   │                          #   - 조항(제N조) 단위 청킹
│   │   │                          #   - case_id = "도로교통법_제27조" 형식
│   │   │                          #   - 줄 시작 앵커(^)로 인라인 참조와 헤더 구분
│   │   │
│   │   ├── roundabout_parser.py   # 회전교차로 문서 파서
│   │   │                          #   - document_type: "roundabout"
│   │   │                          #   - 회전-N 형식 case ID 탐지
│   │   │
│   │   └── registry.py            # 파서 자동 선택 레지스트리
│   │                              #   - get_parser(pdf_path) → 적합한 파서 인스턴스 반환
│   │                              #   - 탐지 전략 (표지 1페이지 기준):
│   │                              #     1. 법률명 2회 이상 등장  → LawParser
│   │                              #     2. "회전교차로" 등장     → RoundaboutParser
│   │                              #     3. "횡단보도"/"보행자"   → StandardsParser
│   │                              #     4. "과실비율" (fallback) → ReviewCasesParser
│   │
│   ├── chunkers/
│   │   ├── core_chunker.py        # 사고유형 핵심 정보 → core 청크 생성
│   │   │                          #   - 사고상황·기본과실비율·수정요소·참고사항 포함
│   │   ├── legal_chunker.py       # 관련 법규 조문 → legal 청크 생성
│   │   │                          #   - ⊙도로교통법 제N조 형식 법조문 추출
│   │   └── precedent_chunker.py   # 법원 판결 → precedent 청크 생성
│   │                              #   - 법원명·사건번호·과실비율 파싱
│   │
│   └── config.yaml                # 청킹 설정 (최대 토큰 수, 필수 메타데이터 필드)
│
├── pyproject.toml                 # 프로젝트 메타데이터 및 의존성 (uv 사용)
└── .gitignore                     # source/**/*.pdf, __pycache__, .venv 제외
```

---

## 문서 유형별 파서 및 청크 결과

| PDF 파일 | 파서 | document_type | 청크 수 (예시) |
|---|---|---|---|
| `fault_ratio_standards_2023.pdf` | StandardsParser | `standards` | ~57개 |
| `fault_ratio_review_cases.pdf` | ReviewCasesParser | `review_cases` | ~90개 |
| `road_traffic_law.pdf` | LawParser | `law` | ~377개 |
| `roundabout_fault_ratio_standards_2025.pdf` | RoundaboutParser | `roundabout` | ~15개 |

---

## 청크 타입 (chunk_type)

| 타입 | 생성 주체 | 내용 |
|---|---|---|
| `core` | CoreChunker | 사고상황 · 기본과실비율 · 수정요소 · 참고사항 |
| `legal` | LegalChunker | 관련 법규 조문 목록 (⊙도로교통법 제N조 형식) |
| `precedent` | PrecedentChunker | 법원 판결 1건 (법원명 · 사건번호 · 과실비율) |

---

## 주요 메타데이터 필드

ChromaDB에 저장되는 청크별 메타데이터입니다. 검색 시 필터 조건으로 활용합니다.

| 필드 | 설명 | 예시 |
|---|---|---|
| `case_id` | 사례 식별자 | `"보1"`, `"도로교통법_제27조"` |
| `chunk_type` | 청크 유형 | `"core"`, `"legal"`, `"precedent"` |
| `document_type` | 문서 유형 | `"standards"`, `"law"`, `"review_cases"`, `"roundabout"` |
| `chapter` | 사례 제목 | `"횡단보도에서 보행자와의 사고"` |
| `hier_level1` | 계층 1단계 (기준서 전용) | `"차대보행자 사고"` |
| `hier_level2` | 계층 2단계 (기준서 전용) | `"횡단보도에서의 사고"` |
| `article_number` | 조항 번호 (법률 전용) | `"제27조"` |
| `law_name` | 법률명 (법률 전용) | `"도로교통법"` |
| `basic_fault_ratio` | 기본 과실비율 | `"{'차량': 70, '보행자': 30}"` |
| `laws_included` | 포함된 법조문 목록 | `"도로교통법 제27조, 제48조"` |

---

## 검색 필터 사용 예시

```python
# 특정 문서 유형만 검색
search(vectordb, "보행자 횡단 사고 과실비율", document_type="standards")

# 법규 청크만 검색
search(vectordb, "보행자 보호 의무", chunk_type="legal")

# 특정 파일 + 핵심 청크만 검색
search(vectordb, "신호위반 교차로 사고",
       file_name="fault_ratio_standards_2023.pdf", chunk_type="core")
```

---

## 레이아웃 패턴 (기준서 문서 전용)

| 패턴 | 구조 |
|---|---|
| A | 사례 테이블 1개 → 사고상황 섹션 바로 연결 |
| B | 사례 테이블 여러 개 연속 → 뒤에 오는 섹션을 공유, `⊙보N` 서브불릿으로 사례별 내용 분리 |
