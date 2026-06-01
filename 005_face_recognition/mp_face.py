# 1. 라이브러리 불러오기
import cv2
import mediapipe as mp

# mediapipe 초기화
mp_face = mp.solutions.face_detection # Face Detection 라이브러리를 사용
mp_drawing = mp.solutions.drawing_utils # 감지된 정보에 그림을 그리겠다.

# camera 동작 프로그램
cap = cv2.VideoCapture(0)
# 카메라의 해상도 크기를 조정
cap.set(3, 640)
cap.set(4, 480)
with mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5
    ) as face_detection:
    while(True):
        ret, frame = cap.read()
        if not ret:
            print('카메라를 인식하지 못했습니다.')
            exit(0)
            
        cv2.imshow('video input', frame)
        # 얼굴 인식시키기
        frame.flags.writeable = False
        # 입력된 이미지를 컬러로 처리하는데 BGR -> RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow('rgb video', image)
        face_result = face_detection.process(image)
        # print(face_result)
        face_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if face_result.detections:
            for detection in face_result.detections:
                print(detection)
                # 찾은 정보를 그리기
                mp_drawing.draw_detection(face_image, detection)
        
        cv2.imshow('face detection', face_image)
        # ESC키를 검출하는 방법
        k = cv2.waitKey(30) & 0xff
        if k == 27: # ESC값
            break

# 메모리 및 카메라 정보 해제
cv2.destroyAllWindows()
cap.release()
