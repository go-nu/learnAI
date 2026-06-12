"""
config_v1.py — 경로·이미지·청킹 전역 상수
패키지 내 모든 모듈이 참조하는 설정값을 한 곳에서 관리합니다.
"""

PDF_PATH         = "./source/fault_ratio_standards_carvcar.pdf"
DB_PATH          = "./chroma_multimodal"
COLLECTION_NAME  = "pdf_table_rag"

IMAGE_OUTPUT_DIR = "./data/extracted_images"   # PDF에서 추출한 원본 이미지 저장 경로
FILTERED_IMG_DIR = "./data/filtered_images"    # 리사이즈 완료 이미지 저장 경로
VISION_MODEL     = "gemini-2.5-flash"          # Gemini 비전 모델 (GOOGLE_API_KEY_VISION 사용)
MAX_IMG_PX       = 2240                        # 긴 변 최대 픽셀
MAX_IMG_RATIO    = 4.5                         # 가로:세로 최대 비율
MAX_IMG_BYTES    = 20 * 1024 * 1024            # 최대 파일 크기 20MB

# 사례별 청킹 설정
# (?m)^차\d+-\d+ : 멀티라인 모드, 줄 시작에 위치한 차N-N 형태만 매칭
#   "⊙ 차16-1", "(차16-1)" 등 앞에 다른 문자가 있는 경우는 자동 제외
CASE_PATTERN   = r'(?m)^차\d+-\d+'
MAX_CASE_CHARS = 2000  # 사례 블록 최대 글자 수 (초과 시 추가 분할)
