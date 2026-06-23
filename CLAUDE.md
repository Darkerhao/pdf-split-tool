# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF 工具箱 - 一个支持 PDF 拆分/合并/预览 及 EPUB 转 PDF 的桌面应用。包含 CLI 脚本和 Tkinter GUI 应用。

## Architecture

```
split_pdf.py                  # CLI 入口：简单的 PDF 拆分脚本
split_pdf_gui.py             # GUI 启动入口，仅做懒加载，暴露核心服务函数
split_pdf_gui_app.py         # 主 Tkinter GUI（~1350 行，单文件但已按职责拆分到 ui/ 和 services/）
pdf_split_task.py            # PDF 拆分任务逻辑（按范围/按章节/自动章节）
task_context.py              # 任务上下文抽象（取消/进度上报），与 UI 解耦

ui/                           # UI 组件模块
  split_tab.py               # 拆分选项卡
  merge_tab.py               # 合并选项卡
  preview.py                 # PDF 预览器
  epub_panel.py              # EPUB 转换面板
  auxiliary_ui.py            # 工具栏/设置/预览的辅助 UI 构建
  app_state.py               # 最近文件、语言、主题等全局状态
  app_runtime.py             # 进度队列、主题应用、UI 开关控制

services/                     # 业务逻辑层
  pdf_service.py             # PDF 解析（范围/章节/预览/命名模板）
  epub_service.py            # EPUB 转 PDF
  settings_service.py        # 设置读写（JSON）
```

关键设计：
- `TaskContext`（task_context.py）是核心抽象，将取消/进度/完成/错误回调封装为 dataclass，业务逻辑不依赖 Tkinter。
- GUI 中后台任务通过 `threading.Thread` + `queue.Queue` + `root.after()` 轮询实现异步进度报告。
- 多语言通过 `STRINGS` 字典 + `T()` 函数实现，切换语言时刷新所有 widget 文本。
- 输出文件命名支持可配置模板（`{name}_{start}-{end}.pdf`）。

## Commands

```bash
# 激活虚拟环境
.venv/Scripts/activate

# 运行 CLI 版本
python split_pdf.py input.pdf output.pdf 5-10 12-15
python split_pdf.py input.pdf --each          # 拆成单页

# 运行 GUI 版本
python split_pdf_gui.py

# 构建 Windows exe（PyInstaller）
python -m PyInstaller split_pdf_gui.spec
```

## Dependencies

核心依赖：PyPDF2（PDF 操作）、tkinter（GUI，Python 内置）、可选 tkinterdnd2（拖拽支持）。

## Cursor 规则

遵循 .cursorrules 中的要求：PEP 8、类型提示、docstring、错误处理、模块化设计。
