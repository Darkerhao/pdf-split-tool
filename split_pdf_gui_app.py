import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PyPDF2 import PdfReader, PdfWriter
import os
import platform
import threading
import queue
import subprocess
import sys
import re
import traceback

from task_context import TaskContext, TaskCancelledError
from pdf_split_task import split_pdf_by_ranges
from ui.preview import open_pdf_previewer as show_pdf_previewer
from ui.merge_tab import build_merge_tab
from ui.epub_panel import build_epub_panels
from ui.split_tab import build_split_tab
from ui.auxiliary_ui import (
    EPUBPanelTexts,
    PreviewTabTexts,
    SettingsTabTexts,
    ToolbarTexts,
    apply_epub_panel_texts,
    apply_preview_tab_texts,
    apply_settings_tab_texts,
    apply_toolbar_texts,
    build_preview_tab,
    build_settings_tab,
    build_toolbar,
)
from ui.app_state import (
    add_recent_file_ui,
    clear_ranges_ui,
    helper_equal_k_parts_ui,
    helper_every_n_pages_ui,
    open_recent_ui,
    set_input_file_ui,
    set_language_ui,
    update_recent_menu_ui,
)
from ui.app_runtime import (
    ThemeConfig,
    apply_theme,
    enqueue_done,
    enqueue_error,
    enqueue_progress,
    load_ui_settings,
    poll_progress_queue,
    save_ui_settings,
    start_running_ui as start_runtime_ui,
    stop_running_ui as stop_runtime_ui,
)
from services.epub_service import (
    EPUB_LIBS_AVAILABLE,
    batch_epub_to_pdf,
    do_epub_convert_with_progress,
    epub_to_pdf_python,
)
from services.pdf_service import (
    build_split_preview,
    parse_chapter_ranges,
    parse_ranges,
    render_template,
    sanitize_filename,
)
from services.settings_service import (
    AppSettings,
    load_app_settings,
    save_app_settings,
)

# 可选：拖拽支持（如果已安装 tkinterdnd2）
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
    DND_AVAILABLE = True
    print("tkinterdnd2 导入成功")
except Exception as e:
    DND_AVAILABLE = False
    print(f"tkinterdnd2 导入失败: {e}")

# 多语言词典
LANG = "zh"
STRINGS = {
    "zh": {
        "title": "PDF 工具箱：拆分 / 合并 / 预览",
        "files": "文件",
        "input_pdf": "输入 PDF 文件",
        "output_pdf": "输出 PDF 文件",
        "browse": "浏览...",
        "pages_total": "总页数：",
        "split": "拆分",
        "range": "页码范围",
        "range_placeholder": "例如：1-3,5,7-9（支持中文逗号）",
        "preview": "预览拆分结果",
        "split_by_range": "按范围拆分",
        "split_each": "拆成单页",
        "merge": "合并",
        "merge_pdf": "合并 PDF",
        "open_output": "打开输出目录",
        "helpers": "范围助手:",
        "every_n": "每N页拆分",
        "equal_k": "均分为K份",
        "clear": "清空范围",
        "theme": "主题:",
        "light": "浅色",
        "dark": "深色",
        "language": "语言:",
        "zh": "中文",
        "en": "EN",
        "template": "命名模板",
        "template_placeholder": "{name}_{start}-{end}.pdf",
        "recent": "最近",
        "epub_frame": "EPUB 转 PDF",
        "epub_input_label": "输入 EPUB 文件",
        "epub_output_label": "输出 PDF 文件",
        "epub_paper_label": "纸张大小",
        "epub_convert": "开始转换",
        "epub_batch_frame": "批量 EPUB 转 PDF",
        "epub_batch_hint": "批量添加 .epub 文件后，将统一输出到所选目录；文件名模板支持 {name}.pdf。",
        "epub_batch_add": "添加 EPUB",
        "epub_batch_remove": "移除选中",
        "epub_batch_clear": "清空列表",
        "epub_batch_paper_label": "批量纸张大小",
        "epub_batch_output_label": "批量输出目录",
        "epub_batch_template_label": "输出文件名模板",
        "epub_batch_convert": "开始批量转换",
        "epub_browse": "浏览...",
    },
    "en": {
        "title": "PDF Toolbox: Split / Merge / Preview",
        "files": "Files",
        "input_pdf": "Input PDF",
        "output_pdf": "Output PDF",
        "browse": "Browse...",
        "pages_total": "Pages:",
        "split": "Split",
        "range": "Page ranges",
        "range_placeholder": "e.g. 1-3,5,7-9",
        "preview": "Preview",
        "split_by_range": "Split by ranges",
        "split_each": "Split to pages",
        "merge": "Merge",
        "merge_pdf": "Merge PDFs",
        "open_output": "Open output dir",
        "helpers": "Helpers:",
        "every_n": "Every N pages",
        "equal_k": "Split K parts",
        "clear": "Clear",
        "theme": "Theme:",
        "light": "Light",
        "dark": "Dark",
        "language": "Lang:",
        "zh": "ZH",
        "en": "EN",
        "template": "Name template",
        "template_placeholder": "{name}_{start}-{end}.pdf",
        "recent": "Recent",
        "epub_frame": "EPUB to PDF",
        "epub_input_label": "Input EPUB",
        "epub_output_label": "Output PDF",
        "epub_paper_label": "Paper size",
        "epub_convert": "Convert",
        "epub_batch_frame": "Batch EPUB to PDF",
        "epub_batch_hint": "Add .epub files below; output to selected directory. Filename template supports {name}.pdf.",
        "epub_batch_add": "Add EPUB",
        "epub_batch_remove": "Remove selected",
        "epub_batch_clear": "Clear list",
        "epub_batch_paper_label": "Batch paper size",
        "epub_batch_output_label": "Output directory",
        "epub_batch_template_label": "Filename template",
        "epub_batch_convert": "Batch Convert",
        "epub_browse": "Browse...",
    },
}

