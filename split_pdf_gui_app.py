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
    push_recent_file,
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
    path = output_entry.get().strip()
    if not path:
        messagebox.showerror("错误", "请先选择输出文件路径！")
        return
    folder = os.path.dirname(path) or os.getcwd()
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
        status_var.set("???? PDF ???")
    except Exception:
        pass

# ?????????
if DND_AVAILABLE:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()

root.title(T("title"))
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
container = ttk.Frame(root, padding=12)
container.grid(row=0, column=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

notebook = ttk.Notebook(container)
notebook.grid(row=0, column=0, sticky="nsew")
container.columnconfigure(0, weight=1)
container.rowconfigure(0, weight=1)

split_tab = ttk.Frame(notebook)
merge_tab = ttk.Frame(notebook)
preview_tab = ttk.Frame(notebook)
settings_tab = ttk.Frame(notebook)

recent_files = []

def update_recent_menu():
    if 'recent_menu' not in globals():
        return
    recent_menu.delete(0, 'end')
    if not recent_files:
        recent_menu.add_command(label='??????', state='disabled')
        return
    for idx, path in enumerate(recent_files):
        recent_menu.add_command(label=path, command=lambda i=idx: open_recent(i))


def add_recent_file(path: str):
    global recent_files
    if not path:
        return
    recent_files = push_recent_file(recent_files, path)
    update_recent_menu()
    if 'SETTINGS_PATH' in globals():
        save_settings()


def open_recent(idx: int):
    if 0 <= idx < len(recent_files):
        set_input_file(recent_files[idx])


def set_language(lang: str):
    global LANG
    if lang not in STRINGS:
        return
    LANG = lang
    try:
        root.title(T("title"))
    except Exception:
        pass
    try:
        recent_btn.configure(text=T("recent"))
    except Exception:
        pass
    if 'SETTINGS_PATH' in globals():
        save_settings()


def toggle_theme_dark():
    theme_dark_var.set(True)
    set_theme(True)


def toggle_theme_light():
    theme_dark_var.set(False)
    set_theme(False)


def set_theme(dark: bool):
    global style
    palette = COLORS["dark"] if dark else COLORS["light"]
    try:
        style.theme_use(DARK_THEME if dark else LIGHT_THEME)
    except Exception:
        pass
    root.configure(bg=palette["bg"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabelframe", background=palette["bg"])
    style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["fg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure("TEntry", fieldbackground=palette["subbg"], foreground=palette["fg"])
    style.configure("TButton", background=palette["subbg"], foreground=palette["fg"])
    style.configure("TCombobox", fieldbackground=palette["subbg"], foreground=palette["fg"])
    style.configure("TMenubutton", background=palette["subbg"], foreground=palette["fg"])
    style.configure("Horizontal.TProgressbar", background=palette["accent"])
    style.configure("TSeparator", background=palette["border"])
    if 'status_bar' in globals():
        status_bar.configure(background=palette["bg"], foreground=palette["fg"])


def save_settings():
    try:
        dark_val = bool(theme_dark_var.get())
    except Exception:
        dark_val = False
    settings = AppSettings(
        input=input_entry.get().strip() if 'input_entry' in globals() else '',
        output=output_entry.get().strip() if 'output_entry' in globals() else '',
        dark=dark_val,
        lang=LANG,
        recent=recent_files,
        template=name_template_var.get() if 'name_template_var' in globals() else '{name}_{start}-{end}.pdf',
        epub_input=epub_input_entry.get().strip() if 'epub_input_entry' in globals() else '',
        epub_output=epub_output_entry.get().strip() if 'epub_output_entry' in globals() else '',
        epub_paper=epub_paper_var.get().strip() if 'epub_paper_var' in globals() else 'a4',
    )
    save_app_settings(SETTINGS_PATH, settings)


def load_settings():
    try:
        settings = load_app_settings(SETTINGS_PATH)
        if settings.input:
            set_input_file(settings.input)
        if settings.output and 'output_entry' in globals():
            output_entry.delete(0, tk.END)
            output_entry.insert(0, settings.output)
        try:
            theme_dark_var.set(bool(settings.dark))
        except Exception:
            pass
        set_theme(bool(settings.dark))
        global LANG, recent_files
        LANG = settings.lang or LANG
        recent_files = settings.recent or []
        update_recent_menu()
        if settings.template and 'name_template_var' in globals():
            name_template_var.set(settings.template)
        if settings.epub_input and 'epub_input_entry' in globals():
            epub_input_entry.delete(0, tk.END)
            epub_input_entry.insert(0, settings.epub_input)
        if settings.epub_output and 'epub_output_entry' in globals():
            epub_output_entry.delete(0, tk.END)
            epub_output_entry.insert(0, settings.epub_output)
        if settings.epub_paper and 'epub_paper_var' in globals():
            epub_paper_var.set(settings.epub_paper)
        try:
            recent_btn.configure(text=T("recent"))
        except Exception:
            pass
    except Exception:
        pass


def post_progress(pct: float, text: str):
    progress_queue.put(("progress", pct, text))


def post_done(msg: str, payload=None):
    progress_queue.put(("done", msg, payload))


def post_error(err):
    progress_queue.put(("error", err))


def start_running_ui():
    global cancel_requested
    cancel_requested = False
    if 'progress_var' in globals():
        progress_var.set(0)
    if 'progress_bar' in globals():
        progress_bar.grid()
    if 'cancel_btn' in globals():
        cancel_btn.grid()
    if 'status_var' in globals():
        status_var.set("????...")
    for widget in globals().get('controls_to_toggle', []):
        try:
            if isinstance(widget, ttk.Combobox):
                widget.configure(state='disabled')
            else:
                widget.configure(state='disabled')
        except Exception:
            pass


def stop_running_ui():
    if 'progress_bar' in globals():
        progress_bar.grid_remove()
    if 'cancel_btn' in globals():
        cancel_btn.grid_remove()
    for widget in globals().get('controls_to_toggle', []):
        try:
            if isinstance(widget, ttk.Combobox):
                widget.configure(state='readonly')
            else:
                widget.configure(state='normal')
        except Exception:
            pass


def poll_queue():
    try:
        while True:
            item = progress_queue.get_nowait()
            kind = item[0]
            if kind == 'progress':
                _, pct, msg = item
                progress_var.set(int(max(0, min(100, pct))))
                status_var.set(str(msg))
            elif kind == 'done':
                _, msg, payload = item
                stop_running_ui()
                progress_var.set(100)
                status_var.set(str(msg))
                if msg:
                    messagebox.showinfo('??', str(msg))
            elif kind == 'error':
                _, err = item
                stop_running_ui()
                status_var.set('????')
                messagebox.showerror('??', str(err))
    except queue.Empty:
        pass
    root.after(150, poll_queue)


def helper_every_n_pages():
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror('??', '?????? PDF ??')
        return
    n = simpledialog.askinteger('?N???', '???????', minvalue=1)
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
        status_var.set(f'??? {n} ?????')
    except Exception as exc:
        messagebox.showerror('??', str(exc))


def helper_equal_k_parts():
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror('??', '?????? PDF ??')
        return
    k = simpledialog.askinteger('???K?', '?????', minvalue=1)
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
        status_var.set(f'???? {k} ?')
    except Exception as exc:
        messagebox.showerror('??', str(exc))


def clear_ranges():
    ranges_entry.delete(0, tk.END)
    ranges_entry.insert(0, RANGES_PLACEHOLDER)
    status_var.set('?????')

notebook.add(split_tab, text="PDF ??")
notebook.add(merge_tab, text="PDF ??")
notebook.add(preview_tab, text="PDF ??")
notebook.add(settings_tab, text="??")

theme_dark_var = tk.BooleanVar(value=False)

# PDF 拆分选项卡内容
# 文件区域
files_frame = ttk.LabelFrame(split_tab, text="文件")
files_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=(0,8))
for c in range(3):
    files_frame.columnconfigure(c, weight=1 if c == 1 else 0)

ttk.Label(files_frame, text="输入 PDF 文件").grid(row=0, column=0, sticky="w", padx=8, pady=6)
input_entry = ttk.Entry(files_frame)
input_entry.grid(row=0, column=1, sticky="ew", padx=4)
ttk.Button(files_frame, text="浏览...", command=select_input_file, width=10).grid(row=0, column=2, padx=8)

ttk.Label(files_frame, text="输出 PDF 文件").grid(row=1, column=0, sticky="w", padx=8, pady=6)
output_entry = ttk.Entry(files_frame)
output_entry.grid(row=1, column=1, sticky="ew", padx=4)
ttk.Button(files_frame, text="浏览...", command=select_output_file, width=10).grid(row=1, column=2, padx=8)

# 页数信息
pages_var = tk.StringVar(value="总页数：-")
ttk.Label(files_frame, textvariable=pages_var, foreground="#666666").grid(row=2, column=1, sticky="w", padx=4, pady=(0,6))

# 预览按钮
preview_btn = ttk.Button(files_frame, text="预览 PDF", command=lambda: open_pdf_previewer(input_entry.get().strip()), width=12)
preview_btn.grid(row=2, column=2, padx=8, pady=4)
preview_btn.configure(state="disabled")  # 初始禁用，选择文件后启用

# 拆分区域
split_frame = ttk.LabelFrame(split_tab, text="拆分")
split_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
split_frame.columnconfigure(1, weight=1)

# 配置 split_tab 的列宽
split_tab.columnconfigure(1, weight=1)

# PDF 合并选项卡内容
merge_tab_frame = ttk.LabelFrame(merge_tab, text="PDF 合并")
merge_tab_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
merge_tab.columnconfigure(0, weight=1)
merge_tab.rowconfigure(0, weight=1)
merge_tab_frame.columnconfigure(0, weight=1)
merge_tab_frame.rowconfigure(0, weight=1)

# 文件列表
merge_listbox = tk.Listbox(merge_tab_frame, selectmode=tk.EXTENDED)
merge_listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

# 滚动条
merge_scrollbar = ttk.Scrollbar(merge_tab_frame, orient="vertical", command=merge_listbox.yview)
merge_scrollbar.grid(row=0, column=1, sticky="ns", pady=4)
merge_listbox.configure(yscrollcommand=merge_scrollbar.set)

# 按钮区域
merge_buttons_frame = ttk.Frame(merge_tab_frame)
merge_buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
for i in range(8):
    merge_buttons_frame.columnconfigure(i, weight=1)

# 添加文件
merge_add_btn = ttk.Button(merge_buttons_frame, text="添加文件")
merge_add_btn.grid(row=0, column=0, padx=4)

# 移除选中
merge_remove_btn = ttk.Button(merge_buttons_frame, text="移除选中")
merge_remove_btn.grid(row=0, column=1, padx=4)

# 上移
merge_up_btn = ttk.Button(merge_buttons_frame, text="上移")
merge_up_btn.grid(row=0, column=2, padx=4)

# 下移
merge_down_btn = ttk.Button(merge_buttons_frame, text="下移")
merge_down_btn.grid(row=0, column=3, padx=4)

# 清空
merge_clear_btn = ttk.Button(merge_buttons_frame, text="清空")
merge_clear_btn.grid(row=0, column=4, padx=4)

# 分割线
ttk.Separator(merge_buttons_frame).grid(row=0, column=5, sticky="ew", padx=8)

# 开始合并
merge_start_btn = ttk.Button(merge_buttons_frame, text="开始合并")
merge_start_btn.grid(row=0, column=6, padx=4)

# 合并按钮事件处理
# 添加文件
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
preview_frame = ttk.LabelFrame(preview_tab, text="PDF 预览")
preview_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
preview_tab.columnconfigure(0, weight=1)
preview_tab.rowconfigure(0, weight=1)
preview_frame.columnconfigure(1, weight=1)

# 预览文件选择
preview_input_var = tk.StringVar()
ttk.Label(preview_frame, text="PDF 文件").grid(row=0, column=0, sticky="w", padx=8, pady=6)
preview_input_entry = ttk.Entry(preview_frame, textvariable=preview_input_var)
preview_input_entry.grid(row=0, column=1, sticky="ew", padx=4)

# 浏览按钮
preview_browse_btn = ttk.Button(preview_frame, text="浏览...")
preview_browse_btn.grid(row=0, column=2, padx=8)

# 预览按钮
preview_open_btn = ttk.Button(preview_frame, text="打开预览", width=12)
preview_open_btn.grid(row=1, column=1, sticky="w", padx=4, pady=6)

# 预览选项卡事件处理
# 浏览文件
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
settings_frame = ttk.LabelFrame(settings_tab, text="设置")
settings_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
settings_tab.columnconfigure(0, weight=1)
settings_tab.rowconfigure(0, weight=1)
settings_frame.columnconfigure(1, weight=1)

# 主题设置
ttk.Label(settings_frame, text="主题").grid(row=0, column=0, sticky="w", padx=8, pady=6)
theme_frame = ttk.Frame(settings_frame)
theme_frame.grid(row=0, column=1, sticky="w", padx=4)
ttk.Button(theme_frame, text="浅色", command=toggle_theme_light).pack(side="left", padx=4)
ttk.Button(theme_frame, text="深色", command=toggle_theme_dark).pack(side="left", padx=4)

# 语言设置
ttk.Label(settings_frame, text="语言").grid(row=1, column=0, sticky="w", padx=8, pady=6)
lang_frame = ttk.Frame(settings_frame)
lang_frame.grid(row=1, column=1, sticky="w", padx=4)
ttk.Button(lang_frame, text="中文", command=lambda: set_language("zh")).pack(side="left", padx=4)
ttk.Button(lang_frame, text="English", command=lambda: set_language("en")).pack(side="left", padx=4)

# 命名模板设置
ttk.Label(settings_frame, text="命名模板").grid(row=2, column=0, sticky="w", padx=8, pady=6)
name_template_var = tk.StringVar(value="{name}_{start}-{end}.pdf")
template_entry = ttk.Entry(settings_frame, textvariable=name_template_var)
template_entry.grid(row=2, column=1, sticky="ew", padx=4)
template_help = ttk.Label(settings_frame, text="{name}=文件名, {start}=开始页, {end}=结束页, {index}=序号", foreground="#666666")
template_help.grid(row=3, column=1, sticky="w", padx=4, pady=(0,6))

# 保存设置按钮
save_settings_btn = ttk.Button(settings_frame, text="保存设置")
save_settings_btn.grid(row=4, column=1, sticky="w", padx=4, pady=6)

def save_settings_from_tab():
    save_settings()
    messagebox.showinfo("提示", "设置已保存！")

save_settings_btn.configure(command=save_settings_from_tab)

ttk.Label(split_frame, text="页码范围").grid(row=0, column=0, sticky="w", padx=8, pady=6)
RANGES_PLACEHOLDER = "例如：1-3,5,7-9（支持中文逗号）"
ranges_entry = ttk.Entry(split_frame)
ranges_entry.grid(row=0, column=1, sticky="ew", padx=4)

def _on_ranges_focus_in(event):
    if ranges_entry.get().strip() == RANGES_PLACEHOLDER:
        ranges_entry.delete(0, tk.END)

def _on_ranges_focus_out(event):
    if not ranges_entry.get().strip():
        ranges_entry.insert(0, RANGES_PLACEHOLDER)

ranges_entry.insert(0, RANGES_PLACEHOLDER)
ranges_entry.bind("<FocusIn>", _on_ranges_focus_in)
ranges_entry.bind("<FocusOut>", _on_ranges_focus_out)

# 预览拆分结果按钮
preview_split_btn = ttk.Button(split_frame, text="预览拆分结果", command=run_preview, width=16)
preview_split_btn.grid(row=0, column=2, padx=8, pady=4)

ttk.Separator(split_frame).grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=4)

# 按范围拆分按钮
split_range_btn = ttk.Button(split_frame, text="按范围拆分", command=run_split, width=18)
split_range_btn.grid(row=2, column=1, sticky="w", padx=4, pady=6)

# 拆成单页按钮
split_each_btn = ttk.Button(split_frame, text="拆成单页", command=run_split_each, width=18)
split_each_btn.grid(row=2, column=1, sticky="e", padx=4, pady=6)

# 章节拆分区域
ttk.Separator(split_frame).grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
ttk.Label(split_frame, text="章节范围（每行为一章：起始页-结束页）").grid(row=4, column=0, sticky="w", padx=8, pady=6)
chapters_text = tk.Text(split_frame, height=8, width=50)
chapters_text.grid(row=4, column=1, sticky="ew", padx=4)
chapters_text.insert("1.0", "例如：\n1-10\n11-25\n26-40\n41-55\n56-70")

# 按章节拆分按钮
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

split_chapters_btn = ttk.Button(split_frame, text="按章节拆分", command=run_split_by_chapters, width=18)
split_chapters_btn.grid(row=5, column=1, sticky="w", padx=4, pady=6)

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

split_auto_chapters_btn = ttk.Button(split_frame, text="自动按章节拆分", command=run_split_by_auto_chapters, width=18)
split_auto_chapters_btn.grid(row=5, column=1, sticky="e", padx=4, pady=6)

# 合并区域
merge_frame = ttk.LabelFrame(container, text="合并")
merge_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
merge_frame.columnconfigure(1, weight=1)

# 合并 PDF 按钮
merge_btn = ttk.Button(merge_frame, text="合并 PDF", command=run_merge, width=18)
merge_btn.grid(row=0, column=0, padx=8, pady=6)

# 打开输出目录按钮
open_output_btn = ttk.Button(merge_frame, text="打开输出目录", command=open_output_dir, width=18)
open_output_btn.grid(row=0, column=1, padx=8, pady=6, sticky="w")

# EPUB 转 PDF 区域
epub_frame = ttk.LabelFrame(container, text="EPUB 转 PDF")
epub_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
for c in range(3):
    epub_frame.columnconfigure(c, weight=1 if c == 1 else 0)

ttk.Label(epub_frame, text="输入 EPUB 文件").grid(row=0, column=0, sticky="w", padx=8, pady=6)
epub_input_entry = ttk.Entry(epub_frame)
epub_input_entry.grid(row=0, column=1, sticky="ew", padx=4)

def select_epub_input():
    fname = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
    if not fname:
        return
    epub_input_entry.delete(0, tk.END)
    epub_input_entry.insert(0, fname)
    # 若输出为空，自动建议输出名
    try:
        base_dir = os.path.dirname(fname)
        base_name = os.path.splitext(os.path.basename(fname))[0]
        suggested = os.path.join(base_dir, f"{base_name}.pdf")
        if not epub_output_entry.get().strip():
            epub_output_entry.insert(0, suggested)
    except Exception:
        pass
    save_settings()

epub_browse_btn = ttk.Button(epub_frame, text="浏览...", command=select_epub_input, width=10)
epub_browse_btn.grid(row=0, column=2, padx=8)

ttk.Label(epub_frame, text="输出 PDF 文件").grid(row=1, column=0, sticky="w", padx=8, pady=6)
epub_output_entry = ttk.Entry(epub_frame)
epub_output_entry.grid(row=1, column=1, sticky="ew", padx=4)

def select_epub_output():
    fname = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not fname:
        return
    epub_output_entry.delete(0, tk.END)
    epub_output_entry.insert(0, fname)
    save_settings()

epub_output_browse_btn = ttk.Button(epub_frame, text="浏览...", command=select_epub_output, width=10)
epub_output_browse_btn.grid(row=1, column=2, padx=8)

ttk.Label(epub_frame, text="纸张").grid(row=2, column=0, sticky="w", padx=8, pady=6)
epub_paper_var = tk.StringVar(value="a4")
epub_paper_combo = ttk.Combobox(epub_frame, textvariable=epub_paper_var, state="readonly", width=12,
                            values=("a4", "a5", "letter", "legal"))
epub_paper_combo.grid(row=2, column=1, sticky="w", padx=4)

# 响应式布局调整
def _legacy_on_window_resize(event):
    """窗口大小变化时的响应式布局调整"""
    window_width = event.width
    
    # 根据窗口宽度调整组件布局
    if window_width < 900:
        # 窄窗口布局
        try:
            files_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=(0,8))
            split_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            merge_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            epub_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            batch_epub_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            
            # 确保所有列都有适当的权重
            for frame in [files_frame, split_frame, merge_frame, epub_frame, batch_epub_frame]:
                try:
                    frame.columnconfigure(1, weight=1)
                except Exception:
                    pass
        except Exception:
            pass
    else:
        # 宽窗口布局
        try:
            files_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=(0,8))
            split_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            merge_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            epub_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
            batch_epub_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        except Exception:
            pass

