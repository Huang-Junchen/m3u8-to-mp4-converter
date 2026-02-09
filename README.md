# M3U8 to MP4 Converter

一个功能强大的Windows桌面应用，用于将M3U8视频流转换为MP4格式。

## 功能特性

- **多格式输入支持**
  - 本地M3U8文件
  - 远程M3U8 URL
  - 拖放文件支持

- **强大的下载功能**
  - 多线程下载TS片段
  - AES-128解密支持
  - 实时进度显示
  - 暂停/继续/停止控制

- **现代化界面**
  - 简洁优雅的UI设计
  - 实时日志显示
  - 进度条和速度显示
  - 多语言支持（中文/英文）

## 系统要求

- Python 3.8+
- Windows / macOS / Linux
- FFmpeg（用于视频转换）

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd m3u8-to-mp4-converter
```

### 2. 创建虚拟环境（推荐）

使用uv创建虚拟环境：

```bash
# 安装 uv（如果尚未安装）
pip install uv

# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

或使用venv：

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装FFmpeg

**Windows:**
1. 下载FFmpeg：https://ffmpeg.org/download.html#build-windows
2. 解压到目录（如 `C:\ffmpeg`）
3. 添加到系统PATH：`C:\ffmpeg\bin`
4. 验证安装：`ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 使用方法

### 启动应用

```bash
python main.py
```

### 转换视频

1. **输入M3U8源**
   - 在"URL or File"输入框中输入M3U8链接
   - 或点击"Browse"选择本地M3U8文件
   - 或直接拖放M3U8文件到输入框

2. **选择输出路径**
   - 点击"Save to"旁的"Browse"按钮
   - 选择保存位置和文件名

3. **开始转换**
   - 点击"Convert"按钮开始下载和转换
   - 可以使用"Pause"暂停/继续
   - 可以使用"Stop"停止转换

4. **查看结果**
   - 转换完成后点击"Open Folder"打开输出文件夹
   - 在"Log"区域查看详细日志

## 打包指南

本项目使用 PyInstaller 打包成独立的可执行文件。

### 快速开始

直接运行打包脚本：

```bash
build
```

或者：

```bash
build_pyinstaller.bat
```

脚本会自动完成以下操作：
1. 检查并安装 PyInstaller（如果未安装）
2. 清理旧的构建文件
3. 执行打包
4. 生成 `dist\M3U8Converter.exe`

### 手动打包

如果需要自定义打包选项，可以手动运行 PyInstaller：

```bash
# 1. 激活虚拟环境
.venv\Scripts\activate

# 2. 安装 PyInstaller
uv pip install pyinstaller

# 3. 执行打包
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "M3U8Converter" ^
    --add-data "resources;resources" ^
    --add-data "i18n;i18n" ^
    --hidden-import PyQt5 ^
    --hidden-import aiohttp ^
    --hidden-import pycryptodome ^
    --hidden-import asyncio_throttle ^
    --hidden-import qfluentwidgets ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --distpath dist ^
    main.py
```

### PyInstaller 参数说明

- `--onefile` - 打包成单个可执行文件
- `--windowed` - 不显示控制台窗口（GUI程序）
- `--name` - 设置可执行文件名称
- `--add-data` - 包含数据文件（格式：源;目标）
- `--hidden-import` - 显式导入模块
- `--exclude-module` - 排除不需要的模块
- `--distpath` - 输出目录

### 常见问题

**错误：No module named pyinstaller**
```bash
uv pip install pyinstaller
```

**错误：Failed to execute script**
- 检查是否所有依赖都已安装：`uv pip install -r requirements.txt`
- 检查 `--hidden-import` 是否包含所有必需的模块

**打包后程序无法启动**
- 确保 FFmpeg 在系统 PATH 中
- 或将 FFmpeg 可执行文件复制到程序目录

**文件太大**
- 正常现象，PyInstaller 打包的文件通常在 80-200 MB
- 包含了 Python 运行时和所有依赖库
- `--include-data-dir` - 包含资源和国际化文件
- `--remove-output` - 清理临时文件

### 打包完成后

1. 检查 `dist` 目录是否生成了可执行文件
2. 将可执行文件复制到独立目录测试
3. 确保FFmpeg在系统PATH中或在程序目录中

## 项目结构

```
m3u8-to-mp4-converter/
├── main.py                   # 应用入口
├── requirements.txt          # 依赖列表
├── README.md                # 项目文档
├── CLAUDE.md                # 项目规范
├── build.bat                # 快速打包脚本
├── build_pyinstaller.bat    # PyInstaller打包脚本
├── src/                     # 核心模块
│   ├── __init__.py
│   ├── downloader.py        # M3U8下载器
│   └── converter.py         # MP4转换器
├── ui/                      # 用户界面
│   ├── __init__.py
│   ├── main_window.py       # 主窗口（经典UI）
│   └── fluent_main_window.py  # 主窗口（Fluent UI）
├── tests/                   # 测试
│   └── test_converter.py
├── resources/               # 资源文件
│   └── styles.qss           # QSS样式表
└── i18n/                    # 国际化
    ├── en_US.ts            # 英文翻译
    └── zh_CN.ts            # 中文翻译
```

## 技术栈

- **UI框架**: PyQt5, PyQt-Fluent-Widgets
- **网络请求**: aiohttp, requests
- **加密**: pycryptodome
- **视频处理**: FFmpeg
- **异步编程**: asyncio
- **打包工具**: PyInstaller

## 开发

### 运行开发版本

```bash
python main.py
```

### UI模式切换

默认使用Fluent UI。要使用经典UI：

```bash
# Windows
set USE_FLUENT_UI=false && python main.py

# Linux/macOS
USE_FLUENT_UI=false python main.py
```

### 测试

```bash
pytest tests/
```

## 常见问题

**Q: FFmpeg not found 错误？**
A: 请确保FFmpeg已安装并添加到系统PATH环境变量中。

**Q: 转换失败怎么办？**
A: 检查日志输出，常见原因包括：
- M3U8链接无效或已过期
- 网络连接问题
- AES密钥获取失败
- 磁盘空间不足

**Q: 支持加密的M3U8吗？**
A: 支持，程序会自动检测并处理AES-128加密。

**Q: 打包后文件太大？**
A: 正常大小，因为包含：
- Python运行时
- PyQt5库
- 所有依赖

Nuitka打包约50-150MB，PyInstaller打包约80-200MB。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持M3U8下载和MP4转换
- AES-128解密支持
- 多线程下载
- 暂停/继续功能
- 中英文界面
- Fluent Design UI
