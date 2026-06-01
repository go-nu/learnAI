# 라이브러리
from ultralytics import YOLO

# 모델
model = YOLO('yolo11s.pt')

results = model.train(
    data='/content/drive/MyDrive/dataset/data.yaml',
    epochs=100, # 학습 횟수
    imgsz=640,  # 이미지 크기
    batch=16,   # 한번에 학습할 갯수
    name='/content/drive/MyDrive/dataset/runs' # 저장 경로
    patience=20, # es 횟수
    device=0,    # GPU 갯수(0)
    save=True
)