"""
Unit tests for M3U8 to MP4 Converter
"""

import unittest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.converter import Converter
from src.downloader import M3U8Downloader


class TestConverter(unittest.TestCase):
    """Test converter functionality"""

    def setUp(self):
        """Setup test fixtures"""
        self.converter = Converter()

    def test_find_ffmpeg(self):
        """Test FFmpeg detection"""
        ffmpeg_path = self.converter._find_ffmpeg()
        # FFmpeg may or may not be installed
        self.assertTrue(ffmpeg_path is None or Path(ffmpeg_path).exists())

    def test_check_ffmpeg(self):
        """Test FFmpeg availability check"""
        result = self.converter.check_ffmpeg()
        self.assertIsInstance(result, bool)


class TestDownloader(unittest.TestCase):
    """Test downloader functionality"""

    def setUp(self):
        """Setup test fixtures"""
        self.downloader = M3U8Downloader(max_workers=5)

    def test_validate_m3u8(self):
        """Test M3U8 validation"""
        # Valid M3U8
        valid_m3u8 = """#EXTM3U
#EXT-X-VERSION:3
#EXTINF:10.0,
segment1.ts
#EXTINF:10.0,
segment2.ts
"""
        self.assertTrue(self.downloader._validate_m3u8(valid_m3u8))

        # Invalid M3U8
        invalid_m3u8 = "Not an M3U8 file"
        self.assertFalse(self.downloader._validate_m3u8(invalid_m3u8))

    def test_parse_encryption_info(self):
        """Test encryption info parsing"""
        line = '#EXT-X-KEY:METHOD=AES-128,URI="key.key",IV=0x12345678'
        info = self.downloader._parse_encryption_info(line)

        self.assertEqual(info['METHOD'], 'AES-128')
        self.assertEqual(info['URI'], '"key.key"')
        self.assertEqual(info['IV'], '0x12345678')


if __name__ == '__main__':
    unittest.main()
