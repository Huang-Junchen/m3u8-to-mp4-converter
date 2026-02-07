"""
M3U8 to MP4 Converter - Main Entry Point
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow as ClassicMainWindow
from ui.fluent_main_window import MainWindow as FluentMainWindow


def setup_asyncio():
    """Setup asyncio for Qt integration"""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []

    try:
        import aiohttp
    except ImportError:
        missing.append('aiohttp')

    try:
        import requests
    except ImportError:
        missing.append('requests')

    try:
        from Crypto.Cipher import AES
    except ImportError:
        missing.append('pycryptodome')

    if missing:
        print("Warning: Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nPlease install them using:")
        print(f"  pip install {' '.join(missing)}")
        print(f"  Or: pip install -r requirements.txt")
        return False

    return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    import shutil

    ffmpeg_path = shutil.which('ffmpeg')

    if ffmpeg_path:
        print(f"FFmpeg found at: {ffmpeg_path}")
        return True
    else:
        print("Warning: FFmpeg not found in system PATH.")
        print("Please install FFmpeg to enable video conversion:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt install ffmpeg (Debian/Ubuntu)")
        return False


def main():
    """Main entry point"""
    # Setup asyncio
    setup_asyncio()

    # Check dependencies
    if not check_dependencies():
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Check FFmpeg
    check_ffmpeg()

    # Create Qt application
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("M3U8 to MP4 Converter")
    app.setOrganizationName("M3U8Converter")
    app.setApplicationVersion("1.0.0")

    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Choose UI mode (Fluent or Classic)
    # Set environment variable USE_FLUENT_UI=false to use classic UI
    use_fluent = os.environ.get('USE_FLUENT_UI', 'true').lower() == 'true'

    if use_fluent:
        try:
            window = FluentMainWindow()
        except ImportError:
            print("PyQt-Fluent-Widgets not available, falling back to classic UI...")
            window = ClassicMainWindow()
    else:
        window = ClassicMainWindow()

    window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
