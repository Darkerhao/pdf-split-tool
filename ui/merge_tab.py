from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass
class MergeTabWidgets:
    frame: ttk.LabelFrame
    listbox: tk.Listbox
    scrollbar: ttk.Scrollbar
    buttons_frame: ttk.Frame
    add_btn: ttk.Button
    remove_btn: ttk.Button
    up_btn: ttk.Button
    down_btn: ttk.Button
    clear_btn: ttk.Button
    start_btn: ttk.Button
    controls: list[tk.Widget]


def build_merge_tab(parent) -> MergeTabWidgets:
    frame = ttk.LabelFrame(parent, text="合并管理器")
    frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    listbox = tk.Listbox(frame, selectmode=tk.EXTENDED)
    listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    scrollbar.grid(row=0, column=1, sticky="ns", pady=4)
    listbox.configure(yscrollcommand=scrollbar.set)

    buttons_frame = ttk.Frame(frame)
    buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
    for column in range(8):
        buttons_frame.columnconfigure(column, weight=1)

    add_btn = ttk.Button(buttons_frame, text="添加 PDF")
    add_btn.grid(row=0, column=0, padx=4)

    remove_btn = ttk.Button(buttons_frame, text="移除选中")
    remove_btn.grid(row=0, column=1, padx=4)

    up_btn = ttk.Button(buttons_frame, text="上移")
    up_btn.grid(row=0, column=2, padx=4)

    down_btn = ttk.Button(buttons_frame, text="下移")
    down_btn.grid(row=0, column=3, padx=4)

    clear_btn = ttk.Button(buttons_frame, text="清空列表")
    clear_btn.grid(row=0, column=4, padx=4)

    ttk.Separator(buttons_frame).grid(row=0, column=5, sticky="ew", padx=8)

    start_btn = ttk.Button(buttons_frame, text="开始合并")
    start_btn.grid(row=0, column=6, padx=4)

    controls = [listbox, add_btn, remove_btn, up_btn, down_btn, clear_btn, start_btn]
    return MergeTabWidgets(
        frame=frame,
        listbox=listbox,
        scrollbar=scrollbar,
        buttons_frame=buttons_frame,
        add_btn=add_btn,
        remove_btn=remove_btn,
        up_btn=up_btn,
        down_btn=down_btn,
        clear_btn=clear_btn,
        start_btn=start_btn,
        controls=controls,
    )
