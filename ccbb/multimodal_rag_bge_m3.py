"""
mutlimodal_rag_bge_m3.py

Multimodal RAG 클래스 파일 — 텍스트·표·이미지 Document 통합 처리

포함 기능
- PyMuPDF(fitz)로 페이지별 텍스트 및 이미지 추출
- Pillow로 이미지 리사이즈 (Claude API 입력 규격 준수)
- Gemini 비전 모델(gemini-2.0-flash)로 이미지 → 텍스트 요약 변환
- 표(Table) → Markdown 변환 후 독립 Document로 저장 (pdfplumber, 분할 없음)
- BAAI/bge-m3 로컬 임베딩 생성
- Chroma VectorStore 생성 및 검색
- 기존 Chroma DB 기반 Retriever 생성
- Gemini LLM 초기화
- basic RAG chain 실행 (텍스트/표/이미지 출처 구분 표기)
- LCEL RunnableLambda 방식 RAG 실행 (텍스트·표·이미지 컨텍스트 포함)

메타데이터 구조
    doc_type : "text"  — 일반 텍스트 chunk
    doc_type : "table" — 표 Document (page / table_index / row_count / col_count 포함)
    doc_type : "image" — 이미지 요약 Document (page / images 포함)

실행 예시
    python mutlimodal_rag_bge_m3.py

사용 예시
    from mutlimodal_rag_bge_m3 import RagBgeM3, get_llm, build_rag_components, runnable_lambda

    rag = RagBgeM3()
    llm = rag.get_llm()
    retriever = rag.build_rag_components()
    answer = rag.runnable_lambda(retriever, llm, "경영책임자의 의무는?")
"""

import os
import shutil
from typing import List, Optional, Tuple

import pdfplumber
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


PDF_PATH = "./source/fault_ratio_standards_carvcar.pdf"
DB_PATH = "./chroma_multimodal"
COLLECTION_NAME = "pdf_table_rag"

IMAGE_OUTPUT_DIR = "./data/extracted_images"   # PDF에서 추출한 원본 이미지 저장 경로
FILTERED_IMG_DIR = "./data/filtered_images"    # 리사이즈 완료 이미지 저장 경로
VISION_MODEL     = "gemini-2.5-flash"           # Gemini 비전 모델 (GOOGLE_API_KEY_VISION 사용)
MAX_IMG_PX       = 2240                        # 긴 변 최대 픽셀 (Claude API 입력 규격)
MAX_IMG_RATIO    = 4.5                         # 가로:세로 최대 비율 (Claude API 입력 규격)
MAX_IMG_BYTES    = 20 * 1024 * 1024            # 최대 파일 크기 20MB


