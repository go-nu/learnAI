"""
pdf_loader_v1.py — PDF 로딩·청킹 Mixin
PyMuPDF 텍스트/이미지 추출, pdfplumber 표 추출, 사례별 청킹,
이미지 리사이즈, Gemini 비전 요약을 담당하는 메서드 모음입니다.
RagBgeM3 클래스에 mixin으로 조합됩니다.
"""

import os
from typing import List, Optional, Tuple

import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config_v1 import (
    CASE_PATTERN, MAX_CASE_CHARS,
    MAX_IMG_PX, MAX_IMG_RATIO, MAX_IMG_BYTES,
)


class PdfLoaderMixin:
    """PDF 로딩·청킹 관련 메서드 Mixin"""

    def _extract_text_and_images_from_pdf(
        self,
    ) -> Tuple[List[Document], str, List[Tuple[str, Optional[tuple]]]]:
        """
        PyMuPDF(fitz)로 PDF에서 페이지별 텍스트와 이미지를 추출합니다.

        반환값
        ------
        (page_documents, merged_text_path, all_image_infos)
        - page_documents   : 페이지별 텍스트 Document 리스트 (doc_type="text")
        - merged_text_path : 전체 텍스트가 저장된 .txt 경로
        - all_image_infos  : (이미지경로, bbox) 튜플 리스트
        """
        import fitz

        os.makedirs(self.image_output_dir, exist_ok=True)
        merged_text_path = os.path.join(self.image_output_dir, "merged_text.txt")
        merged_text = ""
        documents = []
        all_image_infos: List[Tuple[str, Optional[tuple]]] = []

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

                rects = page.get_image_rects(xref)
                img_bbox = (
                    rects[0].x0, rects[0].y0,
                    rects[0].x1, rects[0].y1
                ) if rects else None

                images_info.append((image_path, img_bbox))
                all_image_infos.append((image_path, img_bbox))

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
        return documents, merged_text_path, all_image_infos

    def _split_by_case(self, text_documents: List[Document]) -> List[Document]:
        """
        페이지별 텍스트 Document를 사례 번호(차N-N) 기준으로 분할합니다.

        - CASE_PATTERN으로 줄 시작 사례 번호만 경계로 인식
        - 사례 번호 이전 머리말은 case_id="머리말" 으로 별도 처리
        - MAX_CASE_CHARS 초과 블록은 RecursiveCharacterTextSplitter로 추가 분할
        - 패턴 미발견 시 RecursiveCharacterTextSplitter(800자) 로 자동 폴백
        """
        import re

        if not text_documents:
            return []

        full_text = ""
        char_to_page: List[Tuple[int, int]] = []
        for doc in text_documents:
            start = len(full_text)
            full_text += doc.page_content + "\n\n"
            char_to_page.append((start, doc.metadata.get("page", 0)))

        def get_page(offset: int) -> int:
            page = char_to_page[0][1]
            for start, p in char_to_page:
                if start <= offset:
                    page = p
                else:
                    break
            return page

        source = text_documents[0].metadata.get("source", "") if text_documents else ""
        pattern = re.compile(CASE_PATTERN)
        matches = list(pattern.finditer(full_text))

        if not matches:
            print("  [경고] 사례 번호 패턴을 찾지 못했습니다. RecursiveCharacterTextSplitter로 폴백합니다.")
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            return splitter.split_documents(text_documents)

        chunks: List[Document] = []

        preamble = full_text[: matches[0].start()].strip()
        if preamble:
            chunks.append(Document(
                page_content=preamble,
                metadata={"source": source, "page": get_page(0),
                          "doc_type": "text", "case_id": "머리말"},
            ))

        for i, match in enumerate(matches):
            case_id     = match.group()
            block_start = match.start()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            block_text  = full_text[block_start:block_end].strip()
            page        = get_page(block_start)

            if not block_text:
                continue

            if len(block_text) > MAX_CASE_CHARS:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=MAX_CASE_CHARS, chunk_overlap=100,
                    separators=["\n\n", "\n", " "],
                )
                for j, sub in enumerate(splitter.split_text(block_text)):
                    chunks.append(Document(
                        page_content=sub,
                        metadata={"source": source, "page": page,
                                  "doc_type": "text", "case_id": case_id, "sub_index": j},
                    ))
            else:
                chunks.append(Document(
                    page_content=block_text,
                    metadata={"source": source, "page": page,
                              "doc_type": "text", "case_id": case_id},
                ))

        print(f"  → 사례별 청킹: {len(matches)}개 사례 인식 → {len(chunks)}개 text chunk 생성")
        return chunks

    def _resize_images(self) -> List[str]:
        """
        image_output_dir 내 이미지를 규격에 맞게 리사이즈해 filtered_img_dir에 저장합니다.

        - 지원 포맷: PNG, JPEG, WEBP, BMP
        - 긴 변 > MAX_IMG_PX 또는 비율 > MAX_IMG_RATIO 시 리사이즈
        - 저장 포맷: 항상 PNG (LANCZOS 리샘플링)
        """
        import shutil
        from PIL import Image

        os.makedirs(self.filtered_img_dir, exist_ok=True)
        allowed_formats = ("PNG", "JPEG", "WEBP", "BMP")
        valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

        image_files = [
            os.path.join(self.image_output_dir, f)
            for f in os.listdir(self.image_output_dir)
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

                    if ratio > MAX_IMG_RATIO:
                        if w > h:
                            new_w = min(w, MAX_IMG_PX); new_h = int(new_w / MAX_IMG_RATIO)
                        else:
                            new_h = min(h, MAX_IMG_PX); new_w = int(new_h / MAX_IMG_RATIO)
                    else:
                        if w >= h:
                            new_w = min(w, MAX_IMG_PX); new_h = int(h * (new_w / w))
                        else:
                            new_h = min(h, MAX_IMG_PX); new_w = int(w * (new_h / h))

                    resized = img.resize((new_w, new_h), Image.LANCZOS).convert("RGB")
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

    def _summarize_images_with_vision(
        self,
        image_infos: List[Tuple[str, Optional[tuple]]],
        page_table_map: dict = None,
    ) -> List[Document]:
        """
        Gemini 비전 모델(Base64)로 이미지를 텍스트 요약 Document로 변환합니다.

        - GOOGLE_API_KEY_VISION 환경변수 필요
        - page_table_map 제공 시 이미지 bbox로 동일 페이지 표를 매칭해 page_content에 합산
        """
        import base64
        import re
        from langchain_core.messages import HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI

        vision_api_key = os.getenv("GOOGLE_API_KEY_VISION")
        if not vision_api_key:
            raise EnvironmentError("GOOGLE_API_KEY_VISION 환경 변수를 설정해주세요.")

        vision_llm = ChatGoogleGenerativeAI(
            model=self.vision_model, google_api_key=vision_api_key, temperature=0,
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
            media_type = {".png": "image/png", ".jpg": "image/jpeg",
                          ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")
            try:
                with open(path, "rb") as f:
                    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

                message = HumanMessage(content=[
                    {"type": "image_url",
                     "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
                    {"type": "text", "text": system_text},
                ])
                summary = vision_llm.invoke([message]).content

                match = re.search(r"page_(\d+)_img_\d+", filename)
                page_number = int(match.group(1)) if match else None

                nearest_table_text = ""
                if page_table_map and page_number is not None and img_bbox is not None:
                    matched_table = self._find_nearest_table(
                        img_bbox, page_table_map.get(page_number, [])
                    )
                    if matched_table:
                        rows = matched_table.extract()
                        if rows:
                            nearest_table_text = self._table_to_markdown(rows, page_number, 0)
                            print(f"    [표 매칭] {filename} → page {page_number} 표 연결")
                    else:
                        print(f"    [표 없음] {filename} — 매칭되는 표를 찾지 못했습니다")

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

    @staticmethod
    def _table_to_markdown(table: List[List], page_num: int, table_idx: int) -> str:
        """pdfplumber 2D 리스트 → Markdown 표 문자열로 변환합니다."""
        if not table or not table[0]:
            return ""
        header = f"[TABLE {table_idx} - Page {page_num}]\n"
        rows = []
        for row_idx, row in enumerate(table):
            clean = [str(cell).strip().replace("\n", " ") if cell else "" for cell in row]
            rows.append("| " + " | ".join(clean) + " |")
            if row_idx == 0:
                rows.append("| " + " | ".join(["---"] * len(clean)) + " |")
        return header + "\n".join(rows)

    @staticmethod
    def _find_nearest_table(
        img_bbox: tuple,
        tables_on_page: list,
        margin: float = 5.0,
    ) -> object:
        """이미지 bbox를 포함하는 pdfplumber Table 객체를 반환합니다. 없으면 None."""
        if not img_bbox or not tables_on_page:
            return None
        img_x0, img_y0, img_x1, img_y1 = img_bbox
        for table in tables_on_page:
            t_x0, t_top, t_x1, t_bottom = table.bbox
            if (t_x0 - margin <= img_x0 and t_top  - margin <= img_y0 and
                    img_x1 <= t_x1 + margin and img_y1 <= t_bottom + margin):
                return table
        return None

    def _extract_table_docs(self, pdf_path: str) -> List[Document]:
        """pdfplumber로 각 페이지의 표를 추출해 독립 Document 목록을 반환합니다."""
        table_docs: List[Document] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
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
                            "page":        page_num,
                            "doc_type":    "table",
                            "table_index": t_idx,
                            "row_count":   len(table),
                            "col_count":   len(table[0]) if table else 0,
                        },
                    ))
        return table_docs

    def load_docs(self) -> Optional[List[Document]]:
        """
        PDF에서 텍스트·표·이미지 Document를 통합 추출해 반환합니다.

        처리 흐름
        ---------
        1. PyMuPDF로 페이지별 텍스트 Document + 이미지 파일 저장
        2. _split_by_case()로 사례 번호 기준 텍스트 청킹
        3. pdfplumber로 표 Document 추출
        4. 이미지 리사이즈 후 Gemini 비전 요약 Document 생성
        5. text + table + image 합산, 빈 content 제거 후 반환
        """
        if not os.path.exists(self.pdf_path):
            print(f"[오류] '{self.pdf_path}' 파일이 없습니다.")
            return None

        page_docs, _, all_image_infos = self._extract_text_and_images_from_pdf()

        text_chunks = self._split_by_case(page_docs)
        text_chunks = [d for d in text_chunks if d.page_content.strip()]

        table_docs = self._extract_table_docs(self.pdf_path)

        page_table_map: dict = {}
        with pdfplumber.open(self.pdf_path) as _pdf:
            for _i, _page in enumerate(_pdf.pages):
                _tables = _page.find_tables()
                if _tables:
                    page_table_map[_i + 1] = _tables
        print(f"  → page_table_map: {len(page_table_map)}개 페이지에서 표 위치 수집")

        filtered_image_paths = self._resize_images()
        bbox_lookup = {os.path.basename(p): bbox for p, bbox in all_image_infos}
        filtered_image_infos: List[Tuple[str, Optional[tuple]]] = [
            (p, bbox_lookup.get(os.path.basename(p))) for p in filtered_image_paths
        ]

        image_docs = self._summarize_images_with_vision(filtered_image_infos, page_table_map)

        combined_docs = [d for d in text_chunks + table_docs + image_docs
                         if d.page_content.strip()]
        print(f"  → 텍스트 {len(text_chunks)}개 + 표 {len(table_docs)}개 "
              f"+ 이미지 {len(image_docs)}개 = 총 {len(combined_docs)}개 Document 준비 완료")
        return combined_docs