def T(key: str) -> str:
    return STRINGS.get(LANG, STRINGS["zh"]).get(key, key)

def split_pdf(input_file, output_file, page_ranges=None, split_each_page=False):
    reader = PdfReader(input_file)

    if split_each_page:
        base_name = os.path.splitext(output_file)[0]
        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            file_path = f"{base_name}_page_{i}.pdf"
            with open(file_path, "wb") as f:
                writer.write(f)
        messagebox.showinfo("完成", f"已拆分为单页 PDF 文件，保存在：\n{os.path.dirname(output_file)}")
    else:
        if not page_ranges:
            messagebox.showerror("错误", "请输入有效的页码范围")
            return

        total_pages = len(reader.pages)
        # 仅一段范围时，保持与原行为一致，写入到 output_file
        if len(page_ranges) == 1:
            start, end = page_ranges[0]
            start = max(1, start)
            end = min(total_pages, end)
            if start > end:
                messagebox.showerror("错误", "页码范围无效")
                return
            writer = PdfWriter()
            for page_num in range(start - 1, end):
                writer.add_page(reader.pages[page_num])
            with open(output_file, "wb") as f:
                writer.write(f)
            messagebox.showinfo("完成", f"已导出文件：{output_file}")
            return

        # 多段范围时，为每段生成一个独立文件，文件名附加范围后缀
        base_dir = os.path.dirname(output_file) or os.getcwd()
        base_name = os.path.splitext(os.path.basename(output_file))[0]
        exported = []
        for start, end in page_ranges:
            start = max(1, start)
            end = min(total_pages, end)
            if start > end:
                continue
            writer = PdfWriter()
            for page_num in range(start - 1, end):
                writer.add_page(reader.pages[page_num])
            out_path = os.path.join(base_dir, f"{base_name}_{start}-{end}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            exported.append(out_path)

        if not exported:
            messagebox.showerror("错误", "没有有效的页码范围可导出")
        else:
            messagebox.showinfo("完成", "已导出以下文件：\n" + "\n".join(exported))

def preview_split_result(input_file, page_ranges_str):
    """生成预览信息，显示将导出文件个数与页码范围及页数。"""
    if not input_file:
        messagebox.showerror("错误", "请先选择输入 PDF 文件！")
        return
    preview = build_split_preview(input_file, page_ranges_str)
    if preview.valid_count == 0:
        messagebox.showerror("错误", "所有范围均无效，请检查输入。")
        return
    header = f"将生成 {preview.valid_count} 个文件：\n"
    messagebox.showinfo("预览拆分结果", header + "\n" + "\n".join(preview.lines))

def merge_pdfs(file_list, output_file):
    if not file_list:
        messagebox.showerror("错误", "请先选择要合并的 PDF 文件！")
        return
    writer = PdfWriter()
    added = 0
    for path in file_list:
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
                added += 1
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{path}\n{e}")
            return
    try:
        with open(output_file, "wb") as f:
            writer.write(f)
        messagebox.showinfo("完成", f"已合并 {len(file_list)} 个文件，共 {added} 页\n输出：{output_file}")
    except Exception as e:
        messagebox.showerror("错误", str(e))

def merge_pdfs_with_progress(file_list, output_file):
    if not file_list:
        raise ValueError("请先添加要合并的 PDF 文件")

    writer = PdfWriter()
    total_files = len(file_list)

    for index, file_path in enumerate(file_list, start=1):
        reader = PdfReader(file_path)
        for page in reader.pages:
            writer.add_page(page)
        progress = 90 * index / total_files
        post_progress(progress, f"正在合并 {index}/{total_files}: {os.path.basename(file_path)}")

    with open(output_file, "wb") as file:
        writer.write(file)

    post_progress(100, "PDF 合并完成")
    post_done(f"已合并 {total_files} 个 PDF 文件：{output_file}", [output_file])

def set_input_file(filename: str):
    if not filename:
        return
    input_entry.delete(0, tk.END)
    input_entry.insert(0, filename)
    # 自动填充输出名：与输入同目录，文件名后缀 _split.pdf
    try:
        base_dir = os.path.dirname(filename)
        base_name = os.path.splitext(os.path.basename(filename))[0]
        suggested = os.path.join(base_dir, f"{base_name}_split.pdf")
        if not output_entry.get().strip():
            output_entry.insert(0, suggested)
    except Exception:
        pass
    # 显示总页数
    try:
        reader = PdfReader(filename)
        total = len(reader.pages)
        pages_var.set(f"总页数：{total}")
        status_var.set("已载入 PDF")
        # 启用预览按钮
        preview_btn.configure(state="normal")
    except Exception:
        pages_var.set("总页数：-")
        status_var.set("载入失败，请重新选择")
        # 禁用预览按钮
        preview_btn.configure(state="disabled")
    add_recent_file(filename)

def select_input_file():
    filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if filename:
        set_input_file(filename)

def select_output_file():
    filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF files", "*.pdf")])
    if filename:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, filename)
        save_settings()

def build_tk_task_context():
    """
    构建 Tkinter 环境下的 TaskContext
    
    :return: TaskContext
    """
    return TaskContext(
        is_cancelled=lambda: cancel_requested,
        report_progress=lambda p, msg: progress_queue.put(
            ("progress", p, msg)
        ),
        report_done=lambda msg, payload: progress_queue.put(
            ("done", msg, payload)
        ),
        report_error=lambda err: progress_queue.put(
            ("error", err)
        ),
    )

def run_split():
    input_file = input_entry.get().strip()
    output_file = output_entry.get().strip()
    ranges_str = ranges_entry.get().strip()
    if ranges_str == RANGES_PLACEHOLDER:
        ranges_str = ""

    if not input_file or not output_file:
        messagebox.showerror("错误", "请先选择输入文件和输出文件名！")
        return

    if not ranges_str:
        messagebox.showerror("错误", "请输入页码范围，或使用“拆成单页”按钮。")
        return

    ranges = parse_ranges(ranges_str)
    if not ranges:
        messagebox.showerror("错误", "请输入有效的页码范围。")
        return

    # 在后台线程执行
    def task():
        try:
            ctx = build_tk_task_context()
            split_pdf_by_ranges(ctx, input_file, output_file, ranges)
        except Exception as e:
            post_error(e)

    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

