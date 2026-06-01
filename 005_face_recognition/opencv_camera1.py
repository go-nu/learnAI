# 1. 라이브러리 불러오기
from cvzone.FaceDetectionModule import FaceDetector
import cv2
import time

# 2. 카메라 불러오기
cap = cv2.VideoCapture("./movie.mp4")
detector = FaceDetector()

# 무한반복
while True:
    ret, frame = cap.read()
    # 복제
    cpy_frame = frame.copy()
    img, bboxs = detector.findFaces(frame)
    if not ret:
        break

    # 화면에 보이기
    # if bboxs:
        # center = bboxs[0]["center"]
        # cv2.circle(img, center, 5, (255, 0, 255), cv2.FILLED)

    cv2.imshow('Orginal View', cpy_frame)
    cv2.imshow('AI Mesh View', img)

    # 키입력
    if cv2.waitKey(1) == 27: # ESC
        break

    time.sleep(0.02)

cap.release()
cv2.destroyAllWindows()