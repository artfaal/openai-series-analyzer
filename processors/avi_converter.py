"""
AVI → MKV Converter
Converts .avi files to .mkv container using ffmpeg (remux without re-encoding)
"""

import subprocess
from pathlib import Path
from typing import Optional


class AVIConverter:
    """AVI to MKV file converter"""

    def __init__(self):
        self.ffmpeg_path = 'ffmpeg'

    def needs_conversion(self, file_path: Path) -> bool:
        """
        Checks if file needs conversion

        Args:
            file_path: Path to file

        Returns:
            True if file is .avi, otherwise False
        """
        return file_path.suffix.lower() == '.avi'

    def convert(self, avi_file: Path, output_file: Optional[Path] = None) -> Optional[Path]:
        """
        Converts AVI to MKV (remux without re-encoding)

        Args:
            avi_file: Path to .avi file
            output_file: Path for output file (if None, created next to original)

        Returns:
            Path to created MKV file or None on error
        """
        if not self.needs_conversion(avi_file):
            print(f"⚠️  {avi_file.name} не является AVI файлом")
            return None

        if output_file is None:
            output_file = avi_file.with_suffix('.mkv')

        print(f"\n🔄 Конвертация AVI → MKV: {avi_file.name}")
        print(f"   → {output_file.name}")

        try:
            # ffmpeg -i input.avi -c copy output.mkv
            # -c copy = copy streams without re-encoding (fast)
            cmd = [
                self.ffmpeg_path,
                '-i', str(avi_file),
                '-c', 'copy',  # Copy all streams without re-encoding
                '-y',  # Overwrite output file if exists
                str(output_file)
            ]

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            print(f"✅ Конвертировано: {output_file.name}")
            return output_file

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка ffmpeg при конвертации {avi_file.name}")
            print(f"   {e.stderr}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return None
