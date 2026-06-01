from ultralytics import YOLO
import os

# 스크립트 파일 위치 기준으로 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(base_dir, "./test_image/test2.jpg")

# Load a pretrained YOLO26n model
model = YOLO("weights/best.pt")

# Perform object detection on an image
results = model(img_path)  # Predict on an image
results[0].show()  # Display results

# pandas 형태로 출력하기 
# ONNX export
model.export(format="onnx")

# ONNX 모델로 추론
onnx_model = YOLO("weights/best.onnx")
results = onnx_model(img_path)

# pandas 형태로 출력
df = results[0].to_df()
print(df)


print(df["name"].to_list())        # 클래스 이름
print(df["confidence"].to_list())  # 신뢰도
print(df["box"].to_list())         # 박스 좌표


# 터미널 입력해보기
# yolo predict model=yolo11s.pt source='https://www.youtube.com/watch?v=C32XiyRpUtI' show=True save=True