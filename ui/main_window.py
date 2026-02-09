"""
Main Window UI for M3U8 to MP4 Converter
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMenuBar, QMenu,
    QMessageBox, QProgressBar, QPushButton, QSplitter, QStatusBar,
    QTextEdit, QVBoxLayout, QWidget
)

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.converter import Converter
from src.downloader import M3U8Downloader


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
                delete_segments=False  # We'll delete the entire segments_dir folder manually
            )

            # Verify output file was created
            output_path = Path(self.output_path)
            if success and output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024*1024)
                self.log.emit(f"Conversion completed successfully! File size: {file_size_mb:.2f} MB", "INFO")

                # Delete segments folder
                if self.segments_dir.exists():
                    try:
                        import shutil
                        shutil.rmtree(self.segments_dir)
                        self.log.emit(f"Deleted segments folder: {self.segments_dir}", "INFO")
                    except Exception as e:
                        self.log.emit(f"Warning: Could not delete segments folder: {str(e)}", "WARNING")

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


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_language = "en_US"
        self._init_ui()
        self._load_styles()
        self._apply_translations()

    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("M3U8 to MP4 Converter")
        self.setMinimumSize(900, 700)

        # Create menu bar
        self._create_menu_bar()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel()
        title_label.setObjectName("labelTitle")
        title_label.setText("M3U8 to MP4 Converter")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Input section
        input_group = QGroupBox()
        input_group.setTitle("Input")
        input_layout = QGridLayout()

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter M3U8 URL or drag and drop file here")
        self.url_input.setDragEnabled(True)
        input_layout.addWidget(QLabel("URL or File:"), 0, 0)
        input_layout.addWidget(self.url_input, 0, 1)

        # Browse button
        self.btn_browse = QPushButton()
        self.btn_browse.setObjectName("btnBrowse")
        self.btn_browse.setText("Browse")
        self.btn_browse.clicked.connect(self._browse_m3u8_file)
        input_layout.addWidget(self.btn_browse, 0, 2)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox()
        output_group.setTitle("Output")
        output_layout = QGridLayout()

        # Output path
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output MP4 file path")
        output_layout.addWidget(QLabel("Save to:"), 0, 0)
        output_layout.addWidget(self.output_path, 0, 1)

        # Browse output button
        self.btn_browse_output = QPushButton()
        self.btn_browse_output.setObjectName("btnBrowse")
        self.btn_browse_output.setText("Browse")
        self.btn_browse_output.clicked.connect(self._browse_output_file)
        output_layout.addWidget(self.btn_browse_output, 0, 2)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.btn_convert = QPushButton()
        self.btn_convert.setText("Convert")
        self.btn_convert.clicked.connect(self._start_conversion)

        self.btn_pause = QPushButton()
        self.btn_pause.setObjectName("btnPause")
        self.btn_pause.setText("Pause")
        self.btn_pause.clicked.connect(self._pause_conversion)
        self.btn_pause.setEnabled(False)

        self.btn_stop = QPushButton()
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setText("Stop")
        self.btn_stop.clicked.connect(self._stop_conversion)
        self.btn_stop.setEnabled(False)

        self.btn_open_folder = QPushButton()
        self.btn_open_folder.setObjectName("btnOpenFolder")
        self.btn_open_folder.setText("Open Folder")
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        self.btn_open_folder.setEnabled(False)

        control_layout.addWidget(self.btn_convert)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_open_folder)
        control_layout.addStretch()

        main_layout.addLayout(control_layout)

        # Progress section
        progress_group = QGroupBox()
        progress_group.setTitle("Progress")
        progress_layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # Progress info
        progress_info_layout = QHBoxLayout()

        self.status_label = QLabel()
        self.status_label.setObjectName("labelStatus")
        self.status_label.setText("Status: Ready")
        progress_info_layout.addWidget(self.status_label)

        progress_info_layout.addStretch()

        self.speed_label = QLabel()
        self.speed_label.setText("Speed: -")
        progress_info_layout.addWidget(self.speed_label)

        progress_layout.addLayout(progress_info_layout)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Log section
        log_group = QGroupBox()
        log_group.setTitle("Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        # Clear log button
        clear_log_layout = QHBoxLayout()
        clear_log_layout.addStretch()

        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.setMaximumWidth(100)
        btn_clear_log.clicked.connect(self._clear_log)
        clear_log_layout.addWidget(btn_clear_log)

        log_layout.addLayout(clear_log_layout)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Language menu
        language_menu = menubar.addMenu("Language")

        english_action = QAction("English", self)
        english_action.triggered.connect(lambda: self._change_language("en_US"))
        language_menu.addAction(english_action)

        chinese_action = QAction("中文", self)
        chinese_action.triggered.connect(lambda: self._change_language("zh_CN"))
        language_menu.addAction(chinese_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _load_styles(self):
        """Load QSS styles"""
        try:
            style_file = Path(__file__).parent.parent / "resources" / "styles.qss"
            if style_file.exists():
                with open(style_file, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load styles: {e}")

    def _apply_translations(self):
        """Apply translations based on current language"""
        # This is a simplified version - in production you would use QTranslator
        translations = {
            "en_US": {
                "window_title": "M3U8 to MP4 Converter",
                "input": "Input",
                "output": "Output",
                "url_or_file": "URL or File:",
                "browse": "Browse",
                "save_to": "Save to:",
                "convert": "Convert",
                "pause": "Pause",
                "stop": "Stop",
                "open_folder": "Open Folder",
                "progress": "Progress",
                "log": "Log",
                "clear_log": "Clear Log",
                "status_ready": "Status: Ready",
                "speed": "Speed: -",
            },
            "zh_CN": {
                "window_title": "M3U8 转 MP4 转换器",
                "input": "输入",
                "output": "输出",
                "url_or_file": "URL 或文件:",
                "browse": "浏览",
                "save_to": "保存到:",
                "convert": "转换",
                "pause": "暂停",
                "stop": "停止",
                "open_folder": "打开文件夹",
                "progress": "进度",
                "log": "日志",
                "clear_log": "清空日志",
                "status_ready": "状态: 就绪",
                "speed": "速度: -",
            }
        }

        t = translations.get(self.current_language, translations["en_US"])

        self.setWindowTitle(t["window_title"])
        self.url_input.setPlaceholderText(
            "Enter M3U8 URL or drag and drop file here" if self.current_language == "en_US"
            else "输入 M3U8 URL 或拖放文件到此处"
        )

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
                # Auto-set output path with simpler filename
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
            # Auto-set output path with simpler filename
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
            self.output_path.setText(file_path)

    def _validate_inputs(self) -> bool:
        """Validate user inputs"""
        url = self.url_input.text().strip()
        output = self.output_path.text().strip()

        if not url:
            QMessageBox.warning(
                self,
                "Warning",
                "Please enter M3U8 URL or select a file"
            )
            return False

        if not output:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select output path"
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

    def _pause_conversion(self):
        """Pause/resume conversion"""
        if self.worker:
            if self.btn_pause.text() == "Pause":
                self.worker.pause()
                self.btn_pause.setText("Resume")
                self.status_label.setText("Status: Paused")
                self._log("Conversion paused", "INFO")
            else:
                self.worker.resume()
                self.btn_pause.setText("Pause")
                self.status_label.setText("Status: Converting...")
                self._log("Conversion resumed", "INFO")

    def _stop_conversion(self):
        """Stop conversion"""
        if self.worker:
            reply = QMessageBox.question(
                self,
                "Confirm Stop",
                "Are you sure you want to stop the conversion?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
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

            QMessageBox.information(
                self,
                "Success",
                f"Conversion completed successfully!\n\nSaved to: {self.output_path.text()}"
            )
        else:
            self.status_label.setText("Status: Failed")
            self._log(f"Conversion failed: {message}", "ERROR")

            QMessageBox.critical(
                self,
                "Error",
                f"Conversion failed:\n{message}"
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
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to open folder:\n{str(e)}"
                )

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About M3U8 to MP4 Converter",
            "<h3>M3U8 to MP4 Converter</h3>"
            "<p>A desktop application for converting M3U8 video streams to MP4 format.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Download M3U8 playlists</li>"
            "<li>AES-128 decryption support</li>"
            "<li>Multi-threaded downloading</li>"
            "<li>Convert to MP4 using FFmpeg</li>"
            "</ul>"
            "<p>Powered by PyQt5 and FFmpeg</p>"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Conversion is in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
