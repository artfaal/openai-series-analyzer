"""
MKV Merger
Объединяет видео, аудио и субтитры в финальный MKV файл
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from models.data_models import MediaFile


class MKVMerger:
    """Объединяет медиафайлы в MKV контейнер"""

    def __init__(self):
        self.mkvmerge_path = 'mkvmerge'

    def merge_episode(
        self,
        video: MediaFile,
        audio_tracks: List[MediaFile],
        subtitles: List[MediaFile],
        output_file: Path
    ) -> bool:
        """
        Объединяет видео, аудио и субтитры в один MKV

        Args:
            video: Видеофайл
            audio_tracks: Список аудиотреков
            subtitles: Список субтитров
            output_file: Путь для выходного файла

        Returns:
            True если успешно, False при ошибке
        """
        if not video:
            print(f"⚠️  Видео не найдено")
            return False

        print(f"\n🔧 Обработка эпизода:")
        print(f"   Видео: {video.filename}")
        print(f"   Аудио: {len(audio_tracks)} треков")
        print(f"   Субтитры: {len(subtitles)} треков")

        # Формируем команду mkvmerge
        cmd = [self.mkvmerge_path, '-o', str(output_file)]

        # Добавляем видео
        cmd.extend([str(video.path)])

        # Добавляем аудио дорожки
        for audio in audio_tracks:
            cmd.extend([str(audio.path)])

        # Добавляем субтитры с правильными названиями треков
        for sub in subtitles:
            track_name = sub.subtitle_track or "Russian"
            cmd.extend([
                '--language', '0:rus',
                '--track-name', f'0:{track_name}',
                str(sub.path)
            ])

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            print(f"✅ Создан: {output_file.name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка mkvmerge: {e.stderr}")
            return False
