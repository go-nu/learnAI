"""
pdf_loader_v2.py — PDF 로딩·청킹 Mixin (VL 모델 없음)

v1과의 차이
-----------
- _summarize_images_with_vision() 제거 → 이미지를 텍스트로 변환하지 않음
- _resize_images() 제거 → VL 전처리용 리사이즈 불필요
- _find_nearest_table() 제거 → 이미지-표 VL 매칭 불필요
- _extract_text_and_images_from_pdf() : page_to_images 딕셔너리 반환으로 변경
- _split_by_case() : page_to_images를 받아 image_refs 메타데이터 자동 추가
- _extract_table_docs() : page_to_images를 받아 image_refs 메타데이터 자동 추가
- load_docs() : 텍스트·표만 반환 (이미지 Document 생성 없음)
"""

import os
from typing import Dict, List, Optional, Tuple

import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config_v2 import CASE_PATTERN, MAX_CASE_CHARS


class PdfLoaderMixin:
    """PDF 로딩·청킹 관련 메서드 Mixin"""

    def _extract_text_and_images_from_pdf(
        self,
    ) -> Tuple[List[Document], Dict[int, List[str]]]:
        """
        PyMuPDF(fitz)로 PDF에서 페이지별 텍스트를 추출하고 이미지 파일을 저장합니다.

        이미지는 VL 해석 없이 파일로만 저장하며, 페이지 번호 기반 매핑 딕셔너리로 반환합니다.

        반환값
        ------
        (page_documents, page_to_images)
        - page_documents : 페이지별 텍스트 Document 리스트 (doc_type="text")
        - page_to_images : {page_number(1-based): [이미지파일명, ...]} 딕셔너리
        """
        import fitz

        os.makedirs(self.image_output_dir, exist_ok=True)
        documents: List[Document] = []
        page_to_images: Dict[int, List[str]] = {}

        print(f"  PyMuPDF로 텍스트·이미지 추출 시작: '{self.pdf_path}'")
        doc = fitz.open(self.pdf_path)
        total_images = 0

        for i, page in enumerate(doc):
            page_number = i + 1
            page_text = page.get_text("text").strip()
            page_image_filenames: List[str] = []

            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_ext = base_image["ext"]
                image_filename = f"page_{page_number}_img_{img_index + 1}.{image_ext}"
                image_path = os.path.join(self.image_output_dir, image_filename)
                with open(image_path, "wb") as f:
                    f.write(base_image["image"])
                page_image_filenames.append(image_filename)

            if page_image_filenames:
                page_to_images[page_number] = page_image_filenames
            total_images += len(page_image_filenames)

            documents.append(Document(
                page_content=page_text,
                metadata={
                    "source":     os.path.basename(self.pdf_path),
                    "page":       page_number,
                    "doc_type":   "text",
                    "image_refs": ", ".join(page_image_filenames),
                },
            ))

        print(f"  → PyMuPDF: {len(documents)}페이지 텍스트 추출, "
              f"이미지 {total_images}장 저장 (VL 해석 없음, 출처 매핑용)")
        return documents, page_to_images

    def _split_by_case(
        self,
        text_documents: List[Document],
        page_to_images: Dict[int, List[str]] = None,
    ) -> List[Document]:
        """
        페이지별 텍스트 Document를 사례 번호(차N-N) 기준으로 분할합니다.

        - CASE_PATTERN으로 줄 시작 사례 번호만 경계로 인식
        - 각 청크의 page 번호로 page_to_images를 조회해 image_refs 메타데이터에 추가
        - 사례 번호 이전 머리말은 case_id="머리말" 로 별도 처리
        - MAX_CASE_CHARS 초과 블록은 RecursiveCharacterTextSplitter로 추가 분할
        - 패턴 미발견 시 RecursiveCharacterTextSplitter(800자) 로 자동 폴백
        """
        import re

        if not text_documents:
            return []

        page_to_images = page_to_images or {}

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

        def get_image_refs(page: int) -> str:
            return ", ".join(page_to_images.get(page, []))

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
            page = get_page(0)
            chunks.append(Document(
                page_content=preamble,
                metadata={
                    "source":     source,
                    "page":       page,
                    "doc_type":   "text",
                    "case_id":    "머리말",
                    "image_refs": get_image_refs(page),
                },
            ))

        for i, match in enumerate(matches):
            case_id     = match.group()
            block_start = match.start()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            block_text  = full_text[block_start:block_end].strip()
            page        = get_page(block_start)
            image_refs  = get_image_refs(page)

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
                        metadata={
                            "source":     source,
                            "page":       page,
                            "doc_type":   "text",
                            "case_id":    case_id,
                            "sub_index":  j,
                            "image_refs": image_refs,
                        },
                    ))
            else:
                chunks.append(Document(
                    page_content=block_text,
                    metadata={
                        "source":     source,
                        "page":       page,
                        "doc_type":   "text",
                        "case_id":    case_id,
                        "image_refs": image_refs,
                    },
                ))

        print(f"  → 사례별 청킹: {len(matches)}개 사례 인식 → {len(chunks)}개 text chunk 생성")
        return chunks

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

    def _extract_table_docs(
        self,
        pdf_path: str,
        page_to_images: Dict[int, List[str]] = None,
    ) -> List[Document]:
        """
        pdfplumber로 각 페이지의 표를 추출해 독립 Document 목록을 반환합니다.
        page_to_images를 참조해 각 표 Document에 image_refs 메타데이터를 추가합니다.
        """
        page_to_images = page_to_images or {}
        table_docs: List[Document] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                page_1based = page_num + 1
                image_refs = ", ".join(page_to_images.get(page_1based, []))

                for t_idx, table in enumerate(tables, start=1):
                    if not table:
                        continue
                    md = self._table_to_markdown(table, page_1based, t_idx)
                    if not md.strip():
                        continue
                    table_docs.append(Document(
                        page_content=md,
                        metadata={
                            "source":      pdf_path,
                            "page":        page_num,   # 0-based (기존 vectorstore 필터 호환 유지)
                            "doc_type":    "table",
                            "table_index": t_idx,
                            "row_count":   len(table),
                            "col_count":   len(table[0]) if table else 0,
                            "image_refs":  image_refs,
                        },
                    ))
        return table_docs

    def load_docs(self) -> Optional[List[Document]]:
        """
        PDF에서 텍스트·표 Document를 추출해 반환합니다.
        이미지는 파일로 저장하되 VL 모델 요약 없이 image_refs 메타데이터로만 매핑합니다.

        처리 흐름
        ---------
        1. PyMuPDF로 페이지별 텍스트 Document + 이미지 파일 저장 → page_to_images 생성
        2. _split_by_case()로 사례 번호 기준 텍스트 청킹 (image_refs 메타데이터 포함)
        3. pdfplumber로 표 Document 추출 (image_refs 메타데이터 포함)
        4. text + table 합산, 빈 content 제거 후 반환
           (이미지 Document는 생성하지 않음 — VL 해석 없음)
        """
        if not os.path.exists(self.pdf_path):
            print(f"[오류] '{self.pdf_path}' 파일이 없습니다.")
            return None

        page_docs, page_to_images = self._extract_text_and_images_from_pdf()

        text_chunks = self._split_by_case(page_docs, page_to_images)
        text_chunks = [d for d in text_chunks if d.page_content.strip()]

        table_docs = self._extract_table_docs(self.pdf_path, page_to_images)

        combined_docs = [d for d in text_chunks + table_docs if d.page_content.strip()]
        print(f"  → 텍스트 {len(text_chunks)}개 + 표 {len(table_docs)}개 "
              f"= 총 {len(combined_docs)}개 Document 준비 완료 (이미지 Document 없음)")
        return combined_docs
