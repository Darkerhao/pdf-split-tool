from dataclasses import dataclass
import queue
import tkinter as tk
from tkinter import messagebox, ttk

from services.settings_service import AppSettings, load_app_settings, save_app_settings


@dataclass
class ThemeConfig:
    root: tk.Misc
    style: ttk.Style
    status_bar: ttk.Label | None
    colors: dict
    light_theme: str
    dark_theme: str


def apply_theme(config: ThemeConfig, dark: bool):
    palette = config.colors["dark"] if dark else config.colors["light"]
    try:
        config.style.theme_use(config.dark_theme if dark else config.light_theme)
    except Exception:
        pass

    config.root.configure(bg=palette["bg"])
    config.style.configure("TFrame", background=palette["bg"])
    config.style.configure("TLabelframe", background=palette["bg"])
    config.style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["fg"])
    config.style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    config.style.configure("TEntry", fieldbackground=palette["subbg"], foreground=palette["fg"])
    config.style.configure("TButton", background=palette["subbg"], foreground=palette["fg"])
    config.style.configure("TCombobox", fieldbackground=palette["subbg"], foreground=palette["fg"])
    config.style.configure("TMenubutton", background=palette["subbg"], foreground=palette["fg"])
    config.style.configure("Horizontal.TProgressbar", background=palette["accent"])
    config.style.configure("TSeparator", background=palette["border"])
    if config.status_bar is not None:
        config.status_bar.configure(background=palette["bg"], foreground=palette["fg"])


def save_ui_settings(
    settings_path: str,
    input_entry,
    output_entry,
    theme_dark_var,
    lang: str,
    recent_files: list[str],
    name_template_var,
    epub_input_entry,
    epub_output_entry,
    epub_paper_var,
):
    try:
        dark_val = bool(theme_dark_var.get())
    except Exception:
        dark_val = False

    settings = AppSettings(
        input=input_entry.get().strip() if input_entry is not None else "",
        output=output_entry.get().strip() if output_entry is not None else "",
        dark=dark_val,
        lang=lang,
        recent=recent_files,
        template=name_template_var.get() if name_template_var is not None else "{name}_{start}-{end}.pdf",
        epub_input=epub_input_entry.get().strip() if epub_input_entry is not None else "",
        epub_output=epub_output_entry.get().strip() if epub_output_entry is not None else "",
        epub_paper=epub_paper_var.get().strip() if epub_paper_var is not None else "a4",
    )
    save_app_settings(settings_path, settings)


def load_ui_settings(
    settings_path: str,
    theme_dark_var,
    set_theme,
    set_input_file,
    output_entry,
    name_template_var,
    epub_input_entry,
    epub_output_entry,
    epub_paper_var,
):
    settings = load_app_settings(settings_path)
    if settings.input:
        set_input_file(settings.input)
    if settings.output and output_entry is not None:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, settings.output)
    try:
        theme_dark_var.set(bool(settings.dark))
    except Exception:
        pass
    set_theme(bool(settings.dark))
    if settings.template and name_template_var is not None:
        name_template_var.set(settings.template)
    if settings.epub_input and epub_input_entry is not None:
        epub_input_entry.delete(0, tk.END)
        epub_input_entry.insert(0, settings.epub_input)
    if settings.epub_output and epub_output_entry is not None:
        epub_output_entry.delete(0, tk.END)
        epub_output_entry.insert(0, settings.epub_output)
    if settings.epub_paper and epub_paper_var is not None:
        epub_paper_var.set(settings.epub_paper)
    return settings


def enqueue_progress(progress_queue, pct: float, text: str):
    progress_queue.put(("progress", pct, text))


def enqueue_done(progress_queue, msg: str, payload=None):
    progress_queue.put(("done", msg, payload))


def enqueue_error(progress_queue, err):
    progress_queue.put(("error", err))


def start_running_ui(controls_to_toggle, progress_var, progress_bar, cancel_btn, status_var, running_text: str = "正在运行..."):
    if progress_var is not None:
        progress_var.set(0)
    if progress_bar is not None:
        progress_bar.grid()
    if cancel_btn is not None:
        cancel_btn.grid()
    if status_var is not None:
        status_var.set(running_text)

    for widget in controls_to_toggle:
        try:
            widget.configure(state="disabled")
        except Exception:
            pass


def stop_running_ui(controls_to_toggle, progress_bar, cancel_btn):
    if progress_bar is not None:
        progress_bar.grid_remove()
    if cancel_btn is not None:
        cancel_btn.grid_remove()

    for widget in controls_to_toggle:
        try:
            if isinstance(widget, ttk.Combobox):
                widget.configure(state="readonly")
            else:
                widget.configure(state="normal")
        except Exception:
            pass


def poll_progress_queue(root, progress_queue, progress_var, status_var, stop_running_ui_callback, interval_ms: int = 150):
    try:
        while True:
            item = progress_queue.get_nowait()
            kind = item[0]
            if kind == "progress":
                _, pct, msg = item
                progress_var.set(int(max(0, min(100, pct))))
                status_var.set(str(msg))
            elif kind == "done":
                _, msg, payload = item
                stop_running_ui_callback()
                progress_var.set(100)
                completed_text = str(msg).strip() if msg else "运行完成"
                status_var.set(completed_text)
                if completed_text:
                    messagebox.showinfo("完成", completed_text)
            elif kind == "error":
                _, err = item
                stop_running_ui_callback()
                status_var.set("运行失败")
                messagebox.showerror("错误", str(err))
    except queue.Empty:
        pass

    root.after(interval_ms, lambda: poll_progress_queue(root, progress_queue, progress_var, status_var, stop_running_ui_callback, interval_ms))
