"""
dlib 예제 1: HOG 기반 얼굴 감지
- 모델 파일 없이 바로 실행 가능
- 설치: conda install -c conda-forge dlib opencv
"""

import dlib
import cv2
import sys

def detect_faces(image_path: str, upsample: int = 1):
    """
    이미지에서 얼굴을 감지하고 결과를 화면에 표시합니다.

    Args:
        image_path: 이미지 파일 경로
        upsample:   업샘플 횟수 (클수록 작은 얼굴도 감지, 속도 저하)
    """
    # HOG 기반 정면 얼굴 감지기 (모델 파일 불필요)
    detector = dlib.get_frontal_face_detector()

    img = cv2.imread(image_path)
    if img is None:
        print(f"[오류] 이미지를 불러올 수 없습니다: {image_path}")
        return

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 얼굴 감지
    dets = detector(rgb, upsample)
    print(f"감지된 얼굴 수: {len(dets)}")
    print("얼굴분석 : ", dets)

    for i, d in enumerate(dets):
        print(f"  얼굴 {i+1}: left={d.left()}, top={d.top()}, "
              f"right={d.right()}, bottom={d.bottom()}")

        # 바운딩 박스 그리기
        cv2.rectangle(
            img,
            (d.left(), d.top()),
            (d.right(), d.bottom()),
            (0, 255, 0), 2
        )
        cv2.putText(
            img, f"Face {i+1}",
            (d.left(), d.top() - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

    cv2.imshow("face_detection_result", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 결과 이미지 저장
    output_path = image_path.rsplit(".", 1)[0] + "_detected.jpg"
    cv2.imwrite(output_path, img)
    print(f"결과 저장: {output_path}")

image_path = "./ive.jpg"
detect_faces(image_path)
