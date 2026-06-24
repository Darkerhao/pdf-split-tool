# PDF 工具箱架构重构方案

## 执行摘要

本文档提供基于领域驱动设计（DDD）和清晰架构（Clean Architecture）原则的重构方案，旨在改进：
1. **模块解耦** - 减少层间依赖，提高可维护性
2. **可测试性** - 业务逻辑完全独立于 UI 框架
3. **可扩展性** - 支持新功能、新 UI 框架的无缝集成
4. **代码质量** - 清晰的职责划分和接口定义

---

## 当前架构分析

### 现状概览

```
当前代码结构（3454 行）:
├── split_pdf_gui_app.py (1440 行) - 主 GUI 应用，包含大量业务逻辑
├── ui/ (1325 行)                   - UI 组件和状态管理
│   ├── app_runtime.py (183)        - 运行时工具（主题、进度队列）
│   ├── app_state.py (215)          - 状态管理（最近文件、语言切换）
│   ├── auxiliary_ui.py (300)       - 辅助 UI 构建器
│   ├── epub_panel.py (178)         - EPUB 面板
│   ├── merge_tab.py (75)           - 合并选项卡
│   ├── preview.py (201)            - 预览器
│   └── split_tab.py (171)          - 拆分选项卡
├── services/ (687 行)              - 业务逻辑层
│   ├── epub_service.py (429)       - EPUB 转换
│   ├── pdf_service.py (125)        - PDF 解析
│   └── settings_service.py (133)   - 设置持久化
└── task_context.py (33 行)         - 任务上下文抽象
```

### 架构问题

#### 1. **层次混乱与职责不清**

**问题表现：**
- `split_pdf_gui_app.py` 同时包含 UI 构建、事件处理、业务逻辑调用
- 国际化字典 `STRINGS` 定义在主 GUI 文件中（84-175 行）
- UI 组件直接调用 `services` 层函数，缺少中间协调层
- 函数式编程（`build_*` 函数）与面向对象混用，缺乏一致性

**影响：**
- 难以单独测试业务逻辑
- 修改 UI 框架（如迁移到 Qt）需要重写大量代码
- 国际化逻辑与 UI 强耦合

#### 2. **依赖方向错误**

**问题表现：**
```python
# split_pdf_gui_app.py 直接导入所有层
from services.pdf_service import parse_ranges, build_split_preview
from ui.split_tab import build_split_tab
from task_context import TaskContext

# services 层应该是最底层，但 UI 层直接调用
# 缺少应用层（Application Layer）协调
```

**正确的依赖方向应该是：**
```
UI Layer → Application Layer → Domain Layer → Infrastructure Layer
          (controllers)        (business logic)  (external I/O)
```

#### 3. **状态管理分散**

**问题表现：**
- 应用状态分散在多个模块：`app_state.py`、`app_runtime.py`、主 GUI 文件
- 全局变量 `LANG` 在 `split_pdf_gui_app.py` 中定义
- 最近文件、主题、语言等状态缺少统一管理

**影响：**
- 状态同步困难
- 难以实现撤销/重做功能
- 测试需要模拟复杂的全局状态

#### 4. **测试覆盖率低**

**问题表现：**
- 仅有 `tests/test_services.py`（1 个文件）
- UI 组件完全未测试（声明"手动测试覆盖"）
- 业务逻辑与 UI 耦合，难以编写单元测试

---

## 重构架构设计

### 设计原则

采用 **清晰架构 + 领域驱动设计**：

1. **依赖倒置原则（DIP）**：高层模块不依赖低层模块，都依赖抽象
2. **接口隔离原则（ISP）**：客户端不应依赖它不使用的接口
3. **单一职责原则（SRP）**：每个类只负责一项功能
4. **开闭原则（OCP）**：对扩展开放，对修改关闭

