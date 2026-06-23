import os
import re
import shutil
import subprocess
import traceback

from task_context import TaskCancelledError, TaskContext
from services.pdf_service import sanitize_filename


try:
    from ebooklib import epub
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, A5, letter, legal
    import html2text

    EPUB_LIBS_AVAILABLE = True
    EPUB_LIBS_IMPORT_ERROR = ""
except ImportError as exc:
    EPUB_LIBS_AVAILABLE = False
    EPUB_LIBS_IMPORT_ERROR = str(exc)


def find_ebook_convert() -> str:
    """查找 Calibre 的 ebook-convert 可执行文件路径。"""
    path = shutil.which("ebook-convert")
    if path:
        return path

    candidates = [
        os.path.join("C:\\Program Files\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files (x86)\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files\\Calibre2", "ebook-convert.exe"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return ""


def _detect_declared_encoding(raw_content: bytes) -> str | None:
    head = raw_content[:512].decode("ascii", errors="ignore")
    patterns = [
        r'encoding=["\']([A-Za-z0-9._-]+)["\']',
        r'charset=["\']?([A-Za-z0-9._-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, head, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _decode_epub_content(raw_content: bytes) -> str:
    candidates: list[str] = []
    declared_encoding = _detect_declared_encoding(raw_content)
    if declared_encoding:
        candidates.append(declared_encoding)

    if raw_content.startswith((b"\xff\xfe", b"\xfe\xff")):
        candidates.append("utf-16")

    candidates.extend(
        [
            "utf-8",
            "utf-8-sig",
            "utf-16",
            "gb18030",
            "gbk",
            "gb2312",
            "cp1252",
            "latin-1",
        ]
    )

    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw_content.decode(encoding)
        except (UnicodeDecodeError, UnicodeError, LookupError):
            continue

    return raw_content.decode("utf-8", errors="ignore")


def _terminate_process(proc) -> None:
    if proc is None or proc.poll() is not None:
        return

    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass


def epub_to_pdf_python(
    ctx: TaskContext,
    epub_path: str,
    pdf_path: str,
    paper_size: str = "a4",
):
    """使用 Python 库将 EPUB 转换为 PDF（不依赖 Calibre）。"""
    if not EPUB_LIBS_AVAILABLE:
        raise RuntimeError("缺少必要的 Python 库\n请安装：pip install ebooklib reportlab html2text")

    paper_sizes = {
        "a4": A4,
        "a5": A5,
        "letter": letter,
        "legal": legal,
    }
    page_size = paper_sizes.get(paper_size.lower(), A4)

    ctx.report_progress(20, "正在读取 EPUB 文件...")
    book = epub.read_epub(epub_path)

    pdf_canvas = canvas.Canvas(pdf_path, pagesize=page_size)
    _, height = page_size

    try:
        pdf_canvas.setFont("Helvetica", 12)
    except Exception:
        try:
            pdf_canvas.setFont("Arial", 12)
        except Exception:
            pdf_canvas.setFont("Helvetica", 12)

    html_converter = html2text.HTML2Text()
    html_converter.ignore_links = True
    html_converter.ignore_images = True

    y_position = height - 50
    line_height = 14
    margin = 50

    total_items = sum(1 for item in book.get_items() if item.get_type() == epub.ITEM_DOCUMENT)
    processed_items = 0

    for item in book.get_items():
        ctx.check_cancelled()

        if item.get_type() != epub.ITEM_DOCUMENT:
            continue

        processed_items += 1
        item_progress = (processed_items / total_items) * 60 if total_items else 60
        ctx.report_progress(20 + item_progress, f"正在处理章节 {processed_items}/{total_items}")

        raw_content = item.get_content()
        content = _decode_epub_content(raw_content)

        text = html_converter.handle(content)
        text = re.sub(r"\n\s*\n", "\n\n", text)

        for line in text.split("\n"):
            ctx.check_cancelled()

            line = line.strip()
            if not line:
                y_position -= line_height
                continue

            if y_position < margin:
                pdf_canvas.showPage()
                y_position = height - 50

            safe_line = line.replace("\x00", "").replace("\r", "").strip()
            if not safe_line:
                y_position -= line_height
                continue

            if len(safe_line) > 80:
                words = safe_line.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) > 80:
                        if current_line:
                            try:
                                pdf_canvas.drawString(margin, y_position, current_line)
                            except Exception as draw_err:
                                print(f"[EPUB 转换警告] 绘制文本失败，已跳过：{draw_err}")
                            y_position -= line_height
                            if y_position < margin:
                                pdf_canvas.showPage()
                                y_position = height - 50
                        current_line = word
                    else:
                        current_line += (" " + word) if current_line else word
                if current_line:
                    try:
                        pdf_canvas.drawString(margin, y_position, current_line)
                    except Exception as draw_err:
                        print(f"[EPUB 转换警告] 绘制文本失败，已跳过：{draw_err}")
                    y_position -= line_height
            else:
                try:
                    pdf_canvas.drawString(margin, y_position, safe_line)
                except Exception as draw_err:
                    print(f"[EPUB 转换警告] 绘制文本失败，已跳过：{draw_err}")
                y_position -= line_height

    ctx.report_progress(90, "正在保存 PDF 文件...")
    pdf_canvas.save()
    ctx.report_done(f"已完成 EPUB 转 PDF：{pdf_path}", [pdf_path])


def do_epub_convert_with_progress(
    ctx: TaskContext,
    epub_path: str,
    pdf_path: str,
    paper_size: str = "a4",
):
    """将 EPUB 转为 PDF，优先使用 Python 库，失败则尝试 Calibre。"""
    proc = None
    output_preexisting = os.path.exists(pdf_path)

    def cleanup_partial_output():
        if output_preexisting:
            return
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception:
            pass

    try:
        python_error = None

        try:
            ctx.report_progress(10, f"尝试使用 Python 库转换... (库可用: {EPUB_LIBS_AVAILABLE})")
            epub_to_pdf_python(ctx, epub_path, pdf_path, paper_size)
            return "success"
        except TaskCancelledError:
            cleanup_partial_output()
            ctx.report_done("操作已取消", None)
            return "cancelled"
        except Exception as exc:
            python_error = str(exc)
            ctx.report_progress(20, f"Python 库转换失败：{python_error[:50]}...")

        ctx.check_cancelled()
        exe = find_ebook_convert()
        if not exe:
            error_msg = "转换失败：\n"
            if python_error:
                error_msg += f"1. Python 库错误：{python_error}\n"
            elif EPUB_LIBS_IMPORT_ERROR:
                error_msg += f"1. Python 依赖不可用：{EPUB_LIBS_IMPORT_ERROR}\n"
            error_msg += "2. 未找到 Calibre ebook-convert\n\n"
            error_msg += "解决方案：\n"
            error_msg += "- 安装 Python 库：pip install ebooklib reportlab html2text\n"
            error_msg += "- 或安装 Calibre：https://calibre-ebook.com/download"
            ctx.report_error(error_msg)
            return "error"

        os.makedirs(os.path.dirname(pdf_path) or os.getcwd(), exist_ok=True)
        args = [exe, epub_path, pdf_path, "--paper-size", paper_size]
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as exc:
            ctx.report_error(f"启动 Calibre 转换失败：{str(exc)}")
            return "error"

        last_pct = -1
        while True:
            ctx.check_cancelled()
            if proc.poll() is not None:
                break

            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                continue

            match = re.search(r"(\d{1,3})%", line)
            if match:
                try:
                    pct = int(match.group(1))
                    if 0 <= pct <= 100 and pct != last_pct:
                        last_pct = pct
                        ctx.report_progress(pct, f"转换进度 {pct}%")
                except Exception:
                    pass
            elif last_pct >= 0:
                ctx.report_progress(last_pct, line.strip()[:80])

        code = proc.poll()
        if code == 0:
            ctx.report_done(f"已完成 EPUB 转 PDF：{pdf_path}", [pdf_path])
            return "success"
        else:
            cleanup_partial_output()
            ctx.report_error("Calibre 转换失败，请检查 EPUB 文件与输出路径是否有效。")
            return "error"

    except TaskCancelledError:
        _terminate_process(proc)
        cleanup_partial_output()
        ctx.report_done("操作已取消", None)
        return "cancelled"
    except Exception as final_error:
        _terminate_process(proc)
        cleanup_partial_output()
        error_details = traceback.format_exc()
        ctx.report_error(
            f"转换过程中发生意外错误：\n{final_error}\n\n详细信息：\n{error_details}\n\n请检查文件或尝试其他转换方式。"
        )
        return "error"


def batch_epub_to_pdf(
    ctx: TaskContext,
    epub_files: list[str],
    output_dir: str,
    paper_size: str = "a4",
    filename_template: str = "{name}.pdf",
):
    """批量将 EPUB 文件转换为 PDF。"""
    total_files = len(epub_files)
    if total_files == 0:
        ctx.report_done("没有 EPUB 文件需要转换", None)
        return

    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    failed_count = 0
    failed_files: list[tuple[str, str]] = []
    success_files: list[str] = []
    cancelled_early = False

    try:
        for index, epub_path in enumerate(epub_files):
            ctx.check_cancelled()
            file_name = os.path.basename(epub_path)
            file_error: str | None = None

            def make_sub_progress_callback(file_index: int, current_file_name: str):
                def _report(sub_progress: float, msg: str):
                    bounded_progress = max(0.0, min(100.0, sub_progress))
                    overall = ((file_index + bounded_progress / 100.0) / total_files) * 100.0
                    ctx.report_progress(overall, f"[{file_index + 1}/{total_files}] {current_file_name}：{msg}")

                return _report

            def capture_sub_error(err: str):
                nonlocal file_error
                file_error = str(err)

            sub_ctx = TaskContext(
                is_cancelled=ctx.is_cancelled,
                report_progress=make_sub_progress_callback(index, file_name),
                report_done=lambda *_: None,
                report_error=capture_sub_error,
            )

            try:
                base_name = os.path.splitext(os.path.basename(epub_path))[0]
                try:
                    pdf_filename = filename_template.format(name=base_name)
                except Exception:
                    pdf_filename = f"{base_name}.pdf"

                pdf_filename = sanitize_filename(pdf_filename)
                pdf_path = os.path.join(output_dir, pdf_filename)

                result = do_epub_convert_with_progress(sub_ctx, epub_path, pdf_path, paper_size)
                if result == "success":
                    success_count += 1
                    success_files.append(pdf_path)
                elif result == "cancelled":
                    cancelled_early = True
                    failed_count += 1
                    failed_files.append((epub_path, "用户取消"))
                    ctx.report_progress(100, "转换已取消")
                    break
                else:
                    failed_count += 1
                    failed_files.append((epub_path, file_error or "转换失败"))
                    sub_ctx.report_progress(100, f"转换失败：{file_error or '未知错误'}")
            except Exception as exc:
                failed_count += 1
                failed_files.append((epub_path, str(exc)))
                sub_ctx.report_progress(100, f"转换失败：{str(exc)}")
                continue

        if cancelled_early:
            result_message = f"转换已取消！\n成功：{success_count} 个文件\n失败：{failed_count} 个文件（含取消）\n\n"
        else:
            result_message = f"批量转换完成！\n成功：{success_count} 个文件\n失败：{failed_count} 个文件\n\n"

        if success_files:
            result_message += "成功转换的文件：\n"
            for index, file in enumerate(success_files[:5], 1):
                result_message += f"{index}. {os.path.basename(file)}\n"
            if len(success_files) > 5:
                result_message += f"... 等 {len(success_files) - 5} 个文件\n"

        if failed_files:
            result_message += "\n转换失败的文件：\n"
            for index, (file, error) in enumerate(failed_files[:5], 1):
                result_message += f"{index}. {os.path.basename(file)}\n   错误：{error[:100]}...\n"
            if len(failed_files) > 5:
                result_message += f"... 等 {len(failed_files) - 5} 个文件\n"

        ctx.report_progress(100, "批量转换完成")
        ctx.report_done(result_message, success_files[:1])

    except Exception as final_error:
        error_details = traceback.format_exc()
        ctx.report_error(
            f"批量转换过程中发生意外错误：\n{final_error}\n\n详细信息：\n{error_details}\n\n请检查文件或尝试其他转换方式。"
        )
