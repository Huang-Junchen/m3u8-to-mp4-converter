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

## 项目结构

```
m3u8-to-mp4-converter/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖列表
├── README.md              # 项目文档
├── CLAUDE.md              # 项目规范
├── src/                   # 核心模块
│   ├── downloader.py      # M3U8下载器
│   └── converter.py       # MP4转换器
├── ui/                    # 用户界面
│   └── main_window.py     # 主窗口
├── i18n/                  # 国际化
│   ├── en_US.ts          # 英文翻译
│   └── zh_CN.ts          # 中文翻译
└── resources/             # 资源文件
    └── styles.qss         # QSS样式表
```

## 技术栈

- **UI框架**: PyQt5
- **网络请求**: aiohttp, requests
- **加密**: pycryptodome
- **视频处理**: FFmpeg
- **异步编程**: asyncio

## 开发

### 运行开发版本

```bash
python main.py
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
