"""
AVI → MKV Converter
Конвертирует .avi файлы в .mkv контейнер используя ffmpeg (remux без перекодирования)
"""

import subprocess
from pathlib import Path
from typing import Optional


class AVIConverter:
    """Конвертер AVI файлов в MKV"""

    def __init__(self):
        self.ffmpeg_path = 'ffmpeg'

    def needs_conversion(self, file_path: Path) -> bool:
        """
        Проверяет, нужна ли конвертация файла

        Args:
            file_path: Путь к файлу

        Returns:
            True если файл .avi, иначе False
        """
        return file_path.suffix.lower() == '.avi'

    def convert(self, avi_file: Path, output_file: Optional[Path] = None) -> Optional[Path]:
        """
        Конвертирует AVI в MKV (remux без перекодирования)

        Args:
            avi_file: Путь к .avi файлу
            output_file: Путь для выходного файла (если None, создаётся рядом с оригиналом)

        Returns:
            Path к созданному MKV файлу или None при ошибке
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
            # -c copy = копирование потоков без перекодирования (быстро)
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
