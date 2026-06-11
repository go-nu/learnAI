import fitz
import pdfplumber

pdf_fitz = fitz.open("source/test.pdf")
pdf_plumber = pdfplumber.open("source/test.pdf")

page_fitz    = pdf_fitz[0]      # 1페이지 (0-based)
page_plumber = pdf_plumber.pages[0]

# ── PyMuPDF: 이미지 bbox 출력 ──────────────────────
print("=== 이미지 bbox (PyMuPDF 좌표계, 좌상단 원점) ===")
for i, img in enumerate(page_fitz.get_images(full=True)):
    xref = img[0]
    rects = page_fitz.get_image_rects(xref)
    for r in rects:
        print(f"  이미지 {i+1}: x0={r.x0:.1f}, y0={r.y0:.1f}, x1={r.x1:.1f}, y1={r.y1:.1f}")

# ── pdfplumber: 표 bbox 출력 ───────────────────────
print("\n=== 표 bbox (pdfplumber 좌표계, 좌상단 원점) ===")
for i, table in enumerate(page_plumber.find_tables()):
    b = table.bbox   # (x0, top, x1, bottom)
    print(f"  표 {i+1}: x0={b[0]:.1f}, top={b[1]:.1f}, x1={b[2]:.1f}, bottom={b[3]:.1f}")