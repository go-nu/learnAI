import os
from ultralytics import YOLO

# Load a pretrained YOLO26n model
model = YOLO("yolo11s.pt")

# 스크립트 파일 위치 기준으로 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(base_dir, "ive.jpg")
results = model(img_path)

results[0].show()  # Display results

# 판다스 형태 데이터 처리 구조
# ONNX export
model.export(format="onnx")

# ONNX 모델로 추론
onnx_model = YOLO("yolo11s.onnx")
results = onnx_model(img_path)

# pandas 형태로 출력
df = results[0].to_df()
print(df)

print(df["name"].tolist())        # 클래스 이름
print(df["confidence"].tolist())  # 신뢰도
print(df["box"].tolist())         # 박스 좌표