"""
Fluent Design Main Window UI for M3U8 to MP4 Converter
Using PyQt-Fluent-Widgets library
"""

import sys
import os
from pathlib import Path
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    PushButton, PrimaryPushButton, LineEdit, ProgressBar,
    TextEdit, SubtitleLabel, StrongBodyLabel, BodyLabel,
    InfoBar, InfoBarPosition, setTheme, Theme,
    MessageBox, FolderListDialog, ComboBox, SwitchButton,
    CardWidget, ScrollArea,
    HyperlinkLabel, ImageLabel, IconWidget
)
import asyncio
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.downloader import M3U8Downloader
from src.converter import Converter


class ConversionWorker(QThread):
    """Worker thread for M3U8 download and conversion"""

    # Signals
    progress = pyqtSignal(int, int)  # current, total
    log = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(bool, str)  # success, message
    speed_update = pyqtSignal(str)  # speed string

    def __init__(self, url: str, output_path: str):
        super().__init__()
        self.url = url
        self.output_path = output_path
        # Create segments directory in output path's parent directory
        output_file = Path(output_path)
        self.segments_dir = output_file.parent / f"{output_file.stem}_segments"
        self._paused = False
        self._stopped = False
        self.downloader = None

    def pause(self):
        """Pause the conversion"""
        self._paused = True
        if self.downloader:
            self.downloader.pause()

    def resume(self):
        """Resume the conversion"""
        self._paused = False
        if self.downloader:
            self.downloader.resume()

    def stop(self):
        """Stop the conversion"""
        self._stopped = True
        if self.downloader:
            self.downloader.stop()

    async def _process_local_m3u8(self, m3u8_path: Path):
        """Process local M3U8 file with decryption support"""
        import re
        from Crypto.Cipher import AES

        base_dir = m3u8_path.parent

        # Read M3U8 content
        with open(m3u8_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse encryption info
        key_path = None
        iv = None

        lines = content.strip().split('\n')
        for line in lines:
            if line.startswith('#EXT-X-KEY:'):
                if 'METHOD=AES-128' in line:
                    # Extract URI
                    uri_match = re.search(r'URI="([^"]+)"', line)
                    if uri_match:
                        key_path = base_dir / uri_match.group(1)

                    # Extract IV
                    iv_match = re.search(r'IV=0x([0-9a-fA-F]+)', line)
                    if iv_match:
                        iv = bytes.fromhex(iv_match.group(1))
                break

        # Read key
        key = None
        if key_path and key_path.exists():
            self.log.emit(f"Reading encryption key...", "INFO")
            with open(key_path, 'rb') as f:
                key = f.read()
            self.log.emit(f"Key size: {len(key)} bytes", "INFO")
        else:
            self.log.emit("Warning: Key file not found", "WARNING")

        # Create output directory for segments
        self.segments_dir.mkdir(parents=True, exist_ok=True)
        self.log.emit(f"Segments directory: {self.segments_dir}", "INFO")

        # Parse segments and decrypt if needed
        segments = []
        segment_index = 0
        total_segments = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))

        for line in lines:
            if self._stopped:
                raise Exception("Stopped by user")

            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # This is a segment path
            segment_path = base_dir / line

            if segment_path.exists():
                # Decrypt if key is available
                if key:
                    decrypted_path = self.segments_dir / f"segment_{segment_index:05d}.ts"

                    # Read encrypted data
                    with open(segment_path, 'rb') as f:
                        encrypted_data = f.read()

                    # Decrypt
                    if iv:
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                    else:
                        cipher = AES.new(key, AES.MODE_CBC)

                    decrypted_data = cipher.decrypt(encrypted_data)

                    # Remove PKCS7 padding
                    try:
                        padding_length = decrypted_data[-1]
                        if padding_length <= 16:
                            decrypted_data = decrypted_data[:-padding_length]
                    except:
                        pass  # Invalid padding, skip

                    # Write decrypted data
                    with open(decrypted_path, 'wb') as f:
                        f.write(decrypted_data)

                    segments.append(decrypted_path)
                else:
                    # Just copy the segment path
                    segments.append(segment_path)

                segment_index += 1
                self.progress.emit(segment_index, total_segments)

        encryption_info = {'METHOD': 'AES-128'} if key else None
        self.log.emit(f"Processed {len(segments)} segments", "INFO")

        return segments, encryption_info

    def run(self):
        """Run the conversion process"""
        try:
            asyncio.run(self._convert_async())
        except Exception as e:
            self.log.emit(f"Error: {str(e)}", "ERROR")
            self.finished.emit(False, str(e))

    async def _convert_async(self):
        """Async conversion logic"""
        try:
            self.log.emit(f"Starting conversion from: {self.url}", "INFO")

            # Check if input is a local file
            input_path = Path(self.url)
            is_local_file = input_path.exists() and input_path.suffix.lower() == '.m3u8'

            if is_local_file:
                # Process local file
                self.log.emit("Detected local M3U8 file", "INFO")
                downloaded_files, encryption_info = await self._process_local_m3u8(input_path)
            else:
                # Process remote URL
                self.log.emit("Detected remote URL", "INFO")
                self.downloader = M3U8Downloader(max_workers=10)
                self.downloader.set_callbacks(
                    progress_callback=lambda curr, total, speed=0: self.progress.emit(curr, total),
                    log_callback=lambda msg, level: self.log.emit(msg, level)
                )

                async with self.downloader:
                    # Download segments
                    self.log.emit("Downloading segments...", "INFO")
                    downloaded_files, encryption_info = await self.downloader.download(
                        self.url,
                        self.segments_dir
                    )

                if not downloaded_files:
                    raise Exception("No segments downloaded")

                self.log.emit(f"Downloaded {len(downloaded_files)} segments", "INFO")

            # Check for pause/stop
            if self._stopped:
                self.finished.emit(False, "Conversion stopped by user")
                return

            # Convert to MP4 (common for both local and remote)
            self.log.emit("Converting to MP4...", "INFO")
            self.log.emit(f"Output file: {self.output_path}", "INFO")
            self.log.emit(f"Number of segments: {len(downloaded_files)}", "INFO")

            converter = Converter()

            # Enhanced log callback to also show DEBUG messages
            def enhanced_log(msg, level):
                self.log.emit(msg, level)
                # Print to console as well for debugging
                print(f"[{level}] {msg}")

            converter.set_callbacks(
                progress_callback=lambda curr, total: self.progress.emit(curr, total),
                log_callback=enhanced_log
            )

            self.log.emit(f"FFmpeg path: {converter.ffmpeg_path}", "INFO")

            success = converter.convert_concat(
                downloaded_files,
                Path(self.output_path),
                delete_segments=False  # Keep segments for debugging
            )

            # Verify output file was created
            output_path = Path(self.output_path)
            if success and output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024*1024)
                self.log.emit(f"Conversion completed successfully! File size: {file_size_mb:.2f} MB", "INFO")
                self.finished.emit(True, "Conversion completed")
            elif success and not output_path.exists():
                error_msg = f"Conversion reported success but output file not found at: {self.output_path}"
                self.log.emit(error_msg, "ERROR")
                raise Exception(error_msg)
            else:
                raise Exception("Conversion failed - check logs for details")

        except Exception as e:
            self.log.emit(f"Error during conversion: {str(e)}", "ERROR")
            self.finished.emit(False, str(e))


