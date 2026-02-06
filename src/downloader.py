"""
M3U8 Downloader Module
Handles downloading M3U8 playlists and TS segments with AES-128 decryption support
"""

import os
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Tuple, Callable
from urllib.parse import urljoin, urlparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64


class M3U8Downloader:
    """Downloader for M3U8 video streams"""

    def __init__(self, max_workers: int = 10):
        """
        Initialize the downloader

        Args:
            max_workers: Maximum number of concurrent download workers
        """
        self.max_workers = max_workers
        self.session: Optional[aiohttp.ClientSession] = None
        self._paused = False
        self._stopped = False
        self._progress_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None

    def set_callbacks(self, progress_callback: Callable = None, log_callback: Callable = None):
        """Set progress and log callbacks"""
        self._progress_callback = progress_callback
        self._log_callback = log_callback

    def _log(self, message: str, level: str = "INFO"):
        """Internal logging method"""
        if self._log_callback:
            self._log_callback(message, level)

    def _update_progress(self, current: int, total: int, speed: float = 0):
        """Internal progress update method"""
        if self._progress_callback:
            self._progress_callback(current, total, speed)

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=self.max_workers)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def pause(self):
        """Pause the download process"""
        self._paused = True
        self._log("Download paused", "INFO")

    def resume(self):
        """Resume the download process"""
        self._paused = False
        self._log("Download resumed", "INFO")

    def stop(self):
        """Stop the download process"""
        self._stopped = True
        self._log("Download stopped", "INFO")

    async def _check_pause_stop(self):
        """Check if download is paused or stopped"""
        while self._paused and not self._stopped:
            await asyncio.sleep(0.1)

        if self._stopped:
            raise Exception("Download stopped by user")

    async def fetch_m3u8_content(self, url: str) -> str:
        """
        Fetch M3U8 playlist content

        Args:
            url: M3U8 playlist URL

        Returns:
            M3U8 content as string
        """
        try:
            self._log(f"Fetching M3U8 from: {url}", "INFO")
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
                self._log("M3U8 content fetched successfully", "INFO")
                return content
        except Exception as e:
            self._log(f"Failed to fetch M3U8: {str(e)}", "ERROR")
            raise

    def parse_m3u8(self, content: str, base_url: str) -> Tuple[List[str], Optional[dict]]:
        """
        Parse M3U8 playlist content

        Args:
            content: M3U8 playlist content
            base_url: Base URL for resolving relative paths

        Returns:
            Tuple of (segment URLs, encryption info dict)
        """
        segments = []
        encryption_info = None
        key_url = None
        iv = None

        lines = content.strip().split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#EXT'):
                # Check for encryption info
                if line.startswith('#EXT-X-KEY:'):
                    encryption_info = self._parse_encryption_info(line)
                    # Extract key URL
                    if 'URI' in encryption_info:
                        key_url = encryption_info['URI'].strip('"')
                        if not key_url.startswith('http'):
                            key_url = urljoin(base_url, key_url)
                        encryption_info['key_url'] = key_url
                    # Extract IV
                    if 'IV' in encryption_info:
                        iv_hex = encryption_info['IV'].strip('"').replace('0x', '')
                        iv = bytes.fromhex(iv_hex)
                continue

            # Skip master playlist markers
            if line.startswith('#'):
                continue

            # This is a segment URL
            if line:
                # Handle relative URLs
                if not line.startswith('http'):
                    line = urljoin(base_url, line)
                segments.append(line)

        if encryption_info:
            self._log(f"Encryption detected: {encryption_info.get('METHOD')}", "INFO")

        self._log(f"Parsed {len(segments)} segments", "INFO")
        return segments, encryption_info

    def _parse_encryption_info(self, line: str) -> dict:
        """Parse encryption info from EXT-X-KEY line"""
        info = {}
        parts = line.split(':')[1].split(',')

        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                info[key.strip()] = value.strip()

        return info

    async def fetch_key(self, key_url: str) -> bytes:
        """
        Fetch AES decryption key

        Args:
            key_url: URL of the encryption key

        Returns:
            Encryption key as bytes
        """
        try:
            self._log(f"Fetching encryption key from: {key_url}", "INFO")
            async with self.session.get(key_url) as response:
                response.raise_for_status()
                key = await response.read()
                self._log("Encryption key fetched successfully", "INFO")
                return key
        except Exception as e:
            self._log(f"Failed to fetch encryption key: {str(e)}", "ERROR")
            raise

    async def download_segment(
        self,
        segment_url: str,
        output_path: Path,
        index: int,
        key: Optional[bytes] = None,
        iv: Optional[bytes] = None
    ) -> Path:
        """
        Download a single TS segment

        Args:
            segment_url: URL of the segment
            output_path: Directory to save the segment
            index: Segment index for filename
            key: AES decryption key (if encrypted)
            iv: AES initialization vector

        Returns:
            Path to downloaded segment
        """
        await self._check_pause_stop()

        segment_filename = output_path / f"segment_{index:05d}.ts"
        temp_filename = output_path / f"segment_{index:05d}.ts.tmp"

        try:
            async with self.session.get(segment_url) as response:
                response.raise_for_status()
                data = await response.read()

            # Decrypt if key is provided
            if key:
                data = self._decrypt_segment(data, key, iv)

            # Write to temp file first, then rename
            temp_filename.write_bytes(data)
            temp_filename.rename(segment_filename)

            return segment_filename

        except Exception as e:
            self._log(f"Failed to download segment {index}: {str(e)}", "ERROR")
            if temp_filename.exists():
                temp_filename.unlink()
            raise

    def _decrypt_segment(self, data: bytes, key: bytes, iv: Optional[bytes] = None) -> bytes:
        """
        Decrypt AES-128 encrypted segment

        Args:
            data: Encrypted segment data
            key: AES decryption key
            iv: Initialization vector

        Returns:
            Decrypted data
        """
        try:
            # If no IV provided, use segment index as IV (common pattern)
            if iv is None:
                cipher = AES.new(key, AES.MODE_CBC)
            else:
                cipher = AES.new(key, AES.MODE_CBC, iv)

            # Pad data to AES block size (16 bytes)
            padding_length = 16 - (len(data) % 16)
            if padding_length != 16:
                data = data + bytes([padding_length] * padding_length)

            decrypted = cipher.decrypt(data)
            return decrypted
        except Exception as e:
            self._log(f"Decryption failed: {str(e)}", "ERROR")
            raise

    async def download_segments(
        self,
        segments: List[str],
        output_dir: Path,
        key: Optional[bytes] = None,
        iv: Optional[bytes] = None
    ) -> List[Path]:
        """
        Download all segments concurrently

        Args:
            segments: List of segment URLs
            output_dir: Directory to save segments
            key: AES decryption key (if encrypted)
            iv: AES initialization vector

        Returns:
            List of downloaded segment paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files = []
        total_segments = len(segments)
        completed = 0

        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(self.max_workers)

        async def download_with_semaphore(index: int, url: str):
            nonlocal completed
            async with semaphore:
                result = await self.download_segment(url, output_dir, index, key, iv)
                completed += 1
                self._update_progress(completed, total_segments)
                return result

        # Create download tasks
        tasks = [
            download_with_semaphore(i, url)
            for i, url in enumerate(segments)
        ]

        # Execute downloads
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._log(f"Segment {i} failed: {str(result)}", "ERROR")
            elif isinstance(result, Path):
                downloaded_files.append(result)

        if len(downloaded_files) < total_segments:
            self._log(
                f"Warning: Only {len(downloaded_files)}/{total_segments} segments downloaded",
                "WARNING"
            )

        return sorted(downloaded_files)

    async def download(
        self,
        url: str,
        output_dir: Path,
        validate: bool = True
    ) -> Tuple[List[Path], Optional[dict]]:
        """
        Download M3U8 playlist and all segments

        Args:
            url: M3U8 playlist URL
            output_dir: Directory to save segments
            validate: Whether to validate M3U8 content first

        Returns:
            Tuple of (downloaded segment paths, encryption info)
        """
        try:
            # Reset state
            self._paused = False
            self._stopped = False

            # Fetch M3U8 content
            content = await self.fetch_m3u8_content(url)

            # Validate if requested
            if validate and not self._validate_m3u8(content):
                raise ValueError("Invalid M3U8 format")

            # Parse M3U8
            base_url = url[:url.rfind('/') + 1]
            segments, encryption_info = self.parse_m3u8(content, base_url)

            if not segments:
                raise ValueError("No segments found in M3U8 playlist")

            # Fetch encryption key if needed
            key = None
            iv = None
            if encryption_info and encryption_info.get('METHOD') == 'AES-128':
                key_url = encryption_info.get('key_url')
                if key_url:
                    key = await self.fetch_key(key_url)
                    iv = encryption_info.get('iv')  # Will be bytes if set

            # Download all segments
            self._log(f"Starting download of {len(segments)} segments...", "INFO")
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            downloaded_files = await self.download_segments(
                segments,
                output_dir,
                key,
                iv
            )

            self._log("All segments downloaded successfully", "INFO")
            return downloaded_files, encryption_info

        except Exception as e:
            self._log(f"Download failed: {str(e)}", "ERROR")
            raise

    def _validate_m3u8(self, content: str) -> bool:
        """
        Validate M3U8 content

        Args:
            content: M3U8 content

        Returns:
            True if valid, False otherwise
        """
        if not content:
            return False

        # Check for M3U8 header
        if not content.startswith('#EXTM3U'):
            return False

        # Check for at least one segment
        lines = content.split('\n')
        has_segment = any(
            line.strip() and not line.startswith('#')
            for line in lines
        )

        return has_segment


async def download_m3u8(
    url: str,
    output_dir: str,
    max_workers: int = 10,
    progress_callback: Callable = None,
    log_callback: Callable = None
) -> Tuple[List[Path], Optional[dict]]:
    """
    Convenience function to download M3U8 playlist

    Args:
        url: M3U8 playlist URL or file path
        output_dir: Directory to save segments
        max_workers: Maximum concurrent downloads
        progress_callback: Callback for progress updates
        log_callback: Callback for log messages

    Returns:
        Tuple of (downloaded segment paths, encryption info)
    """
    async with M3U8Downloader(max_workers=max_workers) as downloader:
        downloader.set_callbacks(progress_callback, log_callback)
        return await downloader.download(url, Path(output_dir))
