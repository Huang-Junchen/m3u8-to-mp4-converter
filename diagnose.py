"""
Diagnostic script to help debug M3U8 conversion issues
"""
import sys
import io
from pathlib import Path

# Set stdout encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.converter import Converter


def diagnose_conversion(m3u8_path: str):
    """Diagnose conversion issues"""
    m3u8_file = Path(m3u8_path)

    print("M3U8 File path set")
    print(f"File exists: {m3u8_file.exists()}")
    print()

    # Expected segments directory
    expected_output = m3u8_file.parent / f"{m3u8_file.stem}_segments"

    print(f"Expected segments directory: {expected_output}")
    print(f"Directory exists: {expected_output.exists()}")
    print()

    if expected_output.exists():
        segments = sorted(expected_output.glob("*.ts"))
        print(f"Found {len(segments)} segment files")
        print(f"First few: {[s.name for s in segments[:5]]}")
        print()

        # Try conversion
        output_file = m3u8_file.parent / f"{m3u8_file.stem}.mp4"
        print(f"Output file will be: ...{m3u8_file.parent.name}/{m3u8_file.stem}.mp4")
        print()

        print("Starting conversion...")
        converter = Converter()

        def log_callback(msg, level):
            print(f"[{level}] {msg}")

        converter.set_callbacks(log_callback=log_callback)

        if not converter.ffmpeg_path:
            print("ERROR: FFmpeg not found!")
            return

        print(f"FFmpeg version: {converter.get_ffmpeg_version()}")

        # Create segment list file manually to inspect
        list_file = expected_output / "concat_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for segment in segments:
                segment_path = segment.resolve().as_posix()
                f.write(f"file '{segment_path}'\n")

        print(f"Created list file: {list_file}")
        print(f"First 5 lines:")
        with open(list_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 5:
                    break
                print(f"  {line.rstrip()}")

        # Try conversion
        success = converter.convert_concat(
            segments,
            output_file,
            delete_segments=False
        )

        print()
        if success:
            print(f"SUCCESS! Output file: {output_file}")
            print(f"File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
        else:
            print("FAILED! Check logs above for errors")
    else:
        print("Segments directory not found!")
        print("Please run conversion in GUI first")


def main():
    """Main diagnostic function"""
    # User's M3U8 file path
    m3u8_path = r"E:/迅雷下载/ASMR角色扮演♡海岸线上的心跳｜在海边帮助溺水的你.m3u8/index.m3u8"

    print("=" * 60)
    print("M3U8 Conversion Diagnostic Tool")
    print("=" * 60)
    print()

    try:
        diagnose_conversion(m3u8_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
