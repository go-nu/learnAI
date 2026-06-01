# 라이브러리 불러오기
import os
import shutil # 파일 관리
from datetime import datetime

# 오늘 날짜 시간 구하기
now_date = datetime.today().strftime("%Y%m%d%H%M%S")
# print(now_date)

# 디렉토리 생성 함수
def createFolder(directory):
    try:
        if not os.path.exists(directory): # os.path 사용시 운영체재에 상관없이 사용 가능
            os.makedirs(directory)
    except OSError:
        print("에러 : 디렉토리 생성에러. " + directory)

# 실행
# createFolder('./dataset/test1/test2/test3')

# 원본 디렉토리에 파일 불러오는 함수
org_path = "./dataset/org_data"
file_list = os.listdir(org_path)
print(file_list)

# labels 생성
dataset_labels = {}

# 파일 생성
save_file = open('./dataset/labels.txt', 'w', encoding='utf8')

# dataset 객체 디렉토리 생성
for file in file_list:
    # print(file)
    # 문장분리
    sp_file = file.split('_')
    print("순번:", sp_file[0])
    print("한글이름:", sp_file[1])
    print("영문이름:", sp_file[2])
    # 폴더 생성
    createFolder(f"./dataset/data/{sp_file[2]}")
    # 라벨 만들기
    dataset_labels[sp_file[2]] = sp_file[1]
    print(f'{sp_file[2]},{sp_file[1]}', file=save_file)

# 데이터셋 딕셔너리
print(dataset_labels)

save_file.close()

# 원본파일을 DATASET에 처리하는 함수
org_path = "./dataset/org_data"
file_list = os.listdir(org_path)
for dir in file_list:
    files = os.listdir(org_path + f'/{dir}')
    print('*'*50)
    print(dir)
    print('*'*50)
    print(files)