def run_split_each():
    input_file = input_entry.get().strip()
    output_file = output_entry.get().strip()

    if not input_file or not output_file:
        messagebox.showerror("错误", "请先选择输入文件和输出文件名！")
        return

    def task():
        try:
            from pdf_split_task import split_pdf_by_single_pages
            ctx = build_tk_task_context()
            split_pdf_by_single_pages(ctx, input_file, output_file)
        except Exception as e:
            post_error(e)

    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

def run_preview():
    input_file = input_entry.get().strip()
    ranges_str = ranges_entry.get().strip()
    if ranges_str == RANGES_PLACEHOLDER:
        ranges_str = ""
    try:
        preview_split_result(input_file, ranges_str)
    except Exception as e:
        messagebox.showerror("错误", str(e))

def run_merge():
    open_merge_manager()

def on_cancel():
    global cancel_requested
    cancel_requested = True
    status_var.set("正在取消...")

def open_output_dir():
    path = ''
    try:
        path = output_entry.get().strip() if 'output_entry' in globals() else ''
    except Exception:
        path = ''
    if not path:
        title = "Error" if LANG == "en" else "错误"
        message = "Please select an output path first." if LANG == "en" else "请先选择输出路径。"
        messagebox.showerror(title, message)
        return
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if not folder:
        folder = os.getcwd()
    if not os.path.exists(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as exc:
            title = "Error" if LANG == "en" else "错误"
            messagebox.showerror(title, str(exc))
            return
    open_folder(folder)

def open_folder(folder):
    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)
    except Exception as e:
        messagebox.showerror("错误", str(e))

def open_pdf_previewer(pdf_path):
    show_pdf_previewer(root, pdf_path)

def open_merge_manager():
    try:
        notebook.select(merge_tab)
        status_var.set("已切换到 PDF 合并页签")
    except Exception:
        pass


if DND_AVAILABLE:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()

from split_pdf_gui import __version__

root.title(f"{T('title')} v{__version__}")
root.geometry("1000x820")
root.minsize(900, 700)

style = ttk.Style()
AVAILABLE_THEMES = set(style.theme_names())
LIGHT_THEME = "vista" if (platform.system().lower().startswith("win") and "vista" in AVAILABLE_THEMES) else (("default" if "default" in AVAILABLE_THEMES else style.theme_use()))
DARK_THEME = "clam" if "clam" in AVAILABLE_THEMES else LIGHT_THEME
try:
    style.theme_use(LIGHT_THEME)
except Exception:
    pass

COLORS = {
    "light": {
        "bg": "#f5f5f5",
        "fg": "#1a1a1a",
        "subbg": "#ffffff",
        "accent": "#0078d4",
        "border": "#d0d0d0",
        "text_disabled": "#8a8d91",
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#e1e1e1",
        "subbg": "#252526",
        "accent": "#0e639c",
        "border": "#3e3e42",
        "text_disabled": "#6a6d70",
    },
}

style.configure("TFrame", padding=6, borderwidth=0, background="#f0f0f0")
style.configure("TLabelframe", padding=8, borderwidth=1, relief="solid", background="#f0f0f0")
style.configure("TLabelframe.Label", font=("Arial", 10, "bold"), padding=(0, 0, 0, 5), background="#f0f0f0", foreground="#000000")
style.configure("TButton", padding=6, font=("Arial", 10), background="#ffffff", relief="raised", borderwidth=1, foreground="#000000")
style.configure("TEntry", padding=4, font=("Arial", 10), background="#ffffff", relief="sunken", borderwidth=1, foreground="#000000")
style.configure("TLabel", padding=4, font=("Arial", 10), background="#f0f0f0", foreground="#000000")
style.configure("Horizontal.TProgressbar", thickness=8, background="#00ff00")
style.configure("TSeparator", background="#d0d0d0")
style.configure("TCombobox", padding=4, font=("Arial", 10), background="#ffffff", relief="sunken", borderwidth=1, foreground="#000000")
style.configure("TMenubutton", padding=4, font=("Arial", 10), background="#ffffff", relief="raised", borderwidth=1, foreground="#000000")
style.configure("TNotebook", background="#f0f0f0", borderwidth=1)
style.configure("TNotebook.Tab", padding=(12, 6), font=("Arial", 10), background="#e0e0e0", foreground="#000000")
style.map(
    "TNotebook.Tab",
    background=[("active", "#ffffff"), ("!active", "#e0e0e0")],
    foreground=[("active", "#0078d4"), ("!active", "#000000")],
    relief=[("selected", "sunken"), ("!selected", "raised")],
)

root.configure(bg="#f0f0f0")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

container = ttk.Frame(root, padding=12)
container.grid(row=0, column=0, sticky="nsew")
container.columnconfigure(0, weight=1)
container.rowconfigure(0, weight=1)

notebook = ttk.Notebook(container)
notebook.grid(row=0, column=0, sticky="nsew")
container.columnconfigure(0, weight=1)
container.rowconfigure(0, weight=1)

split_tab = ttk.Frame(notebook)
merge_tab = ttk.Frame(notebook)
preview_tab = ttk.Frame(notebook)
settings_tab = ttk.Frame(notebook)
epub_tab = ttk.Frame(notebook)
epub_tab.columnconfigure(0, weight=1)
epub_tab.rowconfigure(0, weight=1)
notebook.add(epub_tab, text="EPUB 转 PDF")

recent_files = []


def _save_settings_if_ready():
    if 'SETTINGS_PATH' in globals():
        save_settings()



def _apply_recent_files(new_recent_files: list[str]):
    global recent_files
    recent_files = list(new_recent_files)
    update_recent_menu()