def run_epub_convert():
    epub_in = epub_input_entry.get().strip()
    pdf_out = epub_output_entry.get().strip()
    if not epub_in or not pdf_out:
        messagebox.showerror("错误", "请先选择 EPUB 输入与 PDF 输出文件！")
        return
    paper = epub_paper_var.get().strip() or "a4"

    def task():
        try:
            ctx = build_tk_task_context()
            do_epub_convert_with_progress(ctx, epub_in, pdf_out, paper)
        except Exception as e:
            post_error(e)

    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

# 开始转换按钮
epub_convert_btn = ttk.Button(epub_frame, text="开始转换", command=run_epub_convert, width=18)
epub_convert_btn.grid(row=2, column=2, padx=8)

# 批量 EPUB 转 PDF 区域
batch_epub_frame = ttk.LabelFrame(container, text="批量 EPUB 转 PDF")
batch_epub_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
for c in range(3):
    batch_epub_frame.columnconfigure(c, weight=1 if c == 1 else 0)

# 批量文件列表
batch_epub_list = tk.Listbox(batch_epub_frame, selectmode=tk.EXTENDED, height=6)
batch_epub_list.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=8, pady=6)

# 批量操作按钮
batch_buttons_frame = ttk.Frame(batch_epub_frame)
batch_buttons_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
batch_buttons_frame.columnconfigure(4, weight=1)

