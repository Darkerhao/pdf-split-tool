from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass(frozen=True)
class PreviewTabTexts:
    frame_title: str = "PDF 预览"
    input_label: str = "PDF 文件"
    browse_button: str = "浏览..."
    open_button: str = "打开预览"


@dataclass(frozen=True)
class SettingsTabTexts:
    frame_title: str = "设置"
    theme_label: str = "主题"
    light_button: str = "浅色"
    dark_button: str = "深色"
    language_label: str = "语言"
    zh_button: str = "中文"
    en_button: str = "EN"
    template_label: str = "命名模板"
    template_hint: str = "{name}=原文件名, {start}=起始页, {end}=结束页, {index}=序号"
    save_button: str = "保存设置"


@dataclass(frozen=True)
class ToolbarTexts:
    helper_label: str = "范围助手:"
    helper_every_button: str = "每 N 页拆分"
    helper_equal_button: str = "均分为 K 份"
    clear_button: str = "清空范围"
    template_label: str = "命名模板"
    recent_button: str = "最近"
    open_output_button: str = "打开输出目录"


@dataclass(frozen=True)
class EPUBPanelTexts:
    frame_title: str = "EPUB 转 PDF"
    input_label: str = "输入 EPUB 文件"
    output_label: str = "输出 PDF 文件"
    paper_label: str = "纸张大小"
    convert_button: str = "开始转换"
    batch_frame_title: str = "批量 EPUB 转 PDF"
    batch_hint: str = ""
    batch_add: str = "添加 EPUB"
    batch_remove: str = "移除选中"
    batch_clear: str = "清空列表"
    batch_paper_label: str = "批量纸张大小"
    batch_output_label: str = "批量输出目录"
    batch_template_label: str = "输出文件名模板"
    batch_convert: str = "开始批量转换"


def apply_epub_panel_texts(
    widgets,
    texts: EPUBPanelTexts | None = None,
) -> None:
    resolved = texts or EPUBPanelTexts()
    widgets.epub_frame.configure(text=resolved.frame_title)
    widgets.input_label.configure(text=resolved.input_label)
    widgets.output_label.configure(text=resolved.output_label)
    widgets.paper_label.configure(text=resolved.paper_label)
    widgets.convert_btn.configure(text=resolved.convert_button)
    widgets.batch_frame.configure(text=resolved.batch_frame_title)
    if resolved.batch_hint:
        widgets.batch_hint_label.configure(text=resolved.batch_hint)
    widgets.batch_add_btn.configure(text=resolved.batch_add)
    widgets.batch_remove_btn.configure(text=resolved.batch_remove)
    widgets.batch_clear_btn.configure(text=resolved.batch_clear)
    widgets.batch_paper_label.configure(text=resolved.batch_paper_label)
    widgets.batch_output_label.configure(text=resolved.batch_output_label)
    widgets.batch_template_label.configure(text=resolved.batch_template_label)
    widgets.batch_convert_btn.configure(text=resolved.batch_convert)


@dataclass
class PreviewTabWidgets:
    frame: ttk.LabelFrame
    input_label: ttk.Label
    input_var: tk.StringVar
    input_entry: ttk.Entry
    browse_btn: ttk.Button
    open_btn: ttk.Button
    controls: list[tk.Widget]


@dataclass
class SettingsTabWidgets:
    frame: ttk.LabelFrame
    theme_label: ttk.Label
    light_btn: ttk.Button
    dark_btn: ttk.Button
    language_label: ttk.Label
    zh_btn: ttk.Button
    en_btn: ttk.Button
    template_label: ttk.Label
    template_entry: ttk.Entry
    template_hint_label: ttk.Label
    save_btn: ttk.Button
    controls: list[tk.Widget]


@dataclass
class ToolbarWidgets:
    frame: ttk.Frame
    helper_label: ttk.Label
    helper_every_btn: ttk.Button
    helper_equal_btn: ttk.Button
    clear_btn: ttk.Button
    open_output_btn: ttk.Button
    template_label: ttk.Label
    name_template_entry: ttk.Entry
    recent_btn: ttk.Menubutton
    recent_menu: tk.Menu
    controls: list[tk.Widget]


def apply_preview_tab_texts(
    widgets: PreviewTabWidgets,
    texts: PreviewTabTexts | None = None,
) -> None:
    resolved = texts or PreviewTabTexts()
    widgets.frame.configure(text=resolved.frame_title)
    widgets.input_label.configure(text=resolved.input_label)
    widgets.browse_btn.configure(text=resolved.browse_button)
    widgets.open_btn.configure(text=resolved.open_button)


def apply_settings_tab_texts(
    widgets: SettingsTabWidgets,
    texts: SettingsTabTexts | None = None,
) -> None:
    resolved = texts or SettingsTabTexts()
    widgets.frame.configure(text=resolved.frame_title)
    widgets.theme_label.configure(text=resolved.theme_label)
    widgets.light_btn.configure(text=resolved.light_button)
    widgets.dark_btn.configure(text=resolved.dark_button)
    widgets.language_label.configure(text=resolved.language_label)
    widgets.zh_btn.configure(text=resolved.zh_button)
    widgets.en_btn.configure(text=resolved.en_button)
    widgets.template_label.configure(text=resolved.template_label)
    widgets.template_hint_label.configure(text=resolved.template_hint)
    widgets.save_btn.configure(text=resolved.save_button)