def update_recent_menu():
    if 'recent_menu' not in globals():
        return
    empty_label = 'No recent files' if LANG == 'en' else '暂无最近文件'
    update_recent_menu_ui(recent_menu, recent_files, open_recent, empty_label=empty_label)



def add_recent_file(path: str):
    global recent_files
    recent_files = add_recent_file_ui(
        recent_files,
        path,
        _apply_recent_files,
        _save_settings_if_ready,
    )



def open_recent(idx: int):
    open_recent_ui(recent_files, idx, set_input_file)



def get_ranges_placeholder() -> str:
    return "e.g. 1-3,5,7-9" if LANG == "en" else "例如：1-3,5,7-9（支持中文逗号）"


def get_recent_button_text() -> str:
    return "Recent" if LANG == "en" else "最近"


def get_open_output_button_text() -> str:
    return "Open output dir" if LANG == "en" else "打开输出目录"


def get_preview_tab_texts() -> PreviewTabTexts:
    if LANG == "en":
        return PreviewTabTexts(
            frame_title="PDF Preview",
            input_label="PDF file",
            browse_button="Browse...",
            open_button="Open preview",
        )
    return PreviewTabTexts(
        frame_title="PDF 预览",
        input_label="PDF 文件",
        browse_button="浏览...",
        open_button="打开预览",
    )


def get_settings_tab_texts() -> SettingsTabTexts:
    if LANG == "en":
        return SettingsTabTexts(
            frame_title="Settings",
            theme_label="Theme",
            light_button="Light",
            dark_button="Dark",
            language_label="Language",
            zh_button="ZH",
            en_button="EN",
            template_label="Name template",
            template_hint="{name}=source name, {start}=start page, {end}=end page, {index}=sequence",
            save_button="Save settings",
        )
    return SettingsTabTexts(
        frame_title="设置",
        theme_label="主题",
        light_button="浅色",
        dark_button="深色",
        language_label="语言",
        zh_button="中文",
        en_button="EN",
        template_label="命名模板",
        template_hint="{name}=原文件名, {start}=起始页, {end}=结束页, {index}=序号",
        save_button="保存设置",
    )


def get_toolbar_texts() -> ToolbarTexts:
    if LANG == "en":
        return ToolbarTexts(
            helper_label="Helpers:",
            helper_every_button="Every N pages",
            helper_equal_button="Split K parts",
            clear_button="Clear ranges",
            template_label="Name template",
            recent_button=get_recent_button_text(),
            open_output_button=get_open_output_button_text(),
        )
    return ToolbarTexts(
        helper_label="范围助手：",
        helper_every_button="每 N 页拆分",
        helper_equal_button="均分为 K 份",
        clear_button="清空范围",
        template_label="命名模板",
        recent_button=get_recent_button_text(),
        open_output_button=get_open_output_button_text(),
    )


def get_epub_panel_texts() -> EPUBPanelTexts:
    if LANG == "en":
        return EPUBPanelTexts(
            frame_title="EPUB to PDF",
            input_label="Input EPUB",
            output_label="Output PDF",
            paper_label="Paper size",
            convert_button="Convert",
            batch_frame_title="Batch EPUB to PDF",
            batch_hint="Add .epub files below; output to selected directory. Filename template supports {name}.pdf.",
            batch_add="Add EPUB",
            batch_remove="Remove selected",
            batch_clear="Clear list",
            batch_paper_label="Batch paper size",
            batch_output_label="Output directory",
            batch_template_label="Filename template",
            batch_convert="Batch Convert",
        )
    return EPUBPanelTexts(
        frame_title="EPUB 转 PDF",
        input_label="输入 EPUB 文件",
        output_label="输出 PDF 文件",
        paper_label="纸张大小",
        convert_button="开始转换",
        batch_frame_title="批量 EPUB 转 PDF",
        batch_hint="批量添加 .epub 文件后，将统一输出到所选目录；文件名模板支持 {name}.pdf。",
        batch_add="添加 EPUB",
        batch_remove="移除选中",
        batch_clear="清空列表",
        batch_paper_label="批量纸张大小",
        batch_output_label="批量输出目录",
        batch_template_label="输出文件名模板",
        batch_convert="开始批量转换",
    )


def refresh_notebook_titles():
    if 'notebook' not in globals():
        return
    try:
        if 'split_tab' in globals():
            notebook.tab(split_tab, text='PDF Split' if LANG == 'en' else 'PDF 拆分')
        if 'merge_tab' in globals():
            notebook.tab(merge_tab, text='PDF Merge' if LANG == 'en' else 'PDF 合并')
        if 'preview_tab' in globals():
            notebook.tab(preview_tab, text='PDF Preview' if LANG == 'en' else 'PDF 预览')
        if 'settings_tab' in globals():
            notebook.tab(settings_tab, text='Settings' if LANG == 'en' else '设置')
        if 'epub_tab' in globals():
            notebook.tab(epub_tab, text='EPUB to PDF' if LANG == 'en' else 'EPUB 转 PDF')
    except Exception:
        pass


def refresh_ranges_placeholder():
    global RANGES_PLACEHOLDER
    placeholder = get_ranges_placeholder()
    previous_placeholder = globals().get('RANGES_PLACEHOLDER', placeholder)
    if 'ranges_entry' in globals():
        current_text = ranges_entry.get().strip()
        if current_text == previous_placeholder or not current_text:
            ranges_entry.delete(0, tk.END)
            ranges_entry.insert(0, placeholder)
    RANGES_PLACEHOLDER = placeholder


def refresh_auxiliary_texts():
    try:
        if 'preview_widgets' in globals():
            apply_preview_tab_texts(preview_widgets, get_preview_tab_texts())
    except Exception:
        pass
    try:
        if 'settings_widgets' in globals():
            apply_settings_tab_texts(settings_widgets, get_settings_tab_texts())
    except Exception:
        pass
    try:
        if 'toolbar_widgets' in globals():
            apply_toolbar_texts(
                toolbar_widgets,
                get_toolbar_texts(),
                recent_text=get_recent_button_text(),
                open_output_text=get_open_output_button_text(),
            )
    except Exception:
        pass
    try:
        if 'epub_widgets' in globals():
            apply_epub_panel_texts(epub_widgets, get_epub_panel_texts())
    except Exception:
        pass
    refresh_notebook_titles()
    refresh_ranges_placeholder()


