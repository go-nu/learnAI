##########################################################
# 프로그램명 : dlib 라이브러리를 이용한 face 추출 프로그램(dataset)
# 개발일자 : 2026년 05월 21일
# 개발버젼 : v 1.x
# 개발자명 : 홍길동
# 라이브러리 : face recognition, dlib, faiss-cpu:1.7.3
##########################################################

# 라이브러리 불러오기
import os
import numpy as np
from PIL import Image
import faiss
import face_recognition

# 디렉토리에 있는 파일을 불러오는 함수
def read_file(path):
    img_path = []
    # 데이터 가져오기
    for paths, subdirs, files in os.walk(path):
        # print('paths =', paths)
        # print('subdirs =', subdirs)
        # print('files =', files)

        # 파일명을 변수에 넣기
        for name in files:
            img_path.append(os.path.join(paths, name))

    return img_path

# 전처리된 데이터 불러오기
dataset_imgs = read_file('./dataset/data')

print('-' * 50)
print('데이터셋 경로')
print('-' * 50)
for data in dataset_imgs:
    print(data)
print('-' * 50)

# faiss에 얼굴정보를 등록 하고 vectordb로 변환
faceEncode = []
img_paths = []

for path in dataset_imgs:
    path = path.replace('\\', '/')
    print(path)
    # 얼굴 이미지 불러오기
    img = face_recognition.load_image_file(path)
    # print(img)
    # Encode(인코딩)
    face_encode = face_recognition.face_encodings(img)[0]
    # print(face_encode)
    # exit()

    # encoding 된 정보를 변수에 저장
    faceEncode.append(face_encode)
    img_paths.append(path)

print("검출된 얼굴은 총 {}개입니다.".format(len(faceEncode)))

# 인코딩 (벡터DB)로 생성
# 인코딩( 문제:numpy, 답:numpy(?))
# 람다함수
train_labels = np.array(
    [img.split('/')[-2] for img in img_paths]
)

# print(train_labels)
# 데이터 구조
print("faceEncode :", type(faceEncode))
print("train_lables :", type(train_labels))
# exit()

# 인코딩 위한 변환작업
faceEncode = np.array(faceEncode, dtype=np.float32)
print(faceEncode.shape, train_labels.shape)

# Vector DB로 저장
face_index = faiss.IndexFlatL2(128)
# 벡터를 적용
face_index.add(faceEncode)

# 예측하기
# 얼굴인식
test_img = face_recognition.load_image_file('test_img/1.jpg')
test_face = face_recognition.face_locations(test_img)
if len(test_face) != 1:
    print("테스트 얼굴에 1개의 얼굴만 존재해야 합니다.")
    exit()

# 얼굴만 잘라내기(시계방향)
top, right, bottom, left = test_face[0]
print(top, right, bottom, left)

# 범위 확장
top = top - 20
right = right + 20
bottom = bottom + 20
left = left - 20

# 얼굴부분만 추출
face_cut = test_img[top:bottom, left:right]

pil_img = Image.fromarray(face_cut)
pil_img.save('./test.jpg')
img = face_recognition.load_image_file('./test.jpg')

# 인코딩
test_en = face_recognition.face_encodings(img)[0]

# 넘파이
test_en = np.array(test_en, dtype=np.float32).reshape(-1, 128)
# (128) -> (1, 128)

# 예측
val, result = face_index.search(test_en, k=5)

# 값검출
label = [train_labels[i] for i in result[0]]
print(label)

# 벡터데이터 저장
faiss.write_index(
    face_index, 
    './train/face_20260514.bin')