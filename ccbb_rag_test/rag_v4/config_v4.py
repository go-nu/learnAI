SOURCE_DIR       = "./source"                  # 이 디렉토리의 모든 .pdf 파일을 자동 로드
DB_PATH          = "./chroma_bge_m3_v4"        # v2(chroma_bge_m3_v2)와 구분되는 별도 DB 경로
COLLECTION_NAME  = "pdf_text_table_rag"

IMAGE_OUTPUT_DIR = "./data/extracted_images"   # PDF에서 추출한 원본 이미지 저장 (출처 매핑용)

# 사례별 청킹 설정 — 줄 단독으로 나타나는 사례번호만 경계로 인식
# 차N-N : 기존 과실비율 문서 형식
# 회전-N : 2025 회전교차로 문서 형식 ("회전-10", "회전-11" 등)
CASE_PATTERN = r'(?m)^\s*(?:차\d+-\d+|회전-\d+)\s*$'

MAX_CASE_CHARS = 2000

# 법률 조항 청킹 설정
LEGAL_ARTICLE_PATTERN  = r'제\d+조(?:의\d+)?\([^)]+\)'   # 제N조(제목) 또는 제N조의N(제목)
LEGAL_ADDENDUM_PATTERN = r'부칙\s*<[^>]+>'                 # 부칙 <공포일자·번호>
