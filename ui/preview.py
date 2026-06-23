import os
import tkinter as tk
from tkinter import messagebox, ttk

from PyPDF2 import PdfReader


def open_pdf_previewer(master, pdf_path: str):
    if not pdf_path or not os.path.exists(pdf_path):
        messagebox.showerror("错误", "请先选择有效的 PDF 文件！")
        return

    try:
        preview_window = tk.Toplevel(master)
        preview_window.title(f"PDF 预览 - {os.path.basename(pdf_path)}")
        preview_window.geometry("800x600")
        preview_window.minsize(600, 400)

        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))

        page_var = tk.StringVar(value="第 1 页 / 共 0 页")
        ttk.Label(toolbar_frame, textvariable=page_var).pack(side="left", padx=10)

        nav_frame = ttk.Frame(toolbar_frame)
        nav_frame.pack(side="left", padx=10)

        rotate_frame = ttk.Frame(toolbar_frame)
        rotate_frame.pack(side="left", padx=10)

        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side="right", padx=10)

        ttk.Label(zoom_frame, text="缩放：").pack(side="left", padx=2)

        fullscreen = False

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg="#ffffff", bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x")

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        canvas.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        current_page = 0
        total_pages = 0
        zoom = 1.0
        rotation = 0
        doc = None

        def show_page(page_num: int):
            nonlocal current_page

            if page_num < 0:
                page_num = 0
            elif page_num >= total_pages:
                page_num = total_pages - 1

            current_page = page_num
            page_var.set(f"第 {current_page + 1} 页 / 共 {total_pages} 页")
            canvas.delete("all")

            if doc:
                try:
                    page = doc.load_page(current_page)
                    page.set_rotation(rotation % 360)

                    zoom_matrix = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=zoom_matrix)

                    from PIL import Image, ImageTk

                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    photo = ImageTk.PhotoImage(img)

                    canvas.create_image(0, 0, anchor="nw", image=photo)
                    canvas.image = photo
                    canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception as exc:
                    canvas.create_text(400, 300, text=f"渲染失败：{str(exc)}", font=("Segoe UI", 12), fill="red", justify="center")
            else:
                try:
                    from PIL import Image, ImageDraw, ImageTk

                    img = Image.new("RGB", (800, 600), color="#ffffff")
                    drawer = ImageDraw.Draw(img)
                    drawer.text((100, 100), f"PDF 页面 {current_page + 1}", fill=(0, 0, 0))
                    drawer.text((100, 120), f"总页数：{total_pages}", fill=(0, 0, 0))
                    drawer.text((100, 140), "注意：这是一个简化版 PDF 预览", fill=(0, 0, 0))
                    drawer.text((100, 160), "完整渲染需要安装 PyMuPDF", fill=(0, 0, 0))
                    drawer.text((100, 180), "请运行：pip install PyMuPDF", fill=(0, 0, 0))

                    width, height = img.size
                    new_width = int(width * zoom)
                    new_height = int(height * zoom)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    photo = ImageTk.PhotoImage(img)
                    canvas.create_image(0, 0, anchor="nw", image=photo)
                    canvas.image = photo
                    canvas.configure(scrollregion=canvas.bbox("all"))
                except ImportError:
                    canvas.create_text(
                        400,
                        300,
                        text=f"PDF 页面 {current_page + 1}\n总页数：{total_pages}\n\n注意：无法渲染 PDF 页面\n请安装必要的库：Pillow、PyMuPDF",
                        font=("Segoe UI", 12),
                        fill="black",
                        justify="center",
                    )
                except Exception as exc:
                    canvas.create_text(400, 300, text=f"无法显示页面：{str(exc)}", font=("Segoe UI", 12), fill="red", justify="center")

        def set_zoom(level: float):
            nonlocal zoom
            zoom = level
            show_page(current_page)

        def rotate_page(angle: int):
            nonlocal rotation
            rotation += angle
            show_page(current_page)

        def toggle_fullscreen():
            nonlocal fullscreen
            fullscreen = not fullscreen
            preview_window.attributes("-fullscreen", fullscreen)

        ttk.Button(nav_frame, text="第一页", command=lambda: show_page(0)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="上一页", command=lambda: show_page(current_page - 1)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="下一页", command=lambda: show_page(current_page + 1)).pack(side="left", padx=2)
        ttk.Button(nav_frame, text="最后一页", command=lambda: show_page(total_pages - 1)).pack(side="left", padx=2)

        ttk.Button(rotate_frame, text="向左旋转", command=lambda: rotate_page(-90)).pack(side="left", padx=2)
        ttk.Button(rotate_frame, text="向右旋转", command=lambda: rotate_page(90)).pack(side="left", padx=2)

        ttk.Button(zoom_frame, text="50%", command=lambda: set_zoom(0.5)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="75%", command=lambda: set_zoom(0.75)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="100%", command=lambda: set_zoom(1.0)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="150%", command=lambda: set_zoom(1.5)).pack(side="left", padx=2)
        ttk.Button(zoom_frame, text="200%", command=lambda: set_zoom(2.0)).pack(side="left", padx=2)

        ttk.Button(toolbar_frame, text="切换全屏", command=toggle_fullscreen).pack(side="right", padx=10)

        try:
            import fitz

            doc = fitz.open(pdf_path)
            total_pages = len(doc)
        except ImportError:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            doc = None
        except Exception as exc:
            messagebox.showerror("错误", f"无法打开 PDF 文件：{str(exc)}")
            return

        show_page(0)

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

        def on_mouse_wheel(event):
            if event.delta > 0:
                set_zoom(min(3.0, zoom + 0.1))
            else:
                set_zoom(max(0.1, zoom - 0.1))

        def on_close():
            if doc:
                doc.close()
            preview_window.destroy()

        preview_window.bind("<KeyPress>", on_key_press)
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        preview_window.protocol("WM_DELETE_WINDOW", on_close)
    except Exception as exc:
        messagebox.showerror("错误", f"打开 PDF 预览失败：{str(exc)}")
