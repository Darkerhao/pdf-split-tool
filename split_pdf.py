import sys
from PyPDF2 import PdfReader, PdfWriter

def parse_ranges(ranges):
    """解析命令行中的页码范围，例如 ['1-3','7-9']"""
    result = []
    for r in ranges:
        if "-" in r:
            start, end = map(int, r.split("-"))
            result.append((start, end))
        else:
            page = int(r)
            result.append((page, page))
    return result

def split_pdf(input_file, output_file=None, page_ranges=None, split_each_page=False):
    reader = PdfReader(input_file)

    if split_each_page:
        # 每页拆成单独 PDF
        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            with open(f"page_{i}.pdf", "wb") as f:
                writer.write(f)
        print("✅ 已拆分为单页 PDF 文件。")
    else:
        writer = PdfWriter()
        for start, end in page_ranges:
            for page_num in range(start - 1, end):
                if page_num < len(reader.pages):
                    writer.add_page(reader.pages[page_num])
        with open(output_file, "wb") as f:
            writer.write(f)
        print(f"✅ 已导出 {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python split_pdf.py input.pdf output.pdf 5-10 12-15 ...")
        print("或:   python split_pdf.py input.pdf --each")
        sys.exit(1)

    input_file = sys.argv[1]

    if sys.argv[2] == "--each":
        split_pdf(input_file, split_each_page=True)
    else:
        output_file = sys.argv[2]
        ranges = parse_ranges(sys.argv[3:])
        split_pdf(input_file, output_file, page_ranges=ranges)
