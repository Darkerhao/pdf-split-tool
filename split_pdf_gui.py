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
import shutil
import re
import traceback

from task_context import TaskContext, TaskCancelledError
from pdf_split_task import split_pdf_by_ranges

# 尝试导入 EPUB 转换所需的库
try:
    from ebooklib import epub
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, A5, letter, legal
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import html2text
    EPUB_LIBS_AVAILABLE = True
except ImportError:
    EPUB_LIBS_AVAILABLE = False

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
    """打开PDF预览窗口"""
    if not pdf_path or not os.path.exists(pdf_path):
        messagebox.showerror("错误", "请先选择有效的 PDF 文件！")
        return
    
    try:
        # 创建预览窗口
        preview_window = tk.Toplevel(root)
        preview_window.title(f"PDF 预览 - {os.path.basename(pdf_path)}")
        preview_window.geometry("800x600")
        preview_window.minsize(600, 400)
        
        # 创建主框架
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))
        
        # 页码显示
        page_var = tk.StringVar(value="第 1 页 / 共 0 页")
        page_label = ttk.Label(toolbar_frame, textvariable=page_var)
        page_label.pack(side="left", padx=10)
        
        # 导航按钮
        nav_frame = ttk.Frame(toolbar_frame)
        nav_frame.pack(side="left", padx=10)
        
        ttk.Button(nav_frame, text="首页", command=lambda: show_page(0)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="上一页", command=lambda: show_page(current_page - 1)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="下一页", command=lambda: show_page(current_page + 1)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="末页", command=lambda: show_page(total_pages - 1)).pack(side="left", padx=2)
        
        # 旋转按钮
        rotate_frame = ttk.Frame(toolbar_frame)
        rotate_frame.pack(side="left", padx=10)
        
        ttk.Button(rotate_frame, text="向左旋转", command=lambda: rotate_page(-90)).pack(side="left", padx=2)
        ttk.Button(rotate_frame, text="向右旋转", command=lambda: rotate_page(90)).pack(side="left", padx=2)
        
        # 缩放控制
        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side="right", padx=10)
        
        zoom_var = tk.DoubleVar(value=1.0)
        ttk.Label(zoom_frame, text="缩放:").pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="50%", command=lambda: set_zoom(0.5)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="75%", command=lambda: set_zoom(0.75)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="100%", command=lambda: set_zoom(1.0)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="150%", command=lambda: set_zoom(1.5)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="200%", command=lambda: set_zoom(2.0)).pack(side="left", padx=2)
        
        # 初始化全屏变量
        fullscreen = False
        
        # 切换全屏函数（在使用前定义）
        def toggle_fullscreen():
            nonlocal fullscreen
            fullscreen = not fullscreen
            preview_window.attributes("-fullscreen", fullscreen)
        
        # 全屏按钮
        ttk.Button(toolbar_frame, text="全屏", command=toggle_fullscreen).pack(side="right", padx=10)
        
        # 创建Canvas用于显示PDF页面
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="#ffffff", bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # 初始化变量
        current_page = 0
        total_pages = 0
        zoom = 1.0
        rotation = 0
        doc = None
        
        # 显示指定页码
        def show_page(page_num):
            nonlocal current_page
            if page_num < 0:
                page_num = 0
            elif page_num >= total_pages:
                page_num = total_pages - 1
            
            current_page = page_num
            page_var.set(f"第 {current_page + 1} 页 / 共 {total_pages} 页")
            
            # 清除Canvas
            canvas.delete("all")
            
            if doc:
                # 使用PyMuPDF渲染
                try:
                    page = doc.load_page(current_page)
                    # 应用旋转
                    page.set_rotation(rotation % 360)
                    
                    # 计算缩放后的尺寸
                    zoom_matrix = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=zoom_matrix)
                    
                    # 转换为PIL图像
                    from PIL import Image, ImageTk
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # 转换为PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # 显示图像
                    canvas.create_image(0, 0, anchor="nw", image=photo)
                    canvas.image = photo  # 保持引用
                    
                    # 更新滚动区域
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                except Exception as e:
                    canvas.create_text(400, 300, text=f"渲染失败: {str(e)}", 
                                      font=("Segoe UI", 12), fill="red", justify="center")
            else:
                # 简化模式
                try:
                    from PIL import Image, ImageTk, ImageDraw
                    
                    # 创建一个简单的图像
                    img = Image.new('RGB', (800, 600), color='#ffffff')
                    d = ImageDraw.Draw(img)
                    d.text((100, 100), f"PDF页面 {current_page + 1}", fill=(0, 0, 0))
                    d.text((100, 120), f"总页数: {total_pages}", fill=(0, 0, 0))
                    d.text((100, 140), "注意: 这是一个简化的PDF预览", fill=(0, 0, 0))
                    d.text((100, 160), "完整的PDF渲染需要安装PyMuPDF库", fill=(0, 0, 0))
                    d.text((100, 180), "请运行: pip install PyMuPDF", fill=(0, 0, 0))
                    
                    # 缩放图像
                    width, height = img.size
                    new_width = int(width * zoom)
                    new_height = int(height * zoom)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 转换为PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # 显示图像
                    canvas.create_image(0, 0, anchor="nw", image=photo)
                    canvas.image = photo  # 保持引用
                    
                    # 更新滚动区域
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                except ImportError:
                    # 如果缺少必要的库，显示文本信息
                    canvas.create_text(400, 300, text=f"PDF页面 {current_page + 1}\n总页数: {total_pages}\n\n注意: 无法渲染PDF页面\n请安装必要的库: Pillow, PyMuPDF", 
                                      font=("Segoe UI", 12), fill="black", justify="center")
                except Exception as e:
                    canvas.create_text(400, 300, text=f"无法显示页面: {str(e)}", 
                                      font=("Segoe UI", 12), fill="red", justify="center")
        
        # 设置缩放级别
        def set_zoom(level):
            nonlocal zoom
            zoom = level
            show_page(current_page)
        
        # 旋转页面
        def rotate_page(angle):
            nonlocal rotation
            rotation += angle
            show_page(current_page)
        
        # 尝试使用PyMuPDF打开PDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
        except ImportError:
            # 如果没有PyMuPDF，使用简化模式
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            doc = None
        except Exception as e:
            messagebox.showerror("错误", f"无法打开PDF文件: {str(e)}")
            return
        
        # 初始显示第一页
        show_page(0)
        
        # 绑定键盘事件
        def on_key_press(event):
            if event.keysym == "Left":
                show_page(current_page - 1)
            elif event.keysym == "Right":
                show_page(current_page + 1)
            elif event.keysym == "Home":
                show_page(0)
            elif event.keysym == "End":
                show_page(total_pages - 1)
            elif event.keysym == "plus":
                set_zoom(min(3.0, zoom + 0.1))
            elif event.keysym == "minus":
                set_zoom(max(0.1, zoom - 0.1))
            elif event.keysym == "F11":
                toggle_fullscreen()
        
        preview_window.bind("<KeyPress>", on_key_press)
        
        # 绑定鼠标滚轮事件
        def on_mouse_wheel(event):
            if event.delta > 0:
                # 放大
                new_zoom = min(3.0, zoom + 0.1)
                set_zoom(new_zoom)
            else:
                # 缩小
                new_zoom = max(0.1, zoom - 0.1)
                set_zoom(new_zoom)
        
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        
        # 窗口关闭时释放资源
        def on_close():
            if doc:
                doc.close()
            preview_window.destroy()
        
        preview_window.protocol("WM_DELETE_WINDOW", on_close)
        
    except Exception as e:
        messagebox.showerror("错误", f"打开PDF预览失败: {str(e)}")

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
    ttk.Button(btns, text="确定合并", command=on_ok).grid(row=0, column=6, padx=4)
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
    """切换主题：浅色=系统主题；深色=自定义配色。"""
    try:
        global style
        if dark:
            # 使用一个稳定主题作为暗色基底
            try:
                style.theme_use(DARK_THEME)
            except Exception:
                pass
            bg = COLORS["dark"]["bg"]
            fg = COLORS["dark"]["fg"]
            subbg = COLORS["dark"]["subbg"]
            accent = COLORS["dark"]["accent"]
            root.configure(bg=bg)
            style.configure("TFrame", background=bg)
            style.configure("TLabelframe", background=bg, foreground=fg, bordercolor=COLORS["dark"]["border"])
            style.configure("TLabelframe.Label", background=bg, foreground=fg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TEntry", fieldbackground=subbg, foreground=fg, bordercolor=COLORS["dark"]["border"])
            # 普通按钮：深色底、浅色字，悬停变亮，禁用变灰
            style.configure("TButton", background=subbg, foreground=fg, padding=8, bordercolor=COLORS["dark"]["border"])
            style.map(
                "TButton",
                background=[("active", "#3a4150"), ("!active", subbg), ("disabled", "#2a2f3a")],
                foreground=[("disabled", COLORS["dark"]["text_disabled"]), ("!disabled", fg)],
                bordercolor=[("active", accent), ("!active", COLORS["dark"]["border"])]
            )
            style.configure("TSeparator", background=COLORS["dark"]["border"])
            style.configure("Horizontal.TProgressbar", troughcolor=subbg, background=accent)
            style.configure("TCombobox", fieldbackground=subbg, foreground=fg, bordercolor=COLORS["dark"]["border"])
            style.configure("TMenubutton", background=subbg, foreground=fg, bordercolor=COLORS["dark"]["border"])
            status_bar.configure(background=bg, foreground=fg)
        else:
            # 重新创建 Style 并切回浅色主题，清除所有暗色覆盖
            style = ttk.Style()
            try:
                if platform.system().lower().startswith("win"):
                    style.theme_use('vista')
                else:
                    style.theme_use(LIGHT_THEME)
            except Exception:
                pass
            # 重置为默认浅色样式
            style.configure("TFrame", padding=6, borderwidth=0, background="#f0f0f0")
            style.configure("TLabelframe", padding=8, borderwidth=1, relief="solid", background="#f0f0f0")
            style.configure("TLabelframe.Label", font=("Arial", 10, "bold"), padding=(0, 0, 0, 5), background="#f0f0f0")
            style.configure("TButton", padding=6, font=("Arial", 10), background="#ffffff")
            style.configure("TEntry", padding=4, font=("Arial", 10), background="#ffffff")
            style.configure("TLabel", padding=4, font=("Arial", 10), background="#f0f0f0")
            style.configure("Horizontal.TProgressbar", thickness=8, background="#00ff00")
            style.configure("TSeparator", background="#d0d0d0")
            style.configure("TCombobox", padding=4, font=("Arial", 10), background="#ffffff")
            style.configure("TMenubutton", padding=4, font=("Arial", 10), background="#ffffff")
            # 恢复根背景与状态栏为浅色
            root.configure(bg="#f0f0f0")
            status_bar.configure(background="#f0f0f0", foreground="#000000")
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
        # EPUB 相关
        "epub_input": (epub_input_entry.get().strip() if 'epub_input_entry' in globals() else ""),
        "epub_output": (epub_output_entry.get().strip() if 'epub_output_entry' in globals() else ""),
        "epub_paper": (epub_paper_var.get().strip() if 'epub_paper_var' in globals() else "a4"),
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
                # EPUB 相关
                if data.get("epub_input") and 'epub_input_entry' in globals():
                    epub_input_entry.delete(0, tk.END)
                    epub_input_entry.insert(0, data.get("epub_input"))
                if data.get("epub_output") and 'epub_output_entry' in globals():
                    epub_output_entry.delete(0, tk.END)
                    epub_output_entry.insert(0, data.get("epub_output"))
                if 'epub_paper_var' in globals():
                    epub_paper_var.set(data.get("epub_paper", "a4") or "a4")
    except Exception:
        pass

def post_progress(pct: float, text: str):
    progress_queue.put(("progress", pct, text))

def post_done(msg: str, open_paths=None):
    progress_queue.put(("done", msg, open_paths))

def post_error(err: Exception):
    """优化的错误提示函数，提供用户友好的错误信息"""
    error_message = str(err)
    
    # 常见错误类型的用户友好提示
    friendly_messages = {
        "No module named": "缺少必要的依赖库，请运行以下命令安装：\npip install PyPDF2 ebooklib reportlab html2text Pillow",
        "No such file or directory": "文件不存在，请检查文件路径是否正确",
        "Permission denied": "权限不足，请检查文件或文件夹的访问权限",
        "Unsupported file format": "不支持的文件格式，请确保选择的是有效的 PDF 或 EPUB 文件",
        "Failed to read PDF": "无法读取 PDF 文件，可能是文件损坏或格式不兼容",
        "gbk codec can't decode": "文件编码错误，尝试使用其他编码方式打开文件",
        "Merge failed": "合并失败，请确保选择的文件都是有效的 PDF 文件",
    }
    
    # 查找匹配的友好提示
    friendly_message = None
    for key, msg in friendly_messages.items():
        if key in error_message:
            friendly_message = msg
            break
    
    if friendly_message:
        # 提供友好的错误提示
        error_details = traceback.format_exc() if isinstance(err, Exception) else str(err)
        post_error_with_details(f"操作失败：\n{friendly_message}\n\n详细信息：\n{error_details}\n\n请尝试上述解决方法或联系技术支持。")
    else:
        # 通用错误提示
        post_error_with_details(f"操作过程中发生错误：\n{error_message}\n\n请检查操作步骤是否正确，或尝试重启应用程序。\n\n如果问题持续存在，请联系技术支持。")

def post_error_with_details(detailed_message):
    """显示详细的错误信息"""
    progress_queue.put(("error", detailed_message))

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
    # 添加视觉反馈：短暂高亮进度条
    progress_bar.configure(style="Horizontal.TProgressbar")

def finish_running_ui():
    for w in controls_to_toggle:
        try:
            w.configure(state="normal")
        except Exception:
            pass
    cancel_btn.grid_remove()
    progress_bar.grid_remove()
    status_var.set("完成")
    save_settings()
    # 添加完成动画效果
    root.update()
    # 短暂显示成功状态
    status_var.set("操作已成功完成")
    root.after(2000, lambda: status_var.set("就绪"))

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

def find_ebook_convert() -> str:
    """查找 Calibre 的 ebook-convert 可执行文件路径。优先使用 PATH，其次尝试常见安装目录。"""
    path = shutil.which("ebook-convert")
    if path:
        return path
    candidates = [
        os.path.join("C:\\Program Files\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files (x86)\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files\\Calibre2", "ebook-convert.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return ""

def epub_to_pdf_python(
    ctx: TaskContext,
    epub_path: str, 
    pdf_path: str, 
    paper_size: str = "a4"
):
    """使用 Python 库将 EPUB 转换为 PDF（不依赖 Calibre）
    
    参数:
        ctx: 任务上下文，用于报告进度和状态
        epub_path: EPUB 文件路径
        pdf_path: PDF 输出路径
        paper_size: 纸张大小 (a4, a5, letter, legal)
    
    返回值:
        None
    
    异常:
        RuntimeError: 缺少必要的 Python 库
        Exception: 转换过程中的错误
    """
    if not EPUB_LIBS_AVAILABLE:
        raise RuntimeError("缺少必要的 Python 库\n请安装：pip install ebooklib reportlab html2text")
    
    # 纸张大小映射
    paper_sizes = {
        "a4": A4,
        "a5": A5, 
        "letter": letter,
        "legal": legal
    }
    page_size = paper_sizes.get(paper_size.lower(), A4)
    
    # 读取 EPUB
    ctx.report_progress(20, "正在读取 EPUB 文件...")
    book = epub.read_epub(epub_path)
    
    # 创建 PDF
    c = canvas.Canvas(pdf_path, pagesize=page_size)
    width, height = page_size
    
    # 设置字体，支持中文
    try:
        # 尝试使用支持中文的字体
        c.setFont("Helvetica", 12)
    except:
        try:
            # 尝试使用系统默认字体
            c.setFont("Arial", 12)
        except:
            c.setFont("Helvetica", 12)
    
    # 转换 HTML 为文本
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    
    y_position = height - 50
    line_height = 14
    margin = 50
    
    # 计算总章节数用于进度估算
    total_items = sum(1 for item in book.get_items() if item.get_type() == epub.ITEM_DOCUMENT)
    processed_items = 0
    
    for item in book.get_items():
        ctx.check_cancelled()
        
        if item.get_type() == epub.ITEM_DOCUMENT:
            processed_items += 1
            item_progress = (processed_items / total_items) * 60  # 60% 用于内容转换
            ctx.report_progress(20 + item_progress, f"正在处理章节 {processed_items}/{total_items}")
            
            # 获取章节内容，处理编码问题
            raw_content = item.get_content()
            content = None
            
            # 尝试多种编码，使用更安全的方法
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    content = raw_content.decode(encoding)
                    break
                except (UnicodeDecodeError, UnicodeError, LookupError):
                    continue
            
            # 如果所有编码都失败，使用忽略错误的方式
            if content is None:
                try:
                    content = raw_content.decode('utf-8', errors='ignore')
                except Exception:
                    # 最后的保险措施
                    content = str(raw_content, errors='ignore')
            
            # 转换为纯文本
            text = h.handle(content)
            # 清理文本
            text = re.sub(r'\n\s*\n', '\n\n', text)
            lines = text.split('\n')
            
            for line in lines:
                ctx.check_cancelled()
                
                line = line.strip()
                if not line:
                    y_position -= line_height
                    continue
                
                # 检查是否需要新页面
                if y_position < margin:
                    c.showPage()
                    y_position = height - 50
                
                # 处理长行，确保文本安全
                try:
                    # 清理文本，移除可能导致问题的字符
                    safe_line = line.replace('\x00', '').replace('\r', '').strip()
                    if not safe_line:
                        y_position -= line_height
                        continue
                    
                    if len(safe_line) > 80:
                        words = safe_line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line + " " + word) > 80:
                                if current_line:
                                    c.drawString(margin, y_position, current_line)
                                    y_position -= line_height
                                    if y_position < margin:
                                        c.showPage()
                                        y_position = height - 50
                                current_line = word
                            else:
                                current_line += (" " + word) if current_line else word
                        if current_line:
                            c.drawString(margin, y_position, current_line)
                            y_position -= line_height
                    else:
                        c.drawString(margin, y_position, safe_line)
                        y_position -= line_height
                except Exception as e:
                    # 如果单行处理失败，跳过这行
                    y_position -= line_height
                    continue
    
    ctx.report_progress(90, "正在保存 PDF 文件...")
    c.save()
    ctx.report_done(f"已完成 EPUB 转 PDF：{pdf_path}", [pdf_path])

def do_epub_convert_with_progress(
    ctx: TaskContext,
    epub_path: str, 
    pdf_path: str, 
    paper_size: str = "a4"
):
    """将 EPUB 转为 PDF，优先使用 Python 库，失败则尝试 Calibre。
    
    参数:
        ctx: 任务上下文，用于报告进度和状态
        epub_path: EPUB 文件路径
        pdf_path: PDF 输出路径
        paper_size: 纸张大小 (a4, a5, letter, legal)
    
    返回值:
        None
    
    异常:
        Exception: 转换过程中的错误
    """
    import traceback
    
    try:  # 最外层异常捕获
        python_error = None
        
        # 首先尝试使用 Python 库
        try:
            ctx.report_progress(10, f"尝试使用 Python 库转换... (库可用: {EPUB_LIBS_AVAILABLE})")
            epub_to_pdf_python(ctx, epub_path, pdf_path, paper_size)
            ctx.report_done(f"EPUB 文件 '{os.path.basename(epub_path)}' 已成功转换为 PDF。", [pdf_path])
            return
        except Exception as e:
            python_error = str(e)
            ctx.report_progress(20, f"Python 库转换失败：{python_error[:50]}...")
            # 继续尝试 Calibre
    
        # 尝试使用 Calibre
        exe = find_ebook_convert()
        if not exe:
            error_msg = "转换失败：\n"
            if python_error:
                error_msg += f"1. Python 库错误：{python_error}\n"
            error_msg += f"2. 未找到 Calibre ebook-convert\n\n"
            error_msg += "解决方案：\n"
            error_msg += "- 安装 Python 库：pip install ebooklib reportlab html2text\n"
            error_msg += "- 或安装 Calibre：https://calibre-ebook.com/download"
            ctx.report_error(error_msg)
            return
        
        # Calibre 转换逻辑
        os.makedirs(os.path.dirname(pdf_path) or os.getcwd(), exist_ok=True)
        args = [exe, epub_path, pdf_path, "--paper-size", paper_size]
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,  # 使用二进制模式读取
                bufsize=1
            )
        except Exception as e:
            ctx.report_error(f"启动 Calibre 转换失败：{str(e)}")
            return

        progress_pattern = re.compile(rb"(\d{1,3})%")  # 使用二进制模式匹配
        last_pct = -1
        while True:
            ctx.check_cancelled()
            if proc.poll() is not None:
                break
            line_bytes = proc.stdout.readline() if proc.stdout else b""
            if not line_bytes:
                continue
            # 尝试使用 UTF-8 解码，失败则使用忽略错误的方式
            try:
                line = line_bytes.decode('utf-8')
            except UnicodeDecodeError:
                line = line_bytes.decode('gbk', errors='ignore')
            except Exception:
                line = str(line_bytes, errors='ignore')
            m = re.search(r"(\d{1,3})%", line)
            if m:
                try:
                    pct = int(m.group(1))
                    if 0 <= pct <= 100 and pct != last_pct:
                        last_pct = pct
                        ctx.report_progress(pct, f"转换进度 {pct}%")
                except Exception:
                    pass
            else:
                # 非进度行，显示为状态文本（不过于频繁）
                if last_pct >= 0:
                    ctx.report_progress(last_pct, line.strip()[:80])

        code = proc.poll()
        if code == 0:
            ctx.report_done(f"已完成 EPUB 转 PDF：{pdf_path}", [pdf_path])
        else:
            ctx.report_error("Calibre 转换失败，请检查 EPUB 文件与输出路径是否有效。")
    
    except Exception as final_e:
        # 捕获任何未处理的异常
        error_details = traceback.format_exc()
        ctx.report_error(f"转换过程中发生意外错误：\n{final_e}\n\n详细信息：\n{error_details}\n\n请检查文件或尝试其他转换方式。")

def batch_epub_to_pdf(
    ctx: TaskContext,
    epub_files: list[str],
    output_dir: str,
    paper_size: str = "a4",
    filename_template: str = "{name}.pdf"
):
    """批量将 EPUB 文件转换为 PDF
    
    参数:
        ctx: 任务上下文，用于报告进度和状态
        epub_files: EPUB 文件路径列表
        output_dir: 输出目录
        paper_size: 纸张大小 (a4, a5, letter, legal)
        filename_template: 文件名模板，支持 {name} 占位符
    
    返回值:
        None
    
    异常:
        Exception: 转换过程中的错误
    """
    import traceback
    
    total_files = len(epub_files)
    if total_files == 0:
        ctx.report_done("没有 EPUB 文件需要转换", None)
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    failed_files = []
    success_files = []
    
    try:
        for index, epub_path in enumerate(epub_files):
            ctx.check_cancelled()
            
            file_name = os.path.basename(epub_path)
            
            # 为“单文件”构造一个子进度回调
            def make_sub_progress_callback(file_index):
                def _report(sub_progress: float, msg: str):
                    overall = (
                        (file_index + sub_progress / 100.0)
                        / total_files
                        * 100.0
                    )
                    ctx.report_progress(
                        overall,
                        f"[{file_index + 1}/{total_files}] {file_name}：{msg}"
                    )
                return _report
            
            # 为单文件转换创建子任务上下文
            sub_ctx = TaskContext(
                is_cancelled=ctx.is_cancelled,
                report_progress=make_sub_progress_callback(index),
                report_done=lambda *_: None,     # 单文件完成不直接通知 UI
                report_error=lambda err: ctx.report_error(err),
            )
            
            try:
                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(epub_path))[0]
                # 处理文件名模板
                try:
                    pdf_filename = filename_template.format(name=base_name)
                except Exception:
                    pdf_filename = f"{base_name}.pdf"
                
                # 清理文件名
                pdf_filename = sanitize_filename(pdf_filename)
                pdf_path = os.path.join(output_dir, pdf_filename)
                
                # 执行单个文件转换
                do_epub_convert_with_progress(sub_ctx, epub_path, pdf_path, paper_size)
                
                success_count += 1
                success_files.append(pdf_path)
                
            except Exception as e:
                failed_count += 1
                failed_files.append((epub_path, str(e)))
                sub_ctx.report_progress(100, f"转换失败：{str(e)}")
                # 继续处理下一个文件
                continue
        
        # 生成最终结果报告
        result_message = f"批量转换完成！\n"
        result_message += f"成功：{success_count} 个文件\n"
        result_message += f"失败：{failed_count} 个文件\n\n"
        
        if success_files:
            result_message += "成功转换的文件：\n"
            for i, file in enumerate(success_files[:5], 1):
                result_message += f"{i}. {os.path.basename(file)}\n"
            if len(success_files) > 5:
                result_message += f"... 等 {len(success_files) - 5} 个文件\n"
        
        if failed_files:
            result_message += "\n转换失败的文件：\n"
            for i, (file, error) in enumerate(failed_files[:5], 1):
                result_message += f"{i}. {os.path.basename(file)}\n   错误：{error[:100]}...\n"
            if len(failed_files) > 5:
                result_message += f"... 等 {len(failed_files) - 5} 个文件\n"
        
        ctx.report_progress(100, "批量转换完成")
        ctx.report_done(result_message, success_files[:1])  # 只返回第一个成功的文件用于打开目录
        
    except Exception as final_e:
        # 捕获任何未处理的异常
        error_details = traceback.format_exc()
        ctx.report_error(f"批量转换过程中发生意外错误：\n{final_e}\n\n详细信息：\n{error_details}\n\n请检查文件或尝试其他转换方式。")