def add_batch_epub_files():
    """添加多个 EPUB 文件到批量转换列表"""
    files = filedialog.askopenfilenames(title="选择 EPUB 文件", filetypes=[("EPUB files", "*.epub")])
    if files:
        for file in files:
            batch_epub_list.insert("end", file)

def remove_batch_selected():
    """移除选中的 EPUB 文件"""
    selected = list(batch_epub_list.curselection())
    selected.reverse()
    for i in selected:
        batch_epub_list.delete(i)

def clear_batch_list():
    """清空批量转换列表"""
    batch_epub_list.delete(0, "end")

ttk.Button(batch_buttons_frame, text="添加文件", command=add_batch_epub_files, width=12).grid(row=0, column=0, padx=4)
ttk.Button(batch_buttons_frame, text="移除选中", command=remove_batch_selected, width=12).grid(row=0, column=1, padx=4)
ttk.Button(batch_buttons_frame, text="清空列表", command=clear_batch_list, width=12).grid(row=0, column=2, padx=4)

# 批量转换参数设置
ttk.Label(batch_epub_frame, text="统一纸张设置").grid(row=2, column=0, sticky="w", padx=8, pady=6)
batch_epub_paper_var = tk.StringVar(value="a4")
batch_epub_paper_combo = ttk.Combobox(batch_epub_frame, textvariable=batch_epub_paper_var, state="readonly", width=12,
                                    values=("a4", "a5", "letter", "legal"))
