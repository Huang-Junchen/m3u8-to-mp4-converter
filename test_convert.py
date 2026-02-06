"""
Test script for M3U8 to MP4 conversion with decryption
"""
import sys
import re
from pathlib import Path
from Crypto.Cipher import AES

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.converter import Converter


def log_callback(message, level="INFO"):
    """Log callback"""
    if level in ["ERROR", "WARNING"]:
        print(f"\n[{level}] {message}")
    elif level == "INFO":
        print(f"\n[INFO] {message}")


def parse_and_decrypt_m3u8(m3u8_path: str, output_dir: Path) -> list:
    """
    Parse local M3U8 file with AES-128 decryption
    Returns list of decrypted segment paths
    """
    m3u8_file = Path(m3u8_path)

    if not m3u8_file.exists():
        raise FileNotFoundError(f"M3U8 file not found: {m3u8_path}")

    # Get directory containing M3U8 file
    base_dir = m3u8_file.parent

    # Read M3U8 content
    with open(m3u8_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse encryption info
    key_path = None
    iv = None

    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('#EXT-X-KEY:'):
            # Parse EXT-X-KEY line
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
        print(f"Reading encryption key...")
        with open(key_path, 'rb') as f:
            key = f.read()
        print(f"Key size: {len(key)} bytes")
    else:
        print("Warning: Key file not found, files might not be encrypted")

    # Create output directory for decrypted segments
    decrypted_dir = output_dir / "decrypted_segments"
    decrypted_dir.mkdir(parents=True, exist_ok=True)

    # Parse segments and decrypt
    segments = []
    segment_index = 0

    for line in lines:
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # This is a segment path
        segment_path = base_dir / line

        if segment_path.exists():
            # Decrypt if key is available
            if key:
                decrypted_path = decrypted_dir / f"segment_{segment_index:05d}.ts"

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
                padding_length = decrypted_data[-1]
                if padding_length <= 16:
                    decrypted_data = decrypted_data[:-padding_length]

                # Write decrypted data
                with open(decrypted_path, 'wb') as f:
                    f.write(decrypted_data)

                segments.append(decrypted_path)
                print(f"\rDecrypted {segment_index + 1} segments", end='', flush=True)
            else:
                segments.append(segment_path)

            segment_index += 1
        else:
            print(f"\nWarning: Segment not found: {segment_path}")

    print(f"\nTotal segments: {len(segments)}")
    return segments


def main():
    """Main test function"""
    # Input M3U8 file path
    m3u8_path = r"E:/迅雷下载/ASMR角色扮演♡海岸线上的心跳｜在海边帮助溺水的你.m3u8/index.m3u8"

    # Output directory and file
    output_dir = Path(r"E:/迅雷下载/output")
    output_file = output_dir / "ASMR_coastline_heartbeat.mp4"

    print("M3U8 file path set")
    print(f"Output: {output_file}")
    print("-" * 60)

    try:
        # Parse and decrypt M3U8 file
        print("\nStep 1: Parsing and decrypting M3U8 file...")
        segments = parse_and_decrypt_m3u8(m3u8_path, output_dir)

        if not segments:
            print("\nError: No video segments found")
            return

        # Convert to MP4
        print("\nStep 2: Converting to MP4...")
        converter = Converter()
        converter.set_callbacks(log_callback=log_callback)

        if not converter.ffmpeg_path:
            print("\nError: FFmpeg not installed or not in PATH")
            return

        print(f"Using FFmpeg version: {converter.get_ffmpeg_version()}")

        success = converter.convert_concat(
            segments,
            output_file,
            delete_segments=False  # Keep decrypted segments
        )

        if success:
            print(f"\nConversion successful!")
            print(f"Output file: {output_file}")
            if output_file.exists():
                file_size_mb = output_file.stat().st_size / (1024*1024)
                print(f"File size: {file_size_mb:.2f} MB")
        else:
            print("\nConversion failed")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
