##########################################################
# 프로그램명 : FAISS 기반 얼굴 인식 통합 클래스
# 개발일자 : 2026년 05월 16일
# 개발버젼 : v 2.0
# 개발자명 : 홍길동
# 라이브러리 : face_recognition, dlib, faiss-cpu:1.7.3
# 원본파일 : create_dataset.py, faiss_dataset.py,
#             faiss_numpy.py, faiss_train.py, faiss_predict.py
# 수정이력 : Python 3.11 → 3.8 호환 변환
#            - typing 모듈 사용 (List, Dict, Optional, Tuple)
#            - Union 타입 | 연산자 → Optional 으로 변경
##########################################################

from __future__ import annotations  # 타입 힌트 지연 평가 (3.8 호환)

import os
import shutil
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import faiss
import face_recognition


class FaceRecognitionFAISS:
    """
    FAISS 벡터 DB를 활용한 얼굴 인식 통합 클래스.

    [작업 흐름]
      1. create_dataset()   - 원본 데이터 디렉토리 구조 생성 및 labels.txt 저장
      2. extract_faces()    - 원본 이미지에서 얼굴 영역 crop → dataset/data 저장
      3. save_labels_npy()  - crop된 데이터셋 경로에서 라벨 추출 → .npy 저장
      4. train()            - 얼굴 인코딩 → FAISS 인덱스 생성 → .bin 저장
      5. predict()          - 테스트 이미지 얼굴 검출 → 인코딩 → 유사도 검색

    [디렉토리 구조]
      ./dataset/
        org_data/           ← 원본 이미지 (파일명: 순번_한글이름_영문이름.확장자)
          영문이름/          ← create_dataset()이 자동 생성
            이미지파일
        data/               ← extract_faces()가 crop 이미지를 저장
          영문이름/
            이미지파일
        train/              ← FAISS 학습 결과 저장
          face_YYYYMMDD.bin ← FAISS 인덱스
          labels.npy        ← 라벨 배열
        test/               ← 예측 시 임시 저장 폴더
          test.jpg          ← crop된 임시 얼굴 이미지
        labels.txt          ← 영문이름,한글이름 매핑
    """

    def __init__(
        self,
        org_data_path: str = "./dataset/org_data",
        dataset_path: str = "./dataset/data",
        train_dir: str = "./dataset/train",
        test_tmp_path: str = "./dataset/test/test.jpg",
        face_margin: int = 20,
        index_dim: int = 128,
        top_k: int = 5,
        min_vote: int = 3,
    ):
        """
        Parameters
        ----------
        org_data_path  : 원본 이미지가 담긴 디렉토리
        dataset_path   : crop된 얼굴 이미지를 저장할 디렉토리
        train_dir      : FAISS 인덱스(.bin)·라벨(.npy) 저장 디렉토리
        test_tmp_path  : 예측 시 임시 저장할 얼굴 이미지 경로
        face_margin    : 얼굴 bounding box 확장 픽셀 수
        index_dim      : FAISS 벡터 차원 (face_recognition 기본 128)
        top_k          : 유사도 검색 시 반환할 이웃 수
        min_vote       : 예측 결과 최소 투표 수 (미만이면 'unknown' 반환)
        """
        self.org_data_path = org_data_path
        self.dataset_path = dataset_path
        self.train_dir = train_dir
        self.test_tmp_path = test_tmp_path
        self.face_margin = face_margin
        self.index_dim = index_dim
        self.top_k = top_k
        self.min_vote = min_vote

        # 런타임에 로드되는 객체
        # [3.8 변경] faiss.Index | None  →  Optional[faiss.Index]
        self.face_index: Optional[faiss.Index] = None
        self.train_labels: Optional[np.ndarray] = None

    # ------------------------------------------------------------------ #
    #  내부 유틸 메서드                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _create_folder(directory: str) -> None:
        """디렉토리가 없으면 생성한다."""
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print(f"에러 : 디렉토리 생성 실패 → {directory}")

    @staticmethod
    def _read_file(path: str) -> List[str]:
        # [3.8 변경] list[str]  →  List[str]
        """path 하위의 모든 파일 경로를 재귀적으로 수집한다."""
        img_paths = []
        for root, _, files in os.walk(path):
            for name in files:
                img_paths.append(os.path.join(root, name))
        return img_paths

    def _expand_bbox(
        self,
        top: int,
        right: int,
        bottom: int,
        left: int,
    ) -> Tuple[int, int, int, int]:
        # [3.8 변경] 반환 타입 명시를 위해 Tuple[int, int, int, int] 사용
        """얼굴 bounding box를 face_margin만큼 확장한다."""
        m = self.face_margin
        return top - m, right + m, bottom + m, left - m

    @staticmethod
    def _most_frequent(data: list) -> Tuple[object, int]:
        # [3.8 변경] 반환 타입 명시를 위해 Tuple 사용
        """리스트에서 최빈값과 그 등장 횟수를 반환한다."""
        count_list = [data.count(x) for x in data]
        best_idx = count_list.index(max(count_list))
        return data[best_idx], max(count_list)

    def _get_index_path(self) -> str:
        """오늘 날짜로 FAISS 인덱스 파일 경로를 반환한다."""
        today = datetime.today().strftime("%Y%m%d")
        return os.path.join(self.train_dir, "face_{}.bin".format(today))

    def _get_labels_path(self) -> str:
        today = datetime.today().strftime("%Y%m%d")
        return os.path.join(self.train_dir, "labels_{}.npy".format(today))

    # ------------------------------------------------------------------ #
    #  Step 1 : 데이터셋 디렉토리 구조 생성                                 #
    # ------------------------------------------------------------------ #

    def create_dataset(self) -> Dict[str, str]:
        # [3.8 변경] dict[str, str]  →  Dict[str, str]
        """
        org_data 하위에 있는 '순번_한글이름_영문이름' 파일명을 파싱하여
        - 영문이름 폴더를 생성하고
        - labels.txt(영문이름,한글이름)를 저장한다.

        Returns
        -------
        dataset_labels : {영문이름: 한글이름} 딕셔너리
        """
        self._create_folder("./dataset")
        self._create_folder(self.dataset_path)
        self._create_folder(self.train_dir)
        self._create_folder(os.path.dirname(self.test_tmp_path))

        file_list = os.listdir(self.org_data_path)
        dataset_labels: Dict[str, str] = {}

        today = datetime.today().strftime("%Y%m%d")

        labels_txt = os.path.join("./dataset/train", "labels_{}.txt".format(today))
        with open(labels_txt, "w", encoding="utf-8") as f:
            for file in file_list:
                parts = file.split("_")
                if len(parts) < 3:
                    print(f"[skip] 파일명 형식 불일치 : {file}")
                    continue

                seq, kor_name, eng_name = parts[0], parts[1], parts[2]
                print(f"순번: {seq} | 한글이름: {kor_name} | 영문이름: {eng_name}")

                # 영문이름 폴더 생성 (org_data 하위)
                # self._create_folder(os.path.join(self.org_data_path, eng_name))
                # crop 저장용 폴더 생성 (dataset/data 하위)
                self._create_folder(os.path.join(self.dataset_path, eng_name))

                dataset_labels[eng_name] = kor_name
                print("{},{}".format(eng_name, kor_name), file=f)

        print(f"\n[create_dataset] 완료 → labels.txt 저장: {labels_txt}")
        print(f"라벨 목록: {dataset_labels}")
        return dataset_labels

    # ------------------------------------------------------------------ #
    #  Step 2 : 얼굴 영역 crop → dataset/data 저장                         #
    # ------------------------------------------------------------------ #

    def extract_faces(self) -> None:
        """
        org_data 디렉토리의 원본 이미지에서 얼굴을 검출·crop하여
        dataset/data/<영문이름>/ 경로에 저장한다.
        얼굴이 정확히 1개가 아닌 이미지는 건너뛴다.
        """
        train_images = self._read_file(self.org_data_path)

        print("-" * 50)
        print(f"[extract_faces] 처리할 이미지 수: {len(train_images)}")
        print("-" * 50)

        for path_img in train_images:
            path_img = path_img.replace("\\", "/")
            img = face_recognition.load_image_file(path_img)

            img_face = face_recognition.face_locations(img)
            print(f"{path_img} → 검출 얼굴 수: {len(img_face)}")

            if len(img_face) != 1:
                print(
                    f"  ⚠ 얼굴이 {len(img_face)}개 검출됨. 원본 파일을 삭제하시겠습니까? (y/n): ",
                    end="",
                    flush=True,
                )
                answer = input().strip().lower()
                if answer == "y":
                    os.remove(path_img)
                    print(f"  🗑 삭제 완료: {path_img}")
                else:
                    print("  건너뜁니다.")
                continue

            top, right, bottom, left = img_face[0]
            top, right, bottom, left = self._expand_bbox(top, right, bottom, left)

            face_img = img[top:bottom, left:right]

            if face_img.size == 0:
                print(
                    f"  ⚠ 얼굴 crop 결과가 비어 있습니다. 원본 파일을 삭제하시겠습니까? (y/n): ",
                    end="",
                    flush=True,
                )
                answer = input().strip().lower()
                if answer == "y":
                    os.remove(path_img)
                    print(f"  🗑 삭제 완료: {path_img}")
                else:
                    print("  건너뜁니다.")
                continue

            pil_img = Image.fromarray(face_img)

            # 저장 경로 계산: org_data/<순번_한글_영문폴더>/<파일명> → dataset/data/<영문이름>/<파일명>
            dir_path = os.path.dirname(path_img).replace("\\", "/")
            folder = dir_path.split("/")[-1]
            parts = folder.split("_")
            dir_name = parts[-1] if len(parts) >= 3 else folder  # 영문이름만 추출
            file_name = os.path.basename(path_img)

            save_dir = os.path.join(self.dataset_path, dir_name)
            self._create_folder(save_dir)
            save_path = os.path.join(save_dir, file_name)

            pil_img.save(save_path)
            print(f"  ✔ 저장 완료: {save_path}")

        print("[extract_faces] 전체 처리 완료")

    # ------------------------------------------------------------------ #
    #  Step 3 : crop된 얼굴 이미지 재검증                                   #
    # ------------------------------------------------------------------ #

    def check_faces(self) -> None:
        """
        dataset/data 디렉토리의 crop 이미지를 다시 face_locations로 검증한다.
        얼굴이 정확히 1개 검출되지 않으면 삭제 여부를 묻고, y면 파일을 삭제한다.
        """
        cropped_images = self._read_file(self.dataset_path)

        print("-" * 50)
        print(f"[check_faces] 검증할 이미지 수: {len(cropped_images)}")
        print("-" * 50)

        deleted = 0
        skipped = 0
        ok = 0

        for path_img in cropped_images:
            path_img = path_img.replace("\\", "/")
            img = face_recognition.load_image_file(path_img)
            img_face = face_recognition.face_locations(img)
            face_count = len(img_face)

            print(f"{path_img} → 검출 얼굴 수: {face_count}")

            if face_count != 1:
                print(
                    f"  ⚠ 얼굴이 {face_count}개 검출됨. crop·원본 파일을 삭제하시겠습니까? (y/n): ",
                    end="",
                    flush=True,
                )
                answer = input().strip().lower()
                if answer == "y":
                    # crop 이미지 삭제
                    os.remove(path_img)
                    print(f"  🗑 crop 삭제: {path_img}")

                    # 원본 이미지 역추적 후 삭제
                    file_name = os.path.basename(path_img)
                    eng_name = path_img.replace("\\", "/").split("/")[-2]
                    org_folder = next(
                        (
                            d
                            for d in os.listdir(self.org_data_path)
                            if d.split("_")[-1] == eng_name
                        ),
                        None,
                    )
                    if org_folder:
                        org_path = os.path.join(
                            self.org_data_path, org_folder, file_name
                        )
                        if os.path.exists(org_path):
                            os.remove(org_path)
                            print(f"  🗑 원본 삭제: {org_path}")
                        else:
                            print(f"  ⚠ 원본 파일 없음: {org_path}")
                    else:
                        print(f"  ⚠ org_data에서 '{eng_name}' 폴더를 찾을 수 없습니다.")
                    deleted += 1
                else:
                    print("  건너뜁니다.")
                    skipped += 1
            else:
                ok += 1

        print("-" * 50)
        print(
            f"[check_faces] 완료 → 정상: {ok}개 | 삭제: {deleted}개 | 유지(건너뜀): {skipped}개"
        )
        print("-" * 50)

        # ── test 이미지 검증 (읽기 전용, 파일 수정 없음) ──────────────────
        test_dir = os.path.dirname(self.test_tmp_path)
        test_images = self._read_file(test_dir)

        if test_images:
            print("-" * 50)
            print(f"[check_faces] test 이미지 검증 (수정 없음): {len(test_images)}개")
            print("-" * 50)

            for path_img in test_images:
                path_img = path_img.replace("\\", "/")
                img = face_recognition.load_image_file(path_img)
                img_face = face_recognition.face_locations(img)
                face_count = len(img_face)
                status = (
                    "✔ 정상" if face_count == 1 else "⚠ 얼굴 {}개".format(face_count)
                )
                print(
                    f"  [{status}] {os.path.basename(path_img)} → 검출 얼굴 수: {face_count}"
                )

            print("-" * 50)
            print("[check_faces] test 검증 완료 (원본 수정 없음)")
            print("-" * 50)

    # ------------------------------------------------------------------ #
    #  Step 4 : 라벨 배열 저장 (.npy)                                      #
    # ------------------------------------------------------------------ #

    def save_labels_npy(self) -> np.ndarray:
        """
        dataset/data 디렉토리 구조에서 라벨(영문이름)을 추출하여
        train/labels.npy로 저장하고 numpy 배열을 반환한다.
        """
        dataset_imgs = self._read_file(self.dataset_path)

        img_paths = [p.replace("\\", "/") for p in dataset_imgs]
        train_labels = np.array([p.split("/")[-2] for p in img_paths])

        labels_path = self._get_labels_path()
        self._create_folder(self.train_dir)
        np.save(labels_path, train_labels)

        print(f"[save_labels_npy] 라벨 수: {len(train_labels)} → {labels_path}")
        self.train_labels = train_labels
        return train_labels

    # ------------------------------------------------------------------ #
    #  Step 4 : FAISS 인덱스 학습 및 저장                                  #
    # ------------------------------------------------------------------ #

    def train(self, test_img_path: Optional[str] = None) -> faiss.Index:
        # [3.8 변경] str | None  →  Optional[str]
        """
        dataset/data 디렉토리의 crop된 얼굴 이미지를 인코딩하여
        FAISS IndexFlatL2 인덱스를 생성하고 train/<날짜>.bin에 저장한다.

        Parameters
        ----------
        test_img_path : (선택) 저장 전 빠른 예측 테스트에 쓸 이미지 경로

        Returns
        -------
        face_index : 생성된 FAISS 인덱스
        """
        dataset_imgs = self._read_file(self.dataset_path)

        print("-" * 50)
        print("[train] 인코딩 시작")
        print("-" * 50)

        face_encodes: List[np.ndarray] = []
        img_paths: List[str] = []

        for path in dataset_imgs:
            path = path.replace("\\", "/")
            print(f"  처리 중: {path}")
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)
            if not encodings:
                print(f"  ⚠ 얼굴 인코딩 실패, 건너뜁니다: {path}")
                continue
            face_encodes.append(encodings[0])
            img_paths.append(path)

        print(f"\n[train] 총 인코딩된 얼굴 수: {len(face_encodes)}")

        # 라벨 생성 및 저장
        train_labels = np.array([p.split("/")[-2] for p in img_paths])
        np.save(self._get_labels_path(), train_labels)
        self.train_labels = train_labels

        # FAISS 인덱스 생성
        face_encode_np = np.array(face_encodes, dtype=np.float32)
        face_index = faiss.IndexFlatL2(self.index_dim)
        face_index.add(face_encode_np)
        self.face_index = face_index

        # 간단한 예측 테스트 (선택)
        if test_img_path:
            print(f"\n[train] 테스트 예측: {test_img_path}")
            result = self.predict(test_img_path)
            print(f"  예측 결과: {result}")

        # 인덱스 저장
        index_path = self._get_index_path()
        faiss.write_index(face_index, index_path)
        print(f"\n[train] FAISS 인덱스 저장 완료 → {index_path}")

        return face_index

    # ------------------------------------------------------------------ #
    #  Step 5 : 얼굴 예측                                                  #
    # ------------------------------------------------------------------ #

    def load_model(self, index_path: Optional[str] = None) -> None:
        # [3.8 변경] str | None  →  Optional[str]
        """
        저장된 FAISS 인덱스와 라벨 배열을 메모리에 로드한다.

        Parameters
        ----------
        index_path : .bin 파일 경로. None이면 오늘 날짜 파일을 자동으로 탐색한다.
        """
        if index_path is None:
            index_path = self._get_index_path()

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"인덱스 파일을 찾을 수 없습니다: {index_path}")

        labels_path = self._get_labels_path()
        if not os.path.exists(labels_path):
            raise FileNotFoundError(f"라벨 파일을 찾을 수 없습니다: {labels_path}")

        self.face_index = faiss.read_index(index_path)
        self.train_labels = np.load(labels_path)
        print(
            f"[load_model] 로드 완료 → 인덱스: {index_path}, 라벨 수: {len(self.train_labels)}"
        )

    def predict(self, img_path: str) -> str:
        """
        테스트 이미지에서 얼굴을 검출·인코딩하여 FAISS 검색 후 이름을 반환한다.

        Parameters
        ----------
        img_path : 예측할 이미지 파일 경로

        Returns
        -------
        예측된 영문이름 또는 'unknown'
        """
        if self.face_index is None or self.train_labels is None:
            raise RuntimeError(
                "모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요."
            )

        test_img = face_recognition.load_image_file(img_path)
        test_face = face_recognition.face_locations(test_img)

        if len(test_face) != 1:
            print(f"[predict] 얼굴 검출 실패 (검출 수: {len(test_face)})")
            return "unknown"

        top, right, bottom, left = test_face[0]
        print(
            f"[predict] 얼굴 좌표: top={top}, right={right}, bottom={bottom}, left={left}"
        )

        top, right, bottom, left = self._expand_bbox(top, right, bottom, left)
        face_cut = test_img[top:bottom, left:right]

        # 임시 저장 후 재로드 (face_recognition 인코딩 안정성 확보)
        Image.fromarray(face_cut).save(self.test_tmp_path)
        tmp_img = face_recognition.load_image_file(self.test_tmp_path)

        encodings = face_recognition.face_encodings(tmp_img)
        if not encodings:
            print("[predict] 얼굴 인코딩 실패")
            return "unknown"

        test_en = np.array(encodings[0], dtype=np.float32).reshape(1, self.index_dim)

        distance, result = self.face_index.search(test_en, k=self.top_k)
        label = [self.train_labels[i] for i in result[0]]

        print(f"[predict] top-{self.top_k} 라벨: {label}")
        print(f"[predict] top-{self.top_k} 거리: {distance}")

        name, vote_count = self._most_frequent(label)

        if vote_count < self.min_vote:
            print(f"[predict] 투표 수 부족 ({vote_count} < {self.min_vote}) → unknown")
            return "unknown"

        print(f"[predict] 예측 결과: {name} (투표 수: {vote_count})")
        return name

    # ------------------------------------------------------------------ #
    #  편의 메서드 : 전체 파이프라인 일괄 실행                               #
    # ------------------------------------------------------------------ #

    def run_pipeline(self, test_img_path: Optional[str] = None) -> None:
        # [3.8 변경] str | None  →  Optional[str]
        """
        create_dataset → extract_faces → save_labels_npy → train 을 순서대로 실행한다.

        Parameters
        ----------
        test_img_path : 학습 후 테스트할 이미지 경로 (선택)
        """
        print("=" * 60)
        print("[Pipeline] Step 1: 데이터셋 디렉토리 생성")
        print("=" * 60)
        self.create_dataset()

        print("=" * 60)
        print("[Pipeline] Step 2: 얼굴 추출 및 crop 저장")
        print("=" * 60)
        self.extract_faces()

        print("=" * 60)
        print("[Pipeline] Step 3: 라벨 npy 저장")
        print("=" * 60)
        self.save_labels_npy()

        print("=" * 60)
        print("[Pipeline] Step 4: FAISS 인덱스 학습")
        print("=" * 60)
        self.train(test_img_path=test_img_path)

        print("=" * 60)
        print("[Pipeline] 전체 파이프라인 완료")
        print("=" * 60)


# ======================================================================
# 사용 예시
# ======================================================================
# if __name__ == "__main__":
#     # 인스턴스 생성
#     fr = FaceRecognitionFAISS(
#         org_data_path="./dataset/org_data",
#         dataset_path="./dataset/data",
#         train_dir="./dataset/train",
#         test_tmp_path="./dataset/test/test1.jpg",
#         face_margin=20,
#         top_k=5,
#         min_vote=3,
#     )

#     # ── 방법 A: 단계별 실행 ──────────────────────────────────────────
#     # fr.create_dataset()                                     # Step 1
#     # fr.extract_faces()                                      # Step 2
#     # fr.check_faces()                                        # Step 3
#     # fr.save_labels_npy()                                    # Step 4
#     # fr.train(test_img_path='./dataset/test/test1.jpg')      # Step 5

#     # ── 방법 B: 전체 파이프라인 한 번에 ─────────────────────────────
#     # fr.run_pipeline(test_img_path='./dataset/test/test1.jpg')

#     # ── 예측만 (모델이 이미 학습된 경우) ────────────────────────────
#     fr.load_model("./dataset/train/face_20260518.bin")  # 날짜 맞게 수정
#     result = fr.predict("./dataset/test/test2.jpg")
#     print("최종 예측:", result)