class RagBgeM3:
    """BGE-M3 + Chroma + Gemini 기반 LangChain RAG 클래스"""

    def __init__(
        self,
        pdf_path: str = PDF_PATH,
        db_path: str = DB_PATH,
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        search_k: int = 3,
        embedding_device: str = "cuda",
        llm_model: str = "gemini-2.5-flash",
        temperature: float = 0,
        image_output_dir: str = IMAGE_OUTPUT_DIR,
        filtered_img_dir: str = FILTERED_IMG_DIR,
        vision_model: str = VISION_MODEL,
    ):
        load_dotenv()
        self.pdf_path = pdf_path
        self.db_path = db_path
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.search_k = search_k

        # CUDA 요청 시 가용성 확인 — 없으면 CPU로 자동 폴백
        import torch
        if embedding_device == "cuda" and not torch.cuda.is_available():
            print("[경고] CUDA를 사용할 수 없습니다. CPU로 자동 전환합니다.")
            embedding_device = "cpu"
        self.embedding_device = embedding_device
        self.llm_model = llm_model
        self.temperature = temperature
        self.image_output_dir = image_output_dir
        self.filtered_img_dir = filtered_img_dir
        self.vision_model = vision_model

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — PyMuPDF 텍스트·이미지 추출                             #
    # ------------------------------------------------------------------ #
    def _extract_text_and_images_from_pdf(
        self,
    ) -> Tuple[List[Document], str, List[Tuple[str, Optional[tuple]]]]:
        """
        PyMuPDF(fitz)로 PDF에서 페이지별 텍스트와 이미지를 추출합니다.

        - 텍스트: page.get_text("text")로 추출, merged_text.txt에 누적 저장
        - 이미지: page.get_images(full=True)로 추출,
                  page_{N}_img_{M}.{ext} 형식으로 image_output_dir에 저장
        - 이미지 bbox: page.get_image_rects(xref)로 추출, all_image_infos에 누적
        - 반환 Document 메타데이터:
            source   : PDF 파일명
            page     : 1-based 페이지 번호
            doc_type : "text"
            images   : 해당 페이지 이미지 경로 목록 (쉼표 구분 문자열)
        - 반환 all_image_infos : (경로, bbox) 튜플 리스트 — load_docs에서 bbox 매칭에 활용
        """
        import fitz  # PyMuPDF

        os.makedirs(self.image_output_dir, exist_ok=True)
        merged_text_path = os.path.join(self.image_output_dir, "merged_text.txt")
        merged_text = ""
        documents = []
        all_image_infos: List[Tuple[str, Optional[tuple]]] = []  # 전체 이미지 (경로, bbox) 누적

        print(f"  PyMuPDF로 텍스트·이미지 추출 시작: '{self.pdf_path}'")
        doc = fitz.open(self.pdf_path)
        for i, page in enumerate(doc):
            page_number = i + 1
            page_text = page.get_text("text").strip()
            images_info = []

            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext   = base_image["ext"]
                image_filename = f"page_{page_number}_img_{img_index + 1}.{image_ext}"
                image_path = os.path.join(self.image_output_dir, image_filename)
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                # 이미지가 페이지 내 어느 위치에 있는지 bbox 함께 저장
                rects = page.get_image_rects(xref)
                img_bbox = (
                    rects[0].x0, rects[0].y0,
                    rects[0].x1, rects[0].y1
                ) if rects else None

                images_info.append((image_path, img_bbox))      # 페이지별 (경로, bbox)
                all_image_infos.append((image_path, img_bbox))  # 전체 누적

            documents.append(Document(
                page_content=page_text,
                metadata={
                    "source":   os.path.basename(self.pdf_path),
                    "page":     page_number,
                    "doc_type": "text",
                    "images":   ", ".join(path for path, _ in images_info),
                },
            ))
            merged_text += f"\n\n--- Page {page_number} ---\n\n{page_text}"

        with open(merged_text_path, "w", encoding="utf-8") as f:
            f.write(merged_text)

        print(f"  → PyMuPDF: {len(documents)}페이지 텍스트 추출, "
              f"이미지 {len(all_image_infos)}장 저장")
        # image_infos: 전체 이미지의 (경로, bbox) 리스트 — load_docs에서 사용
        return documents, merged_text_path, all_image_infos

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — Pillow 이미지 리사이즈                                  #
    # ------------------------------------------------------------------ #
    def _resize_images(self) -> List[str]:
        """
        image_output_dir 내 이미지를 Claude API 입력 규격에 맞게 리사이즈하고
        filtered_img_dir에 저장합니다.

        - 지원 포맷: PNG, JPEG, WEBP, BMP만 처리 (그 외 건너뜀)
        - 파일 크기 MAX_IMG_BYTES(20MB) 초과 시 건너뜀
        - 긴 변 > MAX_IMG_PX(2240px) 또는 비율 > MAX_IMG_RATIO(4.5) 시 리사이즈
        - 저장 포맷: 항상 PNG, LANCZOS 리샘플링
        """
        from PIL import Image
        import shutil

        os.makedirs(self.filtered_img_dir, exist_ok=True)
        allowed_formats = ("PNG", "JPEG", "WEBP", "BMP")
        valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

        input_dir = self.image_output_dir
        image_files = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if os.path.splitext(f)[1].lower() in valid_exts
        ]

        result_paths = []
        print(f"  이미지 전처리 시작: 총 {len(image_files)}장")

        for path in image_files:
            filename = os.path.basename(path)
            dest = os.path.join(self.filtered_img_dir, filename)

            try:
                if os.path.getsize(path) > MAX_IMG_BYTES:
                    print(f"    [건너뜀] 용량 초과: {filename}")
                    continue

                with Image.open(path) as img:
                    if img.format and img.format.upper() not in allowed_formats:
                        print(f"    [건너뜀] 포맷 불가: {filename}")
                        continue

                    w, h = img.size
                    ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 999
                    needs_resize = max(w, h) > MAX_IMG_PX or ratio > MAX_IMG_RATIO

                    if not needs_resize:
                        shutil.copy(path, dest)
                        result_paths.append(dest)
                        continue

                    # 리사이즈 크기 계산
                    if ratio > MAX_IMG_RATIO:
                        if w > h:
                            new_w = min(w, MAX_IMG_PX)
                            new_h = int(new_w / MAX_IMG_RATIO)
                        else:
                            new_h = min(h, MAX_IMG_PX)
                            new_w = int(new_h / MAX_IMG_RATIO)
                    else:
                        if w >= h:
                            new_w = min(w, MAX_IMG_PX)
                            new_h = int(h * (new_w / w))
                        else:
                            new_h = min(h, MAX_IMG_PX)
                            new_w = int(w * (new_h / h))

                    resized = img.resize((new_w, new_h), Image.LANCZOS).convert("RGB")
                    # 저장 시 확장자를 .png로 통일
                    dest = os.path.join(
                        self.filtered_img_dir,
                        os.path.splitext(filename)[0] + ".png"
                    )
                    resized.save(dest, format="PNG", optimize=True)
                    result_paths.append(dest)
                    print(f"    [리사이즈] {filename} → {new_w}x{new_h}")

            except Exception as e:
                print(f"    [오류] {filename}: {e}")

        print(f"  이미지 전처리 완료: {len(result_paths)}장 → '{self.filtered_img_dir}'")
        return result_paths

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — Anthropic 비전 모델 이미지 요약                         #
    # ------------------------------------------------------------------ #
    def _summarize_images_with_vision(
        self,
        image_infos: List[Tuple[str, Optional[tuple]]],  # (경로, bbox) 리스트
        page_table_map: dict = None,  # {page_number(int): [pdfplumber Table 객체]}
    ) -> List[Document]:
        """
        Gemini 비전 모델(Base64 방식)로 이미지를 텍스트 요약 Document로 변환합니다.

        - GOOGLE_API_KEY_VISION 환경변수 필요 (LLM용 GOOGLE_API_KEY와 별도)
        - 각 이미지를 base64로 인코딩해 Gemini 비전 모델에 전달
        - 파일명에서 페이지 번호를 추출해 메타데이터에 저장
        - page_table_map이 제공되면 이미지 bbox로 동일 페이지 표를 찾아 page_content에 합산
        - 반환 Document:
            page_content : 이미지 요약 + "[관련 표]" (매칭된 표가 있을 때)
            메타데이터:
                source   : PDF 파일명
                page     : 파일명에서 추출한 페이지 번호 (없으면 None)
                doc_type : "image"
                images   : 이미지 파일명
        """
        import base64
        import re
        from langchain_core.messages import HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI

        vision_api_key = os.getenv("GOOGLE_API_KEY_VISION")
        if not vision_api_key:
            raise EnvironmentError("GOOGLE_API_KEY_VISION 환경 변수를 설정해주세요.")

        vision_llm = ChatGoogleGenerativeAI(
            model=self.vision_model,
            google_api_key=vision_api_key,
            temperature=0,
        )

        system_text = (
            "당신은 교통사고 과실비율 문서 내 시각 자료를 분석하는 AI입니다.\n"
            "이미지는 사고 상황 도식도, 교차로 구조, 차량 배치도, 표, 그래프 등 다양한 형태일 수 있습니다.\n"
            "다음 기준으로 요약을 작성하세요:\n"
            "- 차량 위치, 진행 방향, 충돌 지점 등 사고 관련 정보를 명확히 서술\n"
            "- 신호등, 차선, 횡단보도 등 교통 관련 시각 요소를 구체적으로 기술\n"
            "- 표·그래프는 전체 흐름과 특징적 차이만 요약하고 수치 나열은 피함\n"
            "- 검색 가능한 핵심 키워드 포함, 사실 중심 문장으로 작성\n"
            "- 3~5문장 이내 단일 문단으로 출력\n\n"
            "이 이미지는 교통사고 과실비율 문서 내 시각 자료입니다. 핵심 정보를 요약해 주세요."
        )

        image_docs = []
        print(f"  비전 모델 요약 시작: 총 {len(image_infos)}장 ({self.vision_model})")

        for path, img_bbox in image_infos:
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1].lower()
            media_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(ext, "image/png")

            try:
                with open(path, "rb") as f:
                    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

                message = HumanMessage(content=[
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                    },
                    {
                        "type": "text",
                        "text": system_text,
                    },
                ])
                response = vision_llm.invoke([message])
                summary = response.content

                match = re.search(r"page_(\d+)_img_\d+", filename)
                page_number = int(match.group(1)) if match else None

                # ── 이미지와 매칭되는 표 찾기 ──────────────────────────────
                nearest_table_text = ""
                if page_table_map and page_number is not None and img_bbox is not None:
                    tables_on_page = page_table_map.get(page_number, [])
                    matched_table = self._find_nearest_table(img_bbox, tables_on_page)
                    if matched_table:
                        rows = matched_table.extract()
                        if rows:
                            nearest_table_text = self._table_to_markdown(
                                rows, page_number, 0
                            )
                            print(f"    [표 매칭] {filename} → page {page_number} 표 연결")
                    else:
                        print(f"    [표 없음] {filename} — 매칭되는 표를 찾지 못했습니다")

                # 매칭된 표 텍스트를 page_content에 합산
                image_docs.append(Document(
                    page_content=(
                        summary
                        + (f"\n\n[관련 표]\n{nearest_table_text}" if nearest_table_text else "")
                    ),
                    metadata={
                        "source":   os.path.basename(self.pdf_path),
                        "page":     page_number,
                        "doc_type": "image",
                        "images":   filename,
                    },
                ))
                print(f"    [완료] {filename}")

            except Exception as e:
                print(f"    [오류] {filename}: {e}")

        print(f"  비전 요약 완료: {len(image_docs)}개 Document 생성")
        return image_docs

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — 표(Table) → Markdown 변환                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _table_to_markdown(table: List[List], page_num: int, table_idx: int) -> str:
        """
        pdfplumber가 반환한 2D 리스트를 Markdown 표 문자열로 변환합니다.

        변환 예시
        ---------
        [TABLE 2 - Page 3]
        | 구분 | 의무 내용 | 위반 시 처벌 |
        | --- | --- | --- |
        | 경영책임자 | 안전보건관리체계 구축 | 1년 이상 징역 |
        """
        if not table or not table[0]:
            return ""

        header = f"[TABLE {table_idx} - Page {page_num}]\n"
        rows = []
        for row_idx, row in enumerate(table):
            clean = [str(cell).strip().replace("\n", " ") if cell else "" for cell in row]
            rows.append("| " + " | ".join(clean) + " |")
            if row_idx == 0:                          # 헤더 구분선
                rows.append("| " + " | ".join(["---"] * len(clean)) + " |")
        return header + "\n".join(rows)

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — 이미지 bbox와 표 bbox 매칭                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _find_nearest_table(
        img_bbox: tuple,
        tables_on_page: list,
        margin: float = 5.0,
    ) -> object:
        """
        이미지 bbox를 포함하는 pdfplumber Table 객체를 반환합니다.

        PyMuPDF와 pdfplumber 모두 좌상단 원점 좌표계를 사용하므로
        별도 변환 없이 직접 비교 가능합니다.

        Parameters
        ----------
        img_bbox        : (x0, y0, x1, y1)  — PyMuPDF get_image_rects 결과
        tables_on_page  : pdfplumber page.find_tables() 결과 리스트
        margin          : 소수점 오차 허용 범위 (기본 5.0px)

        Returns
        -------
        매칭된 Table 객체, 없으면 None
        """
        if not img_bbox or not tables_on_page:
            return None

        img_x0, img_y0, img_x1, img_y1 = img_bbox

        for table in tables_on_page:
            t_x0, t_top, t_x1, t_bottom = table.bbox
            if (
                t_x0   - margin <= img_x0 and
                t_top  - margin <= img_y0 and
                img_x1 <= t_x1     + margin and
                img_y1 <= t_bottom + margin
            ):
                return table

        return None

    # ------------------------------------------------------------------ #
    #  내부 헬퍼 — 페이지 단위 표 Document 생성                           #
    # ------------------------------------------------------------------ #
    def _extract_table_docs(self, pdf_path: str) -> List[Document]:
        """
        pdfplumber로 각 페이지의 표를 추출해 독립 Document 목록을 반환합니다.

        메타데이터 필드
        ---------------
        source      : PDF 파일 경로
        page        : 0-based 페이지 번호  (PyPDFLoader 기준과 일치)
        doc_type    : "table"
        table_index : 해당 페이지 내 표 순서 (1-based)
        row_count   : 행 수
        col_count   : 열 수
        """
        table_docs: List[Document] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):   # 0-based
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables, start=1):
                    if not table:
                        continue
                    md = self._table_to_markdown(table, page_num + 1, t_idx)
                    if not md.strip():
                        continue
                    table_docs.append(Document(
                        page_content=md,
                        metadata={
                            "source":      pdf_path,
                            "page":        page_num,      # 0-based (PyPDF 호환)
                            "doc_type":    "table",
                            "table_index": t_idx,
                            "row_count":   len(table),
                            "col_count":   len(table[0]) if table else 0,
                        },
                    ))
        return table_docs

    # ------------------------------------------------------------------ #
    #  load_docs — 텍스트 chunk + 표 + 이미지 Document 통합 반환          #
    # ------------------------------------------------------------------ #
    def load_docs(self) -> Optional[List[Document]]:
        """
        PyMuPDF로 PDF를 로드하고 텍스트·표·이미지 LangChain Document 목록을 반환합니다.

        처리 흐름
        ---------
        1. _extract_text_and_images_from_pdf()
           → PyMuPDF로 페이지별 텍스트 Document 목록 + 이미지 파일 저장
        2. RecursiveCharacterTextSplitter
           → 텍스트 Document를 chunk 분할, doc_type="text" 유지
        3. _extract_table_docs()
           → 기존 pdfplumber 표 추출 (변경 없음)
        4. _resize_images()
           → extracted_images/ → filtered_images/ 로 리사이즈
        5. _summarize_images_with_vision(filtered_image_paths)
           → Anthropic Base64로 이미지 요약 Document 생성 (doc_type="image")
        6. combined_docs = text_chunks + table_docs + image_docs
           → 빈 content 제거 후 반환
        """
        if not os.path.exists(self.pdf_path):
            print(f"[오류] '{self.pdf_path}' 파일이 없습니다.")
            print("      → python create_manual_pdf.py 를 먼저 실행하세요!")
            return None

        # ── 1. PyMuPDF 텍스트·이미지 추출 (경로 + bbox 포함) ──────────
        page_docs, _, all_image_infos = self._extract_text_and_images_from_pdf()

        # ── 2. 텍스트 chunk 분할 ────────────────────────────────────────
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        text_chunks = splitter.split_documents(page_docs)
        text_chunks = [d for d in text_chunks if d.page_content.strip()]
        for chunk in text_chunks:
            chunk.metadata["doc_type"] = "text"   # 텍스트 chunk 표시

        # ── 3. 표 추출 (pdfplumber 직접 호출) ──────────────────────────
        table_docs = self._extract_table_docs(self.pdf_path)

        # ── pdfplumber Table 객체(bbox 포함)를 페이지별로 수집 ──────────
        # _extract_table_docs는 Markdown 변환된 Document만 반환하므로
        # bbox 매칭을 위해 Table 객체는 별도로 수집한다
        page_table_map: dict = {}
        with pdfplumber.open(self.pdf_path) as _pdf:
            for _i, _page in enumerate(_pdf.pages):
                _tables = _page.find_tables()
                if _tables:
                    page_table_map[_i + 1] = _tables  # 1-based 페이지 번호
        print(f"  → page_table_map: {len(page_table_map)}개 페이지에서 표 위치 수집")

        # ── 4. 이미지 리사이즈 ──────────────────────────────────────────
        filtered_image_paths = self._resize_images()

        # ── filtered 경로를 기준으로 all_image_infos에서 bbox 재구성 ────
        # _resize_images는 파일명을 보존하므로 basename으로 매칭
        bbox_lookup = {
            os.path.basename(path): bbox
            for path, bbox in all_image_infos
        }
        filtered_image_infos: List[Tuple[str, Optional[tuple]]] = [
            (path, bbox_lookup.get(os.path.basename(path)))
            for path in filtered_image_paths
        ]

        # ── 5. 이미지 → 텍스트 요약 Document 생성 (표 bbox 매칭 포함) ──
        image_docs = self._summarize_images_with_vision(
            filtered_image_infos,
            page_table_map,
        )

        # ── 6. 합산 및 빈 content 제거 ──────────────────────────────────
        combined_docs = text_chunks + table_docs + image_docs
        combined_docs = [d for d in combined_docs if d.page_content.strip()]

        print(f"  → 텍스트 chunk {len(text_chunks)}개 + 표 {len(table_docs)}개 "
              f"+ 이미지 {len(image_docs)}개 = 총 {len(combined_docs)}개 Document 준비 완료")
        return combined_docs

    def get_embeddings(self):
        """BAAI/bge-m3 로컬 임베딩 — API 키 불필요, 색인/검색 모두 사용"""
        from langchain_huggingface import HuggingFaceEmbeddings

        print("  임베딩: BAAI/bge-m3 (로컬, API 키 불필요)")
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": self.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )

    def create_vectorstore(self):
        """LangChain Chroma VectorStore를 생성하고 PDF chunk(텍스트+표)를 저장합니다."""
        print("=" * 50)
        print("[실습 1] VectorStore 생성 및 문서 저장")

        docs = self.load_docs()
        if docs is None:
            return None

        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)

        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.get_embeddings(),
            collection_name=self.collection_name,
            persist_directory=self.db_path,
        )

        n_text  = sum(1 for d in docs if d.metadata.get("doc_type") == "text")
        n_table = sum(1 for d in docs if d.metadata.get("doc_type") == "table")
        n_image = sum(1 for d in docs if d.metadata.get("doc_type") == "image")
        print(f"  → 텍스트 {n_text}개 + 표 {n_table}개 + 이미지 {n_image}개 = 총 {len(docs)}개 chunk를 "
              f"'{self.db_path}'에 저장했습니다.")
        return vectorstore

    def similarity_search(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """VectorStore에서 유사도 검색을 실행합니다. (텍스트·표 모두 검색)"""
        print("=" * 50)
        print("[실습 2] 유사도 검색 (similarity_search)")

        query = query or "경영책임자가 지켜야 할 안전 의무는 무엇인가요?"
        results = vectorstore.similarity_search(query, k=k)

        print(f"  질문: '{query}'")
        print(f"  → {len(results)}개 결과 반환\n")
        for i, doc in enumerate(results):
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  [결과 {i + 1}] {icon} [{dtype.upper()}]")
            print(f"    내용: {doc.page_content[:200]}...")
            print(f"    출처: {doc.metadata}")
        print()
        return results

    def search_with_score(self, vectorstore, query: Optional[str] = None, k: int = 3):
        """VectorStore에서 유사도 점수와 함께 검색합니다. (텍스트·표 모두 검색)"""
        print("=" * 50)
        print("[실습 3] 점수 포함 검색 (similarity_search_with_score)")

        query = query or "중대재해 발생 시 처벌 수위는?"
        results = vectorstore.similarity_search_with_score(query, k=k)

        print(f"  질문: '{query}'\n")
        for doc, score in results:
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  점수: {score:.4f}  ← 낮을수록 유사 (Chroma는 거리 기준)  "
                  f"{icon} [{dtype.upper()}]")
            print(f"  내용: {doc.page_content[:200]}...")
            print()
        return results

    def search_with_filter(
        self,
        vectorstore,
        query: Optional[str] = None,
        page: int = 0,
        k: int = 3,
    ):
        """metadata 필터로 검색 범위를 좁혀 검색합니다. (page 기준, 텍스트+표 포함)"""
        print("=" * 50)
        print("[실습 4] metadata 필터 검색")

        query = query or "재해 발생 요건"
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"page": page},
        )

        print(f"  질문: '{query}'  (page={page} chunk만 검색)")
        print(f"  → {len(results)}개 결과\n")
        for doc in results:
            dtype = doc.metadata.get("doc_type", "text")
            icon  = "📊" if dtype == "table" else "📄"
            print(f"  {icon} [{dtype.upper()}]  "
                  f"p.{doc.metadata.get('page', '?')}  "
                  f"출처: {doc.metadata.get('source', '')}")
            print(f"  내용: {doc.page_content[:200]}...")
            print()
        return results

    def search_tables_only(
        self,
        vectorstore,
        query: Optional[str] = None,
        k: int = 3,
    ):
        """
        표(Table) Document만 대상으로 유사도 검색합니다.

        doc_type="table" 메타데이터 필터를 사용하므로
        텍스트 chunk는 결과에 포함되지 않습니다.
        """
        print("=" * 50)
        print("[실습 5] 표 전용 검색 (search_tables_only)")

        query = query or "처벌 기준 및 처벌 수위"
        results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"doc_type": "table"},
        )

        print(f"  질문: '{query}'  (표 Document만 검색)")
        print(f"  → {len(results)}개 표 결과\n")
        for i, doc in enumerate(results):
            meta = doc.metadata
            print(f"  📊 [표 결과 {i + 1}]  "
                  f"p.{meta.get('page', '?')} / "
                  f"표 {meta.get('table_index', '?')} / "
                  f"{meta.get('row_count', '?')}행×{meta.get('col_count', '?')}열")
            print(f"  {doc.page_content}")
            print()
        return results

    def build_rag_components(self):
        """기존 chroma_db_bge_m3에서 Retriever를 준비합니다.
        DB가 없거나 표(doc_type='table') 또는 이미지(doc_type='image')가 0개면 자동으로 재빌드합니다."""
        needs_rebuild = False

        if not os.path.exists(self.db_path):
            print(f"  '{self.db_path}' DB가 없어 새로 빌드합니다.")
            needs_rebuild = True
        else:
            embeddings = self.get_embeddings()
            vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.db_path,
            )
            all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
            n_table = sum(1 for m in all_meta if m.get("doc_type") == "table")
            n_image = sum(1 for m in all_meta if m.get("doc_type") == "image")
            if n_table == 0 or n_image == 0:
                print(f"  기존 DB에 표 또는 이미지 Document가 없습니다. 재빌드합니다.")
                needs_rebuild = True

        if needs_rebuild:
            vectorstore = self.create_vectorstore()
            if vectorstore is None:
                raise RuntimeError("VectorStore 빌드에 실패했습니다.")

        total = vectorstore._collection.count()
        all_meta = vectorstore._collection.get(include=["metadatas"])["metadatas"] or []
        n_table = sum(1 for m in all_meta if m.get("doc_type") == "table")
        n_image = sum(1 for m in all_meta if m.get("doc_type") == "image")
        n_text  = total - n_table - n_image
        print(f"  VectorStore 로드 완료: 텍스트 {n_text}개 + 표 {n_table}개 + 이미지 {n_image}개 = 총 {total}개 chunk")

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.search_k},
        )
        return retriever

    def get_llm(self):
        """Gemini LLM을 초기화합니다."""
        api_key = os.getenv("GOOGLE_API_KEY_VISION")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY 환경 변수를 설정해주세요.")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=api_key,
            temperature=self.temperature,
        )

    def basic_rag_chain(self, retriever, llm, human_message: str):
        """기본 LCEL RAG chain을 실행합니다."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 교통사고 과실비율 전문 AI 어시스턴트입니다.\n"
                    "블랙박스 영상 분석 결과와 아래 참고 문서를 바탕으로 과실비율에 대한 의견을 제공합니다.\n"
                    "\n"
                    "[답변 규칙]\n"
                    "1. 반드시 아래 컨텍스트 문서만을 근거로 답하세요.\n"
                    "2. 컨텍스트에 근거가 없으면 '제공된 문서에서 해당 사고 유형을 찾을 수 없습니다'라고 답하세요.\n"
                    "3. 답변 말미에 반드시 출처(source, page)를 표기하세요.\n"
                    "\n"
                    "[컨텍스트 유형별 활용 방법]\n"
                    "- [텍스트]: 사고 상황 설명, 법적 근거, 판례를 인용할 때 활용하세요.\n"
                    "- [표]: 기본 과실비율 수치와 수정요소(+/- 값)를 반드시 정확히 계산하여 적용하세요.\n"
                    "  단, 과실비율의 합이 100%를 초과하는 경우 인과관계를 고려해 조정 가능함을 안내하세요.\n"
                    "- [이미지]: 교차로 구조, 차량 진입 방향, 충돌 위치 등 공간적 배치 정보를 설명할 때 활용하세요.\n"
                    "\n"
                    "[답변 형식]\n"
                    "1. 사고 유형 : 해당 차16-N 유형 명시\n"
                    "2. 기본 과실비율 : A N% : B N%\n"
                    "3. 수정요소 적용 : 해당 항목과 수치 나열 후 최종 과실비율 계산\n"
                    "4. 근거 : 관련 법조문 또는 판례\n"
                    "5. 출처 : source / page\n"
                    "\n"
                    "한국어로, 전문적이되 이해하기 쉽게 답변하세요.",
                ),
                ("human", "### 컨텍스트\n{context}\n\n### 질문\n{question}"),
            ]
        )

        # 검색된 docs를 클로저 변수로 보관해 답변 후 메타데이터 출력에 활용
        _retrieved: list = []

        def format_docs(docs: list) -> str:
            """Document 리스트 → 출처·doc_type 포함 텍스트 블록.
            이미지 Document는 page_context(동일 페이지 텍스트)를 컨텍스트에 추가합니다."""
            _retrieved.clear()
            _retrieved.extend(docs)   # 검색된 docs 보관

            blocks = []
            for d in docs:
                dtype  = d.metadata.get("doc_type", "text")
                source = d.metadata.get("source", "?")
                page   = d.metadata.get("page", "?")

                if dtype == "table":
                    label = f"[출처: {source} p.{page}] [표]"
                    blocks.append(f"{label}\n{d.page_content}")
                elif dtype == "image":
                    label = f"[출처: {source} p.{page}] [이미지]"
                    # 이미지 요약 + 동일 페이지 텍스트를 함께 컨텍스트로 구성
                    page_context = d.metadata.get("page_context", "")
                    content = d.page_content
                    if page_context:
                        content += f"\n[동일 페이지 텍스트 참고]\n{page_context}"
                    blocks.append(f"{label}\n{content}")
                else:
                    label = f"[출처: {source} p.{page}] [텍스트]"
                    blocks.append(f"{label}\n{d.page_content}")

            return "\n\n".join(blocks)

        rag_chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        answer = rag_chain.invoke(human_message)

        # ── 참조 Document 메타데이터 출력 ──────────────────────────────────
        meta_lines = "\n" + "─" * 50 + "\n[참조 문서 메타데이터]\n"
        for i, doc in enumerate(_retrieved, 1):
            dtype  = doc.metadata.get("doc_type", "?")
            page   = doc.metadata.get("page", "?")
            source = doc.metadata.get("source", "?")
            images = doc.metadata.get("images", "")
            t_idx  = doc.metadata.get("table_index", "")
            p_ctx  = doc.metadata.get("page_context", "")

            if dtype == "table":
                extra = (
                    f"표 인덱스: {t_idx} / "
                    f"행: {doc.metadata.get('row_count','?')} × "
                    f"열: {doc.metadata.get('col_count','?')}"
                )
            elif dtype == "image":
                extra = f"이미지 파일: {images}"
                if p_ctx:
                    extra += f" / 페이지 텍스트 앞 50자: {p_ctx[:50]}..."
            else:
                extra = ""

            meta_lines += (
                f"  [{i}] doc_type: {dtype:<6}  │  "
                f"source: {source}  │  "
                f"page: {page}"
            )
            if extra:
                meta_lines += f"\n       {extra}"
            meta_lines += "\n"

        return answer + meta_lines

    def runnable_lambda(self, retriever, llm, human_message: str):
        """LCEL RunnableLambda 방식으로 전처리/후처리를 포함한 RAG를 실행합니다."""

        def preprocess(query: str) -> dict:
            """질문을 정제하고 DB에서 관련 문서를 검색해 context 구성.
            이미지 Document는 page_context(동일 페이지 텍스트)도 컨텍스트에 포함합니다.
            retrieved_docs를 postprocess까지 전달하기 위해 반환 dict에 포함합니다."""
            cleaned = query.strip().rstrip("?!.")
            docs = retriever.invoke(cleaned)
            blocks = []
            for d in docs:
                dtype = d.metadata.get("doc_type", "text")
                page  = d.metadata.get("page", "?")
                if dtype == "table":
                    t_idx = d.metadata.get("table_index", "?")
                    label = f"[표 — p.{page}, 표{t_idx}]"
                    blocks.append(f"{label}\n{d.page_content}")
                elif dtype == "image":
                    img_file = d.metadata.get("images", "?")
                    label = f"[이미지 — p.{page}, {img_file}]"
                    # 이미지 요약 + 동일 페이지 텍스트를 함께 컨텍스트로 구성
                    page_context = d.metadata.get("page_context", "")
                    content = d.page_content
                    if page_context:
                        content += f"\n[동일 페이지 텍스트 참고]\n{page_context}"
                    blocks.append(f"{label}\n{content}")
                else:
                    label = f"[텍스트 — p.{page}]"
                    blocks.append(f"{label}\n{d.page_content}")
            context = "\n\n".join(blocks)
            # retrieved_docs를 postprocess까지 전달하기 위해 함께 반환
            return {"context": context, "question": cleaned, "retrieved_docs": docs}

        def postprocess(inputs: dict) -> str:
            """답변 본문에 참조 Document 메타데이터를 추가하여 반환합니다."""
            answer = inputs.get("answer", "")
            docs   = inputs.get("retrieved_docs", [])

            # ── 답변 본문 ──────────────────────────────────────────────────
            result = f"[교통사고 과실비율 기반 답변]\n{answer.strip()}\n"

            # ── 참조 Document 메타데이터 출력 ──────────────────────────────
            result += "\n" + "─" * 50 + "\n"
            result += "[참조 문서 메타데이터]\n"
            for i, doc in enumerate(docs, 1):
                dtype  = doc.metadata.get("doc_type", "?")
                page   = doc.metadata.get("page", "?")
                source = doc.metadata.get("source", "?")
                images = doc.metadata.get("images", "")
                t_idx  = doc.metadata.get("table_index", "")
                p_ctx  = doc.metadata.get("page_context", "")

                # doc_type별 부가 정보 구성
                if dtype == "table":
                    extra = (
                        f"표 인덱스: {t_idx} / "
                        f"행: {doc.metadata.get('row_count','?')} × "
                        f"열: {doc.metadata.get('col_count','?')}"
                    )
                elif dtype == "image":
                    extra = f"이미지 파일: {images}"
                    if p_ctx:
                        extra += f" / 페이지 텍스트 앞 50자: {p_ctx[:50]}..."
                else:
                    extra = ""

                result += (
                    f"  [{i}] doc_type: {dtype:<6}  │  "
                    f"source: {source}  │  "
                    f"page: {page}"
                )
                if extra:
                    result += f"\n       {extra}"
                result += "\n"

            return result

        def merge_llm_output(inputs: dict) -> dict:
            """LLM 출력(answer)과 retrieved_docs를 하나의 dict로 합산합니다."""
            return {
                "answer":         inputs["answer"],
                "retrieved_docs": inputs["retrieved_docs"],
            }

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "주어진 참고 문서만을 근거로 정확하게 답하세요.\n"
                    "[표] 레이블이 붙은 내용은 문서의 표(Table)이므로 수치와 항목을 정확히 인용하세요.",
                ),
                ("human", "참고 문서:\n{context}\n\n질문: {question}"),
            ]
        )

        # preprocess 결과의 retrieved_docs를 보존하면서 LLM 호출 후 postprocess로 전달
        chain = (
            RunnableLambda(preprocess)
            | RunnablePassthrough.assign(
                answer=(
                    (lambda x: {"context": x["context"], "question": x["question"]})
                    | prompt
                    | llm
                    | StrOutputParser()
                )
            )
            | RunnableLambda(merge_llm_output)
            | RunnableLambda(postprocess)
        )

        return chain.invoke(human_message)

    def run_cli(self):
        """질문을 입력받아 RAG 답변을 출력하는 CLI 실행 함수입니다."""
        try:
            llm = self.get_llm()
            retriever = self.build_rag_components()
        except Exception as exc:
            print("llm, vectorDB 호출에 실패하였습니다.")
            print(f"[상세 오류] {exc}")
            return

        while True:
            human_message = input("[질문(q:종료)]")
            if human_message == "q":
                return

            ai_message = self.runnable_lambda(retriever, llm, human_message)
            print("\n" + "=" * 60)
            print(ai_message)
            print("=" * 60 + "\n")


# -----------------------------------------------------------------------------
# 기존 함수명 호환용 래퍼
# 기존 소스에서 import 하던 함수명을 그대로 사용할 수 있게 유지합니다.
# -----------------------------------------------------------------------------
_default_rag = RagBgeM3()


def load_docs():
    return _default_rag.load_docs()


def get_embeddings():
    return _default_rag.get_embeddings()


def create_vectorstore():
    return _default_rag.create_vectorstore()


def similarity_search(vectorstore):
    return _default_rag.similarity_search(vectorstore)


def search_with_score(vectorstore):
    return _default_rag.search_with_score(vectorstore)


def search_with_filter(vectorstore):
    return _default_rag.search_with_filter(vectorstore)


def search_tables_only(vectorstore):
    return _default_rag.search_tables_only(vectorstore)


def build_rag_components():
    return _default_rag.build_rag_components()


def get_llm():
    return _default_rag.get_llm()


def basic_rag_chain(retriever, llm, human_message):
    return _default_rag.basic_rag_chain(retriever, llm, human_message)


def runnable_lambda(retriever, llm, human_message):
    return _default_rag.runnable_lambda(retriever, llm, human_message)


if __name__ == "__main__":
    RagBgeM3().run_cli()