def set_language(lang: str):
    global LANG
    LANG = set_language_ui(
        lang,
        STRINGS,
        LANG,
        root,
        recent_btn,
        None,
    )
    _save_settings_if_ready()
    update_recent_menu()
    refresh_auxiliary_texts()


def toggle_theme_dark():
    theme_dark_var.set(True)
    set_theme(True)


def toggle_theme_light():
    theme_dark_var.set(False)
    set_theme(False)


def set_theme(dark: bool):
    apply_theme(
        ThemeConfig(
            root=root,
            style=style,
            status_bar=status_bar if 'status_bar' in globals() else None,
            colors=COLORS,
            light_theme=LIGHT_THEME,
            dark_theme=DARK_THEME,
        ),
        dark,
    )

def save_settings():
    save_ui_settings(
        SETTINGS_PATH,
        input_entry if 'input_entry' in globals() else None,
        output_entry if 'output_entry' in globals() else None,
        theme_dark_var,
        LANG,
        recent_files,
        name_template_var if 'name_template_var' in globals() else None,
        epub_input_entry if 'epub_input_entry' in globals() else None,
        epub_output_entry if 'epub_output_entry' in globals() else None,
        epub_paper_var if 'epub_paper_var' in globals() else None,
    )

def load_settings():
    global LANG, recent_files
    try:
        settings = load_ui_settings(
            SETTINGS_PATH,
            theme_dark_var,
            set_theme,
            set_input_file,
            output_entry if 'output_entry' in globals() else None,
            name_template_var if 'name_template_var' in globals() else None,
            epub_input_entry if 'epub_input_entry' in globals() else None,
            epub_output_entry if 'epub_output_entry' in globals() else None,
            epub_paper_var if 'epub_paper_var' in globals() else None,
        )
        LANG = settings.lang or LANG
        recent_files = settings.recent or []
        update_recent_menu()
        refresh_auxiliary_texts()
    except Exception:
        pass

def post_progress(pct: float, text: str):
    enqueue_progress(progress_queue, pct, text)

def post_done(msg: str, payload=None):
    enqueue_done(progress_queue, msg, payload)

def post_error(err):
    enqueue_error(progress_queue, err)

def start_running_ui():
    global cancel_requested
    cancel_requested = False
    start_runtime_ui(controls_to_toggle, progress_var, progress_bar, cancel_btn, status_var)

def stop_running_ui():
    stop_runtime_ui(controls_to_toggle, progress_bar, cancel_btn)

def poll_queue():
    poll_progress_queue(root, progress_queue, progress_var, status_var, stop_running_ui)

def helper_every_n_pages():
    input_file = input_entry.get().strip()
    error_title = 'Error' if LANG == 'en' else '错误'
    if not input_file:
        messagebox.showerror(error_title, 'Please select a PDF file first.' if LANG == 'en' else '请先选择 PDF 文件！')
        return
    n = simpledialog.askinteger(
        'Split Every N Pages' if LANG == 'en' else '每 N 页拆分',
        'Enter pages per split:' if LANG == 'en' else '请输入每份包含的页数：',
        minvalue=1,
    )
    if not n:
        return
    try:
        total = len(PdfReader(input_file).pages)
        parts = []
        for start in range(1, total + 1, n):
            end = min(total, start + n - 1)
            parts.append(f'{start}-{end}')
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ', '.join(parts))
        status_var.set(f'Generated ranges every {n} pages' if LANG == 'en' else f'已生成每 {n} 页的范围')
    except Exception as exc:
        messagebox.showerror(error_title, str(exc))


def helper_equal_k_parts():
    input_file = input_entry.get().strip()
    error_title = 'Error' if LANG == 'en' else '错误'
    if not input_file:
        messagebox.showerror(error_title, 'Please select a PDF file first.' if LANG == 'en' else '请先选择 PDF 文件！')
        return
    k = simpledialog.askinteger(
        'Split Into K Parts' if LANG == 'en' else '均分为 K 份',
        'Enter number of parts:' if LANG == 'en' else '请输入份数：',
        minvalue=1,
    )
    if not k:
        return
    try:
        total = len(PdfReader(input_file).pages)
        if k > total:
            k = total
        base, rem = divmod(total, k)
        parts = []
        start = 1
        for i in range(k):
            size = base + (1 if i < rem else 0)
            end = start + size - 1
            parts.append(f'{start}-{end}')
            start = end + 1
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ', '.join(parts))
        status_var.set(f'Generated {k} equal parts' if LANG == 'en' else f'已生成均分为 {k} 份的范围')
    except Exception as exc:
        messagebox.showerror(error_title, str(exc))


def clear_ranges():
    ranges_entry.delete(0, tk.END)
    ranges_entry.insert(0, RANGES_PLACEHOLDER)
    status_var.set('Cleared page ranges' if LANG == 'en' else '已清空页码范围')

notebook.add(split_tab, text="PDF 拆分")
notebook.add(merge_tab, text="PDF 合并")
notebook.add(preview_tab, text="PDF 预览")
notebook.add(settings_tab, text="设置")
refresh_notebook_titles()

theme_dark_var = tk.BooleanVar(value=False)

