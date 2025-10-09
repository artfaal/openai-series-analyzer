"""
Track Embedder
Встраивает внешние аудио и субтитры в MKV контейнер
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from models.data_models import MediaFile


class TrackEmbedder:
    """Встраивает внешние треки (аудио, субтитры) в MKV"""

    def __init__(self):
        self.mkvmerge_path = 'mkvmerge'

    def has_external_tracks(
        self,
        audio_files: List[MediaFile],
        subtitle_files: List[MediaFile]
    ) -> bool:
        """
        Проверяет наличие внешних треков

        Args:
            audio_files: Список внешних аудиофайлов
            subtitle_files: Список внешних субтитров

        Returns:
            True если есть внешние треки
        """
        return len(audio_files) > 0 or len(subtitle_files) > 0

    def embed_tracks(
        self,
        mkv_file: Path,
        audio_files: List[MediaFile],
        subtitle_files: List[MediaFile],
        output_file: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Встраивает внешние треки в MKV файл

        Args:
            mkv_file: Исходный MKV файл
            audio_files: Список внешних аудиофайлов для встраивания
            subtitle_files: Список субтитров для встраивания
            output_file: Выходной файл (если None, заменяет оригинал)

        Returns:
            Path к результирующему файлу или None при ошибке
        """
        if not self.has_external_tracks(audio_files, subtitle_files):
            return mkv_file  # Нечего встраивать

        if output_file is None:
            output_file = mkv_file.parent / f"{mkv_file.stem}_embedded.mkv"

        print(f"\n📦 Встраивание внешних треков в {mkv_file.name}")
        print(f"   Аудио: {len(audio_files)}, Субтитры: {len(subtitle_files)}")

        try:
            # Формируем команду mkvmerge
            cmd = [
                self.mkvmerge_path,
                '-o', str(output_file),
                str(mkv_file)
            ]

            # Добавляем аудиотреки
            for audio in audio_files:
                cmd.append(str(audio.path))
                print(f"   + Аудио: {audio.filename}")

            # Добавляем субтитры с метаданными
            for sub in subtitle_files:
                # Устанавливаем язык и название трека
                track_name = sub.subtitle_track or "Russian"
                cmd.extend([
                    '--language', '0:rus',
                    '--track-name', f'0:{track_name}',
                    str(sub.path)
                ])
                print(f"   + Субтитры: {track_name}")

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            print(f"✅ Треки встроены: {output_file.name}")
            return output_file

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка mkvmerge при встраивании треков")
            print(f"   {e.stderr}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return None
