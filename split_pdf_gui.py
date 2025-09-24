import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PyPDF2 import PdfReader, PdfWriter
import os
import platform
import threading
import queue
import json
import subprocess
import sys

# 可选：拖拽支持（如果已安装 tkinterdnd2）
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES  # type: ignore
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False

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

def parse_ranges(ranges_str):
    """解析输入的页码范围字符串，例如 '1-3,5,7-9'"""
    ranges = []
    # 同时支持中文逗号与英文逗号分隔
    normalized = ranges_str.replace("，", ",").strip()
    if not normalized:
        return ranges
    parts = normalized.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start, end = int(start_str), int(end_str)
                if start > end:
                    start, end = end, start
                ranges.append((start, end))
            except ValueError:
                continue
        elif part.isdigit():
            page = int(part)
            ranges.append((page, page))
    return ranges

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
    ranges = parse_ranges(page_ranges_str)
    if not ranges:
        messagebox.showerror("错误", "请输入有效的页码范围！")
        return
    reader = PdfReader(input_file)
    total = len(reader.pages)
    lines = []
    valid_count = 0
    for idx, (start, end) in enumerate(ranges, start=1):
        s = max(1, start)
        e = min(total, end)
        if s > e:
            lines.append(f"{idx}) {start}-{end} 超出范围，跳过")
            continue
        pages = e - s + 1
        lines.append(f"{idx}) {s}-{e} （{pages} 页）")
        valid_count += 1
    if valid_count == 0:
        messagebox.showerror("错误", "所有范围均无效，请检查输入。")
        return
    header = f"将生成 {valid_count} 个文件：\n"
    messagebox.showinfo("预览拆分结果", header + "\n" + "\n".join(lines))

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
    except Exception:
        pages_var.set("总页数：-")
        status_var.set("载入失败，请重新选择")
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
            do_split_with_progress(input_file, output_file, ranges)
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
            do_split_each_with_progress(input_file, output_file)
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

def open_merge_manager():
    dlg = tk.Toplevel(root)
    dlg.title("合并管理器")
    dlg.geometry("560x360")
    dlg.grab_set()

    frame = ttk.Frame(dlg, padding=10)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(0, weight=1)

    lb = tk.Listbox(frame, selectmode=tk.EXTENDED)
    lb.grid(row=0, column=0, columnspan=2, sticky="nsew")

    btns = ttk.Frame(frame)
    btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)
    for i in range(8):
        btns.columnconfigure(i, weight=1)

    def add_files():
        items = filedialog.askopenfilenames(title="选择 PDF", filetypes=[("PDF files", "*.pdf")])
        for it in items:
            lb.insert("end", it)

    def remove_sel():
        sel = list(lb.curselection())
        sel.reverse()
        for i in sel:
            lb.delete(i)

    def move_up():
        sel = list(lb.curselection())
        if not sel:
            return
        for i in sel:
            if i == 0:
                continue
            txt = lb.get(i)
            lb.delete(i)
            lb.insert(i-1, txt)
        lb.selection_clear(0, "end")
        for i in [max(0, s-1) for s in sel]:
            lb.selection_set(i)

    def move_down():
        sel = list(lb.curselection())
        if not sel:
            return
        n = lb.size()
        for i in reversed(sel):
            if i >= n-1:
                continue
            txt = lb.get(i)
            lb.delete(i)
            lb.insert(i+1, txt)
        lb.selection_clear(0, "end")
        for i in [min(n-1, s+1) for s in sel]:
            lb.selection_set(i)

    def clear_all():
        lb.delete(0, "end")

    def on_ok():
        files = list(lb.get(0, "end"))
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
        dlg.destroy()

    # 简单拖拽排序
    drag_data = {"index": None}
    def on_start_drag(event):
        drag_data["index"] = lb.nearest(event.y)
    def on_drag_motion(event):
        idx = drag_data.get("index")
        if idx is None:
            return
        i = lb.nearest(event.y)
        if i != idx and 0 <= idx < lb.size():
            txt = lb.get(idx)
            lb.delete(idx)
            lb.insert(i, txt)
            lb.selection_clear(0, "end")
            lb.selection_set(i)
            drag_data["index"] = i
    lb.bind("<Button-1>", on_start_drag)
    lb.bind("<B1-Motion>", on_drag_motion)

    ttk.Button(btns, text="添加文件", command=add_files).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="移除选中", command=remove_sel).grid(row=0, column=1, padx=4)
    ttk.Button(btns, text="上移", command=move_up).grid(row=0, column=2, padx=4)
    ttk.Button(btns, text="下移", command=move_down).grid(row=0, column=3, padx=4)
    ttk.Button(btns, text="清空", command=clear_all).grid(row=0, column=4, padx=4)
    ttk.Separator(btns).grid(row=0, column=5, sticky="ew", padx=8)
    ttk.Button(btns, text="确定合并", style="Accent.TButton", command=on_ok).grid(row=0, column=6, padx=4)
    ttk.Button(btns, text="取消", command=dlg.destroy).grid(row=0, column=7, padx=4)