# PDF 拆分选项卡内容
# 文件区域
RANGES_PLACEHOLDER = get_ranges_placeholder()
split_widgets = build_split_tab(split_tab, RANGES_PLACEHOLDER)
files_frame = split_widgets.files_frame
input_entry = split_widgets.input_entry
input_browse_btn = split_widgets.input_browse_btn
output_entry = split_widgets.output_entry
output_browse_btn = split_widgets.output_browse_btn
pages_var = split_widgets.pages_var
preview_btn = split_widgets.preview_btn
split_frame = split_widgets.split_frame
ranges_entry = split_widgets.ranges_entry
preview_split_btn = split_widgets.preview_split_btn
split_range_btn = split_widgets.split_range_btn
split_each_btn = split_widgets.split_each_btn
chapters_text = split_widgets.chapters_text
split_chapters_btn = split_widgets.split_chapters_btn
split_auto_chapters_btn = split_widgets.split_auto_chapters_btn

input_browse_btn.configure(command=select_input_file)
output_browse_btn.configure(command=select_output_file)
preview_btn.configure(command=lambda: open_pdf_previewer(input_entry.get().strip()))

def merge_add_files():
    items = filedialog.askopenfilenames(title="选择 PDF", filetypes=[("PDF files", "*.pdf")])
    for it in items:
        merge_listbox.insert("end", it)

# 移除选中
def merge_remove_selected():
    sel = list(merge_listbox.curselection())
    sel.reverse()
    for i in sel:
        merge_listbox.delete(i)

# 上移
def merge_move_up():
    sel = list(merge_listbox.curselection())
    if not sel:
        return
    for i in sel:
        if i == 0:
            continue
        txt = merge_listbox.get(i)
        merge_listbox.delete(i)
        merge_listbox.insert(i-1, txt)
    merge_listbox.selection_clear(0, "end")
    for i in [max(0, s-1) for s in sel]:
        merge_listbox.selection_set(i)

# 下移
def merge_move_down():
    sel = list(merge_listbox.curselection())
    if not sel:
        return
    n = merge_listbox.size()
    for i in reversed(sel):
        if i >= n-1:
            continue
        txt = merge_listbox.get(i)
        merge_listbox.delete(i)
        merge_listbox.insert(i+1, txt)
    merge_listbox.selection_clear(0, "end")
    for i in [min(n-1, s+1) for s in sel]:
        merge_listbox.selection_set(i)

# 清空
def merge_clear_all():
    merge_listbox.delete(0, "end")

# 开始合并
def merge_start():
    files = list(merge_listbox.get(0, "end"))
    if not files:
        messagebox.showerror("错误", "请先添加要合并的 PDF")
        return
    out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="保存合并后的 PDF")
    if not out:
        return
    def task():
        try:
            merge_pdfs_with_progress(files, out)
        except Exception as e:
            post_error(e)
    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

# 绑定按钮事件
merge_widgets = build_merge_tab(merge_tab)
merge_tab_frame = merge_widgets.frame
merge_listbox = merge_widgets.listbox
merge_scrollbar = merge_widgets.scrollbar
merge_buttons_frame = merge_widgets.buttons_frame
merge_add_btn = merge_widgets.add_btn
merge_remove_btn = merge_widgets.remove_btn
merge_up_btn = merge_widgets.up_btn
merge_down_btn = merge_widgets.down_btn
merge_clear_btn = merge_widgets.clear_btn
merge_start_btn = merge_widgets.start_btn

merge_add_btn.configure(command=merge_add_files)
merge_remove_btn.configure(command=merge_remove_selected)
merge_up_btn.configure(command=merge_move_up)
merge_down_btn.configure(command=merge_move_down)
merge_clear_btn.configure(command=merge_clear_all)
merge_start_btn.configure(command=merge_start)

# 简单拖拽排序
merge_drag_data = {"index": None}
def merge_on_start_drag(event):
    merge_drag_data["index"] = merge_listbox.nearest(event.y)
def merge_on_drag_motion(event):
    idx = merge_drag_data.get("index")
    if idx is None:
        return
    i = merge_listbox.nearest(event.y)
    if i != idx and 0 <= idx < merge_listbox.size():
        txt = merge_listbox.get(idx)
        merge_listbox.delete(idx)
        merge_listbox.insert(i, txt)
        merge_listbox.selection_clear(0, "end")
        merge_listbox.selection_set(i)
        merge_drag_data["index"] = i
merge_listbox.bind("<Button-1>", merge_on_start_drag)
merge_listbox.bind("<B1-Motion>", merge_on_drag_motion)

# PDF 预览选项卡内容
preview_widgets = build_preview_tab(preview_tab, get_preview_tab_texts())
preview_frame = preview_widgets.frame
preview_input_var = preview_widgets.input_var
preview_input_entry = preview_widgets.input_entry
preview_browse_btn = preview_widgets.browse_btn
preview_open_btn = preview_widgets.open_btn

def preview_browse_file():
    filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if filename:
        preview_input_var.set(filename)

# 打开预览
def preview_open():
    filename = preview_input_var.get().strip()
    if filename:
        open_pdf_previewer(filename)
    else:
        messagebox.showerror("错误", "请先选择 PDF 文件！")

# 绑定按钮事件
preview_browse_btn.configure(command=preview_browse_file)
preview_open_btn.configure(command=preview_open)

# EPUB 转换选项卡内容（如果库可用）
name_template_var = tk.StringVar(value="{name}_{start}-{end}.pdf")
settings_widgets = build_settings_tab(settings_tab, name_template_var, get_settings_tab_texts())
settings_frame = settings_widgets.frame
save_settings_btn = settings_widgets.save_btn
settings_widgets.light_btn.configure(command=toggle_theme_light)
settings_widgets.dark_btn.configure(command=toggle_theme_dark)
settings_widgets.zh_btn.configure(command=lambda: set_language("zh"))
settings_widgets.en_btn.configure(command=lambda: set_language("en"))

def save_settings_from_tab():
    save_settings()
    messagebox.showinfo("提示", "设置已保存！")

save_settings_btn.configure(command=save_settings_from_tab)

def _on_ranges_focus_in(event):
    if ranges_entry.get().strip() == RANGES_PLACEHOLDER:
        ranges_entry.delete(0, tk.END)


def _on_ranges_focus_out(event):
    if not ranges_entry.get().strip():
        ranges_entry.insert(0, RANGES_PLACEHOLDER)


