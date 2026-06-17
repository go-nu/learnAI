"""
pdf_loader_v4.py — PDF 로딩·청킹 Mixin (VL 모델 없음)

v4 개선사항
-----------
- _build_case_title_map_from_tables(): table 셀 기반 case_id → case_title 매핑 (1순위)
- _extract_case_title_from_block(): line 기반 사례명 추출 (fallback)
- _split_by_case(): case_title_map 인자 추가, title-summary chunk 추가 생성
- load_docs(): CASE_PATTERN 문서에 case_title_map 전달
"""

import os
from typing import Dict, List, Optional, Tuple

import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config_v4 import (
    CASE_PATTERN,
    LEGAL_ADDENDUM_PATTERN,
    LEGAL_ARTICLE_PATTERN,
    MAX_CASE_CHARS,
)


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

    def _extract_case_title_from_block(self, block_text: str, case_id: str) -> str:
        """block_text에서 사례명("사고"가 포함된 제목 줄)을 추출합니다."""
        lines = [line.strip() for line in block_text.splitlines() if line.strip()]

        # case_id 바로 다음 줄이 사례명인 경우
        for i, line in enumerate(lines):
            if line == case_id and i + 1 < len(lines):
                candidate = lines[i + 1].strip()
                if candidate and "사고" in candidate:
                    return candidate

        # PDF 추출 과정에서 case_id와 제목이 같은 줄에 붙는 경우 대비
        for line in lines[:8]:
            if case_id in line and "사고" in line:
                candidate = line.replace(case_id, "").strip()
                if candidate:
                    return candidate

        # 앞쪽 몇 줄 중 "사고"가 포함된 줄을 사례명 후보로 사용
        for line in lines[:8]:
            if "사고" in line and line != case_id:
                return line

        return ""

    def _split_by_case(
        self,
        text_documents: List[Document],
        page_to_images: Dict[int, List[str]] = None,
        case_title_map: Dict[str, str] = None,
    ) -> List[Document]:
        """
        페이지별 텍스트 Document를 사례 번호(차N-N / 회전-N) 기준으로 분할합니다.

        - CASE_PATTERN으로 줄 단독 사례 번호만 경계로 인식
        - 각 청크의 page 번호로 page_to_images를 조회해 image_refs 메타데이터에 추가
        - 사례 번호 이전 머리말은 case_id="머리말" 로 별도 처리
        - MAX_CASE_CHARS 초과 블록은 RecursiveCharacterTextSplitter로 추가 분할
        - 패턴 미발견 시 RecursiveCharacterTextSplitter(800자) 로 자동 폴백
        - case_title 추출 후 page_content 헤더 및 구분 metadata 필드 추가
        """
        import re

        _DEBUG_CASES = {"회전-10", "회전-11", "회전-15"}

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

        def build_extra_meta(case_title: str) -> dict:
            has_exit        = "진출" in case_title
            has_lane_change = "차로변경" in case_title
            if "후진입 직후 차로변경" in case_title:
                lane_change_actor = "후진입 차량"
                collision_stage   = "후진입 직후"
            elif "차로변경하여 진출" in case_title:
                lane_change_actor = "선진입 차량"
                collision_stage   = "진출 과정"
            elif "회전 중 차로변경" in case_title:
                lane_change_actor = "회전 중 차량"
                collision_stage   = "회전 중"
            else:
                lane_change_actor = ""
                collision_stage   = ""
            return {
                "has_exit":          has_exit,
                "has_lane_change":   has_lane_change,
                "lane_change_actor": lane_change_actor,
                "collision_stage":   collision_stage,
            }

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
            case_id     = match.group().strip()
            block_start = match.start()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            block_text  = full_text[block_start:block_end].strip()
            page        = get_page(block_start)
            image_refs  = get_image_refs(page)

            if not block_text:
                continue

            # 1순위: table 기반 매핑 / 2순위: line 기반 fallback
            case_title = (case_title_map or {}).get(case_id, "")
            if not case_title:
                case_title = self._extract_case_title_from_block(block_text, case_id)
            extra_meta  = build_extra_meta(case_title)

            if case_id in _DEBUG_CASES:
                print(f"  [청킹 확인] case_id={case_id} / case_title={case_title}")

            # 구조화 헤더 구성
            header = f"[사례번호] {case_id}\n"
            if case_title:
                header += f"[사례명] {case_title}\n"
            header += "\n"

            if len(block_text) > MAX_CASE_CHARS:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=MAX_CASE_CHARS, chunk_overlap=100,
                    separators=["\n\n", "\n", " "],
                )
                for j, sub in enumerate(splitter.split_text(block_text)):
                    sub_header = header + f"[분할번호] {j}\n\n"
                    chunks.append(Document(
                        page_content=sub_header + sub,
                        metadata={
                            "source":     source,
                            "page":       page,
                            "doc_type":   "text",
                            "case_id":    case_id,
                            "case_title": case_title,
                            "sub_index":  j,
                            "image_refs": image_refs,
                            **extra_meta,
                        },
                    ))
            else:
                chunks.append(Document(
                    page_content=header + block_text,
                    metadata={
                        "source":     source,
                        "page":       page,
                        "doc_type":   "text",
                        "case_id":    case_id,
                        "case_title": case_title,
                        "image_refs": image_refs,
                        **extra_meta,
                    },
                ))

            # title-summary chunk: 사례명 검색 정확도 강화 (본문 chunk의 대체가 아닌 추가)
            if case_title:
                chunks.append(Document(
                    page_content=f"[사례번호] {case_id}\n[사례명] {case_title}",
                    metadata={
                        "source":     source,
                        "page":       page,
                        "doc_type":   "summary",
                        "case_id":    case_id,
                        "case_title": case_title,
                        "image_refs": image_refs,
                        **extra_meta,
                    },
                ))

        n_summary = sum(1 for c in chunks if c.metadata.get("doc_type") == "summary")
        n_text    = len(chunks) - n_summary
        print(f"  → 사례별 청킹: {len(matches)}개 사례 인식 → 본문 {n_text}개 + 요약 {n_summary}개 chunk 생성")
        return chunks

    def _split_by_article(
        self,
        text: str,
        source: str,
        section: str = "본문",
        char_to_page: List[Tuple[int, int]] = None,
        text_offset: int = 0,
    ) -> List[Document]:
        """
        법률 조항 패턴(LEGAL_ARTICLE_PATTERN)으로 텍스트를 조항별로 분할합니다.

        - 조항 이전 머리말은 article_id="머리말"로 별도 청크
        - 패턴 미발견 시 전체를 article_id="전문" 단일 청크로 반환
        - 메타데이터: section, article_id, page, doc_type="text"
        - char_to_page: (full_text 내 시작 오프셋, 페이지 번호) 리스트 (페이지 복원용)
        - text_offset: full_text 내에서 text가 시작되는 절대 위치
        """
        import re

        # char_to_page 기반 페이지 번호 조회 헬퍼
        def get_page(offset_in_text: int) -> int:
            if not char_to_page:
                return 0
            abs_pos = offset_in_text + text_offset   # full_text 기준 절대 위치
            page = char_to_page[0][1]
            for start, p in char_to_page:
                if start <= abs_pos:
                    page = p
                else:
                    break
            return page

        pattern = re.compile(LEGAL_ARTICLE_PATTERN)
        matches = list(pattern.finditer(text))

        # 조항 패턴 미발견 시 전체를 단일 청크로 반환
        if not matches:
            print(f"  [법률 조항] 패턴 미발견 → 전문(全文) 단일 chunk 생성 (section={section})")
            return [Document(
                page_content=text.strip(),
                metadata={
                    "source":     source,
                    "section":    section,
                    "article_id": "전문",
                    "page":       get_page(0),
                    "doc_type":   "text",
                },
            )]

        chunks: List[Document] = []

        # 첫 번째 조항 앞 머리말(전문·목적 등)을 별도 청크로 생성
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chunks.append(Document(
                page_content=preamble,
                metadata={
                    "source":     source,
                    "section":    section,
                    "article_id": "머리말",
                    "page":       get_page(0),
                    "doc_type":   "text",
                },
            ))

        # 조항별 블록을 Document로 생성
        for i, match in enumerate(matches):
            article_id  = match.group()                                          # 조항 제목(예: 제1조(목적))
            block_start = match.start()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block_text  = text[block_start:block_end].strip()

            if not block_text:
                continue

            chunks.append(Document(
                page_content=block_text,
                metadata={
                    "source":     source,
                    "section":    section,
                    "article_id": article_id,
                    "page":       get_page(block_start),   # 조항 시작 위치 기준 페이지
                    "doc_type":   "text",
                },
            ))

        print(f"  → 조항별 청킹: {len(matches)}개 조항 인식 → {len(chunks)}개 chunk 생성 (section={section})")
        return chunks

    def _split_addendum(
        self,
        text: str,
        source: str,
        char_to_page: List[Tuple[int, int]] = None,
        text_offset: int = 0,
    ) -> List[Document]:
        """
        부칙 선언문 패턴(LEGAL_ADDENDUM_PATTERN)으로 텍스트를 부칙별로 분할합니다.

        - 부칙 내부 제1조·제2조는 분리하지 않고 부칙 단위 전체를 하나의 청크로 유지
        - 패턴 미발견 시 전체를 단일 청크로 반환
        - 메타데이터: section="부칙", article_id(부칙 선언문), page, doc_type="text"
        - char_to_page: (full_text 내 시작 오프셋, 페이지 번호) 리스트 (페이지 복원용)
        - text_offset: full_text 내에서 text가 시작되는 절대 위치
        """
        import re

        # char_to_page 기반 페이지 번호 조회 헬퍼
        def get_page(offset_in_text: int) -> int:
            if not char_to_page:
                return 0
            abs_pos = offset_in_text + text_offset
            page = char_to_page[0][1]
            for start, p in char_to_page:
                if start <= abs_pos:
                    page = p
                else:
                    break
            return page

        pattern = re.compile(LEGAL_ADDENDUM_PATTERN)
        matches = list(pattern.finditer(text))

        # 부칙 패턴 미발견 시 전체를 단일 청크로 반환
        if not matches:
            print("  [부칙] 패턴 미발견 → 부칙 단일 chunk 생성")
            return [Document(
                page_content=text.strip(),
                metadata={
                    "source":     source,
                    "section":    "부칙",
                    "article_id": "부칙",
                    "page":       get_page(0),
                    "doc_type":   "text",
                },
            )]

        chunks: List[Document] = []

        # 부칙 번호별 블록을 하나의 청크로 생성 (내부 조항 미분리)
        for i, match in enumerate(matches):
            article_id  = match.group()                                          # 부칙 선언문(예: 부칙 <2024.1.1>)
            block_start = match.start()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block_text  = text[block_start:block_end].strip()

            if not block_text:
                continue

            chunks.append(Document(
                page_content=block_text,
                metadata={
                    "source":     source,
                    "section":    "부칙",
                    "article_id": article_id,
                    "page":       get_page(block_start),   # 부칙 시작 위치 기준 페이지
                    "doc_type":   "text",
                },
            ))

        print(f"  → 부칙 청킹: {len(matches)}개 부칙 선언문 → {len(chunks)}개 chunk 생성")
        return chunks

    def _build_case_title_map_from_tables(self, pdf_path: str) -> Dict[str, str]:
        """
        pdfplumber로 PDF 표를 순회해 case_id → case_title 매핑을 생성합니다.

        - 각 행에서 CASE_PATTERN과 일치하는 셀을 case_id로 인식
        - 같은 행의 case_id 이후 첫 번째 유효 셀을 case_title로 사용
        - 이미 매핑이 존재하는 case_id는 덮어쓰지 않음 (첫 등장 우선)
        - re.fullmatch() 실패 시 re.search()로 보조 매칭
        """
        import re

        _CELL_CASE_RE  = re.compile(r'차\d+-\d+|회전-\d+')
        _MAX_TITLE_LEN = 100   # 본문 셀 오염 방지용 길이 상한

        title_map: Dict[str, str] = {}

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for table in (page.extract_tables() or []):
                    for row in table:
                        if not row:
                            continue
                        cells = [
                            str(c).replace("\n", " ").strip() if c is not None else ""
                            for c in row
                        ]
                        for i, cell in enumerate(cells):
                            if not cell:
                                continue
                            # fullmatch 우선, 실패 시 search로 보조 매칭
                            m = re.fullmatch(_CELL_CASE_RE, cell) or re.search(_CELL_CASE_RE, cell)
                            if not m:
                                continue
                            case_id = m.group().strip()
                            if case_id in title_map:
                                continue
                            # 같은 행에서 case_id 이후 첫 번째 유효 셀을 title로
                            for j in range(i + 1, len(cells)):
                                candidate = cells[j]
                                if candidate and len(candidate) <= _MAX_TITLE_LEN:
                                    title_map[case_id] = candidate
                                    break

        print(f"  → table 기반 case_title 매핑: {len(title_map)}개 생성")
        for k, v in list(title_map.items())[:3]:
            print(f"     {k} → {v}")

        return title_map

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
                            "source":      os.path.basename(pdf_path),
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
        source_dir 내의 모든 PDF를 순회하며 텍스트·표 Document를 추출해 반환합니다.
        각 PDF마다 문서 유형을 자동 감지해 청킹 전략을 독립적으로 선택합니다.

        처리 흐름 (PDF 1개당)
        ---------------------
        1. source_dir 에서 .pdf 파일 목록 수집
        2. PyMuPDF로 페이지별 텍스트 + 이미지 저장 → page_to_images 생성
        3. 앞 3페이지(sample_text) 및 전체(full_text) 합산
        4. 문서 유형 감지 후 청킹 분기:
           - LEGAL_ARTICLE_PATTERN 감지 → 조항별 청킹
             - LEGAL_ADDENDUM_PATTERN도 감지 → 본문/부칙 분리 후 각각 청킹
           - CASE_PATTERN 감지           → 사례별 청킹 (_split_by_case)
           - 미감지                       → RecursiveCharacterTextSplitter(800자) 폴백
        5. pdfplumber로 표 Document 추출 (image_refs 메타데이터 포함)
        6. 전체 PDF 결과 합산 후 반환
        """
        import glob
        import re

        # source_dir 내 모든 PDF 수집
        pdf_files = sorted(glob.glob(os.path.join(self.source_dir, "*.pdf")))
        if not pdf_files:
            print(f"[오류] '{self.source_dir}' 디렉토리에 PDF 파일이 없습니다.")
            return None

        print(f"  → {len(pdf_files)}개 PDF 감지: "
              f"{[os.path.basename(f) for f in pdf_files]}")

        all_text_chunks: List[Document] = []
        all_table_docs:  List[Document] = []

        for pdf_path in pdf_files:
            fname = os.path.basename(pdf_path)
            print(f"\n{'─' * 45}")
            print(f"  [처리중] {fname}")

            # 각 PDF 경로를 인스턴스에 임시 설정 (기존 헬퍼 메서드 재사용)
            self.pdf_path = pdf_path

            page_docs, page_to_images = self._extract_text_and_images_from_pdf()
            if not page_docs:
                print(f"  [건너뜀] {fname}: 텍스트 추출 결과 없음")
                continue

            # 전체 텍스트 합산 및 char_to_page 매핑 구성 (법률 문서 페이지 복원용)
            full_text    = ""
            char_to_page: List[Tuple[int, int]] = []
            for doc in page_docs:
                char_to_page.append((len(full_text), doc.metadata.get("page", 0)))
                full_text += doc.page_content + "\n\n"

            sample_text = "\n\n".join(d.page_content for d in page_docs[:3])
            source      = page_docs[0].metadata.get("source", fname)

            # 문서 유형 감지 및 청킹 전략 분기
            if re.search(CASE_PATTERN, full_text):
                # 과실비율 문서 감지 → 사례별 청킹 (전체 텍스트 기준으로 감지: 앞 페이지가 표지/목차인 경우 대비)
                print(f"  [{fname}] 과실비율 문서 감지 → 사례별 청킹")
                case_title_map = self._build_case_title_map_from_tables(pdf_path)
                text_chunks = self._split_by_case(page_docs, page_to_images, case_title_map=case_title_map)

            elif re.search(LEGAL_ARTICLE_PATTERN, sample_text):
                # 법률 문서 감지 → 조항별 청킹
                print(f"  [{fname}] 법률 문서 감지 → 조항별 청킹")

                if re.search(LEGAL_ADDENDUM_PATTERN, full_text):
                    # 부칙 선언문 발견 → 본문 / 부칙 분리 후 각각 청킹
                    addendum_match  = re.search(LEGAL_ADDENDUM_PATTERN, full_text)
                    body_text       = full_text[: addendum_match.start()]
                    addendum_text   = full_text[addendum_match.start():]
                    # text_offset: 부칙 텍스트는 full_text 내 addendum_match.start() 위치에서 시작
                    body_chunks     = self._split_by_article(
                        body_text, source, section="본문",
                        char_to_page=char_to_page, text_offset=0,
                    )
                    addendum_chunks = self._split_addendum(
                        addendum_text, source,
                        char_to_page=char_to_page, text_offset=addendum_match.start(),
                    )
                    text_chunks     = body_chunks + addendum_chunks
                else:
                    # 부칙 없음 → 전체를 본문으로 처리
                    text_chunks = self._split_by_article(
                        full_text, source, section="본문",
                        char_to_page=char_to_page, text_offset=0,
                    )

            else:
                # 패턴 미감지 → 일반 폴백 청킹
                print(f"  [{fname}] 일반 문서 감지 → RecursiveCharacterTextSplitter(800자) 폴백")
                splitter    = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
                text_chunks = splitter.split_documents(page_docs)

            text_chunks = [d for d in text_chunks if d.page_content.strip()]
            table_docs  = self._extract_table_docs(pdf_path, page_to_images)
            table_docs  = [d for d in table_docs if d.page_content.strip()]

            print(f"  [{fname}] 텍스트 {len(text_chunks)}개 + 표 {len(table_docs)}개")
            all_text_chunks.extend(text_chunks)
            all_table_docs.extend(table_docs)

        # 전체 합산 결과 출력
        combined_docs = all_text_chunks + all_table_docs
        print(f"\n{'─' * 45}")
        print(f"  → 전체 {len(pdf_files)}개 PDF: "
              f"텍스트 {len(all_text_chunks)}개 + 표 {len(all_table_docs)}개 "
              f"= 총 {len(combined_docs)}개 Document 준비 완료")
        return combined_docs if combined_docs else None