batch_epub_paper_combo.grid(row=2, column=1, sticky="w", padx=4)

# 批量输出路径设置
ttk.Label(batch_epub_frame, text="输出目录").grid(row=3, column=0, sticky="w", padx=8, pady=6)
batch_output_dir_entry = ttk.Entry(batch_epub_frame)
batch_output_dir_entry.grid(row=3, column=1, sticky="ew", padx=4)

def select_batch_output_dir():
    """选择批量转换的输出目录"""
    directory = filedialog.askdirectory(title="选择输出目录")
    if directory:
        batch_output_dir_entry.delete(0, tk.END)
        batch_output_dir_entry.insert(0, directory)

ttk.Button(batch_epub_frame, text="浏览...", command=select_batch_output_dir, width=10).grid(row=3, column=2, padx=8)

# 文件名规则设置
ttk.Label(batch_epub_frame, text="文件名规则").grid(row=4, column=0, sticky="w", padx=8, pady=6)
batch_filename_var = tk.StringVar(value="{name}.pdf")
batch_filename_entry = ttk.Entry(batch_epub_frame, textvariable=batch_filename_var, width=40)
batch_filename_entry.grid(row=4, column=1, sticky="w", padx=4)

# 开始批量转换按钮
def run_batch_epub_convert():
    """执行批量 EPUB 转换"""
    epub_files = list(batch_epub_list.get(0, "end"))
    output_dir = batch_output_dir_entry.get().strip()
    paper = batch_epub_paper_var.get().strip() or "a4"
    filename_template = batch_filename_var.get().strip() or "{name}.pdf"
    
    if not epub_files:
        messagebox.showerror("错误", "请先添加 EPUB 文件到批量转换列表！")
        return
    
    if not output_dir:
        messagebox.showerror("错误", "请选择输出目录！")
        return
    
    def task():
        try:
            ctx = build_tk_task_context()
            batch_epub_to_pdf(ctx, epub_files, output_dir, paper, filename_template)
        except Exception as e:
            post_error(e)
    
    start_running_ui()
    threading.Thread(target=task, daemon=True).start()

