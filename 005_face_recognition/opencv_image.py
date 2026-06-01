# 1. 라이브러리
import cv2
import numpy as np

# 2. 사진 불러오기
img = cv2.imread('./photo.jpg') # RGB -> cv2 메모리 적재 시, BGR로 변환

# 3. 이미지 출력
# cv2.imshow("Img View", img)

# 4. 저장
# cv2.imwrite("dog.jpg", img)

# # 5. 이미지 분리(BGR)
# b, g, r = cv2.split(img)
# zeros = np.zeros_like(b)

# # 각 색상별 3채널 이미지 생성 (OpenCV는 BGR 순서)
# blue_img = cv2.merge([b, zeros, zeros])  # B 만 있고 G, R 은 0
# green_img = cv2.merge([zeros, g, zeros]) # G 만 있고 B, R 은 0
# red_img = cv2.merge([zeros, zeros, r])   # R 만 있고 B, G 은 0

# # 결과 출력
# cv2.imshow("Blue Channel (Colored)", blue_img)
# cv2.imshow("Green Channel (Colored)", green_img)
# cv2.imshow("Red Channel (Colored)", red_img)

# 6. resize, 크기를 튜플 형태로 입력
# resized = cv2.resize(img, (300, 200))
# cv2.imshow("Resized", resized)

# 7. rotation
# rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
# cv2.imshow("Rotated", rotated)

# 8. crop(특정 부분 분리해서 자르기)
# cropped = img[50:250, 100:300]
# cv2.imshow("Cropped", cropped)

# 9. 이진화 binarization
gray = cv2.imread("photo.jpg", cv2.IMREAD_GRAYSCALE)
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
cv2.imshow("Binary", binary)


cv2.waitKey(0)
cv2.destroyAllWindows()