ranges_entry.bind("<FocusIn>", _on_ranges_focus_in)
ranges_entry.bind("<FocusOut>", _on_ranges_focus_out)
preview_split_btn.configure(command=run_preview)
split_range_btn.configure(command=run_split)
split_each_btn.configure(command=run_split_each)

def run_split_by_chapters():
    input_file = input_entry.get().strip()
    output_file = output_entry.get().strip()
    chapters_input = chapters_text.get("1.0", tk.END).strip()
    
    if not input_file or not output_file:
        messagebox.showerror("错误", "请先选择输入文件和输出文件名！")
        return
    
    if not chapters_input:
        messagebox.showerror("错误", "请输入章节范围！")
        return
    
    try:
        chapter_ranges = parse_chapter_ranges(chapters_input)
    except ValueError as exc:
        messagebox.showerror("错误", str(exc))
        return

    if not chapter_ranges:
        messagebox.showerror("错误", "没有有效的章节范围！")
        return
    
    def task():
        try:
            from pdf_split_task import split_pdf_by_chapters
            ctx = build_tk_task_context()
            split_pdf_by_chapters(ctx, input_file, output_file, chapter_ranges, chapters_per_unit=1)
        except Exception as e:
            post_error(e)
    
    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

split_chapters_btn.configure(command=run_split_by_chapters)

# 自动按章节拆分按钮
def run_split_by_auto_chapters():
    input_file = input_entry.get().strip()
    output_file = output_entry.get().strip()
    
    if not input_file or not output_file:
        messagebox.showerror("错误", "请先选择输入文件和输出文件名！")
        return
    
    def task():
        try:
            from pdf_split_task import split_pdf_by_auto_chapters
            ctx = build_tk_task_context()
            split_pdf_by_auto_chapters(ctx, input_file, output_file)
        except Exception as e:
            post_error(e)
    
    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

split_auto_chapters_btn.configure(command=run_split_by_auto_chapters)

def select_epub_input():
    fname = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
    if not fname:
        return
    epub_input_entry.delete(0, tk.END)
    epub_input_entry.insert(0, fname)
    try:
        base_dir = os.path.dirname(fname)
        base_name = os.path.splitext(os.path.basename(fname))[0]
        suggested = os.path.join(base_dir, f"{base_name}.pdf")
        if not epub_output_entry.get().strip():
            epub_output_entry.insert(0, suggested)
    except Exception:
        pass
    save_settings()


def select_epub_output():
    fname = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not fname:
        return
    epub_output_entry.delete(0, tk.END)
    epub_output_entry.insert(0, fname)
    save_settings()


def run_epub_convert():
    epub_in = epub_input_entry.get().strip()
    pdf_out = epub_output_entry.get().strip()
    if not epub_in or not pdf_out:
        messagebox.showerror(
            "Error" if LANG == "en" else "错误",
            "Please select EPUB input and PDF output paths first." if LANG == "en" else "请先选择 EPUB 输入文件和 PDF 输出路径！",
        )
        return
    paper = epub_paper_var.get().strip() or "a4"

    def task():
        try:
            ctx = build_tk_task_context()
            do_epub_convert_with_progress(ctx, epub_in, pdf_out, paper)
        except Exception as exc:
            post_error(exc)

    start_running_ui()
    threading.Thread(target=task, daemon=True).start()


def add_batch_epub_files():
    files = filedialog.askopenfilenames(
        title="Select EPUB files" if LANG == "en" else "选择 EPUB 文件",
        filetypes=[("EPUB files", "*.epub")],
    )
    if not files:
        return
    for file_path in files:
        batch_epub_list.insert("end", file_path)


def remove_batch_selected():
    selected = list(batch_epub_list.curselection())
    selected.reverse()
    for index in selected:
        batch_epub_list.delete(index)


def clear_batch_list():
    batch_epub_list.delete(0, "end")


def select_batch_output_dir():
    directory = filedialog.askdirectory(title="Select output directory" if LANG == "en" else "选择输出目录")
    if not directory:
        return
    batch_output_dir_entry.delete(0, tk.END)
    batch_output_dir_entry.insert(0, directory)


def run_batch_epub_convert():
    epub_files = list(batch_epub_list.get(0, "end"))
    output_dir = batch_output_dir_entry.get().strip()
    paper = batch_epub_paper_var.get().strip() or "a4"
    filename_template = batch_filename_var.get().strip() or "{name}.pdf"

    if not epub_files:
        messagebox.showerror(
            "Error" if LANG == "en" else "错误",
            "Please add EPUB files to convert." if LANG == "en" else "请先添加要转换的 EPUB 文件！",
        )
        return
    if not output_dir:
        messagebox.showerror(
            "Error" if LANG == "en" else "错误",
            "Please select an output directory first." if LANG == "en" else "请先选择输出目录！",
        )
        return

    def task():
        try:
            ctx = build_tk_task_context()
            batch_epub_to_pdf(ctx, epub_files, output_dir, paper, filename_template)
        except Exception as exc:
            post_error(exc)

    start_running_ui()
    threading.Thread(target=task, daemon=True).start()


epub_widgets = build_epub_panels(epub_tab)
epub_frame = epub_widgets.epub_frame
epub_input_entry = epub_widgets.input_entry
epub_browse_btn = epub_widgets.browse_btn
epub_output_entry = epub_widgets.output_entry
epub_output_browse_btn = epub_widgets.output_browse_btn
epub_paper_var = epub_widgets.paper_var
epub_paper_combo = epub_widgets.paper_combo
epub_convert_btn = epub_widgets.convert_btn
batch_epub_frame = epub_widgets.batch_frame
batch_epub_list = epub_widgets.batch_list
batch_buttons_frame = epub_widgets.batch_buttons_frame
batch_add_btn = epub_widgets.batch_add_btn
batch_remove_btn = epub_widgets.batch_remove_btn
batch_clear_btn = epub_widgets.batch_clear_btn
batch_epub_paper_var = epub_widgets.batch_paper_var
batch_epub_paper_combo = epub_widgets.batch_paper_combo
batch_output_dir_entry = epub_widgets.batch_output_dir_entry
batch_output_browse_btn = epub_widgets.batch_output_browse_btn
batch_filename_var = epub_widgets.batch_filename_var
batch_filename_entry = epub_widgets.batch_filename_entry
batch_convert_btn = epub_widgets.batch_convert_btn