batch_convert_btn = ttk.Button(batch_epub_frame, text="开始批量转换", command=run_batch_epub_convert, width=18)
batch_convert_btn.grid(row=5, column=2, padx=8, pady=6)

# 状态栏
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
toolbar = ttk.Frame(root, padding=(12,6))
toolbar.grid(row=4, column=0, sticky="ew")
toolbar.columnconfigure(10, weight=1)

ttk.Label(toolbar, text="范围助手:").grid(row=0, column=0, padx=(0,6))
ttk.Button(toolbar, text="每N页拆分", command=helper_every_n_pages).grid(row=0, column=1, padx=4)
ttk.Button(toolbar, text="均分为K份", command=helper_equal_k_parts).grid(row=0, column=2, padx=4)
ttk.Button(toolbar, text="清空范围", command=clear_ranges).grid(row=0, column=3, padx=4)

# 模板输入
ttk.Label(toolbar, text="命名模板").grid(row=0, column=4, padx=(12,4))
name_template_entry = ttk.Entry(toolbar, textvariable=name_template_var, width=26)
name_template_entry.grid(row=0, column=5, padx=2)

# 语言切换与最近
# language_var = tk.StringVar(value=LANG)
# ttk.Label(toolbar, text=T("language")).grid(row=0, column=8, padx=(12,2))
# ttk.Button(toolbar, text=T("zh"), command=lambda: set_language("zh"), width=4).grid(row=0, column=9, padx=2)
# ttk.Button(toolbar, text=T("en"), command=lambda: set_language("en"), width=4).grid(row=0, column=10, padx=2)

