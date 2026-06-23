from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass
class EPUBPanelWidgets:
    epub_frame: ttk.LabelFrame
    input_label: ttk.Label
    input_entry: ttk.Entry
    browse_btn: ttk.Button
    output_label: ttk.Label
    output_entry: ttk.Entry
    output_browse_btn: ttk.Button
    paper_label: ttk.Label
    paper_var: tk.StringVar
    paper_combo: ttk.Combobox
    convert_btn: ttk.Button
    batch_frame: ttk.LabelFrame
    batch_hint_label: ttk.Label
    batch_list: tk.Listbox
    batch_buttons_frame: ttk.Frame
    batch_add_btn: ttk.Button
    batch_remove_btn: ttk.Button
    batch_clear_btn: ttk.Button
    batch_paper_label: ttk.Label
    batch_paper_var: tk.StringVar
    batch_paper_combo: ttk.Combobox
    batch_output_label: ttk.Label
    batch_output_dir_entry: ttk.Entry
    batch_output_browse_btn: ttk.Button
    batch_template_label: ttk.Label
    batch_filename_var: tk.StringVar
    batch_filename_entry: ttk.Entry
    batch_convert_btn: ttk.Button
    controls: list[tk.Widget]


def build_epub_panels(container) -> EPUBPanelWidgets:
    container.columnconfigure(0, weight=1)

    epub_frame = ttk.LabelFrame(container, text="EPUB 转 PDF")
    epub_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    epub_frame.columnconfigure(1, weight=1)

    input_label = ttk.Label(epub_frame, text="输入 EPUB 文件")
    input_label.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    input_entry = ttk.Entry(epub_frame)
    input_entry.grid(row=0, column=1, sticky="ew", padx=4)
    browse_btn = ttk.Button(epub_frame, text="浏览...", width=10)
    browse_btn.grid(row=0, column=2, padx=8)

    output_label = ttk.Label(epub_frame, text="输出 PDF 文件")
    output_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
    output_entry = ttk.Entry(epub_frame)
    output_entry.grid(row=1, column=1, sticky="ew", padx=4)
    output_browse_btn = ttk.Button(epub_frame, text="浏览...", width=10)
    output_browse_btn.grid(row=1, column=2, padx=8)

    paper_label = ttk.Label(epub_frame, text="纸张大小")
    paper_label.grid(row=2, column=0, sticky="w", padx=8, pady=6)
    paper_var = tk.StringVar(value="a4")
    paper_combo = ttk.Combobox(
        epub_frame,
        textvariable=paper_var,
        state="readonly",
        width=12,
        values=("a4", "a5", "letter", "legal"),
    )
    paper_combo.grid(row=2, column=1, sticky="w", padx=4)

    convert_btn = ttk.Button(epub_frame, text="开始转换", width=18)
    convert_btn.grid(row=2, column=2, padx=8)

    batch_frame = ttk.LabelFrame(container, text="批量 EPUB 转 PDF")
    batch_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
    batch_frame.columnconfigure(1, weight=1)
    batch_frame.rowconfigure(1, weight=1)

    batch_hint_label = ttk.Label(
        batch_frame,
        text="批量添加 .epub 文件后，将统一输出到所选目录；文件名模板支持 {name}.pdf。",
    )
    batch_hint_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(6, 2))

    batch_list = tk.Listbox(batch_frame, selectmode=tk.EXTENDED, height=6)
    batch_list.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=8, pady=6)

    batch_buttons_frame = ttk.Frame(batch_frame)
    batch_buttons_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
    batch_buttons_frame.columnconfigure(4, weight=1)

    batch_add_btn = ttk.Button(batch_buttons_frame, text="添加 EPUB", width=12)
    batch_add_btn.grid(row=0, column=0, padx=4)

    batch_remove_btn = ttk.Button(batch_buttons_frame, text="移除选中", width=12)
    batch_remove_btn.grid(row=0, column=1, padx=4)

    batch_clear_btn = ttk.Button(batch_buttons_frame, text="清空列表", width=12)
    batch_clear_btn.grid(row=0, column=2, padx=4)

    batch_paper_label = ttk.Label(batch_frame, text="批量纸张大小")
    batch_paper_label.grid(row=3, column=0, sticky="w", padx=8, pady=6)
    batch_paper_var = tk.StringVar(value="a4")
    batch_paper_combo = ttk.Combobox(
        batch_frame,
        textvariable=batch_paper_var,
        state="readonly",
        width=12,
        values=("a4", "a5", "letter", "legal"),
    )
    batch_paper_combo.grid(row=3, column=1, sticky="w", padx=4)

    batch_output_label = ttk.Label(batch_frame, text="批量输出目录")
    batch_output_label.grid(row=4, column=0, sticky="w", padx=8, pady=6)
    batch_output_dir_entry = ttk.Entry(batch_frame)
    batch_output_dir_entry.grid(row=4, column=1, sticky="ew", padx=4)

    batch_output_browse_btn = ttk.Button(batch_frame, text="浏览...", width=10)
    batch_output_browse_btn.grid(row=4, column=2, padx=8)

    batch_template_label = ttk.Label(batch_frame, text="输出文件名模板")
    batch_template_label.grid(row=5, column=0, sticky="w", padx=8, pady=6)
    batch_filename_var = tk.StringVar(value="{name}.pdf")
    batch_filename_entry = ttk.Entry(batch_frame, textvariable=batch_filename_var, width=40)
    batch_filename_entry.grid(row=5, column=1, sticky="w", padx=4)

    batch_convert_btn = ttk.Button(batch_frame, text="开始批量转换", width=18)
    batch_convert_btn.grid(row=6, column=2, padx=8, pady=6)

    controls = [
        input_entry,
        browse_btn,
        output_entry,
        output_browse_btn,
        paper_combo,
        convert_btn,
        batch_list,
        batch_add_btn,
        batch_remove_btn,
        batch_clear_btn,
        batch_paper_combo,
        batch_output_dir_entry,
        batch_output_browse_btn,
        batch_filename_entry,
        batch_convert_btn,
    ]
    return EPUBPanelWidgets(
        epub_frame=epub_frame,
        input_label=input_label,
        input_entry=input_entry,
        browse_btn=browse_btn,
        output_label=output_label,
        output_entry=output_entry,
        output_browse_btn=output_browse_btn,
        paper_label=paper_label,
        paper_var=paper_var,
        paper_combo=paper_combo,
        convert_btn=convert_btn,
        batch_frame=batch_frame,
        batch_hint_label=batch_hint_label,
        batch_list=batch_list,
        batch_buttons_frame=batch_buttons_frame,
        batch_add_btn=batch_add_btn,
        batch_remove_btn=batch_remove_btn,
        batch_clear_btn=batch_clear_btn,
        batch_paper_label=batch_paper_label,
        batch_paper_var=batch_paper_var,
        batch_paper_combo=batch_paper_combo,
        batch_output_label=batch_output_label,
        batch_output_dir_entry=batch_output_dir_entry,
        batch_output_browse_btn=batch_output_browse_btn,
        batch_template_label=batch_template_label,
        batch_filename_var=batch_filename_var,
        batch_filename_entry=batch_filename_entry,
        batch_convert_btn=batch_convert_btn,
        controls=controls,
    )
