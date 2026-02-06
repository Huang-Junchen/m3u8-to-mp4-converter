"""
Quick conversion test using existing segments
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.converter import Converter


def quick_convert():
    """Quick conversion test"""
    # Segments directory
    segments_dir = Path(r"E:/迅雷下载/ASMR角色扮演♡海岸线上的心跳｜在海边帮助溺水的你.m3u8/index_segments")
    output_file = Path(r"E:/迅雷下载/ASMR角色扮演♡海岸线上的心跳｜在海边帮助溺水的你.m3u8/test_output.mp4")

    print("=" * 60)
    print("Quick Conversion Test")
    print("=" * 60)
    print()

    # Get all segment files
    segments = sorted(segments_dir.glob("*.ts"))
    print(f"Found {len(segments)} segment files")
    print(f"Output: {output_file}")
    print()

    if not segments:
        print("ERROR: No segment files found!")
        return

    # Create converter
    converter = Converter()

    def log_callback(msg, level):
        if level in ["ERROR", "INFO"]:
            print(f"[{level}] {msg}")

    converter.set_callbacks(log_callback=log_callback)

    if not converter.ffmpeg_path:
        print("ERROR: FFmpeg not found!")
        return

    print(f"FFmpeg: {converter.ffmpeg_path}")
    print(f"Version: {converter.get_ffmpeg_version()}")
    print()

    print("Starting conversion...")
    print("-" * 60)

    success = converter.convert_concat(
        segments,
        output_file,
        delete_segments=False
    )

    print("-" * 60)
    print()

    if success:
        print(f"SUCCESS!")
        print(f"Output file: {output_file}")
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024*1024)
            print(f"File size: {size_mb:.2f} MB")
    else:
        print("FAILED!")
        print("Check the logs above for errors")


if __name__ == "__main__":
    quick_convert()
