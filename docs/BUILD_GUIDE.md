# 构建和发布指南

## 📦 自动构建（GitHub Actions）

### 方式 1：标签发布（推荐）

当你推送一个版本标签时，GitHub Actions 会自动构建所有平台的安装包：

```bash
# 创建版本标签
git tag v1.0.0
git push origin v1.0.0
```

**自动生成的包：**
- ✅ Windows 安装器 (`PDF_Toolbox_Setup.exe`)
- ✅ Windows 可执行文件 (`pdf-toolbox-windows-x64.exe`)
- ✅ macOS DMG (`PDF-Toolbox.dmg`)
- ✅ macOS 可执行文件 (`pdf-toolbox-macos-x64`)
- ✅ Linux AppImage (`PDF_Toolbox-x86_64.AppImage`)
- ✅ Linux 可执行文件 (`pdf-toolbox-linux-x64`)

### 方式 2：手动触发

1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择 "Build and Release" 或 "Build Installers"
4. 点击 "Run workflow"
5. 下载构建好的 Artifacts

## 🛠️ 本地构建

### Windows

```batch
REM 方式 1：使用构建脚本（推荐）
build.bat

REM 方式 2：手动构建
pyinstaller split_pdf_gui.spec

REM 方式 3：创建安装器（需要安装 NSIS）
choco install nsis
makensis installer.nsi
```

### macOS / Linux

```bash
# 方式 1：使用构建脚本（推荐）
chmod +x build.sh
./build.sh

# 方式 2：手动构建
pyinstaller split_pdf_gui.spec
```

### 构建输出

- 可执行文件：`dist/split_pdf_gui.exe` (Windows) 或 `dist/pdf-toolbox` (Unix)
- Windows 安装器：`PDF_Toolbox_Setup.exe`

## 📋 构建前准备

### 安装依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Windows 安装器（可选）

安装 NSIS（Nullsoft Scriptable Install System）：

```batch
choco install nsis
```

或从 [NSIS 官网](https://nsis.sourceforge.io/) 下载

### macOS DMG（可选）

```bash
brew install create-dmg
```

### Linux AppImage（可选）

```bash
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage
```

## 🎯 不同平台的打包格式

### Windows
1. **EXE 文件** - 单文件可执行程序，无需安装
2. **Setup.exe** - NSIS 安装器，包含卸载功能和开始菜单快捷方式
3. **MSI 安装包** - Windows Installer 格式（需要 WiX Toolset）
4. **便携版 ZIP** - 解压即用

### macOS
1. **App Bundle** - `.app` 文件，macOS 原生应用格式
2. **DMG** - 磁盘映像，可拖拽安装
3. **PKG** - 安装包，使用 Apple Installer
4. **便携版 ZIP** - 解压即用

### Linux
1. **AppImage** - 单文件，无需安装，在任何 Linux 发行版运行
2. **DEB** - Debian/Ubuntu 安装包
3. **RPM** - RedHat/Fedora/CentOS 安装包
4. **Flatpak** - 跨发行版沙盒应用
5. **Snap** - Ubuntu Snap 包
6. **二进制文件** - 单个可执行文件

## 🔧 自定义构建

### 修改图标

将你的图标文件放置在项目根目录：
- Windows: `icon.ico` (256x256 推荐)
- macOS: `icon.icns` (1024x1024 推荐)
- Linux: `icon.png` (512x512 推荐)

### 修改版本号

编辑以下文件：
- `installer.nsi` - NSIS 安装器版本
- `split_pdf_gui.spec` - PyInstaller 配置
- `.github/workflows/*.yml` - CI/CD 工作流

### 添加依赖文件

编辑 `split_pdf_gui.spec`，在 `datas` 列表中添加：

```python
datas=[
    ('presentation/i18n/locales', 'presentation/i18n/locales'),
    ('assets', 'assets'),  # 添加资源文件夹
],
```

## 📊 构建大小优化

### 减小文件大小

1. **排除不需要的模块：**
   ```bash
   pyinstaller --exclude-module matplotlib --exclude-module numpy ...
   ```

2. **使用 UPX 压缩：**
   ```bash
   pip install pyinstaller[encryption]
   pyinstaller --upx-dir=/path/to/upx ...
   ```

3. **不打包 Tkinter：**
   如果系统已有 Python，可以不打包 Tkinter（减少约 10MB）

## 🚀 发布流程

### 完整发布流程

1. **更新版本号**
   ```bash
   # 编辑 installer.nsi, __version__ 等文件
   ```

2. **提交代码**
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git push
   ```

3. **创建标签**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **等待 GitHub Actions 构建**
   - 进入 Actions 查看构建进度
   - 构建完成后会自动创建 Release

5. **编辑 Release 说明**
   - 添加更新日志
   - 补充安装说明
   - 发布 Release

## 📝 CI/CD 工作流说明

### `build.yml` - 基础构建
- 构建所有平台的可执行文件
- 自动上传 Artifacts
- 标签推送时创建 Release

### `build-installers.yml` - 安装器构建
- 构建 Windows NSIS 安装器
- 构建 macOS DMG
- 构建 Linux AppImage

## 🐛 常见问题

### Q: 构建失败怎么办？
A: 检查 GitHub Actions 日志，常见原因：
- 缺少依赖
- 路径错误
- Python 版本不兼容

### Q: 为什么文件这么大？
A: PyInstaller 会打包整个 Python 环境。可以：
- 使用 `--exclude-module` 排除不需要的模块
- 使用 UPX 压缩
- 考虑使用 Nuitka 代替 PyInstaller

### Q: macOS 提示"无法打开，因为它来自身份不明的开发者"？
A: 需要对 App 进行代码签名。用户可以右键 → "打开" 绕过。

### Q: Linux AppImage 无法运行？
A: 检查是否有执行权限：
```bash
chmod +x PDF_Toolbox-x86_64.AppImage
```

## 📚 相关资源

- [PyInstaller 文档](https://pyinstaller.org/)
- [NSIS 文档](https://nsis.sourceforge.io/Docs/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [create-dmg](https://github.com/create-dmg/create-dmg)
- [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy)

---

**提示：** 首次构建建议先在本地测试，确保没有问题后再推送标签触发自动构建。