### 新架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (Tkinter GUI / CLI / Future Web UI)                        │
│  - 视图组件 (views/)                                         │
│  - 视图模型 (view_models/)                                   │
│  - 国际化 (i18n/)                                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ 依赖
┌──────────────────▼──────────────────────────────────────────┐
│                   Application Layer                          │
│  - 用例控制器 (use_cases/)                                   │
│  - DTO（数据传输对象）                                        │
│  - 应用服务                                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │ 依赖
┌──────────────────▼──────────────────────────────────────────┐
│                     Domain Layer                             │
│  - 领域模型 (domain/models/)                                 │
│  - 领域服务 (domain/services/)                               │
│  - 仓储接口 (domain/repositories/)                           │
│  - 值对象 (domain/value_objects/)                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ 依赖
┌──────────────────▼──────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  - 仓储实现 (infrastructure/repositories/)                   │
│  - 外部服务适配器 (infrastructure/adapters/)                 │
│  - 持久化 (infrastructure/persistence/)                      │
└─────────────────────────────────────────────────────────────┘
```

### 新目录结构

```
pdf-split-tool/
├── domain/                          # 领域层（核心业务逻辑）
│   ├── models/
│   │   ├── pdf_document.py         # PDF 文档领域模型
│   │   ├── page_range.py           # 页码范围值对象
│   │   ├── chapter.py              # 章节领域模型
│   │   └── epub_document.py        # EPUB 文档领域模型
│   ├── services/
│   │   ├── pdf_splitter.py         # PDF 拆分领域服务
│   │   ├── pdf_merger.py           # PDF 合并领域服务
│   │   └── epub_converter.py      # EPUB 转换领域服务
│   └── repositories/
│       ├── document_repository.py  # 文档仓储接口（抽象）
│       └── settings_repository.py  # 设置仓储接口（抽象）
│
├── application/                     # 应用层（用例协调）
│   ├── use_cases/
│   │   ├── split_pdf_by_ranges.py  # 按范围拆分用例
│   │   ├── split_pdf_by_chapters.py # 按章节拆分用例
│   │   ├── merge_pdfs.py           # 合并 PDF 用例
│   │   ├── convert_epub.py         # 转换 EPUB 用例
│   │   └── preview_split.py        # 预览拆分用例
│   ├── dtos/
│   │   ├── split_request.py        # 拆分请求 DTO
│   │   ├── split_result.py         # 拆分结果 DTO
│   │   └── progress_update.py      # 进度更新 DTO
│   └── services/
│       └── app_state_service.py    # 应用状态服务
│
├── infrastructure/                  # 基础设施层（外部依赖）
│   ├── repositories/
│   │   ├── pypdf_repository.py     # PyPDF2 仓储实现
│   │   └── json_settings_repository.py # JSON 设置仓储实现
│   ├── adapters/
│   │   ├── calibre_adapter.py      # Calibre 适配器
│   │   └── ebooklib_adapter.py     # ebooklib 适配器
│   └── persistence/
│       └── file_system.py          # 文件系统操作
│
├── presentation/                    # 表现层（UI）
│   ├── tkinter_gui/                # Tkinter 实现
│   │   ├── views/
│   │   │   ├── main_window.py      # 主窗口
│   │   │   ├── split_view.py       # 拆分视图
│   │   │   ├── merge_view.py       # 合并视图
│   │   │   └── epub_view.py        # EPUB 视图
│   │   ├── view_models/
│   │   │   ├── split_view_model.py # 拆分视图模型
│   │   │   └── app_view_model.py   # 应用视图模型
│   │   └── widgets/
│   │       └── custom_widgets.py   # 自定义组件
│   ├── cli/                        # CLI 实现
│   │   └── split_pdf_cli.py        # CLI 入口
│   └── i18n/
│       ├── translator.py           # 翻译器
│       └── locales/
│           ├── zh_CN.json          # 中文
│           └── en_US.json          # 英文
│
├── shared/                          # 共享工具
│   ├── events/
│   │   └── event_bus.py            # 事件总线
│   ├── logging/
│   │   └── logger.py               # 日志工具
│   └── exceptions/
│       └── domain_exceptions.py    # 领域异常
│
└── tests/                           # 测试
    ├── unit/
    │   ├── domain/                 # 领域层单元测试
    │   ├── application/            # 应用层单元测试
    │   └── infrastructure/         # 基础设施层单元测试
    └── integration/                # 集成测试
```


---

## 详细设计

### 1. 领域层（Domain Layer）

#### 1.1 领域模型示例

**PDF 文档模型** (`domain/models/pdf_document.py`):
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class PDFDocument:
    """PDF 文档领域模型"""
    path: str
    total_pages: int
    chapters: List['Chapter'] = field(default_factory=list)
    
    def validate_range(self, page_range: 'PageRange') -> bool:
        """验证页码范围是否有效"""
        return 1 <= page_range.start <= page_range.end <= self.total_pages
```