# 近期文件
recent_files = []

def add_recent_file(path: str):
    global recent_files
    if not path:
        return
    path = os.path.abspath(path)
    if path in recent_files:
        recent_files.remove(path)
    recent_files.insert(0, path)
    recent_files = recent_files[:8]
    update_recent_menu()
    save_settings()

def open_recent(idx: int):
    if 0 <= idx < len(recent_files):
        set_input_file(recent_files[idx])

# 语言切换（简单：更新标题并提示重启以完全生效）
def set_language(new_lang: str):
    global LANG
    LANG = new_lang
    root.title(T("title"))
    save_settings()
    try:
        messagebox.showinfo("Info", "语言已切换，下次启动将完全生效。/ Language changed, restart to fully apply.")
    except Exception:
        pass

# 命名模板
def sanitize_filename(name: str) -> str:
    bad = '\\/:*?"<>|'
    for ch in bad:
        name = name.replace(ch, '_')
    return name

def render_template(base_name: str, start: int, end: int, index: int, template_text: str) -> str:
    if not template_text:
        template_text = "{name}_{start}-{end}.pdf"
    try:
        fname = template_text.format(name=base_name, start=start, end=end, index=index)
    except Exception:
        fname = f"{base_name}_{start}-{end}.pdf"
    return sanitize_filename(fname)

def helper_every_n_pages():
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请先选择输入 PDF。")
        return
    try:
        n = simpledialog.askinteger("每N页拆分", "请输入 N (>=1):", minvalue=1)
        if not n:
            return
        reader = PdfReader(input_file)
        total = len(reader.pages)
        parts = []
        start = 1
        while start <= total:
            end = min(start + n - 1, total)
            parts.append(f"{start}-{end}")
            start = end + 1
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ", ".join(parts))
        status_var.set(f"已按每{n}页生成 {len(parts)} 段范围")
    except Exception as e:
        messagebox.showerror("错误", str(e))

def helper_equal_k_parts():
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请先选择输入 PDF。")
        return
    try:
        k = simpledialog.askinteger("均分为K份", "请输入 K (>=1):", minvalue=1)
        if not k:
            return
        reader = PdfReader(input_file)
        total = len(reader.pages)
        base = total // k
        rem = total % k
        parts = []
        start = 1
        for i in range(k):
            size = base + (1 if i < rem else 0)
            end = start + size - 1
            parts.append(f"{start}-{end}")
            start = end + 1
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ", ".join(parts))
        status_var.set(f"已均分为 {k} 份")
    except Exception as e:
        messagebox.showerror("错误", str(e))

def clear_ranges():
    ranges_entry.delete(0, tk.END)
    ranges_entry.insert(0, RANGES_PLACEHOLDER)
    status_var.set("已清空范围")

def toggle_theme_dark():
    theme_dark_var.set(True)
    set_theme(dark=True)

def toggle_theme_light():
    theme_dark_var.set(False)
    set_theme(dark=False)

