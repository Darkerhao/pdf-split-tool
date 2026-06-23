PDF 工具箱（拆分 / 合并 / 预览）

项目简介
本项目提供一个简单易用的 GUI 工具，支持：
- 按范围拆分 PDF（多范围=多文件；单范围=单文件）
- 按章节拆分 PDF（支持手动章节范围与自动章节拆分）
- 拆成单页（每页生成一个 PDF）
- 预览拆分结果（显示将生成几个文件、每个文件的页码范围与页数）
- 合并多个 PDF 到一个 PDF
- EPUB 转 PDF（支持单文件/批量，优先使用 Python 库，失败后回退到 Calibre，带进度与可取消）
- 拖拽导入输入文件（可选安装 tkinterdnd2）
- 最近文件菜单（记忆最近 8 个）
- 多语言切换（中文/英文）、快捷键支持
- 合并管理器（可拖拽排序）
- 分段导出命名模板（自定义文件名格式）
- 打开输出目录

运行方式
方式一：直接运行 Python 脚本
1) 安装依赖：
   pip install PyPDF2
   # 可选（启用拖拽输入）
   pip install tkinterdnd2
   # 可选（启用 EPUB 转 PDF）
   # 方案一：使用 Python 库（推荐，无需额外安装）
   pip install ebooklib reportlab html2text
   # 方案二：使用 Calibre（功能更强大）
   # 请安装 Calibre，并确保命令 ebook-convert 可用：
   # https://calibre-ebook.com/download
2) 运行 GUI：
   python split_pdf_gui.py
3）打包
  pyinstaller split_pdf_gui.spec

方式二：使用打包好的可执行文件
- 双击 dist/split_pdf_gui.exe（如需新版功能，请按“打包为 EXE”章节重新打包）

功能说明
1. 按范围拆分
- 输入页码范围，如：1-155, 156-245（支持中文逗号“，”）
- 多段范围：对每一段生成一个文件，文件名会在输出名后追加“_起-止”，例如：
  输出名为 output.pdf，则生成：output_1-155.pdf、output_156-245.pdf
- 单段范围：生成一个文件，直接使用你在“输出 PDF 文件”栏里填写的文件名（保持与旧版行为一致）
- 页码从 1 开始；超出总页数的范围会被自动裁剪；start > end 会自动调整为升序

2. 拆成单页
- 将每一页单独导出为一个 PDF 文件，输出名会在末尾追加 _page_序号

3. 按章节拆分
- 支持手动填写章节范围并按行导出，每行章节范围生成一个文件
- 支持自动按章节拆分，适合已有章节结构的 PDF

4. 预览拆分结果
- 在真正导出前，显示将要生成几个文件、每个文件的页码范围与页数
- 无效范围会在预览中标注并被跳过

5. 合并 PDF
- 选择多个 PDF 文件，合并为一个 PDF 输出
 - 使用“合并管理器”可添加/移除/上移/下移/拖拽排序，点击“确定合并”开始

6. 拖拽、最近文件、多语言、快捷键、输出目录
- 可把 PDF 直接拖进“输入 PDF 文件”输入框（需安装 tkinterdnd2）
- 顶部“最近”菜单展示最近 8 个 PDF
- 语言切换：工具栏右侧语言按钮（中文/EN）
- 可通过工具栏按钮直接打开当前输出目录
- 快捷键：
  - Ctrl+P：预览拆分
  - Ctrl+Enter：按范围拆分
  - Ctrl+M：打开合并管理器
  - Ctrl+L / Ctrl+D：切换浅色/深色主题

使用步骤（GUI）
1) 选择“输入 PDF 文件”
2) 设置“输出 PDF 文件”路径（用于单段范围文件名或作为多段范围的命名前缀与输出目录）
3) 在“页码范围”中填写如 1-155, 156-245
4) 可先点击“预览拆分结果”确认将生成的文件与页数
5) 点击“按范围拆分”或“拆成单页”；若需合并，点击“合并 PDF”并选择多个文件

EPUB 转 PDF（GUI）
1) 在“EPUB 转 PDF”区块中选择输入的 .epub 文件与输出 .pdf 文件
2) 选择纸张（a4/a5/letter/legal）
3) 点击“开始转换”；若系统已安装 Calibre 且 ebook-convert 在 PATH 中，会显示转换进度
4) 可随时点击“取消运行”中止
5) 批量转换时，在“批量 EPUB 转 PDF”区块中添加多个 .epub，选择输出目录、纸张与文件名模板后开始转换