recent_btn = ttk.Menubutton(toolbar, text=T("recent"))
recent_menu = tk.Menu(recent_btn, tearoff=0)
recent_btn["menu"] = recent_menu
recent_btn.grid(row=0, column=11, padx=(12,2))

# 控件集合（执行期间禁用）
controls_to_toggle = []
for w in [input_entry, output_entry, ranges_entry, chapters_text]:
    controls_to_toggle.append(w)
for parent in [files_frame, split_frame, merge_frame, toolbar]:
    for child in parent.winfo_children():
        if isinstance(child, ttk.Button) or isinstance(child, ttk.Entry) or isinstance(child, tk.Text):
            controls_to_toggle.append(child)

# 将 EPUB 区域控件也加入可禁用列表
for child in epub_frame.winfo_children():
    if isinstance(child, ttk.Button) or isinstance(child, ttk.Entry) or isinstance(child, ttk.Combobox):
        controls_to_toggle.append(child)

# 将批量 EPUB 区域控件也加入可禁用列表
for child in batch_epub_frame.winfo_children():
    if isinstance(child, ttk.Button) or isinstance(child, ttk.Entry) or isinstance(child, ttk.Combobox) or isinstance(child, tk.Listbox):
        controls_to_toggle.append(child)

# 进度队列与取消标志
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
