# ccbb — 교통사고 과실비율 RAG 파이프라인

## 요구사항

```bash
pip install pdfplumber pyyaml langchain langchain-community langchain-huggingface chromadb sentence-transformers
```

---

## 실행 방법

### 1. 전체 PDF → ChromaDB 벡터 DB 구축 + 검색
```bash
python rag_pdf_tables.py
```
- `source/` 안의 PDF를 자동 스캔해 단일 ChromaDB에 적재
- 실행 후 인터랙티브 검색 모드 진입

### 2. 구조화 청킹 파이프라인
```bash
cd fault_ratio_rag
python pipeline.py <PDF_경로>
```

---

## 파일 · 폴더 역할

```
ccbb/
├── rag_pdf_tables.py             # 메인 RAG 파이프라인 (PDF → 임베딩 → ChromaDB)
├── main.py                       # 진입점
├── source/                       # 원본 PDF 저장 폴더
│   ├── fault_ratio_standards_2023.pdf
│   ├── roundabout_fault_ratio_standards_2025.pdf
│   ├── fault_ratio_review_cases.pdf
│   └── road_traffic_law_2026.pdf
├── ccbb_html/                    # 웹 UI HTML (업로드·검색·결과 화면)
└── fault_ratio_rag/              # 과실비율 문서 전용 구조화 청킹 패키지
    ├── pipeline.py               # 실행 진입점 — run(pdf) / print_summary(chunks)
    ├── registry.py               # PDF 자동 분류 → 적합한 파서 반환
    ├── config.yaml               # 청크 크기·필수 메타데이터 필드 설정
    ├── requirements.txt          # 패키지 의존성
    ├── models/
    │   └── chunk.py              # Chunk / ChunkMetadata 데이터 클래스
    ├── parsers/
    │   ├── base_parser.py        # 추상 베이스 파서
    │   ├── pedestrian_parser.py  # 보행자 사고 문서 파서 (Pattern A/B 감지)
    │   └── roundabout_parser.py  # 회전교차로 문서 파서 (전부 Pattern A)
    └── chunkers/
        ├── core_chunker.py       # 사고유형 핵심 정보 → core 청크
        ├── legal_chunker.py      # 관련 법규 조문 → legal 청크
        └── precedent_chunker.py  # 법원 판결 1건 → precedent 청크
```

---

## 청크 타입

| 타입 | 내용 |
|------|------|
| `core` | 사고상황 · 기본과실비율 · 수정요소 · 참고사항 |
| `legal` | 관련 법규 조문 목록 |
| `precedent` | 개별 법원 판결 1건 |

## Pattern A / B

| 패턴 | 조건 |
|------|------|
| A | case 테이블 1개 → 섹션 바로 연결 |
| B | case 테이블 2개 이상 연속 → 섹션 공유, ⊙보N 서브불릿으로 사례별 분리 |
