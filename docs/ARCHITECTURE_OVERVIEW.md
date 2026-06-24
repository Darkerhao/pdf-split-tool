# PDF 工具箱架构总览

## 文档目的

本文档提供 PDF 工具箱项目的完整架构视图，帮助开发者快速理解：
- 整体架构设计（清晰架构 + 领域驱动设计）
- 各层职责和依赖关系
- 核心组件和接口
- 重构历史和进度

## 架构原则

### 设计原则

1. **依赖倒置原则 (DIP)** - 高层模块不依赖低层模块，都依赖抽象
2. **单一职责原则 (SRP)** - 每个类只负责一项功能
3. **开闭原则 (OCP)** - 对扩展开放，对修改关闭
4. **接口隔离原则 (ISP)** - 客户端不应依赖它不使用的接口

### 架构模式

- **清晰架构 (Clean Architecture)** - 分层架构，依赖单向流动
- **领域驱动设计 (DDD)** - 领域模型驱动设计
- **MVVM 模式** - 表现层使用 Model-View-ViewModel
- **用例模式 (Use Case)** - 应用层使用用例控制器

---

## 层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  表现层：UI 组件、视图模型、国际化                            │
│  依赖：Application Layer                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Application Layer                          │
│  应用层：用例控制器、DTO、应用服务                            │
│  依赖：Domain Layer                                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                     Domain Layer                             │
│  领域层：领域模型、领域服务接口、仓储接口                      │
│  依赖：无（纯业务逻辑）                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  基础设施层：仓储实现、外部服务适配器                          │
│  依赖：Domain Layer（实现其接口）                             │
└─────────────────────────────────────────────────────────────┘

                   ┌──────────────────┐
                   │   Shared Layer   │
                   │  共享工具和异常   │
                   └──────────────────┘
```

---

## 目录结构

```
pdf-split-tool/
├── domain/                          # 领域层（核心业务逻辑）
│   ├── models/                      # 领域模型
│   │   ├── pdf_document.py          # PDF 文档聚合根
│   │   ├── page_range.py            # 页码范围值对象
│   │   ├── chapter.py               # 章节模型
│   │   ├── epub_document.py         # EPUB 文档模型
│   │   └── app_settings.py          # 应用设置模型
│   ├── services/                    # 领域服务接口
│   │   ├── pdf_service.py           # PDF 拆分/合并接口
│   │   └── epub_service.py          # EPUB 转换接口
│   └── repositories/                # 仓储接口
│       ├── document_repository.py   # 文档仓储接口
│       └── settings_repository.py   # 设置仓储接口
│
├── application/                     # 应用层（用例协调）
│   ├── use_cases/                   # 用例控制器
│   │   ├── split_pdf_by_ranges.py   # 按范围拆分用例
│   │   ├── split_pdf_by_chapters.py # 按章节拆分用例
│   │   ├── split_pdf_each_page.py   # 拆分单页用例
│   │   ├── merge_pdfs.py            # 合并 PDF 用例
│   │   ├── convert_epub.py          # 转换 EPUB 用例
│   │   └── preview_split.py         # 预览拆分用例
│   ├── dtos/                        # 数据传输对象
│   │   ├── split_request.py         # 拆分请求
│   │   ├── split_result.py          # 拆分结果
│   │   ├── merge_request.py         # 合并请求
│   │   ├── merge_result.py          # 合并结果
│   │   ├── epub_request.py          # EPUB 请求
│   │   ├── epub_result.py           # EPUB 结果
│   │   └── preview_result.py        # 预览结果
│   └── services/                    # 应用服务
│       └── app_state_service.py     # 应用状态服务
│
├── infrastructure/                  # 基础设施层（外部依赖）
│   ├── repositories/                # 仓储实现
│   │   ├── pypdf_repository.py      # PyPDF2 文档仓储
│   │   └── json_settings_repository.py # JSON 设置仓储
│   ├── adapters/                    # 外部服务适配器
│   │   ├── calibre_adapter.py       # Calibre EPUB 转换器
│   │   └── epub_adapter.py          # Python EPUB 转换器
│   └── services/                    # 基础设施服务
│       └── pdf_splitter_service.py  # PDF 拆分/合并实现
│
├── presentation/                    # 表现层（UI）[待重构]
│   ├── tkinter_gui/                 # Tkinter 实现
│   │   ├── views/                   # 视图组件
│   │   ├── view_models/             # 视图模型
│   │   └── widgets/                 # 自定义组件
│   └── i18n/                        # 国际化
│       ├── translator.py            # 翻译器
│       └── locales/                 # 语言文件
│
├── shared/                          # 共享工具
│   ├── events/
│   │   └── event_bus.py             # 事件总线
│   ├── logging/
│   │   └── logger.py                # 日志工具
│   └── exceptions/
│       └── domain_exceptions.py     # 领域异常
│
└── tests/                           # 测试
    └── unit/
        ├── domain/                  # 领域层测试（22 个）
        ├── infrastructure/          # 基础设施层测试（7 个）
        └── application/             # 应用层测试（33 个）