class ConverterInterface(ScrollArea):
    """Main converter interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.worker = None
        self.current_language = "en_US"
        self._init_ui()
        self._apply_translations()

    def _init_ui(self):
        """Initialize the UI"""
        self.setObjectName("converterInterface")
        self.setWidgetResizable(True)

        # Create container widget
        self.container = CardWidget()
        self.container.setFixedHeight(780)

        # Main layout
        layout = QVBoxLayout(self.container)
        layout.setSpacing(20)
        layout.setContentsMargins(35, 35, 35, 35)

        # Title
        title = SubtitleLabel("M3U8 to MP4 Converter")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = BodyLabel("Convert M3U8 video streams to MP4 format with ease")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Input section card
        input_card = CardWidget()
        input_layout = QVBoxLayout(input_card)

        # Input header
        input_header = SubtitleLabel("Input Source")
        input_layout.addWidget(input_header)

        # URL input
        url_row = QHBoxLayout()
        url_label = StrongBodyLabel("URL or File:")
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("Enter M3U8 URL or drag and drop file here")
        self.url_input.setDragEnabled(True)
        url_row.addWidget(url_label)
        url_row.addWidget(self.url_input, 1)

        self.btn_browse = PushButton("Browse")
        self.btn_browse.clicked.connect(self._browse_m3u8_file)
        url_row.addWidget(self.btn_browse)

        input_layout.addLayout(url_row)
        layout.addWidget(input_card)

        # Output section card
        output_card = CardWidget()
        output_layout = QVBoxLayout(output_card)

        # Output header
        output_header = SubtitleLabel("Output Settings")
        output_layout.addWidget(output_header)

        # Output path
        output_row = QHBoxLayout()
        output_label = StrongBodyLabel("Save to:")
        self.output_path = LineEdit()
        self.output_path.setPlaceholderText("Select output MP4 file path")
        output_row.addWidget(output_label)
        output_row.addWidget(self.output_path, 1)

        self.btn_browse_output = PushButton("Browse")
        self.btn_browse_output.clicked.connect(self._browse_output_file)
        output_row.addWidget(self.btn_browse_output)

        output_layout.addLayout(output_row)
        layout.addWidget(output_card)

        # Control buttons
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)

        control_header = SubtitleLabel("Controls")
        control_layout.addWidget(control_header)

        control_row = QHBoxLayout()
        control_row.addStretch(1)

        self.btn_convert = PrimaryPushButton("Convert")
        self.btn_convert.clicked.connect(self._start_conversion)
        control_row.addWidget(self.btn_convert)

        self.btn_pause = PushButton("Pause")
        self.btn_pause.clicked.connect(self._pause_conversion)
        self.btn_pause.setEnabled(False)
        control_row.addWidget(self.btn_pause)

        self.btn_stop = PushButton("Stop")
        self.btn_stop.clicked.connect(self._stop_conversion)
        self.btn_stop.setEnabled(False)
        control_row.addWidget(self.btn_stop)

        self.btn_open_folder = PushButton("Open Folder")
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        self.btn_open_folder.setEnabled(False)
        control_row.addWidget(self.btn_open_folder)

        control_row.addStretch(1)
        control_layout.addLayout(control_row)
        layout.addWidget(control_card)

        # Progress section
        progress_card = CardWidget()
        progress_layout = QVBoxLayout(progress_card)

        progress_header = SubtitleLabel("Conversion Progress")
        progress_layout.addWidget(progress_header)

        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        # Progress info
        progress_info_row = QHBoxLayout()
        self.status_label = BodyLabel("Status: Ready")
        progress_info_row.addWidget(self.status_label)
        progress_info_row.addStretch()
        self.speed_label = BodyLabel("Speed: -")
        progress_info_row.addWidget(self.speed_label)
        progress_layout.addLayout(progress_info_row)

        layout.addWidget(progress_card)

        # Log section
        log_card = CardWidget()
        log_layout = QVBoxLayout(log_card)

        log_header = SubtitleLabel("Conversion Log")
        log_layout.addWidget(log_header)

        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(180)
        log_layout.addWidget(self.log_text)

        # Clear log button
        clear_log_row = QHBoxLayout()
        clear_log_row.addStretch()
        btn_clear_log = PushButton("Clear Log")
        btn_clear_log.clicked.connect(self._clear_log)
        clear_log_row.addWidget(btn_clear_log)
        log_layout.addLayout(clear_log_row)

        layout.addWidget(log_card)
        layout.addStretch()

        # Set scroll area widget
        self.setWidget(self.container)

        # Enable drag and drop on the scroll area
        self.setAcceptDrops(True)

    def _apply_translations(self):
        """Apply translations based on current language"""
        translations = {
            "en_US": {
                "window_title": "M3U8 to MP4 Converter",
                "url_or_file": "Enter M3U8 URL or drag and drop file here",
                "save_to": "Select output MP4 file path",
                "browse": "Browse",
                "convert": "Convert",
                "pause": "Pause",
                "stop": "Stop",
                "open_folder": "Open Folder",
                "clear_log": "Clear Log",
                "status_ready": "Status: Ready",
                "speed": "Speed: -",
            },
            "zh_CN": {
                "window_title": "M3U8 转 MP4 转换器",
                "url_or_file": "输入 M3U8 URL 或拖放文件到此处",
                "save_to": "选择输出 MP4 文件路径",
                "browse": "浏览",
                "convert": "转换",
                "pause": "暂停",
                "stop": "停止",
                "open_folder": "打开文件夹",
                "clear_log": "清空日志",
                "status_ready": "状态: 就绪",
                "speed": "速度: -",
            }
        }

        t = translations.get(self.current_language, translations["en_US"])
        self.url_input.setPlaceholderText(t["url_or_file"])
        self.output_path.setPlaceholderText(t["save_to"])

    def _change_language(self, language: str):
        """Change application language"""
        self.current_language = language
        self._apply_translations()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            if file_path.endswith('.m3u8'):
                self.url_input.setText(file_path)
                # Auto-set output path
                if not self.output_path.text():
                    import time
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    output_file = Path(file_path).parent.parent / f"converted_{timestamp}.mp4"
                    self.output_path.setText(str(output_file))

    def _browse_m3u8_file(self):
        """Browse for M3U8 file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select M3U8 File" if self.current_language == "en_US" else "选择 M3U8 文件",
            "",
            "M3U8 Files (*.m3u8);;All Files (*.*)"
        )

        if file_path:
            self.url_input.setText(file_path)
            # Auto-set output path
            if not self.output_path.text():
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_file = Path(file_path).parent.parent / f"converted_{timestamp}.mp4"
                self.output_path.setText(str(output_file))

    def _browse_output_file(self):
        """Browse for output file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output Path" if self.current_language == "en_US" else "选择输出路径",
            "",
            "MP4 Video (*.mp4)"
        )

        if file_path:
            self.output_path.setText(str(file_path))

    def _validate_inputs(self) -> bool:
        """Validate user inputs"""
        url = self.url_input.text().strip()
        output = self.output_path.text().strip()

        if not url:
            InfoBar.warning(
                title="Warning",
                content="Please enter M3U8 URL or select a file",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        if not output:
            InfoBar.warning(
                title="Warning",
                content="Please select output path",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        return True

    def _start_conversion(self):
        """Start the conversion process"""
        if not self._validate_inputs():
            return

        url = self.url_input.text().strip()
        output = self.output_path.text().strip()

        # Create and start worker
        self.worker = ConversionWorker(url, output)
        self.worker.progress.connect(self._on_progress_update)
        self.worker.log.connect(self._on_log_message)
        self.worker.finished.connect(self._on_conversion_finished)

        # Update UI
        self.btn_convert.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_open_folder.setEnabled(False)
        self.status_label.setText("Status: Converting...")
        self.progress_bar.setValue(0)

        # Start worker
        self.worker.start()

        self._log("Starting conversion...", "INFO")
        InfoBar.success(
            title="Started",
            content="Conversion process has started",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _pause_conversion(self):
        """Pause/resume conversion"""
        if self.worker:
            if self.btn_pause.text() == "Pause":
                self.worker.pause()
                self.btn_pause.setText("Resume")
                self.status_label.setText("Status: Paused")
                self._log("Conversion paused", "INFO")
                InfoBar.info(
                    title="Paused",
                    content="Conversion has been paused",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                self.worker.resume()
                self.btn_pause.setText("Pause")
                self.status_label.setText("Status: Converting...")
                self._log("Conversion resumed", "INFO")
                InfoBar.success(
                    title="Resumed",
                    content="Conversion has been resumed",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )

    def _stop_conversion(self):
        """Stop conversion"""
        if self.worker:
            # Show confirmation dialog
            title = "Confirm Stop" if self.current_language == "en_US" else "确认停止"
            content = "Are you sure you want to stop the conversion?" if self.current_language == "en_US" else "确定要停止转换吗？"

            msg = MessageBox(title, content, self)
            if msg.exec():
                self.worker.stop()
                self._on_conversion_finished(False, "Stopped by user")

    def _on_progress_update(self, current: int, total: int):
        """Handle progress update"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"Status: Converting... ({current}/{total})")

    def _on_log_message(self, message: str, level: str):
        """Handle log message"""
        self._log(message, level)

    def _log(self, message: str, level: str = "INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#4caf50",
            "WARNING": "#ff9800",
            "ERROR": "#f44336",
            "DEBUG": "#2196f3"
        }
        color = color_map.get(level, "#333333")

        html = f'<span style="color: #666;">[{timestamp}]</span> ' \
               f'<span style="color: {color}; font-weight: bold;">[{level}]</span> ' \
               f'<span>{message}</span>'

        self.log_text.append(html)

    def _clear_log(self):
        """Clear log text"""
        self.log_text.clear()

    def _on_conversion_finished(self, success: bool, message: str):
        """Handle conversion finished"""
        self.btn_convert.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setText("Pause")

        if success:
            self.status_label.setText("Status: Completed")
            self.progress_bar.setValue(100)
            self.btn_open_folder.setEnabled(True)
            self._log(f"Conversion completed: {message}", "INFO")

            InfoBar.success(
                title="Success",
                content=f"Conversion completed successfully!\nSaved to: {self.output_path.text()}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            self.status_label.setText("Status: Failed")
            self._log(f"Conversion failed: {message}", "ERROR")

            InfoBar.error(
                title="Error",
                content=f"Conversion failed: {message}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

        self.worker = None

    def _open_output_folder(self):
        """Open output folder in file explorer"""
        output_path = Path(self.output_path.text())
        if output_path.exists():
            import subprocess
            import platform

            folder_path = output_path.parent

            try:
                if platform.system() == "Windows":
                    os.startfile(folder_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
            except Exception as e:
                InfoBar.error(
                    title="Error",
                    content=f"Failed to open folder: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )


class MainWindow(FluentWindow):
    """Fluent Design main window"""

    def __init__(self):
        super().__init__()
        self._init_window()
        self._create_navigation()

        # Set theme
        setTheme(Theme.AUTO)

    def _init_window(self):
        """Initialize window properties"""
        self.setWindowTitle("M3U8 to MP4 Converter")
        self.setMinimumSize(1000, 750)

    def _create_navigation(self):
        """Create navigation interface"""
        # Create converter interface
        self.converter_interface = ConverterInterface(self)

        # Add to navigation
        self.addSubInterface(
            self.converter_interface,
            FluentIcon.VIDEO,
            "Converter"
        )

        # Create about interface
        self.about_interface = AboutInterface(self)
        self.addSubInterface(
            self.about_interface,
            FluentIcon.INFO,
            "About",
            position=NavigationItemPosition.BOTTOM
        )

        # Set default interface
        self.navigationInterface.setCurrentItem(
            self.converter_interface.objectName()
        )

    def closeEvent(self, event):
        """Handle window close event"""
        if self.converter_interface.worker and self.converter_interface.worker.isRunning():
            title = "Confirm Exit"
            content = "Conversion is in progress. Are you sure you want to exit?"

            msg = MessageBox(title, content, self)
            if msg.exec():
                self.converter_interface.worker.stop()
                self.converter_interface.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class AboutInterface(ScrollArea):
    """About interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI"""
        self.setObjectName("aboutInterface")
        self.setWidgetResizable(True)

        # Create container widget
        container = CardWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = SubtitleLabel("M3U8 to MP4 Converter")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Version
        version = BodyLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        # Description
        desc_layout = QVBoxLayout()
        desc = BodyLabel(
            "A desktop application for converting M3U8 video streams to MP4 format.\n\n"
            "Features:\n"
            "• Download M3U8 playlists from URL or local files\n"
            "• AES-128 decryption support\n"
            "• Multi-threaded downloading\n"
            "• Convert to MP4 using FFmpeg\n"
            "• Modern Fluent Design UI\n\n"
            "Powered by PyQt5 and PyQt-Fluent-Widgets"
        )
        desc.setWordWrap(True)
        desc_layout.addWidget(desc)
        layout.addLayout(desc_layout)

        # GitHub link
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        github_link = HyperlinkLabel("https://github.com/zhiyiYo/PyQt-Fluent-Widgets", self)
        github_link.setText("UI Library: PyQt-Fluent-Widgets")
        github_link.setIcon(FluentIcon.GITHUB)
        link_layout.addWidget(github_link)
        link_layout.addStretch()
        layout.addLayout(link_layout)

        layout.addStretch()

        self.setWidget(container)