# 主窗口初始化
if DND_AVAILABLE:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()
root.title("PDF 工具箱：拆分 / 合并 / 预览")
root.geometry("900x750")
root.minsize(900, 850)
root.maxsize(1000, 1600)

# 设置窗口图标（如果有）
try:
    # 这里可以添加图标设置代码
    pass
except Exception:
    pass

# 主题样式
style = ttk.Style()
AVAILABLE_THEMES = set(style.theme_names())
LIGHT_THEME = "vista" if (platform.system().lower().startswith("win") and "vista" in AVAILABLE_THEMES) else ("default" if "default" in AVAILABLE_THEMES else style.theme_use())
DARK_THEME = "clam" if "clam" in AVAILABLE_THEMES else LIGHT_THEME
try:
    style.theme_use(LIGHT_THEME)
except Exception:
    pass

# 现代化颜色方案
COLORS = {
    "light": {
        "bg": "#f5f5f5",
        "fg": "#1a1a1a",
        "subbg": "#ffffff",
        "accent": "#0078d4",
        "accent_hover": "#005a9e",
        "border": "#d0d0d0",
        "text_disabled": "#8a8d91",
        "success": "#107c10",
        "warning": "#ffb900",
        "error": "#d13438",
        "header": "#ffffff",
        "shadow": "#e0e0e0",
        "hover": "#f0f0f0"
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#e1e1e1",
        "subbg": "#252526",
        "accent": "#0e639c",
        "accent_hover": "#1177bb",
        "border": "#3e3e42",
        "text_disabled": "#6a6d70",
        "success": "#107c10",
        "warning": "#d83b01",
        "error": "#e81123",
        "header": "#2d2d30",
        "shadow": "#1a1a1a",
        "hover": "#2a2d2e"
    }
}

