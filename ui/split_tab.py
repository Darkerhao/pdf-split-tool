from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass(frozen=True)
class SplitTabTexts:
    files_frame_title: str = "文件"
    input_label: str = "输入 PDF 文件"
    browse_button: str = "浏览..."
    output_label: str = "输出 PDF 文件"
    pages_default: str = "总页数：-"
    preview_button: str = "预览 PDF"
    split_frame_title: str = "拆分"
    ranges_label: str = "页码范围"
    preview_split_button: str = "预览拆分结果"
    split_range_button: str = "按范围拆分"
    split_each_button: str = "拆成单页"
    chapters_label: str = "章节范围（每行一个，格式：起始页-结束页）"
    chapters_example: str = "示例：\n1-10\n11-25\n26-40\n41-55\n56-70"
    split_chapters_button: str = "按章节拆分"
    split_auto_chapters_button: str = "自动识别章节"


@dataclass
class SplitTabWidgets:
    files_frame: ttk.LabelFrame
    input_label: ttk.Label
    input_entry: ttk.Entry
    input_browse_btn: ttk.Button
    output_label: ttk.Label
    output_entry: ttk.Entry
    output_browse_btn: ttk.Button
    pages_var: tk.StringVar
    preview_btn: ttk.Button
    split_frame: ttk.LabelFrame
    ranges_label: ttk.Label
    ranges_entry: ttk.Entry
    preview_split_btn: ttk.Button
    split_range_btn: ttk.Button
    split_each_btn: ttk.Button
    chapters_label: ttk.Label
    chapters_text: tk.Text
    split_chapters_btn: ttk.Button
    split_auto_chapters_btn: ttk.Button
    controls: list[tk.Widget]


def apply_split_tab_texts(
    widgets: SplitTabWidgets,
    texts: SplitTabTexts | None = None,
) -> None:
    resolved = texts or SplitTabTexts()
    widgets.files_frame.configure(text=resolved.files_frame_title)
    widgets.input_label.configure(text=resolved.input_label)
    widgets.input_browse_btn.configure(text=resolved.browse_button)
    widgets.output_label.configure(text=resolved.output_label)
    widgets.output_browse_btn.configure(text=resolved.browse_button)
    widgets.pages_var.set(resolved.pages_default)
    widgets.preview_btn.configure(text=resolved.preview_button)
    widgets.split_frame.configure(text=resolved.split_frame_title)
    widgets.ranges_label.configure(text=resolved.ranges_label)
    widgets.preview_split_btn.configure(text=resolved.preview_split_button)
    widgets.split_range_btn.configure(text=resolved.split_range_button)
    widgets.split_each_btn.configure(text=resolved.split_each_button)
    widgets.chapters_label.configure(text=resolved.chapters_label)
    widgets.split_chapters_btn.configure(text=resolved.split_chapters_button)
    widgets.split_auto_chapters_btn.configure(text=resolved.split_auto_chapters_button)


def build_split_tab(parent, ranges_placeholder: str, texts: SplitTabTexts | None = None) -> SplitTabWidgets:
    files_frame = ttk.LabelFrame(parent)
    files_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=4, pady=(0, 8))
    for column in range(3):
        files_frame.columnconfigure(column, weight=1 if column == 1 else 0)

    input_label = ttk.Label(files_frame)
    input_label.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    input_entry = ttk.Entry(files_frame)
    input_entry.grid(row=0, column=1, sticky="ew", padx=4)
    input_browse_btn = ttk.Button(files_frame, width=10)
    input_browse_btn.grid(row=0, column=2, padx=8)

    output_label = ttk.Label(files_frame)
    output_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
    output_entry = ttk.Entry(files_frame)
    output_entry.grid(row=1, column=1, sticky="ew", padx=4)
    output_browse_btn = ttk.Button(files_frame, width=10)
    output_browse_btn.grid(row=1, column=2, padx=8)

    pages_var = tk.StringVar()
    ttk.Label(files_frame, textvariable=pages_var, foreground="#666666").grid(row=2, column=1, sticky="w", padx=4, pady=(0, 6))

    preview_btn = ttk.Button(files_frame, width=12)
    preview_btn.grid(row=2, column=2, padx=8, pady=4)
    preview_btn.configure(state="disabled")

    split_frame = ttk.LabelFrame(parent)
    split_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
    split_frame.columnconfigure(1, weight=1)
    parent.columnconfigure(1, weight=1)

    ranges_label = ttk.Label(split_frame)
    ranges_label.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    ranges_entry = ttk.Entry(split_frame)
    ranges_entry.grid(row=0, column=1, sticky="ew", padx=4)
    ranges_entry.insert(0, ranges_placeholder)

    preview_split_btn = ttk.Button(split_frame, width=16)
    preview_split_btn.grid(row=0, column=2, padx=8, pady=4)

    ttk.Separator(split_frame).grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=4)

    split_range_btn = ttk.Button(split_frame, width=18)
    split_range_btn.grid(row=2, column=1, sticky="w", padx=4, pady=6)

    split_each_btn = ttk.Button(split_frame, width=18)
    split_each_btn.grid(row=2, column=1, sticky="e", padx=4, pady=6)

    ttk.Separator(split_frame).grid(row=3, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
    chapters_label = ttk.Label(split_frame)
    chapters_label.grid(row=4, column=0, sticky="w", padx=8, pady=6)
    chapters_text = tk.Text(split_frame, height=8, width=50)
    chapters_text.grid(row=4, column=1, sticky="ew", padx=4)

    split_chapters_btn = ttk.Button(split_frame, width=18)
    split_chapters_btn.grid(row=5, column=1, sticky="w", padx=4, pady=6)

    split_auto_chapters_btn = ttk.Button(split_frame, width=18)
    split_auto_chapters_btn.grid(row=5, column=1, sticky="e", padx=4, pady=6)

    controls = [
        input_entry,
        input_browse_btn,
        output_entry,
        output_browse_btn,
        preview_btn,
        ranges_entry,
        preview_split_btn,
        split_range_btn,
        split_each_btn,
        chapters_text,
        split_chapters_btn,
        split_auto_chapters_btn,
    ]
    widgets = SplitTabWidgets(
        files_frame=files_frame,
        input_label=input_label,
        input_entry=input_entry,
        input_browse_btn=input_browse_btn,
        output_label=output_label,
        output_entry=output_entry,
        output_browse_btn=output_browse_btn,
        pages_var=pages_var,
        preview_btn=preview_btn,
        split_frame=split_frame,
        ranges_label=ranges_label,
        ranges_entry=ranges_entry,
        preview_split_btn=preview_split_btn,
        split_range_btn=split_range_btn,
        split_each_btn=split_each_btn,
        chapters_label=chapters_label,
        chapters_text=chapters_text,
        split_chapters_btn=split_chapters_btn,
        split_auto_chapters_btn=split_auto_chapters_btn,
        controls=controls,
    )
    apply_split_tab_texts(widgets, texts)
    resolved_texts = texts or SplitTabTexts()
    chapters_text.insert("1.0", resolved_texts.chapters_example)
    return widgets
