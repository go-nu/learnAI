"""
chunk_verify.py

Multimodal RAG 파이프라인 청크 검증 스크립트.

실행 방법
    python chunk_verify.py

검증 항목
    STEP 1. 이미지 추출 파일 확인 (extracted_images/ 디렉토리)
    STEP 2. DB 내 image Document 내용 출력
    STEP 3. Chroma DB doc_type 분포 확인
    STEP 4. doc_type 필터로 이미지 청크 강제 검색
    STEP 5. 키워드 유사도 검색에서 이미지 포함 여부 확인
"""

import os
import re
from collections import Counter

from dotenv import load_dotenv

# 검증 대상 경로 — multimodal_rag_bge_m3.py 의 상수와 일치
IMAGE_OUTPUT_DIR = "./data/extracted_images"
FILTERED_IMG_DIR = "./data/filtered_images"
DB_PATH          = "./chroma_multimodal"
COLLECTION_NAME  = "pdf_table_rag"

# 유사도 검색 테스트 쿼리 — 과실비율 문서 도식도에 있을 법한 키워드
SEARCH_QUERIES = [
    "차량 도식도 교차로 직진 좌회전",
    "차16 사고 차량 위치 진입 방향",
    "교차로 충돌 A차량 B차량",
]

_IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class ChunkVerifier:

    def __init__(self):
        load_dotenv()
        from multimodal_rag_bge_m3 import RagBgeM3
        self.rag = RagBgeM3()
        self._vectorstore = None  # lazy load

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — Chroma DB lazy load                                     #
    # ------------------------------------------------------------------ #
    def _get_vectorstore(self):
        if self._vectorstore is not None:
            return self._vectorstore

        from langchain_chroma import Chroma

        if not os.path.exists(DB_PATH):
            raise RuntimeError(
                f"[오류] '{DB_PATH}' DB가 없습니다.\n"
                "       먼저 multimodal_rag_bge_m3.py 를 실행해 DB를 생성하세요."
            )
        self._vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.rag.get_embeddings(),
            persist_directory=DB_PATH,
        )
        return self._vectorstore

    # ------------------------------------------------------------------ #
    #  STEP 1 — 이미지 추출 파일 확인                                       #
    # ------------------------------------------------------------------ #
    def verify_extracted_images(self):
        print("=" * 60)
        print("[STEP 1] 이미지 추출 파일 확인")
        print("=" * 60)
        print()

        folders = [
            ("[extracted_images/]", IMAGE_OUTPUT_DIR, ""),
            ("[filtered_images/]",  FILTERED_IMG_DIR, " (리사이즈 완료)"),
        ]

        for label, folder, suffix in folders:
            print(f"  {label}")
            if not os.path.exists(folder):
                print("    폴더 없음 — 이미지 추출이 실행되지 않았습니다\n")
                continue

            files = sorted(
                f for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() in _IMG_EXTS
            )

            if not files:
                print("    (파일 없음)\n")
                continue

            for fname in files:
                fpath    = os.path.join(folder, fname)
                size_kb  = os.path.getsize(fpath) / 1024
                match    = re.search(r"page_(\d+)_img_\d+", fname)
                page_str = f"page {match.group(1)}" if match else "page ?"
                print(f"    {fname:<35s} │ {size_kb:>6.1f} KB  │  {page_str}")

            print(f"  → 총 {len(files)}개 파일{suffix}\n")

    # ------------------------------------------------------------------ #
    #  STEP 2 — image Document 요약 내용 확인                              #
    # ------------------------------------------------------------------ #
    def verify_image_summaries(self):
        print("=" * 60)
        print("[STEP 2] image Document 요약 내용 확인")
        print("=" * 60)
        print()

        vs   = self._get_vectorstore()
        data = vs._collection.get(include=["metadatas", "documents"])

        image_items = [
            (meta, doc)
            for meta, doc in zip(data["metadatas"], data["documents"])
            if meta.get("doc_type") == "image"
        ]

        if not image_items:
            print("  [경고] DB에 image Document가 없습니다. "
                  "파이프라인 STEP 3~5(비전 요약)를 확인하세요.")
            print()
            return

        for idx, (meta, doc) in enumerate(image_items, start=1):
            img_file = meta.get("images", "?")
            page     = meta.get("page", "?")
            print(f"  [이미지 {idx}/{len(image_items)}]")
            print(f"  파일명 : {img_file}")
            print(f"  페이지 : {page}")
            print(f"  요약   :")
            for line in doc.strip().splitlines():
                print(f"    {line}")
            print("  " + "─" * 40)
            print()

    # ------------------------------------------------------------------ #
    #  STEP 3 — Chroma DB doc_type 분포                                   #
    # ------------------------------------------------------------------ #
    def verify_db_distribution(self):
        print("=" * 60)
        print("[STEP 3] Chroma DB doc_type 분포")
        print("=" * 60)
        print()

        vs       = self._get_vectorstore()
        all_meta = vs._collection.get(include=["metadatas"])["metadatas"] or []
        counter  = Counter(m.get("doc_type", "unknown") for m in all_meta)
        total    = sum(counter.values())

        max_bar  = 30
        for dtype in ("text", "table", "image"):
            count   = counter.get(dtype, 0)
            bar_len = round((count / total) * max_bar) if total > 0 else 0
            print(f"  {dtype:<6}: {count:>4}개  {'█' * bar_len}")

        for dtype, count in counter.items():
            if dtype not in ("text", "table", "image"):
                bar_len = round((count / total) * max_bar) if total > 0 else 0
                print(f"  {dtype:<6}: {count:>4}개  {'█' * bar_len}")

        print("  " + "─" * 33)
        print(f"  합계  : {total:>4}개")
        print()

        if counter.get("image", 0) == 0:
            print("  [경고] image Document가 0개입니다!")
            print()

    # ------------------------------------------------------------------ #
    #  STEP 4 — doc_type 필터 이미지 강제 검색                             #
    # ------------------------------------------------------------------ #
    def verify_image_filter_search(self):
        print("=" * 60)
        print("[STEP 4] doc_type 필터 이미지 강제 검색")
        print("=" * 60)
        print()

        vs      = self._get_vectorstore()
        results = vs.similarity_search(
            "교차로 차량",
            k=10,
            filter={"doc_type": "image"},
        )

        if not results:
            print("  [실패] 필터 검색 결과 없음 — DB에 image 청크가 저장되지 않았습니다")
            print()
            return

        for i, doc in enumerate(results, start=1):
            fname   = doc.metadata.get("images", "?")
            page    = doc.metadata.get("page", "?")
            preview = doc.page_content[:150].replace("\n", " ")
            print(f"  [{i}] 파일명: {fname}  │  페이지: {page}")
            print(f"       요약: {preview}...")
            print()

        print(f"  → 총 {len(results)}개 image 청크 확인")
        print()

    # ------------------------------------------------------------------ #
    #  STEP 5 — 키워드 유사도 검색 (이미지 포함 여부)                       #
    # ------------------------------------------------------------------ #
    def verify_similarity_search(self):
        print("=" * 60)
        print("[STEP 5] 키워드 유사도 검색 (이미지 포함 여부)")
        print("=" * 60)
        print()

        vs = self._get_vectorstore()

        for query in SEARCH_QUERIES:
            results = vs.similarity_search(query, k=5)
            print(f'  쿼리: "{query}"')

            img_count = 0
            for rank, doc in enumerate(results, start=1):
                dtype   = doc.metadata.get("doc_type", "?")
                page    = doc.metadata.get("page", "?")
                preview = doc.page_content[:80].replace("\n", " ")
                img_tag = "  ← 이미지 검색됨" if dtype == "image" else ""

                corner = "└─" if rank == len(results) else "├─"
                print(f"  {corner} 순위 {rank} │ {dtype:<5} │ p.{str(page):<3} │ {preview}{img_tag}")

                if dtype == "image":
                    img_count += 1

            tag = f"[포함] — 5개 중 {img_count}개 이미지" if img_count > 0 else "[미포함]"
            print(f"  결과: {tag}")
            print()

    # ------------------------------------------------------------------ #
    #  전체 실행                                                           #
    # ------------------------------------------------------------------ #
    def run_all(self):
        steps = [
            self.verify_extracted_images,
            self.verify_image_summaries,
            self.verify_db_distribution,
            self.verify_image_filter_search,
            self.verify_similarity_search,
        ]
        for step in steps:
            try:
                step()
            except Exception as e:
                print(f"  [STEP 오류] {e}\n")


if __name__ == "__main__":
    ChunkVerifier().run_all()
