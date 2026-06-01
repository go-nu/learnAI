from ultralytics import YOLO
import cv2
import os

model = YOLO("yolo11s.pt")

# ONNX export
model.export(format="onnx")

# ONNX 모델 로드
onnx_model = YOLO("yolo11s.onnx")

# 웹캠 or 영상 파일
cap = cv2.VideoCapture(0)  # 0: 웹캠, 파일 경로 입력 가능

while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임 읽기 실패")
        break

    # frame(numpy array) 직접 전달
    results = onnx_model(frame, classes=0)  # person 만 인식

    # pandas 형태로 출력
    df = results[0].to_df()

    # 인식된 class가 1개인 경우만 처리
    if len(df) == 1:
        print(df)

        # 결과 화면에 표시
        annotated_frame = results[0].plot()
        cv2.imshow("YOLO", annotated_frame)
    else:
        cv2.imshow("YOLO", frame)

    # q 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()