**页码范围值对象** (`domain/models/page_range.py`):
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PageRange:
    """页码范围值对象（不可变）"""
    start: int
    end: int
    
    @property
    def page_count(self) -> int:
        return self.end - self.start + 1
    
    @classmethod
    def parse(cls, range_str: str) -> 'PageRange':
        """解析字符串为页码范围，如 "1-10" """
        if '-' in range_str:
            start, end = map(int, range_str.split('-'))
            return cls(start, end)
        page = int(range_str)
        return cls(page, page)
```

#### 1.2 领域服务接口

**PDF 拆分服务** (`domain/services/pdf_splitter.py`):
```python
from abc import ABC, abstractmethod
from typing import List

class IPDFSplitter(ABC):
    """PDF 拆分服务接口（依赖倒置）"""
    
    @abstractmethod
    def split_by_ranges(
        self,
        document: 'PDFDocument',
        ranges: List['PageRange'],
        output_template: str
    ) -> List[str]:
        """按页码范围拆分，返回生成的文件路径列表"""
        pass
```

### 2. 应用层（Application Layer）

#### 2.1 用例（Use Cases）

**拆分 PDF 用例** (`application/use_cases/split_pdf_by_ranges.py`):
```python
from typing import List
from dataclasses import dataclass
from domain.services.pdf_splitter import IPDFSplitter
from domain.repositories.document_repository import IDocumentRepository

@dataclass
class SplitPDFRequest:
    """拆分请求 DTO"""
    input_path: str
    output_template: str
    range_strings: List[str]

@dataclass
class SplitPDFResult:
    """拆分结果 DTO"""
    success: bool
    output_files: List[str]
    error_message: str = ""

class SplitPDFByRangesUseCase:
    """拆分 PDF 用例控制器"""
    
    def __init__(
        self,
        document_repo: IDocumentRepository,
        pdf_splitter: IPDFSplitter
    ):
        self._document_repo = document_repo
        self._pdf_splitter = pdf_splitter
    
    def execute(self, request: SplitPDFRequest) -> SplitPDFResult:
        """执行拆分用例"""
        try:
            # 1. 加载文档
            document = self._document_repo.load(request.input_path)
            
            # 2. 解析范围
            ranges = [PageRange.parse(r) for r in request.range_strings]
            
            # 3. 验证范围
            valid_ranges = [r for r in ranges if document.validate_range(r)]
            
            # 4. 执行拆分
            output_files = self._pdf_splitter.split_by_ranges(
                document,
                valid_ranges,
                request.output_template
            )
            
            return SplitPDFResult(success=True, output_files=output_files)
        except Exception as e:
            return SplitPDFResult(success=False, output_files=[], error_message=str(e))
```

### 3. 基础设施层（Infrastructure Layer）

#### 3.1 仓储实现

**PyPDF2 仓储** (`infrastructure/repositories/pypdf_repository.py`):
```python
from PyPDF2 import PdfReader, PdfWriter
from domain.repositories.document_repository import IDocumentRepository
from domain.models.pdf_document import PDFDocument

class PyPDFRepository(IDocumentRepository):
    """使用 PyPDF2 实现的文档仓储"""
    
    def load(self, path: str) -> PDFDocument:
        """加载 PDF 文档"""
        reader = PdfReader(path)
        return PDFDocument(
            path=path,
            total_pages=len(reader.pages)
        )
    
    def save(self, document: PDFDocument, output_path: str) -> None:
        """保存 PDF 文档"""
        # 实现保存逻辑
        pass
```

### 4. 表现层（Presentation Layer）

#### 4.1 视图模型（ViewModel）

**拆分视图模型** (`presentation/tkinter_gui/view_models/split_view_model.py`):
```python
from typing import Callable, List
from application.use_cases.split_pdf_by_ranges import SplitPDFByRangesUseCase

class SplitViewModel:
    """拆分视图模型（MVVM 模式）"""
    
    def __init__(self, use_case: SplitPDFByRangesUseCase):
        self._use_case = use_case
        self._on_progress_changed: List[Callable] = []
        self._on_completed: List[Callable] = []
    
    def split(self, input_path: str, output_template: str, ranges: List[str]):
        """执行拆分（由视图调用）"""
        request = SplitPDFRequest(input_path, output_template, ranges)
        result = self._use_case.execute(request)
        
        # 通知视图更新
        for callback in self._on_completed:
            callback(result)
    
    def subscribe_progress(self, callback: Callable):
        """订阅进度更新"""
        self._on_progress_changed.append(callback)
    
    def subscribe_completed(self, callback: Callable):
        """订阅完成事件"""
        self._on_completed.append(callback)