def set_theme(dark: bool):
    """切换主题：浅色=系统主题；深色=自定义配色。
    修复“点浅色页面仍然变黑”的问题，并让暗色更协调。
    """
    try:
        global style
        if dark:
            # 使用一个稳定主题作为暗色基底
            try:
                style.theme_use(DARK_THEME)
            except Exception:
                pass
            bg = "#1f2330"
            fg = "#e6e6e6"
            subbg = "#2a2f3a"
            accent = "#539bf5"
            root.configure(bg=bg)
            style.configure("TFrame", background=bg)
            style.configure("TLabelframe", background=bg, foreground=fg)
            style.configure("TLabelframe.Label", background=bg, foreground=fg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TEntry", fieldbackground=subbg, foreground=fg)
            # 普通按钮：深色底、浅色字，悬停变亮，禁用变灰
            style.configure("TButton", background=subbg, foreground=fg, padding=6)
            style.map(
                "TButton",
                background=[("active", "#3a4150"), ("!active", subbg), ("disabled", "#2a2f3a")],
                foreground=[("disabled", "#8a8f98"), ("!disabled", fg)],
            )
            # 强调按钮：用于主要动作
            style.configure("Accent.TButton", background=accent, foreground="#0b1320", padding=6)
            style.map(
                "Accent.TButton",
                background=[("active", "#6aa8ff"), ("!active", accent), ("disabled", "#3a4760")],
                foreground=[("disabled", "#c7cfdb"), ("!disabled", "#0b1320")],
            )
            style.configure("TSeparator", background=subbg)
            style.configure("Horizontal.TProgressbar", troughcolor=subbg, background=accent)
            status_bar.configure(background=bg, foreground=fg)
        else:
            # 重新创建 Style 并切回浅色主题，清除所有暗色覆盖
            style = ttk.Style()
            try:
                style.theme_use(LIGHT_THEME)
            except Exception:
                pass
            # 恢复根背景与状态栏为浅色
            fallback_bg = style.lookup("TFrame", "background") or DEFAULT_BG
            fallback_fg = style.lookup("TLabel", "foreground") or "black"
            root.configure(bg=fallback_bg)
            status_bar.configure(background=fallback_bg, foreground=fallback_fg)
        save_settings()
    except Exception:
        pass

def save_settings():
    try:
        dark_val = bool(theme_dark_var.get())
    except Exception:
        dark_val = False
    data = {
        "input": input_entry.get().strip(),
        "output": output_entry.get().strip(),
        "dark": dark_val,
        "lang": LANG,
        "recent": recent_files,
        "template": name_template_var.get() if 'name_template_var' in globals() else "{name}_{start}-{end}.pdf",
    }
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_settings():
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if data.get("input"):
                    input_entry.insert(0, data.get("input"))
                if data.get("output"):
                    output_entry.insert(0, data.get("output"))
                dark = bool(data.get("dark", False))
                try:
                    theme_dark_var.set(dark)
                except Exception:
                    pass
                set_theme(dark)
                global LANG, recent_files
                LANG = data.get("lang", LANG)
                recent_files = data.get("recent", []) or []
                update_recent_menu()
                # 模板
                tmpl = data.get("template")
                if tmpl and 'name_template_var' in globals():
                    name_template_var.set(tmpl)
    except Exception:
        pass

def post_progress(pct: float, text: str):
    progress_queue.put(("progress", pct, text))

def post_done(msg: str, open_paths=None):
    progress_queue.put(("done", msg, open_paths))

def post_error(err: Exception):
    progress_queue.put(("error", str(err)))

def poll_queue():
    try:
        while True:
            item = progress_queue.get_nowait()
            kind = item[0]
            if kind == "progress":
                pct, text = item[1], item[2]
                progress_var.set(int(pct))
                progress_bar["value"] = pct
                status_var.set(text)
            elif kind == "done":
                msg, paths = item[1], item[2]
                finish_running_ui()
                messagebox.showinfo("完成", msg)
                if paths:
                    if messagebox.askyesno("打开文件夹", "是否打开输出文件夹？"):
                        folder = os.path.dirname(paths[0]) if isinstance(paths, list) else os.path.dirname(paths)
                        open_folder(folder)
            elif kind == "error":
                finish_running_ui()
                messagebox.showerror("错误", item[1])
    except queue.Empty:
        pass
    root.after(120, poll_queue)

def update_recent_menu():
    try:
        recent_menu.delete(0, "end")
        if not recent_files:
            recent_menu.add_command(label="-", state="disabled")
        else:
            for i, path in enumerate(recent_files):
                display = (os.path.basename(path) + "  ·  " + os.path.dirname(path))
                recent_menu.add_command(label=display, command=lambda idx=i: open_recent(idx))
    except Exception:
        pass

def start_running_ui():
    global cancel_requested
    cancel_requested = False
    for w in controls_to_toggle:
        try:
            w.configure(state="disabled")
        except Exception:
            pass
    cancel_btn.grid()
    progress_bar.grid()
    progress_bar["value"] = 0
    progress_var.set(0)
    status_var.set("执行中...")

def finish_running_ui():
    for w in controls_to_toggle:
        try:
            w.configure(state="normal")
        except Exception:
            pass
    cancel_btn.grid_remove()
    status_var.set("完成")
    save_settings()

def do_split_with_progress(input_file: str, output_file: str, ranges):
    reader = PdfReader(input_file)
    total_pages = len(reader.pages)
    # compute total steps
    pages_to_write = 0
    for start, end in ranges:
        s = max(1, start)
        e = min(total_pages, end)
        if s <= e:
            pages_to_write += (e - s + 1)
    if pages_to_write == 0:
        raise ValueError("没有有效页可导出")

    if len(ranges) == 1:
        start, end = ranges[0]
        s = max(1, start)
        e = min(total_pages, end)
        writer = PdfWriter()
        step = 0
        for page_num in range(s - 1, e):
            if cancel_requested:
                post_done("已取消", None)
                return
            writer.add_page(reader.pages[page_num])
            step += 1
            post_progress(step * 100.0 / pages_to_write, f"正在写入第 {step}/{pages_to_write} 页")
        # 单段也允许使用模板（若用户自定义了不同扩展名则仍以模板为准）
        base_dir = os.path.dirname(output_file) or os.getcwd()
        base_name = os.path.splitext(os.path.basename(output_file))[0]
        fname = render_template(base_name, s, e, 1, name_template_var.get())
        out_path = os.path.join(base_dir, fname)
        with open(out_path, "wb") as f:
            writer.write(f)
        post_done(f"已导出文件：{out_path}", [out_path])
        return

    base_dir = os.path.dirname(output_file) or os.getcwd()
    base_name = os.path.splitext(os.path.basename(output_file))[0]
    step = 0
    exported = []
    for start, end in ranges:
        s = max(1, start)
        e = min(total_pages, end)
        if s > e:
            continue
        writer = PdfWriter()
        for page_num in range(s - 1, e):
            if cancel_requested:
                post_done("已取消", None)
                return
            writer.add_page(reader.pages[page_num])
            step += 1
            post_progress(step * 100.0 / pages_to_write, f"正在写入第 {step}/{pages_to_write} 页")
        fname = render_template(base_name, s, e, len(exported)+1, name_template_var.get())
        out_path = os.path.join(base_dir, fname)
        with open(out_path, "wb") as f:
            writer.write(f)
        exported.append(out_path)
    if not exported:
        raise ValueError("没有有效的页码范围可导出")
    post_done("已导出以下文件：\n" + "\n".join(exported), exported)

def do_split_each_with_progress(input_file: str, output_file: str):
    reader = PdfReader(input_file)
    total = len(reader.pages)
    base_name = os.path.splitext(output_file)[0]
    for i, page in enumerate(reader.pages, start=1):
        if cancel_requested:
            post_done("已取消", None)
            return
        writer = PdfWriter()
        writer.add_page(page)
        file_path = f"{base_name}_page_{i}.pdf"
        with open(file_path, "wb") as f:
            writer.write(f)
        post_progress(i * 100.0 / total, f"正在导出第 {i}/{total} 页")
    post_done("已拆分为单页 PDF 文件", [base_name + "_page_1.pdf"])  # 用第一页路径定位目录

def merge_pdfs_with_progress(file_list, output_file):
    # 预统计总页数
    total = 0
    for p in file_list:
        try:
            total += len(PdfReader(p).pages)
        except Exception:
            pass
    writer = PdfWriter()
    added = 0
    for path in file_list:
        reader = PdfReader(path)
        for page in reader.pages:
            if cancel_requested:
                post_done("已取消", None)
                return
            writer.add_page(page)
            added += 1
            if total:
                post_progress(added * 100.0 / total, f"合并进度 {added}/{total}")
    with open(output_file, "wb") as f:
        writer.write(f)
    post_done(f"已合并 {len(file_list)} 个文件，共 {added} 页\n输出：{output_file}", [output_file])

# ================= 界面部分 =================
root = tk.Tk()
root.title("PDF 工具箱：拆分 / 合并 / 预览")
root.geometry("720x360")
root.minsize(680, 360)

# 主题样式
style = ttk.Style()
AVAILABLE_THEMES = set(style.theme_names())
LIGHT_THEME = "vista" if (platform.system().lower().startswith("win") and "vista" in AVAILABLE_THEMES) else ("default" if "default" in AVAILABLE_THEMES else style.theme_use())
DARK_THEME = "clam" if "clam" in AVAILABLE_THEMES else LIGHT_THEME
try:
    style.theme_use(LIGHT_THEME)
except Exception:
    pass

# 主容器
container = ttk.Frame(root, padding=12)
container.grid(row=0, column=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
container.columnconfigure(1, weight=1)

# 文件区域
files_frame = ttk.LabelFrame(container, text="文件")
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
ttk.Label(files_frame, textvariable=pages_var, foreground="#666").grid(row=2, column=1, sticky="w", padx=4, pady=(0,6))

# 拆分区域
split_frame = ttk.LabelFrame(container, text="拆分")
split_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
split_frame.columnconfigure(1, weight=1)

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

ttk.Button(split_frame, text="预览拆分结果", command=run_preview, width=16, style="Accent.TButton").grid(row=0, column=2, padx=8)
ttk.Separator(split_frame).grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
ttk.Button(split_frame, text="按范围拆分", command=run_split, width=18, style="Accent.TButton").grid(row=2, column=1, sticky="w", padx=4, pady=6)
ttk.Button(split_frame, text="拆成单页", command=run_split_each, width=18).grid(row=2, column=1, sticky="e", padx=4, pady=6)

# 合并区域
merge_frame = ttk.LabelFrame(container, text="合并")
merge_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
ttk.Button(merge_frame, text="合并 PDF", command=run_merge, width=18, style="Accent.TButton").grid(row=0, column=0, padx=8, pady=6)
ttk.Button(merge_frame, text="打开输出目录", command=open_output_dir, width=18).grid(row=0, column=1, padx=8, pady=6)

# 状态栏
status_var = tk.StringVar(value="就绪")
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", padding=(10,4))
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
cancel_btn.grid(row=1, column=0, sticky="e", padx=12)
cancel_btn.grid_remove()

# 顶部工具栏（主题切换、范围助手）
toolbar = ttk.Frame(root, padding=(12,4))
toolbar.grid(row=1, column=0, sticky="ew")
toolbar.columnconfigure(10, weight=1)

ttk.Label(toolbar, text="范围助手:").grid(row=0, column=0, padx=(0,6))
ttk.Button(toolbar, text="每N页拆分", command=helper_every_n_pages).grid(row=0, column=1, padx=4)
ttk.Button(toolbar, text="均分为K份", command=helper_equal_k_parts).grid(row=0, column=2, padx=4)
ttk.Button(toolbar, text="清空范围", command=clear_ranges).grid(row=0, column=3, padx=4)

# 模板输入
ttk.Label(toolbar, text="命名模板").grid(row=0, column=4, padx=(12,4))
name_template_var = tk.StringVar(value="{name}_{start}-{end}.pdf")
name_template_entry = ttk.Entry(toolbar, textvariable=name_template_var, width=26)
name_template_entry.grid(row=0, column=5, padx=2)

# 语言切换与最近
language_var = tk.StringVar(value=LANG)
ttk.Label(toolbar, text=T("language")).grid(row=0, column=8, padx=(12,2))
ttk.Button(toolbar, text=T("zh"), command=lambda: set_language("zh"), width=4).grid(row=0, column=9, padx=2)
ttk.Button(toolbar, text=T("en"), command=lambda: set_language("en"), width=4).grid(row=0, column=10, padx=2)

recent_btn = ttk.Menubutton(toolbar, text=T("recent"))
recent_menu = tk.Menu(recent_btn, tearoff=0)
recent_btn["menu"] = recent_menu
recent_btn.grid(row=0, column=11, padx=(12,2))

# 控件集合（执行期间禁用）
controls_to_toggle = []
for w in [input_entry, output_entry, ranges_entry]:
    controls_to_toggle.append(w)
for parent in [files_frame, split_frame, merge_frame, toolbar]:
    for child in parent.winfo_children():
        if isinstance(child, ttk.Button) or isinstance(child, ttk.Entry):
            controls_to_toggle.append(child)

# 进度队列与取消标志
progress_queue: "queue.Queue" = queue.Queue()
cancel_requested = False

# 设置文件
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

# 启动轮询与加载设置
root.after(150, poll_queue)
load_settings()

# 拖拽到输入框（可选）
if DND_AVAILABLE:
    try:
        def _handle_drop(event):
            data = event.data
            # Windows 下可能是大括号包裹路径或多个文件
            if data.startswith("{") and data.endswith("}"):
                data = data[1:-1]
            first = data.split() [0]
            if first.lower().endswith(".pdf") and os.path.exists(first):
                set_input_file(first)
        input_entry.drop_target_register(DND_FILES)
        input_entry.dnd_bind('<<Drop>>', _handle_drop)
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
