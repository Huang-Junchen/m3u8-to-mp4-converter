# M3U8 to MP4 Converter

强大的桌面应用，将 M3U8 视频流转换为 MP4 格式。

## ✨ 功能特性

- **多格式输入支持**：本地 M3U8 文件、远程 URL、拖放
- **强大的下载功能**：多线程下载、AES-128 解密、实时进度
- **现代化界面**：Fluent Design UI、中英文支持、日志显示

## 🚀 快速开始

### 系统要求

- Python 3.8+
- Windows / macOS / Linux
- FFmpeg

### 安装依赖

**推荐使用 uv（快速包管理器）：**
```bash
# 安装依赖
uv sync
```

**或使用传统方式：**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 安装 FFmpeg

**Windows:**
1. 下载：https://ffmpeg.org/download.html#build-windows
2. 解压到目录（如 `C:\ffmpeg`）
3. 添加到系统 PATH：`C:\ffmpeg\bin`
4. 验证：`ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 运行

**使用 uv：**
```bash
uv run python main.py
```

**或传统方式：**
```bash
python main.py
```

## 📖 使用方法

1. **输入 M3U8 源**
   - 在 "URL or File" 输入框输入链接
   - 或点击 "Browse" 选择本地文件
   - 或直接拖放文件到输入框

2. **选择输出路径**
   - 点击 "Save to" 旁的 "Browse" 按钮
   - 选择保存位置和文件名

3. **开始转换**
   - 点击 "Convert" 按钮
   - 可以使用 "Pause" 暂停/继续
   - 可以使用 "Stop" 停止

4. **查看结果**
   - 转换完成后点击 "Open Folder" 打开输出文件夹
   - 在 "Log" 区域查看详细日志

## 📦 打包

### 快速打包

```bash
build.bat
# 或
build_pyinstaller.bat
```

### 手动打包

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装 PyInstaller
uv pip install pyinstaller

# 执行打包
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

### 常见问题

**No module named pyinstaller？**
```bash
uv pip install pyinstaller
```

**打包后程序无法启动？**
- 确保 FFmpeg 在系统 PATH 中
- 或将 FFmpeg 可执行文件复制到程序目录

**文件太大？**
- 正常现象，PyInstaller 打包约 80-200 MB
- 包含了 Python 运行时和所有依赖库

## 📁 项目结构

```
m3u8-to-mp4-converter/
├── main.py                   # 应用入口
├── requirements.txt          # 依赖列表
├── build.bat                 # 快速打包脚本
├── build_pyinstaller.bat     # PyInstaller 打包脚本
├── src/                      # 核心模块
│   ├── downloader.py         # M3U8 下载器
│   └── converter.py          # MP4 转换器
├── ui/                       # 用户界面
│   ├── main_window.py        # 主窗口（经典 UI）
│   └── fluent_main_window.py # 主窗口（Fluent UI）
├── resources/                # 资源文件
│   └── styles.qss            # QSS 样式表
└── i18n/                     # 国际化
    ├── en_US.ts              # 英文翻译
    └── zh_CN.ts              # 中文翻译
```

## 🛠️ 开发

### UI 模式切换

默认使用 Fluent UI。要使用经典 UI：

```bash
# Windows
set USE_FLUENT_UI=false && python main.py

# Linux/macOS
USE_FLUENT_UI=false python main.py
```

## 🐛 常见问题

**Q: FFmpeg not found？**
A: 确保已安装并添加到系统 PATH 环境变量中。

**Q: 转换失败？**
A: 检查日志，常见原因：
- M3U8 链接无效或已过期
- 网络连接问题
- AES 密钥获取失败
- 磁盘空间不足

**Q: 支持加密的 M3U8？**
A: 支持，程序会自动检测并处理 AES-128 加密。

## 📄 License

MIT License
