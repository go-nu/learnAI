import cv2
import numpy as np
import easyocr

def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 200)
    return edged

def find_plate_contour(edged, img):
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    plate_contour = None
    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        # 꼭짓점이 4개 = 사각형 → 번호판 후보
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / h

            # 한국 번호판 가로세로 비율: 약 2.0 ~ 5.0
            if 2.0 < aspect_ratio < 5.0 and w > 100:
                plate_contour = approx
                break

    return plate_contour

def order_points(pts):
    """4개의 꼭짓점을 [좌상, 우상, 우하, 좌하] 순으로 정렬"""
    rect = np.zeros((4, 2), dtype="float32")
    pts = pts.reshape(4, 2).astype("float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # 좌상단 (x+y 최소)
    rect[2] = pts[np.argmax(s)]   # 우하단 (x+y 최대)

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 우상단 (y-x 최소)
    rect[3] = pts[np.argmax(diff)]  # 좌하단 (y-x 최대)

    return rect

def correct_perspective(img, contour):
    """원근 변환으로 번호판을 정면으로 보정"""
    rect = order_points(contour)
    (tl, tr, br, bl) = rect

    # 출력 이미지 크기 계산
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    # 목적지 좌표 (펼쳐진 직사각형)
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    return warped

def run_ocr(plate_img):
    """EasyOCR로 번호판 텍스트 추출"""
    # OCR 전 추가 전처리
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(thresh)

    return results

def postprocess_ocr(results):
    """OCR 결과에서 번호판 텍스트만 추출"""
    plate_text = ""
    for (bbox, text, confidence) in results:
        if confidence > 0.5:
            # 숫자, 한글만 필터링
            filtered = ''.join(c for c in text if c.isdigit() or '\uAC00' <= c <= '\uD7A3')
            plate_text += filtered

    return plate_text

def recognize_plate(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("이미지를 불러올 수 없습니다.")

    # Step 1: 전처리 및 번호판 윤곽 검출
    edged = preprocess_image(img)
    plate_contour = find_plate_contour(edged, img)

    if plate_contour is None:
        print("번호판을 찾지 못했습니다. 전체 이미지로 OCR 시도...")
        plate_img = img  # fallback
    else:
        # Step 2: 기울기 보정 (Perspective Transform)
        plate_img = correct_perspective(img, plate_contour)

    # Step 3: OCR 수행 및 후처리
    ocr_results = run_ocr(plate_img)
    plate_number = postprocess_ocr(ocr_results)

    print(f"인식된 번호판: {plate_number}")
    return plate_number, plate_img

# 실행
plate_number, plate_img = recognize_plate("car1.jpg")
cv2.imwrite("plate_result.jpg", plate_img)