```

---

## 各层详细说明

### 1. 共享层 (Shared Layer)

**职责：** 提供跨层使用的工具和异常定义

**核心组件：**
- `EventBus` - 事件总线，解耦组件通信
- `DomainException` - 领域异常基类
  - `DocumentNotFoundError` - 文档不存在
  - `InvalidDocumentFormatError` - 文档格式无效
  - `InvalidPageRangeError` - 页码范围无效
  - `ChaptersNotFoundError` - 章节不存在
  - `ConversionFailedError` - 转换失败

**依赖：** 无

**状态：** ✅ 已完成

---

### 2. 领域层 (Domain Layer)

**职责：** 纯业务逻辑，不依赖外部框架和库

**核心组件：**

#### 2.1 领域模型 (Models)

- **PDFDocument** - PDF 文档聚合根
  - 属性：path, total_pages, chapters, metadata
  - 方法：validate_range(), normalize_ranges(), get_chapter_at_page()
  
- **PageRange** - 页码范围值对象（不可变）
  - 属性：start, end
  - 方法：page_count, parse()
  
- **Chapter** - 章节模型
  - 属性：title, start_page, end_page, level
  - 方法：page_range, page_count
  
- **EPUBDocument** - EPUB 文档模型
  - 属性：path, title, author, metadata
  
- **AppSettings** - 应用设置模型
  - 属性：language, recent_files, output_template, etc.

#### 2.2 领域服务接口 (Services)

- **IPDFSplitter** - PDF 拆分服务接口
  - split_by_ranges() - 按范围拆分
  - split_into_single_pages() - 拆分单页
  - split_by_chapters() - 按章节拆分
  
- **IPDFMerger** - PDF 合并服务接口
  - merge() - 合并多个 PDF
  
- **IEPUBConverter** - EPUB 转换服务接口
  - convert() - 转换为 PDF
  - is_available() - 检查可用性

#### 2.3 仓储接口 (Repositories)

- **IDocumentRepository** - 文档仓储接口
  - load() - 加载文档
  
- **ISettingsRepository** - 设置仓储接口
  - load() - 加载设置
  - save() - 保存设置
  - add_recent_file() - 添加最近文件
  - clear_recent_files() - 清空最近文件

**依赖：** 无

**测试：** 22 个单元测试 ✅

**状态：** ✅ 已完成

---

### 3. 基础设施层 (Infrastructure Layer)

**职责：** 实现领域层接口，处理外部依赖（文件系统、第三方库）

**核心组件：**

#### 3.1 仓储实现 (Repositories)

- **PyPDFRepository** - 使用 PyPDF2 实现文档仓储
  - 加载 PDF 文档
  - 提取页数和元数据
  - 提取章节信息（从书签）
  
- **JSONSettingsRepository** - 使用 JSON 实现设置仓储
  - JSON 文件持久化
  - 最近文件管理（去重、限制 8 个）
  - 路径规范化

#### 3.2 服务实现 (Services)

- **PyPDFSplitter** - 使用 PyPDF2 实现 PDF 拆分
  - 按范围拆分
  - 拆分单页
  - 按章节拆分
  - 文件名模板渲染
  
- **PyPDFMerger** - 使用 PyPDF2 实现 PDF 合并
  - 合并多个 PDF
  - 支持进度回调

#### 3.3 适配器 (Adapters)

- **CalibreAdapter** - Calibre ebook-convert 适配器
  - 调用 Calibre 命令行工具
  - 自动检测安装路径
  - 进度报告
  
- **PythonEPUBAdapter** - Python 库适配器
  - 使用 ebooklib + reportlab
  - 不需要外部依赖
  
- **CompositeEPUBConverter** - 组合转换器
  - Python 优先，Calibre 回退
  - 自动选择可用转换器

**依赖：** Domain Layer（实现其接口）

**测试：** 7 个单元测试 ✅

**状态：** ✅ 已完成

---

### 4. 应用层 (Application Layer)

**职责：** 协调业务流程，连接领域层和基础设施层

**核心组件：**

#### 4.1 用例控制器 (Use Cases)

每个用例封装一个完整的业务操作：

- **SplitPDFByRangesUseCase** - 按范围拆分 PDF
  - 输入：SplitByRangesRequest
  - 输出：SplitResult
  - 流程：加载文档 → 解析范围 → 验证 → 拆分
  
- **SplitPDFByChaptersUseCase** - 按章节拆分 PDF
  - 输入：SplitByChaptersRequest
  - 输出：SplitResult
  - 流程：加载文档 → 检查章节 → 拆分
  
- **SplitPDFEachPageUseCase** - 拆分为单页
  - 输入：SplitEachPageRequest
  - 输出：SplitResult
  
- **MergePDFsUseCase** - 合并多个 PDF
  - 输入：MergePDFsRequest
  - 输出：MergeResult
  - 流程：验证输入 → 合并
  
- **ConvertEPUBUseCase** - EPUB 转 PDF
  - 输入：ConvertEPUBRequest
  - 输出：ConvertEPUBResult
  - 流程：检查转换器 → 创建文档 → 转换
  
- **PreviewSplitUseCase** - 预览拆分结果
  - 输入：SplitByRangesRequest / SplitByChaptersRequest
  - 输出：PreviewResult
  - 流程：加载文档 → 生成预览列表

#### 4.2 数据传输对象 (DTOs)

- **Request DTOs** - 封装输入参数
  - SplitByRangesRequest
  - SplitByChaptersRequest
  - SplitEachPageRequest
  - MergePDFsRequest
  - ConvertEPUBRequest
  
- **Result DTOs** - 封装输出结果
  - SplitResult - 成功/失败 + 文件列表/错误消息
  - MergeResult - 成功/失败 + 输出路径/错误消息
  - ConvertEPUBResult - 成功/失败 + 输出路径/错误消息
  - PreviewResult - 预览项列表

#### 4.3 应用服务 (Services)

- **AppStateService** - 应用状态管理
  - 加载/保存设置
  - 最近文件管理
  - 语言和模板管理

**依赖：** Domain Layer

**测试：** 33 个单元测试 ✅

**状态：** ✅ 已完成

---

### 5. 表现层 (Presentation Layer)

**职责：** UI 实现，与用户交互

**核心组件：** [待重构]

#### 5.1 视图模型 (ViewModels) [计划中]

- SplitViewModel - 拆分视图模型
- MergeViewModel - 合并视图模型
- EPUBViewModel - EPUB 视图模型
- AppViewModel - 应用视图模型

#### 5.2 视图 (Views) [待重构]

- MainWindow - 主窗口
- SplitView - 拆分视图
- MergeView - 合并视图
- EPUBView - EPUB 视图

#### 5.3 国际化 (i18n) [待重构]

- Translator - 翻译器
- zh_CN.json - 中文
- en_US.json - 英文

**依赖：** Application Layer

**测试：** 待编写

**状态：** ⏳ 待重构

---

## 依赖关系图

```
Presentation Layer
      ↓ 使用