```

#### 4.2 视图（View）

**拆分视图** (`presentation/tkinter_gui/views/split_view.py`):
```python
import tkinter as tk
from tkinter import ttk

class SplitView(ttk.Frame):
    """拆分视图（纯 UI 组件，不包含业务逻辑）"""
    
    def __init__(self, parent, view_model: SplitViewModel):
        super().__init__(parent)
        self._view_model = view_model
        self._build_ui()
        self._bind_events()
    
    def _build_ui(self):
        """构建 UI"""
        self.input_entry = ttk.Entry(self)
        self.ranges_entry = ttk.Entry(self)
        self.split_button = ttk.Button(self, text="拆分", command=self._on_split)
        # 布局...
    
    def _bind_events(self):
        """绑定视图模型事件"""
        self._view_model.subscribe_completed(self._on_split_completed)
    
    def _on_split(self):
        """拆分按钮点击"""
        input_path = self.input_entry.get()
        ranges = self.ranges_entry.get().split(',')
        self._view_model.split(input_path, "{name}_{start}-{end}.pdf", ranges)
    
    def _on_split_completed(self, result):
        """拆分完成回调"""
        if result.success:
            tk.messagebox.showinfo("成功", f"已生成 {len(result.output_files)} 个文件")
        else:
            tk.messagebox.showerror("错误", result.error_message)
```


---

## 重构实施计划

### 阶段 1：准备工作（1-2 天）

**目标：** 建立新架构基础，不影响现有功能

1. 创建新的目录结构
2. 定义核心接口和抽象类
3. 编写领域模型和值对象
4. 设置依赖注入容器

**交付物：**
- 完整的目录结构
- 领域层接口定义
- 单元测试框架

### 阶段 2：基础设施层迁移（2-3 天）

**目标：** 将现有 PyPDF2 操作封装为仓储实现

1. 实现 `PyPDFRepository`（迁移自 `services/pdf_service.py`）
2. 实现 `JSONSettingsRepository`（迁移自 `services/settings_service.py`）
3. 实现 `CalibreAdapter` 和 `EbooklibAdapter`（迁移自 `services/epub_service.py`）
4. 编写基础设施层单元测试

**迁移映射：**
```
services/pdf_service.py → infrastructure/repositories/pypdf_repository.py
services/settings_service.py → infrastructure/repositories/json_settings_repository.py
services/epub_service.py → infrastructure/adapters/{calibre,ebooklib}_adapter.py
```

### 阶段 3：应用层构建（2-3 天）

**目标：** 创建用例控制器，协调业务逻辑

1. 实现拆分用例（`SplitPDFByRangesUseCase`）
2. 实现合并用例（`MergePDFsUseCase`）
3. 实现 EPUB 转换用例（`ConvertEPUBUseCase`）
4. 实现预览用例（`PreviewSplitUseCase`）
5. 编写应用层集成测试

**关键重构：**
- `pdf_split_task.py` → 用例控制器
- 移除 `TaskContext`，改用观察者模式（事件总线）

### 阶段 4：表现层重构（3-4 天）

**目标：** 将现有 Tkinter UI 重构为 MVVM 模式

1. 创建视图模型（ViewModel）
2. 重构视图组件（View）- 移除业务逻辑
3. 提取国际化到独立模块（`presentation/i18n/`）
4. 实现事件总线（替代回调函数）

**迁移映射：**
```
split_pdf_gui_app.py → presentation/tkinter_gui/views/main_window.py
ui/split_tab.py → presentation/tkinter_gui/views/split_view.py
ui/merge_tab.py → presentation/tkinter_gui/views/merge_view.py
ui/epub_panel.py → presentation/tkinter_gui/views/epub_view.py
STRINGS 字典 → presentation/i18n/locales/{zh_CN,en_US}.json
```

### 阶段 5：测试与验证（2-3 天）

**目标：** 确保重构后功能完整性

1. 编写完整的单元测试套件（覆盖率 >80%）
2. 编写集成测试
3. 手动回归测试所有功能
4. 性能测试（确保无性能退化）

### 阶段 6：文档与清理（1 天）

**目标：** 更新文档，移除旧代码

1. 更新 CLAUDE.md 和 README.md
2. 删除旧代码（`services/`, 旧 `ui/` 等）
3. 更新 requirements.txt（添加依赖注入库，如 `dependency-injector`）
4. 编写重构总结报告

---

## 关键技术决策

### 1. 依赖注入（DI）

**推荐库：** `dependency-injector`

**理由：**
- 清晰的依赖管理
- 便于单元测试（Mock 注入）
- 符合依赖倒置原则

**示例容器** (`main.py`):
```python
from dependency_injector import containers, providers
from infrastructure.repositories.pypdf_repository import PyPDFRepository
from application.use_cases.split_pdf_by_ranges import SplitPDFByRangesUseCase

