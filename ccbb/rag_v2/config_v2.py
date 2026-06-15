"""
config_v2.py — 경로·청킹 전역 상수
VL 모델 없이 텍스트·표만 임베딩하며, 이미지는 출처 매핑(image_refs)으로 관리합니다.
"""

PDF_PATH         = "./source/fault_ratio_standards_carvcar.pdf"
DB_PATH          = "./chroma_bge_m3_v2"       # v1(chroma_multimodal)과 구분되는 별도 DB 경로
COLLECTION_NAME  = "pdf_text_table_rag"

IMAGE_OUTPUT_DIR = "./data/extracted_images"   # PDF에서 추출한 원본 이미지 저장 (출처 매핑용)

# 사례별 청킹 설정
CASE_PATTERN   = r'(?m)^차\d+-\d+'
MAX_CASE_CHARS = 2000
