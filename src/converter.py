"""
M3U8 to MP4 Converter Module
Handles conversion of downloaded TS segments to MP4 using FFmpeg
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable, List
import re


class Converter:
    """Converter for merging TS segments to MP4"""

    def __init__(self):
        """Initialize the converter"""
        self._log_callback: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None
        self.ffmpeg_path = self._find_ffmpeg()

    def set_callbacks(self, progress_callback: Callable = None, log_callback: Callable = None):
        """Set progress and log callbacks"""
        self._progress_callback = progress_callback
        self._log_callback = log_callback

    def _log(self, message: str, level: str = "INFO"):
        """Internal logging method"""
        if self._log_callback:
            self._log_callback(message, level)

    def _update_progress(self, current: int, total: int):
        """Internal progress update method"""
        if self._progress_callback:
            self._progress_callback(current, total)

    def _find_ffmpeg(self) -> Optional[str]:
        """
        Find FFmpeg executable in system PATH

        Returns:
            Path to FFmpeg executable or None
        """
        # Check if ffmpeg is in PATH
        ffmpeg_path = shutil.which('ffmpeg')

        if ffmpeg_path:
            self._log(f"Found FFmpeg at: {ffmpeg_path}", "INFO")
            return ffmpeg_path

        # Check common installation paths
        common_paths = [
            r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
            r"C:\FFmpeg\bin\ffmpeg.exe",
            r"/usr/local/bin/ffmpeg",
            r"/usr/bin/ffmpeg",
        ]

        for path in common_paths:
            if os.path.exists(path):
                self._log(f"Found FFmpeg at: {path}", "INFO")
                return path

        self._log("FFmpeg not found in system", "WARNING")
        return None

    def check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available

        Returns:
            True if FFmpeg is available, False otherwise
        """
        if not self.ffmpeg_path:
            self.ffmpeg_path = self._find_ffmpeg()
        return self.ffmpeg_path is not None

    def get_ffmpeg_version(self) -> Optional[str]:
        """
        Get FFmpeg version

        Returns:
            FFmpeg version string or None
        """
        if not self.check_ffmpeg():
            return None

        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )

            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split('\n')[0]
                version_match = re.search(r'version (\S+)', first_line)
                if version_match:
                    return version_match.group(1)

        except Exception as e:
            self._log(f"Failed to get FFmpeg version: {str(e)}", "ERROR")

        return None

    def create_segment_list(self, segments: List[Path], output_file: Path) -> Path:
        """
        Create a file list for FFmpeg concat demuxer

        Args:
            segments: List of segment file paths
            output_file: Path to output the list file

        Returns:
            Path to created list file
        """
        list_file = Path(output_file).with_suffix('.txt')

        with open(list_file, 'w', encoding='utf-8') as f:
            for segment in segments:
                # Use absolute paths and escape backslashes on Windows
                segment_path = segment.resolve().as_posix()
                f.write(f"file '{segment_path}'\n")

        self._log(f"Created segment list file: {list_file}", "INFO")
        return list_file

    def convert_concat(
        self,
        segments: List[Path],
        output_file: Path,
        delete_segments: bool = True
    ) -> bool:
        """
        Convert TS segments to MP4 using FFmpeg concat demuxer

        Args:
            segments: List of TS segment files
            output_file: Output MP4 file path
            delete_segments: Whether to delete segment files after conversion

        Returns:
            True if conversion successful, False otherwise
        """
        if not segments:
            self._log("No segments to convert", "ERROR")
            return False

        if not self.check_ffmpeg():
            self._log("FFmpeg not available. Cannot convert.", "ERROR")
            return False

        try:
            self._log("Starting conversion...", "INFO")

            # Create segment list file
            list_file = self.create_segment_list(segments, output_file)

            # Build FFmpeg command
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                "-y",  # Overwrite output file
                str(output_file)
            ]

            self._log(f"Running FFmpeg: {' '.join(cmd)}", "DEBUG")

            # Run FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                universal_newlines=True
            )

            # Monitor progress
            total_segments = len(segments)
            current_segment = 0

            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break

                if output:
                    # Try to parse progress
                    # FFmpeg doesn't provide easy progress for concat, so we estimate
                    self._log(output.strip(), "DEBUG")

            return_code = process.poll()

            # Read any remaining error output
            error_output = process.stderr.read()

            # Clean up list file
            if list_file.exists():
                list_file.unlink()

            if return_code != 0:
                self._log(f"FFmpeg failed with return code: {return_code}", "ERROR")
                self._log(f"Error output: {error_output}", "ERROR")
                return False

            self._log(f"Conversion completed: {output_file}", "INFO")

            # Delete segment files if requested
            if delete_segments:
                self._delete_segments(segments)

            return True

        except Exception as e:
            self._log(f"Conversion failed: {str(e)}", "ERROR")
            return False

    def convert_with_progress(
        self,
        segments: List[Path],
        output_file: Path,
        delete_segments: bool = True
    ) -> bool:
        """
        Convert TS segments to MP4 with progress reporting

        Args:
            segments: List of TS segment files
            output_file: Output MP4 file path
            delete_segments: Whether to delete segment files after conversion

        Returns:
            True if conversion successful, False otherwise
        """
        if not segments:
            self._log("No segments to convert", "ERROR")
            return False

        if not self.check_ffmpeg():
            self._log("FFmpeg not available. Cannot convert.", "ERROR")
            return False

        try:
            self._log("Starting conversion with progress tracking...", "INFO")

            # Create segment list file
            list_file = self.create_segment_list(segments, output_file)

            # Build FFmpeg command with progress reporting
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                "-progress", "pipe:1",  # Write progress to stdout
                "-y",
                str(output_file)
            ]

            self._log(f"Running FFmpeg: {' '.join(cmd)}", "DEBUG")

            # Run FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                universal_newlines=True
            )

            # Parse progress
            total_segments = len(segments)
            duration = None

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break

                if output:
                    # Parse progress: out_time_ms, total_size, etc.
                    if '=' in output:
                        key, value = output.strip().split('=', 1)

                        if key == 'out_time_ms':
                            # Convert microseconds to seconds
                            time_ms = int(value) / 1_000_000
                            self._log(f"Processed time: {time_ms:.2f}s", "DEBUG")

            return_code = process.poll()

            # Read any remaining error output
            error_output = process.stderr.read()

            # Clean up list file
            if list_file.exists():
                list_file.unlink()

            if return_code != 0:
                self._log(f"FFmpeg failed with return code: {return_code}", "ERROR")
                self._log(f"Error output: {error_output}", "ERROR")
                return False

            self._log(f"Conversion completed: {output_file}", "INFO")

            # Delete segment files if requested
            if delete_segments:
                self._delete_segments(segments)

            return True

        except Exception as e:
            self._log(f"Conversion failed: {str(e)}", "ERROR")
            return False

    def _delete_segments(self, segments: List[Path]):
        """
        Delete segment files

        Args:
            segments: List of segment file paths to delete
        """
        deleted = 0
        for segment in segments:
            try:
                if segment.exists():
                    segment.unlink()
                    deleted += 1
            except Exception as e:
                self._log(f"Failed to delete {segment}: {str(e)}", "WARNING")

        self._log(f"Deleted {deleted}/{len(segments)} segment files", "INFO")

    def get_video_info(self, video_file: Path) -> Optional[dict]:
        """
        Get video file information using FFprobe

        Args:
            video_file: Path to video file

        Returns:
            Dictionary with video information or None
        """
        ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')

        if not os.path.exists(ffprobe_path):
            self._log("FFprobe not available", "WARNING")
            return None

        try:
            cmd = [
                ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,codec_name,duration",
                "-of", "json",
                str(video_file)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )

            if result.returncode == 0:
                import json
                return json.loads(result.stdout)

        except Exception as e:
            self._log(f"Failed to get video info: {str(e)}", "ERROR")

        return None

    def merge_and_convert(
        self,
        segments: List[Path],
        output_file: Path,
        video_codec: str = "copy",
        audio_codec: str = "copy",
        delete_segments: bool = True
    ) -> bool:
        """
        Merge and convert TS segments with codec options

        Args:
            segments: List of TS segment files
            output_file: Output MP4 file path
            video_codec: Video codec (copy, libx264, etc.)
            audio_codec: Audio codec (copy, aac, etc.)
            delete_segments: Whether to delete segment files after conversion

        Returns:
            True if conversion successful, False otherwise
        """
        if not segments:
            self._log("No segments to convert", "ERROR")
            return False

        if not self.check_ffmpeg():
            self._log("FFmpeg not available. Cannot convert.", "ERROR")
            return False

        try:
            self._log("Starting conversion with custom codecs...", "INFO")

            # Create segment list file
            list_file = self.create_segment_list(segments, output_file)

            # Build FFmpeg command
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c:v", video_codec,
                "-c:a", audio_codec,
                "-y",
                str(output_file)
            ]

            self._log(f"Running FFmpeg: {' '.join(cmd)}", "DEBUG")

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=3600  # 1 hour timeout
            )

            # Clean up list file
            if list_file.exists():
                list_file.unlink()

            if result.returncode != 0:
                self._log(f"FFmpeg error: {result.stderr}", "ERROR")
                return False

            self._log(f"Conversion completed: {output_file}", "INFO")

            # Delete segment files if requested
            if delete_segments:
                self._delete_segments(segments)

            return True

        except subprocess.TimeoutExpired:
            self._log("Conversion timeout after 1 hour", "ERROR")
            return False
        except Exception as e:
            self._log(f"Conversion failed: {str(e)}", "ERROR")
            return False


def convert_to_mp4(
    segments: List[Path],
    output_file: str,
    progress_callback: Callable = None,
    log_callback: Callable = None,
    delete_segments: bool = True
) -> bool:
    """
    Convenience function to convert segments to MP4

    Args:
        segments: List of TS segment files
        output_file: Output MP4 file path
        progress_callback: Callback for progress updates
        log_callback: Callback for log messages
        delete_segments: Whether to delete segment files after conversion

    Returns:
        True if conversion successful, False otherwise
    """
    converter = Converter()
    converter.set_callbacks(progress_callback, log_callback)
    return converter.convert_concat(segments, Path(output_file), delete_segments)
