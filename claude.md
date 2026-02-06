# M3U8 to MP4 Converter - 技术规范

## 项目概述
开发一个Windows桌面应用，用于将m3u8视频流转换为MP4格式文件。

## 技术要求

### 必须功能
1. **输入支持**
   - 本地m3u8文件
   - 远程m3u8 URL
   - 拖放操作支持

2. **转换核心**
   - 多线程下载TS片段
   - AES-128解密支持
   - FFmpeg转码集成
   - 实时进度显示

3. **用户界面**
   - 简洁的现代化界面
   - 实时日志显示
   - 进度条和速度显示
   - 转换历史记录

### 可选功能
- 批量转换队列
- 代理服务器支持
- 自定义输出参数
- 自动更新检查

## 实现细节

### 依赖库
```python
# requirements.txt
PyQt5>=5.15
aiohttp>=3.8
requests>=2.28
asyncio
pycryptodome  # AES解密
```

### 约定与规则 
1. 使用uv和venv来管理python环境
2. 每次修改进行对应的commit
3. git提交时注意数据的隐私性和安全性
