from typing import List, Tuple
from PyPDF2 import PdfReader, PdfWriter
import os

from task_context import TaskContext, TaskCancelledError


def split_pdf_by_ranges(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
    ranges: List[Tuple[int, int]],
):
    """
    PDF 拆分任务（按页码范围）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF
    :param ranges: [(start_page, end_page)]，页码从 1 开始（包含）
    """

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        writer = PdfWriter()

        # 计算总工作量（用于进度）
        total_units = sum(end - start + 1 for start, end in ranges)
        completed_units = 0

        if total_units <= 0:
            raise ValueError("拆分范围为空")

        ctx.report_progress(0, "开始拆分 PDF")

        for start, end in ranges:
            if start < 1 or end > total_pages or start > end:
                raise ValueError(f"非法页码范围: {start}-{end}")

            for page_index in range(start - 1, end):
                ctx.check_cancelled()

                writer.add_page(reader.pages[page_index])

                completed_units += 1
                progress = completed_units / total_units * 100

                ctx.report_progress(
                    progress,
                    f"处理中：第 {page_index + 1} 页 / 共 {total_pages}  页"
                )

        ctx.check_cancelled()

        with open(output_path, "wb") as f:
            writer.write(f)

        ctx.report_progress(100, "拆分完成")
        ctx.report_done("PDF 拆分完成", output_path)

    except TaskCancelledError:
        ctx.report_done("操作已取消", None)

    except Exception as e:
        ctx.report_error(str(e))


def split_pdf_by_single_pages(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
):
    """
    PDF 拆分任务（拆成单页）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF 基础路径
    """

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        if total_pages <= 0:
            raise ValueError("PDF 无页面")

        base_name = os.path.splitext(output_path)[0]
        ctx.report_progress(0, "开始拆分为单页")

        for page_index in range(total_pages):
            ctx.check_cancelled()

            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])

            file_path = f"{base_name}_page_{page_index + 1}.pdf"
            with open(file_path, "wb") as f:
                writer.write(f)

            progress = (page_index + 1) / total_pages * 100
            ctx.report_progress(
                progress,
                f"处理中：第 {page_index + 1} 页 / 共 {total_pages} 页"
            )

        ctx.report_progress(100, "拆分完成")
        ctx.report_done("已拆分为单页 PDF 文件", f"{base_name}_page_1.pdf")

    except TaskCancelledError:
        ctx.report_done("操作已取消", None)

    except Exception as e:
        ctx.report_error(str(e))