# 应用Windows风格样式
style = ttk.Style()
try:
    # 使用Windows默认主题
    if platform.system().lower().startswith("win"):
        style.theme_use('vista')
    else:
        style.theme_use('default')
except Exception:
    pass

# 设置Windows风格样式
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

# 选项卡样式
style.configure("TNotebook", background="#f0f0f0", borderwidth=1)
style.configure("TNotebook.Tab", padding=(12, 6), font=("Arial", 10), background="#e0e0e0", foreground="#000000")
style.map("TNotebook.Tab",
          background=[("active", "#ffffff"), ("!active", "#e0e0e0")],
          foreground=[("active", "#0078d4"), ("!active", "#000000")],
          relief=[("selected", "sunken"), ("!selected", "raised")])

# 设置窗口背景色
root.configure(bg="#f0f0f0")

# 主容器和选项卡
container = ttk.Frame(root, padding=12)
container.grid(row=0, column=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# 创建选项卡控件
notebook = ttk.Notebook(container)
notebook.grid(row=0, column=0, sticky="nsew")
container.columnconfigure(0, weight=1)
container.rowconfigure(0, weight=1)

# 创建选项卡页面
split_tab = ttk.Frame(notebook)
merge_tab = ttk.Frame(notebook)
preview_tab = ttk.Frame(notebook)
settings_tab = ttk.Frame(notebook)

# 如果 EPUB 库可用，添加 EPUB 转换选项卡
if EPUB_LIBS_AVAILABLE:
    epub_tab = ttk.Frame(notebook)

# 添加选项卡到笔记本
notebook.add(split_tab, text="PDF 拆分")
notebook.add(merge_tab, text="PDF 合并")
notebook.add(preview_tab, text="PDF 预览")
if EPUB_LIBS_AVAILABLE:
    notebook.add(epub_tab, text="EPUB 转换")
notebook.add(settings_tab, text="设置")

# 主题开关变量
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
merge_frame = ttk.LabelFrame(merge_tab, text="PDF 合并")
merge_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
merge_tab.columnconfigure(0, weight=1)
merge_tab.rowconfigure(0, weight=1)
merge_frame.columnconfigure(0, weight=1)
merge_frame.rowconfigure(0, weight=1)

# 文件列表
merge_listbox = tk.Listbox(merge_frame, selectmode=tk.EXTENDED)
merge_listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

# 滚动条
merge_scrollbar = ttk.Scrollbar(merge_frame, orient="vertical", command=merge_listbox.yview)
merge_scrollbar.grid(row=0, column=1, sticky="ns", pady=4)
merge_listbox.configure(yscrollcommand=merge_scrollbar.set)

# 按钮区域
merge_buttons_frame = ttk.Frame(merge_frame)
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
if EPUB_LIBS_AVAILABLE:
    epub_frame = ttk.LabelFrame(epub_tab, text="EPUB 转换")
    epub_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    epub_tab.columnconfigure(0, weight=1)
    epub_tab.rowconfigure(0, weight=1)
    epub_frame.columnconfigure(1, weight=1)
    
    # EPUB 文件选择
    epub_input_var = tk.StringVar()
    ttk.Label(epub_frame, text="输入 EPUB 文件").grid(row=0, column=0, sticky="w", padx=8, pady=6)
    epub_input_entry = ttk.Entry(epub_frame, textvariable=epub_input_var)
    epub_input_entry.grid(row=0, column=1, sticky="ew", padx=4)
    epub_browse_btn = ttk.Button(epub_frame, text="浏览...")
    epub_browse_btn.grid(row=0, column=2, padx=8)
    
    # PDF 输出路径
    epub_output_var = tk.StringVar()
    ttk.Label(epub_frame, text="输出 PDF 文件").grid(row=1, column=0, sticky="w", padx=8, pady=6)
    epub_output_entry = ttk.Entry(epub_frame, textvariable=epub_output_var)
    epub_output_entry.grid(row=1, column=1, sticky="ew", padx=4)
    epub_output_btn = ttk.Button(epub_frame, text="浏览...")
    epub_output_btn.grid(row=1, column=2, padx=8)
    
    # 纸张大小选择
    epub_paper_var = tk.StringVar(value="a4")
    ttk.Label(epub_frame, text="纸张大小").grid(row=2, column=0, sticky="w", padx=8, pady=6)
    epub_paper_combo = ttk.Combobox(epub_frame, textvariable=epub_paper_var, values=["a4", "a5", "letter", "legal"])
    epub_paper_combo.grid(row=2, column=1, sticky="w", padx=4)
    epub_paper_combo.configure(state="readonly")
    
    # 转换按钮
    epub_convert_btn = ttk.Button(epub_frame, text="转换 EPUB 为 PDF")
    epub_convert_btn.grid(row=3, column=1, sticky="w", padx=4, pady=6)
    
    # 批量转换按钮
    epub_batch_btn = ttk.Button(epub_frame, text="批量转换 EPUB")
    epub_batch_btn.grid(row=3, column=1, sticky="e", padx=4, pady=6)
    
    # EPUB 转换选项卡事件处理
    # 浏览 EPUB 文件
    def epub_browse_input():
        filename = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
        if filename:
            epub_input_var.set(filename)
            # 自动填充输出名
            base_dir = os.path.dirname(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            suggested = os.path.join(base_dir, f"{base_name}.pdf")
            if not epub_output_var.get().strip():
                epub_output_var.set(suggested)
    
    # 浏览输出路径
    def epub_browse_output():
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if filename:
            epub_output_var.set(filename)
    
    # 转换 EPUB 为 PDF
    def epub_convert():
        epub_path = epub_input_var.get().strip()
        pdf_path = epub_output_var.get().strip()
        paper_size = epub_paper_var.get().strip()
        
        if not epub_path:
            messagebox.showerror("错误", "请先选择 EPUB 文件！")
            return
        if not pdf_path:
            messagebox.showerror("错误", "请先选择输出 PDF 路径！")
            return
        
        def task():
            try:
                ctx = build_tk_task_context()
                epub_to_pdf_python(ctx, epub_path, pdf_path, paper_size)
            except Exception as e:
                post_error(e)
        
        start_running_ui()
        threading.Thread(target=task, daemon=True).start()
    
    # 批量转换 EPUB
    def epub_batch_convert():
        epub_files = filedialog.askopenfilenames(title="选择 EPUB 文件", filetypes=[("EPUB files", "*.epub")])
        if not epub_files:
            return
        
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if not output_dir:
            return
        
        paper_size = epub_paper_var.get().strip()
        
        def task():
            try:
                ctx = build_tk_task_context()
                batch_epub_to_pdf(ctx, epub_files, output_dir, paper_size)
            except Exception as e:
                post_error(e)
        
        start_running_ui()
        threading.Thread(target=task, daemon=True).start()
    
    # 绑定按钮事件
epub_browse_btn.configure(command=epub_browse_input)
epub_output_btn.configure(command=epub_browse_output)
epub_convert_btn.configure(command=epub_convert)
epub_batch_btn.configure(command=epub_batch_convert)

# 设置选项卡内容
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
    
    # 解析章节范围
    chapter_ranges = []
    lines = chapters_input.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if "-" in line:
            try:
                start_str, end_str = line.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start > end:
                    start, end = end, start
                chapter_ranges.append((start, end))
            except ValueError:
                messagebox.showerror("错误", f"第{i+1}行章节范围格式错误：{line}")
                return
        else:
            messagebox.showerror("错误", f"第{i+1}行章节范围格式错误，缺少'-'：{line}")
            return
    
    if not chapter_ranges:
        messagebox.showerror("错误", "没有有效的章节范围！")
        return
    
    def task():
        try:
            from pdf_split_task import split_pdf_by_chapters
            ctx = build_tk_task_context()
            split_pdf_by_chapters(ctx, input_file, output_file, chapter_ranges)
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
def on_window_resize(event):
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

# 绑定窗口大小变化事件
root.bind("<Configure>", on_window_resize)

def run_epub_convert():
    epub_in = epub_input_entry.get().strip()
    pdf_out = epub_output_entry.get().strip()
    if not epub_in or not pdf_out:
        messagebox.showerror("错误", "请先选择 EPUB 输入与 PDF 输出文件！")
        return
    paper = epub_paper_var.get().strip() or "a4"

    def task():
        try:
            do_epub_convert_with_progress(epub_in, pdf_out, paper)
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
name_template_var = tk.StringVar(value="{name}_{start}-{end}.pdf")
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