Application Layer (Use Cases + DTOs)
      ↓ 调用
Domain Layer (Interfaces)
      ↑ 实现
Infrastructure Layer (Implementations)
```

**关键点：**
1. 依赖方向：外层依赖内层，内层不知道外层存在
2. 领域层完全独立，不依赖任何外部框架
3. 基础设施层实现领域层定义的接口
4. 应用层协调领域层和基础设施层
5. 表现层只依赖应用层

---

## 设计模式使用

### 1. 仓储模式 (Repository Pattern)
- 接口：IDocumentRepository, ISettingsRepository
- 实现：PyPDFRepository, JSONSettingsRepository
- 好处：隔离数据访问逻辑，易于替换实现

### 2. 适配器模式 (Adapter Pattern)
- CalibreAdapter, PythonEPUBAdapter 适配不同的 EPUB 转换工具
- 好处：统一接口，支持多种实现

### 3. 用例模式 (Use Case Pattern)
- 每个业务操作一个用例类
- 好处：清晰的业务边界，易于测试

### 4. DTO 模式 (Data Transfer Object)
- Request/Result 对象封装输入输出
- 好处：明确的接口契约，类型安全

### 5. 工厂方法模式 (Factory Method)
- Result.create_success() / Result.create_error()
- 好处：简化对象创建，统一创建逻辑

### 6. 组合模式 (Composite Pattern)
- CompositeEPUBConverter 组合多个转换器
- 好处：提供回退机制，提高可用性

---

## 测试策略

### 单元测试覆盖

| 层次 | 测试数量 | 状态 | 覆盖率 |
|------|---------|------|--------|
| 领域层 | 22 | ✅ | ~85% |
| 基础设施层 | 7 | ✅ | ~80% |
| 应用层 | 33 | ✅ | ~90% |
| 表现层 | 0 | ⏳ | 0% |
| **总计** | **62** | ✅ | **~85%** |

### 测试类型

1. **单元测试** - 测试单个类/函数
   - 使用 Mock 隔离依赖
   - 测试所有路径（成功、失败、边界）
   
2. **集成测试** - 测试组件协作
   - 测试用例 + 仓储 + 服务
   - 使用真实依赖或测试替身

3. **手动测试** - UI 功能测试
   - 当前主要依赖手动测试
   - 重构后将增加自动化 UI 测试

---

## 技术栈

### 核心依赖

- **Python 3.8+** - 编程语言
- **PyPDF2 3.0+** - PDF 操作
- **tkinter** - GUI 框架（Python 内置）

### 可选依赖

- **ebooklib** - EPUB 读取（Python EPUB 转换）
- **reportlab** - PDF 生成（Python EPUB 转换）
- **html2text** - HTML 转文本（Python EPUB 转换）
- **Calibre** - EPUB 转换（外部工具）

### 开发工具

- **pytest** - 测试框架
- **unittest.mock** - Mock 框架
- **pyinstaller** - 打包工具

---

## 重构进度

### 已完成 (75%)

1. ✅ **阶段 1：准备工作** (2024-06-24)
   - 创建目录结构
   - 定义核心接口
   - 编写领域模型
   - 设置共享工具

2. ✅ **阶段 2：基础设施层迁移** (2024-06-24)
   - 实现仓储
   - 实现 PDF 服务
   - 实现 EPUB 适配器
   - 编写基础设施层测试

3. ✅ **阶段 3：应用层构建** (2024-06-24)
   - 创建 DTO
   - 实现用例控制器
   - 实现应用服务
   - 编写应用层测试

### 进行中 (25%)

4. ⏳ **阶段 4：表现层重构** (计划 3-4 天)
   - 提取国际化
   - 创建视图模型
   - 重构视图组件
   - 实现事件总线

### 待完成 (0%)

5. ⏳ **阶段 5：测试与验证** (计划 2-3 天)
   - 完整的单元测试
   - 集成测试
   - 手动回归测试
   - 性能测试

6. ⏳ **阶段 6：文档与清理** (计划 1 天)
   - 更新文档
   - 删除旧代码
   - 编写总结报告

---

## 重构收益

### 可测试性提升

**重构前：**
- 业务逻辑与 Tkinter 强耦合
- 难以 Mock 外部依赖
- 测试覆盖率 < 20%

**重构后：**
- 领域层和应用层完全独立于 UI
- 接口驱动，易于 Mock
- 测试覆盖率 > 80%

### 可维护性改进

**重构前：**
- 职责不清，修改一处影响多处
- 依赖方向混乱
- 难以理解代码意图

**重构后：**
- 每层职责明确
- 单向依赖，符合 SOLID 原则
- 代码自文档化

### 可扩展性增强

**重构前：**
- 添加新功能需要修改多个文件
- UI 框架绑定，无法迁移
- 难以支持插件系统

**重构后：**
- 新功能只需添加新用例
- UI 框架可替换（CLI / Web / Qt）
- 开闭原则，对扩展开放

---

## 相关文档

- [ARCHITECTURE_REFACTORING.md](./ARCHITECTURE_REFACTORING.md) - 重构方案详细设计
- [REFACTORING_PHASE1_REPORT.md](./REFACTORING_PHASE1_REPORT.md) - 阶段 1 完成报告
- [REFACTORING_PHASE2_REPORT.md](./REFACTORING_PHASE2_REPORT.md) - 阶段 2 完成报告
- [REFACTORING_PHASE3_REPORT.md](./REFACTORING_PHASE3_REPORT.md) - 阶段 3 完成报告
- [CLAUDE.md](../CLAUDE.md) - 项目开发指南

---

**最后更新：** 2026-06-24  
**当前状态：** 应用层完成，准备开始表现层重构  
**进度：** 75% (3/4 核心层完成)
