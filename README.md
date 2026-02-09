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

本项目提供了两种打包方式：PyInstaller（推荐新手）和 Nuitka（性能更好）。

### 方案A：使用PyInstaller（推荐 - 简单快速）

**优点：**
- 不需要C编译器
- 设置简单，5分钟完成
- 适合快速打包

**步骤：**

直接运行打包脚本：

```bash
build_pyinstaller.bat
```

脚本会自动完成以下操作：
1. 安装PyInstaller（如果未安装）
2. 执行打包
3. 生成 `dist\M3U8Converter.exe`

**手动打包：**

```bash
uv pip install pyinstaller

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
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --distpath dist ^
    main.py
```

### 方案B：使用Nuitka（性能更好）

**优点：**
- 性能更优
- 启动更快
- 文件可能更小

**缺点：**
- 需要安装C编译器（6-8 GB工具）
- 安装时间15-30分钟

#### 步骤1：安装Visual Studio Build Tools

1. **下载安装程序**
   - 访问：https://visualstudio.microsoft.com/downloads/
   - 或使用直接链接：https://aka.ms/vs/17/release/vs_buildtools.exe

2. **运行安装程序**
   - 双击运行 `vs_buildtools.exe`
   - 选择 **"Desktop development with C++"** 工作负载
   - 确保以下组件被选中：
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 11 SDK（或 Windows 10 SDK）

3. **等待安装完成**
   - 下载大小：约 6-8 GB
   - 安装时间：15-30分钟

4. **验证安装**
   - 按 `Win` 键搜索 "Developer Command Prompt for VS 2022"
   - 打开后输入：`cl`
   - 应显示编译器版本信息

#### 步骤2：运行打包脚本

**智能打包脚本（推荐）：**

```bash
build_auto.bat
```

此脚本会：
- 自动检测编译器
- 自动设置编译环境
- 自动安装Nuitka（如果需要）
- 清理旧的构建文件
- 执行完整打包

**标准打包脚本：**

```bash
build.bat
```

**手动打包：**

```bash
# 1. 激活虚拟环境
.venv\Scripts\activate

# 2. 设置编译环境（如果需要）
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# 3. 运行Nuitka
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=pyqt5 ^
    --windows-console-mode=disable ^
    --company-name="M3U8Converter" ^
    --product-name="M3U8 to MP4 Converter" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --include-data-dir=resources=resources ^
    --include-data-dir=i18n=i18n ^
    --include-package=PyQt5 ^
    --include-package=aiohttp ^
    --include-package=pycryptodome ^
    --remove-output ^
    --output-dir=dist ^
    main.py
```

### 常见打包问题

**错误：No module named nuitka**
```bash
uv pip install nuitka
```

**错误：No C compiler found**
**方案1：使用 PyInstaller（推荐，最简单）**
```bash
build_pyinstaller.bat
```

**方案2：使用 x64 Native Tools Command Prompt**
1. 按 `Win` 键
2. 搜索 "x64 Native Tools Command Prompt for VS 2022"
3. 打开后运行：
```bash
cd /d "D:\Project\m3u8-to-mp4-converter"
build_with_compiler.bat
```

**方案3：诊断问题**
```bash
diagnose_vs.bat
```
这会检查你的 Visual Studio 安装并给出具体建议。

**错误：Failed to find Qt**
- 确保 `--enable-plugin=pyqt5` 参数存在
- 检查PyQt5是否正确安装

### 打包参数说明

**PyInstaller 参数：**
- `--onefile` - 单文件打包
- `--windowed` - 无控制台窗口
- `--add-data` - 包含数据文件
- `--hidden-import` - 显式导入模块
- `--exclude-module` - 排除不需要的模块

**Nuitka 参数：**
- `--standalone` - 独立可执行文件
- `--onefile` - 单文件打包
- `--enable-plugin=pyqt5` - PyQt5支持
- `--windows-console-mode=disable` - 无控制台窗口
- `--include-data-dir` - 包含资源和国际化文件
- `--remove-output` - 清理临时文件

### Nuitka vs PyInstaller 对比

| 特性 | Nuitka | PyInstaller |
|------|--------|-------------|
| 编译需求 | 需要C编译器 | 不需要编译器 |
| 性能 | 更快（编译成C） | 较慢（Python解释） |
| 文件大小 | 较大 | 较大 |
| 启动速度 | 快 | 慢 |
| 兼容性 | 好 | 很好 |
| 设置复杂度 | 高 | 低 |

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
├── build.bat                # Nuitka打包脚本
├── build_auto.bat           # 智能打包脚本
├── build_pyinstaller.bat    # PyInstaller打包脚本
├── build_with_compiler.bat  # 改进的Nuitka打包脚本
├── check_compiler.bat       # 编译器检查脚本
├── diagnose_vs.bat          # Visual Studio诊断工具
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
- **打包工具**: PyInstaller, Nuitka

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