注意：
- 程序会优先尝试使用 Python 库（ebooklib + reportlab）进行转换，无需安装额外软件
- 如果 Python 库转换失败，会自动尝试使用 Calibre 的 ebook-convert
- Windows 安装 Calibre 时可勾选"Add to PATH"；若未加入 PATH，本工具会尝试在常见安装目录中查找
- 若仍无法找到，请手动将 Calibre 的安装目录加入系统环境变量 PATH

命令行脚本（可选）
也可使用 split_pdf.py 在命令行拆分：
  python split_pdf.py input.pdf output.pdf 5-10 12-15
或每页导出：
  python split_pdf.py input.pdf --each

打包为 EXE（可选）
1) 安装依赖：
   pip install pyinstaller PyPDF2
2) 使用项目内的 spec 打包（推荐）：
   pyinstaller split_pdf_gui.spec
   生成的可执行文件位于 dist/ 目录
3) 或者直接命令打包（需显式补上 GUI 启动模块）：
   pyinstaller --noconsole --onefile --name split_pdf_gui --hidden-import split_pdf_gui_app split_pdf_gui.py

常见问题
- 预览显示“超出范围，跳过”：说明输入的起止超出了 PDF 实际页数，导出时会跳过无效段
- 使用中文逗号也可分隔多个范围：例如 1-3，5，7-9
- 如果出现“权限不足/无法写入”，请检查输出目录是否可写，或更换输出路径

变更说明（相对旧版）
- 修复“按范围拆分”原来只输出一个合并文件的问题：现在多段范围将生成多个文件，单段范围保持沿用原单文件导出行为
- 修复“按范围拆分”对超范围页码直接报错的问题：现在会自动裁剪到有效页码，完全无效的范围会被跳过
- 修复 GUI 中“开始转换”按钮调用 EPUB 转 PDF 时缺少任务上下文的问题
- 修复“按章节拆分”实际按每 5 章合并输出的问题：现在手动填写章节范围时，每行章节生成一个文件
- 新增“预览拆分结果”与“合并 PDF”
- 优化范围解析与容错（支持中文逗号、自动裁剪页码、start>end 自动纠正）
- 新增拖拽导入、最近文件、多语言与快捷键、合并排序管理器
- 新增命名模板：支持 {name} {start} {end} {index}，默认 {name}_{start}-{end}.pdf
- 新增 EPUB 转 PDF：基于 Calibre 的 ebook-convert，支持纸张选择、进度与可取消

英文版（English README）
PDF Toolbox (Split / Merge / Preview)

Overview
This desktop GUI helps you split and merge PDFs with ease. Highlights:
- Split by ranges (multiple ranges = multiple files; single range = one file)
- Split by chapters (manual ranges or automatic chapter detection)
- Split into single pages
- Preview the output before exporting
- Merge multiple PDFs into one
- Convert EPUB to PDF (single file or batch; Python libraries first, Calibre fallback)
- Drag-and-drop to load input (optional dependency)
- Recent files menu (remembers last 8)
- Language switch (ZH/EN) and keyboard shortcuts
- Merge Manager with drag-to-reorder
- Naming template for range outputs
- Open the current output directory from the toolbar

Install & Run
1) Install dependencies:
   pip install PyPDF2
   # Optional for drag-and-drop
   pip install tkinterdnd2
   # Optional for EPUB conversion without Calibre
   pip install ebooklib reportlab html2text
2) Start the GUI:
   python split_pdf_gui.py

Shortcuts
- Ctrl+P: Preview split
- Ctrl+Enter: Split by ranges
- Ctrl+M: Open Merge Manager
- Ctrl+L / Ctrl+D: Toggle Light/Dark theme

Naming Template
- Default: {name}_{start}-{end}.pdf
- Supported variables: {name}, {start}, {end}, {index}
  - name: base output name without extension
  - start/end: 1-based page numbers, auto-clamped to valid range
  - index: segment index starting from 1

Build to EXE (optional)
- Recommended: `pyinstaller split_pdf_gui.spec`
- Direct command also works when adding the hidden import:
  `pyinstaller --noconsole --onefile --name split_pdf_gui --hidden-import split_pdf_gui_app split_pdf_gui.py`

Screenshots / Demo GIF
- Expected placeholder files can be placed under `docs/`:
  - `docs/main-ui.png`
  - `docs/merge-manager.png`
  - `docs/preview.png`
  - `docs/demo.gif`
- See `docs/README-images.md` for capture guidance.
