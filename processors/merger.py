"""
MKV Merger
Combines video, audio and subtitles into final MKV file
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from models.data_models import MediaFile

logger = logging.getLogger(__name__)


class MKVMerger:
    """Combines media files into MKV container"""

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
        Combines video, audio and subtitles into one MKV

        Args:
            video: Video file
            audio_tracks: List of audio tracks
            subtitles: List of subtitles
            output_file: Path for output file

        Returns:
            True if successful, False on error
        """
        logger.info(f"=== MKV Merger ===")
        logger.info(f"Выходной файл: {output_file}")

        if not video:
            print(f"⚠️  Видео не найдено")
            logger.error("Видео не найдено")
            return False

        logger.info(f"Видео: {video.path}")
        logger.info(f"Аудио треков: {len(audio_tracks)}")
        for idx, audio in enumerate(audio_tracks):
            logger.info(f"  Аудио {idx}: {audio.path}")
        logger.info(f"Субтитров: {len(subtitles)}")
        for idx, sub in enumerate(subtitles):
            logger.info(f"  Субтитры {idx}: {sub.path} (трек: {sub.subtitle_track})")

        print(f"\n🔧 Обработка эпизода:")
        print(f"   Видео: {video.filename}")
        print(f"   Аудио: {len(audio_tracks)} треков")
        print(f"   Субтитры: {len(subtitles)} треков")

        # Build mkvmerge command
        cmd = [self.mkvmerge_path, '-o', str(output_file)]

        # Add video
        cmd.extend([str(video.path)])

        # Add audio tracks
        for audio in audio_tracks:
            cmd.extend([str(audio.path)])

        # Add subtitles with proper track names
        for sub in subtitles:
            track_name = sub.subtitle_track or "Russian"
            cmd.extend([
                '--language', '0:rus',
                '--track-name', f'0:{track_name}',
                str(sub.path)
            ])

        logger.info(f"Команда mkvmerge: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            logger.info(f"mkvmerge stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"mkvmerge stderr: {result.stderr}")
            print(f"✅ Создан: {output_file.name}")
            logger.info(f"Успешно создан: {output_file}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка mkvmerge: {e.stderr}")
            logger.error(f"Ошибка mkvmerge при финальном объединении")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"Stderr: {e.stderr}")
            logger.error(f"Stdout: {e.stdout}")
            return False
