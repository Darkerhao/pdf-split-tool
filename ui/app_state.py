import os
import tkinter as tk
from tkinter import messagebox, simpledialog

from PyPDF2 import PdfReader

from services.settings_service import DEFAULT_LANGUAGE, push_recent_file


DEFAULT_PAGES_PREFIX = "总页数："
DEFAULT_LOADED_MESSAGE = "已加载 PDF"
DEFAULT_LOAD_FAILED_MESSAGE = "加载失败，请重新选择"
DEFAULT_EMPTY_RECENT_LABEL = "暂无最近文件"
DEFAULT_TITLE_TEXT = "PDF 工具箱：拆分 / 合并 / 预览"
DEFAULT_RECENT_TEXT = "最近"
DEFAULT_ERROR_TITLE = "错误"
DEFAULT_NO_INPUT_MESSAGE = "请先选择 PDF 文件"
DEFAULT_EVERY_N_DIALOG_TITLE = "每 N 页拆分"
DEFAULT_EVERY_N_DIALOG_PROMPT = "请输入每份页数："
DEFAULT_EVERY_N_SUCCESS_TEMPLATE = "已生成每 {n} 页范围"
DEFAULT_EQUAL_K_DIALOG_TITLE = "均分为 K 份"
DEFAULT_EQUAL_K_DIALOG_PROMPT = "请输入份数："
DEFAULT_EQUAL_K_SUCCESS_TEMPLATE = "已生成均分 {k} 份范围"
DEFAULT_CLEAR_MESSAGE = "已清空范围"


def _get_localized_text(strings: dict, lang: str, key: str, fallback: str) -> str:
    primary = strings.get(lang, {}) if isinstance(strings, dict) else {}
    default = strings.get(DEFAULT_LANGUAGE, {}) if isinstance(strings, dict) else {}
    return primary.get(key) or default.get(key) or fallback


def _resolve_language(strings: dict, requested_lang: str, current_lang: str) -> str:
    if not isinstance(strings, dict) or not strings:
        return DEFAULT_LANGUAGE

    for candidate in (requested_lang, current_lang, DEFAULT_LANGUAGE):
        if candidate in strings:
            return candidate

    return next(iter(strings))


def set_input_file_ui(
    filename: str,
    input_entry,
    output_entry,
    pages_var,
    status_var,
    preview_btn,
    add_recent_callback,
    pages_prefix: str = DEFAULT_PAGES_PREFIX,
    loaded_message: str = DEFAULT_LOADED_MESSAGE,
    load_failed_message: str = DEFAULT_LOAD_FAILED_MESSAGE,
):
    if not filename:
        return

    input_entry.delete(0, tk.END)
    input_entry.insert(0, filename)

    try:
        base_dir = os.path.dirname(filename)
        base_name = os.path.splitext(os.path.basename(filename))[0]
        suggested = os.path.join(base_dir, f"{base_name}_split.pdf")
        if not output_entry.get().strip():
            output_entry.insert(0, suggested)
    except Exception:
        pass

    try:
        reader = PdfReader(filename)
        total = len(reader.pages)
        pages_var.set(f"{pages_prefix}{total}")
        status_var.set(loaded_message)
        preview_btn.configure(state="normal")
    except Exception:
        pages_var.set(f"{pages_prefix}-")
        status_var.set(load_failed_message)
        preview_btn.configure(state="disabled")

    add_recent_callback(filename)


def update_recent_menu_ui(
    recent_menu,
    recent_files: list[str],
    open_recent_callback,
    empty_label: str = DEFAULT_EMPTY_RECENT_LABEL,
):
    recent_menu.delete(0, "end")
    displayable_recent_files = [
        (index, path)
        for index, path in enumerate(recent_files or [])
        if isinstance(path, str) and path.strip()
    ]
    if not displayable_recent_files:
        recent_menu.add_command(label=empty_label, state="disabled")
        return

    for index, path in displayable_recent_files:
        recent_menu.add_command(label=path, command=lambda i=index: open_recent_callback(i))


def add_recent_file_ui(recent_files: list[str], path: str, update_menu_callback, save_settings_callback):
    if not path:
        return list(recent_files)

    new_recent_files = push_recent_file(recent_files, path)
    update_menu_callback(new_recent_files)
    save_settings_callback()
    return new_recent_files


def open_recent_ui(recent_files: list[str], index: int, set_input_file_callback):
    if 0 <= index < len(recent_files):
        set_input_file_callback(recent_files[index])


def set_language_ui(lang: str, strings: dict, current_lang: str, root, recent_btn, save_settings_callback):
    new_lang = _resolve_language(strings, lang, current_lang)

    title = _get_localized_text(strings, new_lang, "title", DEFAULT_TITLE_TEXT)
    recent_text = _get_localized_text(strings, new_lang, "recent", DEFAULT_RECENT_TEXT)

    try:
        if title:
            root.title(title)
    except Exception:
        pass

    try:
        recent_btn.configure(text=recent_text)
    except Exception:
        pass

    save_settings_callback()
    return new_lang


def helper_every_n_pages_ui(
    input_file: str,
    ranges_entry,
    status_var,
    askinteger=simpledialog.askinteger,
    showerror=messagebox.showerror,
    error_title: str = DEFAULT_ERROR_TITLE,
    no_input_message: str = DEFAULT_NO_INPUT_MESSAGE,
    dialog_title: str = DEFAULT_EVERY_N_DIALOG_TITLE,
    dialog_prompt: str = DEFAULT_EVERY_N_DIALOG_PROMPT,
    success_message_template: str = DEFAULT_EVERY_N_SUCCESS_TEMPLATE,
):
    if not input_file:
        showerror(error_title, no_input_message)
        return

    n = askinteger(dialog_title, dialog_prompt, minvalue=1)
    if not n:
        return

    try:
        total = len(PdfReader(input_file).pages)
        parts = []
        for start in range(1, total + 1, n):
            end = min(total, start + n - 1)
            parts.append(f"{start}-{end}")
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ", ".join(parts))
        status_var.set(success_message_template.format(n=n))
    except Exception as exc:
        showerror(error_title, str(exc))


def helper_equal_k_parts_ui(
    input_file: str,
    ranges_entry,
    status_var,
    askinteger=simpledialog.askinteger,
    showerror=messagebox.showerror,
    error_title: str = DEFAULT_ERROR_TITLE,
    no_input_message: str = DEFAULT_NO_INPUT_MESSAGE,
    dialog_title: str = DEFAULT_EQUAL_K_DIALOG_TITLE,
    dialog_prompt: str = DEFAULT_EQUAL_K_DIALOG_PROMPT,
    success_message_template: str = DEFAULT_EQUAL_K_SUCCESS_TEMPLATE,
):
    if not input_file:
        showerror(error_title, no_input_message)
        return

    k = askinteger(dialog_title, dialog_prompt, minvalue=1)
    if not k:
        return

    try:
        total = len(PdfReader(input_file).pages)
        if k > total:
            k = total
        base, rem = divmod(total, k)
        parts = []
        start = 1
        for index in range(k):
            size = base + (1 if index < rem else 0)
            end = start + size - 1
            parts.append(f"{start}-{end}")
            start = end + 1
        ranges_entry.delete(0, tk.END)
        ranges_entry.insert(0, ", ".join(parts))
        status_var.set(success_message_template.format(k=k))
    except Exception as exc:
        showerror(error_title, str(exc))


def clear_ranges_ui(ranges_entry, placeholder: str, status_var, message: str = DEFAULT_CLEAR_MESSAGE):
    ranges_entry.delete(0, tk.END)
    ranges_entry.insert(0, placeholder)
    status_var.set(message)
