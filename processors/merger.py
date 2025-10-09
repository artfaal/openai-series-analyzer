"""
MKV Merger
Combines video, audio and subtitles into final MKV file
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from models.data_models import MediaFile


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
        if not video:
            print(f"⚠️  Видео не найдено")
            return False

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
