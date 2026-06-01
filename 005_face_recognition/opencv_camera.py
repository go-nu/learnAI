# 1. 라이브러리 불러오기
from cvzone.FaceMeshModule import FaceMeshDetector
import cv2

# 2. 카메라 불러오기
cap = cv2.VideoCapture("./movie.mp4")
detector = FaceMeshDetector(maxFaces=5)

# 무한반복
while True:
    ret, frame = cap.read()
    # 복제
    cpy_frame = frame.copy()
    img, faces = detector.findFaceMesh(frame)
    if not ret:
        break

    # 화면에 보이기
    if faces:
        print(faces[0])

    cv2.imshow('Orginal View', cpy_frame)
    cv2.imshow('AI Mesh View', img)

    # 키입력
    if cv2.waitKey(1) == 27: # ESC
        break

cap.release()
cv2.destroyAllWindows()