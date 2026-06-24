# GitHub Actions 失败原因和解决方案

## 🔴 常见失败原因

### 1. **缺少文件引用**
**问题：** 工作流引用了不存在的文件
```yaml
--icon=icon.ico  # 文件不存在
```

**解决：** 
- 移除对不存在文件的引用
- 或者创建这些文件后再引用

### 2. **依赖问题**
**问题：** 某些依赖在特定平台无法安装
```yaml
--hidden-import=tkinterdnd2  # 某些平台没有这个包
```

**解决：**
- 只安装必需的依赖
- 使用可选依赖处理

### 3. **路径问题**
**问题：** Windows 和 Unix 路径分隔符不同
```yaml
# Windows: presentation/i18n/locales;presentation/i18n/locales
# Unix:    presentation/i18n/locales:presentation/i18n/locales
```

**解决：**
- 为不同平台使用不同的构建步骤
- 使用条件判断 `if: matrix.os == 'windows-latest'`

## ✅ 已修复的问题

### 修复 1：移除不存在的图标引用
**原代码：**
```yaml
--icon=icon.ico
```

**修复后：**
```yaml
# 移除 --icon 参数，或者先创建图标文件
```

### 修复 2：移除可选依赖
**原代码：**
```yaml
--hidden-import=tkinterdnd2
```

**修复后：**
```yaml
# 移除此行，只保留必需的依赖
```

### 修复 3：创建简化版工作流
**新文件：** `.github/workflows/build-simple.yml`

**特点：**
- ✅ 不依赖外部文件（icon.ico, .spec）
- ✅ 最小依赖（只需 PyPDF2 + pyinstaller）
- ✅ 明确的平台分离
- ✅ 可靠的构建流程

## 🚀 如何测试

### 方式 1：推送代码测试
```bash
git add .github/workflows/
git commit -m "fix: 修复 GitHub Actions 构建问题"
git push origin main
```

### 方式 2：手动触发
1. 进入 GitHub 仓库
2. 点击 **Actions**
3. 选择 **Build Executables**
4. 点击 **Run workflow**
5. 查看构建日志

### 方式 3：推送标签（正式发布）
```bash
git tag v1.0.1
git push origin v1.0.1
```

## 📊 工作流对比

| 工作流 | 复杂度 | 依赖 | 推荐场景 |
|--------|--------|------|---------|
| `build-simple.yml` | 低 | 最少 | ✅ 推荐：日常开发 |
| `build.yml` | 中 | 中等 | 需要自定义配置 |
| `build-installers.yml` | 高 | 最多 | 正式发布（NSIS/DMG） |

## 🎯 推荐使用

**开始使用 `build-simple.yml`：**
- 最稳定可靠
- 最少依赖
- 最容易调试

**成功后再尝试高级版本：**
- 添加图标支持
- 创建安装器
- 添加代码签名

## 🔍 如何查看失败日志

1. 进入 GitHub 仓库
2. 点击 **Actions** 标签
3. 点击失败的工作流运行
4. 展开红色的步骤查看详细错误
5. 根据错误信息修复问题

## 📝 常见错误信息

### 错误 1: File not found
```
Error: Unable to find icon.ico
```
**解决：** 移除 `--icon` 参数或创建图标文件

### 错误 2: Module not found
```
ModuleNotFoundError: No module named 'tkinterdnd2'
```
**解决：** 移除 `--hidden-import=tkinterdnd2` 或安装该包

### 错误 3: Permission denied
```
Error: Permission denied
```
**解决：** 检查 GITHUB_TOKEN 权限设置

### 错误 4: Build timeout
```
Error: The operation was canceled.
```
**解决：** 简化构建，移除不必要的步骤

## 💡 最佳实践

1. **先本地测试**
   ```bash
   pyinstaller --noconsole --onefile split_pdf_gui.py
   ```

2. **使用最小依赖**
   - 只安装必需的包
   - 避免可选依赖

3. **分步调试**
   - 先让基础构建成功
   - 再逐步添加功能

4. **查看完整日志**
   - 展开所有步骤
   - 阅读完整错误信息

5. **使用 workflow_dispatch**
   - 允许手动触发
   - 方便调试测试

## 🎊 现在应该可以成功了

提交修复后的工作流：
```bash
git add .github/workflows/
git commit -m "fix: 简化 GitHub Actions 构建配置"
git push origin main
```

查看构建结果：
https://github.com/Darkerhao/pdf-split-tool/actions

---

**注意：** 如果还有问题，请查看 Actions 日志中的具体错误信息，并根据错误提示进行调整。