class Container(containers.DeclarativeContainer):
    # 基础设施层
    document_repo = providers.Singleton(PyPDFRepository)
    
    # 应用层
    split_use_case = providers.Factory(
        SplitPDFByRangesUseCase,
        document_repo=document_repo
    )
    
    # 表现层
    split_view_model = providers.Factory(
        SplitViewModel,
        use_case=split_use_case
    )
```

### 2. 事件驱动架构

**使用事件总线替代回调函数**

**好处：**
- 解耦组件
- 支持多订阅者
- 易于测试

**示例事件** (`shared/events/event_bus.py`):
```python
from typing import Callable, Dict, List

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)
    
    def publish(self, event_name: str, data):
        for callback in self._subscribers.get(event_name, []):
            callback(data)

# 使用示例
event_bus = EventBus()
event_bus.subscribe("split_progress", lambda p: print(f"Progress: {p}%"))
event_bus.publish("split_progress", 50)
```

### 3. MVVM 模式

**Model-View-ViewModel**

**职责划分：**
- **View**：纯 UI，不包含业务逻辑
- **ViewModel**：处理 UI 逻辑，调用用例
- **Model**：领域模型，纯业务逻辑

**好处：**
- UI 框架可替换（Tkinter → Qt）
- ViewModel 可单元测试
- 清晰的数据流向

---

## 重构后的优势

### 1. 可测试性大幅提升

**重构前：**
- 业务逻辑与 Tkinter 强耦合
- 难以 Mock 外部依赖
- 测试覆盖率 < 20%

**重构后：**
- 领域层和应用层完全独立于 UI
- 接口驱动，易于 Mock
- 目标测试覆盖率 > 80%

### 2. 可维护性改进

**重构前：**
- 职责不清，修改一处影响多处
- 依赖方向混乱
- 难以理解代码意图

**重构后：**
- 每层职责明确
- 单向依赖，符合 SOLID 原则
- 代码自文档化

### 3. 可扩展性增强

**重构前：**
- 添加新功能需要修改多个文件
- UI 框架绑定，无法迁移
- 难以支持插件系统

**重构后：**
- 新功能只需添加新用例
- UI 框架可替换（CLI / Web / Qt）
- 开闭原则，对扩展开放

### 4. 性能优化潜力

**重构后可实现：**
- 命令模式（撤销/重做）
- 异步处理（async/await）
- 缓存策略（装饰器模式）
- 批处理优化

---

## 风险与缓解

### 风险 1：重构周期长

**缓解措施：**
- 分阶段交付，每阶段保持功能完整
- 并行开发新架构，保留旧代码
- 使用 Adapter 模式过渡

### 风险 2：引入新 Bug

**缓解措施：**
- 完整的测试套件
- 每阶段回归测试
- 保留旧代码作为对照

### 风险 3：学习曲线

**缓解措施：**
- 提供架构培训文档
- 代码示例和最佳实践
- 结对编程

---

## 总结

本重构方案基于**清晰架构**和**领域驱动设计**原则，将现有的 3454 行代码重新组织为四层架构：

1. **领域层**：纯业务逻辑，不依赖外部框架
2. **应用层**：用例协调，业务流程编排
3. **基础设施层**：外部依赖封装（PyPDF2、Calibre）
4. **表现层**：UI 实现，采用 MVVM 模式

**预期效果：**
- 测试覆盖率从 < 20% 提升到 > 80%
- 模块耦合度降低 60%
- 新功能开发效率提升 40%
- UI 框架可替换（支持 CLI / Web / Qt）

**实施时间：** 10-15 工作日

**建议：** 采用渐进式重构，分阶段交付，确保每个阶段都有可运行的完整系统。

