# 1. 라이브러리 불러오기
import dlib
import cv2
import sys
import time

# 2. 카메라 불러오기
cap = cv2.VideoCapture("./movie.mp4")
detector = dlib.get_frontal_face_detector()

cap.set(3, 480)
cap.set(4, 320)

# 무한반복
while True:
    ret, frame = cap.read()
    # 복제
    cpy_frame = frame.copy()
    dets = detector(cpy_frame, 1)

    if not ret:
        break

    # 화면에 보이기
    # if bboxs:
        # center = bboxs[0]["center"]
        # cv2.circle(img, center, 5, (255, 0, 255), cv2.FILLED)

    cv2.imshow('Orginal View', cpy_frame)

    for i, d in enumerate(dets):
        print(f"  얼굴 {i+1}: left={d.left()}, top={d.top()}, "
              f"right={d.right()}, bottom={d.bottom()}")

        # 바운딩 박스 그리기
        cv2.rectangle(
            frame,
            (d.left(), d.top()),
            (d.right(), d.bottom()),
            (0, 0, 255), 2
        )
        cv2.putText(
            frame, f"Face {i+1}",
            (d.left(), d.top() - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

    cv2.imshow('AI Mesh View', frame)

    # 키입력
    if cv2.waitKey(1) == 27: # ESC
        break

cap.release()
cv2.destroyAllWindows()