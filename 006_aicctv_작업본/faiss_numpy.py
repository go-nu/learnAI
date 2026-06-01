# 라이브러리 불러오기
import os
import numpy as np
from PIL import Image
import faiss
import face_recognition

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

# 정답 불러오기
dataset_imgs = read_file('./dataset/org_data')

img_paths = []
for path in dataset_imgs:
    path = path.replace('\\', '/')
    img_paths.append(path)

print(img_paths)
# exit()

# 람다함수
train_labels = np.array(
    [img.split('/')[-2] for img in img_paths]
)

np.save('./train/labels.npy', train_labels)