epub_browse_btn.configure(command=select_epub_input)
epub_output_browse_btn.configure(command=select_epub_output)
epub_convert_btn.configure(command=run_epub_convert)
batch_add_btn.configure(command=add_batch_epub_files)
batch_remove_btn.configure(command=remove_batch_selected)
batch_clear_btn.configure(command=clear_batch_list)
batch_output_browse_btn.configure(command=select_batch_output_dir)
batch_convert_btn.configure(command=run_batch_epub_convert)

status_var = tk.StringVar(value="就绪")
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", padding=(10,6), font=("Arial", 9), background="#f0f0f0")
status_bar.grid(row=3, column=0, sticky="ew")

# 记录窗口默认背景色，便于浅色主题恢复
try:
    DEFAULT_BG = style.lookup("TFrame", "background") or ""
except Exception:
    DEFAULT_BG = ""

# 进度与取消
progress_var = tk.IntVar(value=0)
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100, variable=progress_var, length=240)
progress_bar.grid(row=2, column=0, sticky="ew", padx=12)
progress_bar.grid_remove()
cancel_btn = ttk.Button(root, text="取消运行", command=on_cancel, width=12)
cancel_btn.grid(row=2, column=0, sticky="e", padx=12)
cancel_btn.grid_remove()

# 底部工具栏（主题切换、范围助手）
toolbar_widgets = build_toolbar(
    root,
    name_template_var,
    get_recent_button_text(),
    get_open_output_button_text(),
    get_toolbar_texts(),
)
toolbar = toolbar_widgets.frame
recent_btn = toolbar_widgets.recent_btn
recent_menu = toolbar_widgets.recent_menu
toolbar_widgets.helper_every_btn.configure(command=helper_every_n_pages)
toolbar_widgets.helper_equal_btn.configure(command=helper_equal_k_parts)
toolbar_widgets.clear_btn.configure(command=clear_ranges)
toolbar_widgets.open_output_btn.configure(command=open_output_dir)
refresh_auxiliary_texts()

controls_to_toggle = []
controls_to_toggle.extend(split_widgets.controls)
controls_to_toggle.extend(merge_widgets.controls)
controls_to_toggle.extend(preview_widgets.controls)
controls_to_toggle.extend(settings_widgets.controls)
controls_to_toggle.extend(toolbar_widgets.controls)
controls_to_toggle.extend(epub_widgets.controls)

progress_queue: "queue.Queue" = queue.Queue()
cancel_requested = False

# 设置文件
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

# 启动轮询与加载设置
root.after(150, poll_queue)
load_settings()

# 响应式布局处理
def on_window_resize(event):
    """处理窗口大小变化事件"""
    window_width = event.width
    window_height = event.height
    
    # 根据窗口宽度调整元素布局
    if window_width < 850:
        # 窄窗口布局
        container.columnconfigure(2, weight=0)
        # 调整工具栏布局
        toolbar.columnconfigure(10, weight=1)
        
        # 调整输入框宽度
        input_entry.configure(width=max(30, window_width // 20))
        output_entry.configure(width=max(30, window_width // 20))
        ranges_entry.configure(width=max(25, window_width // 25))
    else:
        # 宽窗口布局
        container.columnconfigure(2, weight=0)
        
        # 调整输入框宽度
        input_entry.configure(width=max(40, window_width // 15))
        output_entry.configure(width=max(40, window_width // 15))
        ranges_entry.configure(width=max(30, window_width // 20))
    
    # 确保状态栏和进度条始终可见
    status_bar.grid(row=3, column=0, sticky="ew")
    if progress_bar.winfo_ismapped():
        progress_bar.grid(row=2, column=0, sticky="ew", padx=12)
    if cancel_btn.winfo_ismapped():
        cancel_btn.grid(row=1, column=0, sticky="e", padx=12)
    
    # 调整主容器内边距
    container.configure(padding=min(12, window_width // 60))

# 绑定窗口大小变化事件
root.bind("<Configure>", on_window_resize)

# 拖拽到输入框（可选）
if DND_AVAILABLE:
    try:
        def _handle_drop(event):
            paths = root.tk.splitlist(event.data)
            if not paths:
                return
            first = paths[0]
            if first.lower().endswith(".pdf") and os.path.exists(first):
                set_input_file(first)
        input_entry.drop_target_register(DND_FILES)
        input_entry.dnd_bind('<<Drop>>', _handle_drop)
    except Exception:
        pass

# 拖拽到批量 EPUB 列表框（可选）
if DND_AVAILABLE:
    try:
        def _handle_epub_drop(event):
            paths = root.tk.splitlist(event.data)
            if not paths:
                return
            for path in paths:
                if path.lower().endswith(".epub") and os.path.exists(path):
                    batch_epub_list.insert("end", path)
        batch_epub_list.drop_target_register(DND_FILES)
        batch_epub_list.dnd_bind('<<Drop>>', _handle_epub_drop)
    except Exception:
        pass

# 快捷键
try:
    root.bind('<Control-p>', lambda e: run_preview())
    root.bind('<Control-P>', lambda e: run_preview())
    root.bind('<Control-Return>', lambda e: run_split())
    root.bind('<Control-m>', lambda e: open_merge_manager())
    root.bind('<Control-M>', lambda e: open_merge_manager())
    root.bind('<Control-l>', lambda e: toggle_theme_light())
    root.bind('<Control-d>', lambda e: toggle_theme_dark())
except Exception:
    pass

root.mainloop()
