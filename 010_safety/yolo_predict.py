from ultralytics import YOLO

# Load a pretrained YOLO11s model
model = YOLO("weights/best.pt")

# 이미지 추출
results = model.predict(
    source="./test_image/test1.jpg",
    classes=[1, 3],
    conf=0.5, # 인식률
    iou=0.45, # 겹치는 영역
    save=True
)

# 결과 파싱
for result in results:
    boxes = result.boxes
    for box in boxes:
        cls = int(box.cls) # cls = idx
        conf = float(box.conf)
        xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2], pandas를 list로 치환
        print(f"클래스: {model.names[cls]}, 신뢰도: {conf:.2f}, 좌표: {xyxy}")