def apply_toolbar_texts(
    widgets: ToolbarWidgets,
    texts: ToolbarTexts | None = None,
    *,
    recent_text: str | None = None,
    open_output_text: str | None = None,
) -> None:
    resolved = texts or ToolbarTexts()
    widgets.helper_label.configure(text=resolved.helper_label)
    widgets.helper_every_btn.configure(text=resolved.helper_every_button)
    widgets.helper_equal_btn.configure(text=resolved.helper_equal_button)
    widgets.clear_btn.configure(text=resolved.clear_button)
    widgets.open_output_btn.configure(
        text=open_output_text if open_output_text is not None else resolved.open_output_button
    )
    widgets.template_label.configure(text=resolved.template_label)
    widgets.recent_btn.configure(text=recent_text if recent_text is not None else resolved.recent_button)


def build_preview_tab(parent, texts: PreviewTabTexts | None = None) -> PreviewTabWidgets:
    frame = ttk.LabelFrame(parent)
    frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    input_var = tk.StringVar()
    input_label = ttk.Label(frame)
    input_label.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    input_entry = ttk.Entry(frame, textvariable=input_var)
    input_entry.grid(row=0, column=1, sticky="ew", padx=4)

    browse_btn = ttk.Button(frame)
    browse_btn.grid(row=0, column=2, padx=8)

    open_btn = ttk.Button(frame, width=12)
    open_btn.grid(row=1, column=1, sticky="w", padx=4, pady=6)

    widgets = PreviewTabWidgets(
        frame=frame,
        input_label=input_label,
        input_var=input_var,
        input_entry=input_entry,
        browse_btn=browse_btn,
        open_btn=open_btn,
        controls=[input_entry, browse_btn, open_btn],
    )
    apply_preview_tab_texts(widgets, texts)
    return widgets


def build_settings_tab(parent, name_template_var: tk.StringVar, texts: SettingsTabTexts | None = None) -> SettingsTabWidgets:
    frame = ttk.LabelFrame(parent)
    frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    theme_label = ttk.Label(frame)
    theme_label.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    theme_frame = ttk.Frame(frame)
    theme_frame.grid(row=0, column=1, sticky="w", padx=4)
    light_btn = ttk.Button(theme_frame)
    light_btn.pack(side="left", padx=4)
    dark_btn = ttk.Button(theme_frame)
    dark_btn.pack(side="left", padx=4)

    language_label = ttk.Label(frame)
    language_label.grid(row=1, column=0, sticky="w", padx=8, pady=6)
    lang_frame = ttk.Frame(frame)
    lang_frame.grid(row=1, column=1, sticky="w", padx=4)
    zh_btn = ttk.Button(lang_frame)
    zh_btn.pack(side="left", padx=4)
    en_btn = ttk.Button(lang_frame)
    en_btn.pack(side="left", padx=4)

    template_label = ttk.Label(frame)
    template_label.grid(row=2, column=0, sticky="w", padx=8, pady=6)
    template_entry = ttk.Entry(frame, textvariable=name_template_var)
    template_entry.grid(row=2, column=1, sticky="ew", padx=4)
    template_hint_label = ttk.Label(frame, foreground="#666666")
    template_hint_label.grid(row=3, column=1, sticky="w", padx=4, pady=(0, 6))

    save_btn = ttk.Button(frame)
    save_btn.grid(row=4, column=1, sticky="w", padx=4, pady=6)

    widgets = SettingsTabWidgets(
        frame=frame,
        theme_label=theme_label,
        light_btn=light_btn,
        dark_btn=dark_btn,
        language_label=language_label,
        zh_btn=zh_btn,
        en_btn=en_btn,
        template_label=template_label,
        template_entry=template_entry,
        template_hint_label=template_hint_label,
        save_btn=save_btn,
        controls=[light_btn, dark_btn, zh_btn, en_btn, template_entry, save_btn],
    )
    apply_settings_tab_texts(widgets, texts)
    return widgets


def build_toolbar(
    parent,
    name_template_var: tk.StringVar,
    recent_text: str,
    open_output_text: str,
    texts: ToolbarTexts | None = None,
) -> ToolbarWidgets:
    frame = ttk.Frame(parent, padding=(12, 6))
    frame.grid(row=4, column=0, sticky="ew")
    frame.columnconfigure(10, weight=1)

    helper_label = ttk.Label(frame)
    helper_label.grid(row=0, column=0, padx=(0, 6))
    helper_every_btn = ttk.Button(frame)
    helper_every_btn.grid(row=0, column=1, padx=4)
    helper_equal_btn = ttk.Button(frame)
    helper_equal_btn.grid(row=0, column=2, padx=4)
    clear_btn = ttk.Button(frame)
    clear_btn.grid(row=0, column=3, padx=4)
    open_output_btn = ttk.Button(frame)
    open_output_btn.grid(row=0, column=4, padx=4)


    template_label = ttk.Label(frame)
    template_label.grid(row=0, column=5, padx=(12, 4))
    name_template_entry = ttk.Entry(frame, textvariable=name_template_var, width=26)
    name_template_entry.grid(row=0, column=6, padx=2)

    recent_btn = ttk.Menubutton(frame)
    recent_menu = tk.Menu(recent_btn, tearoff=0)
    recent_btn["menu"] = recent_menu
    recent_btn.grid(row=0, column=11, padx=(12, 2))

    widgets = ToolbarWidgets(
        frame=frame,
        helper_label=helper_label,
        helper_every_btn=helper_every_btn,
        helper_equal_btn=helper_equal_btn,
        clear_btn=clear_btn,
        open_output_btn=open_output_btn,
        template_label=template_label,
        name_template_entry=name_template_entry,
        recent_btn=recent_btn,
        recent_menu=recent_menu,
        controls=[helper_every_btn, helper_equal_btn, clear_btn, open_output_btn, name_template_entry, recent_btn],
    )
    apply_toolbar_texts(widgets, texts, recent_text=recent_text, open_output_text=open_output_text)
    return widgets
