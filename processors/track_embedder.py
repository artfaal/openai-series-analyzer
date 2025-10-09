"""
Track Embedder
Embeds external audio and subtitles into MKV container
"""

import subprocess
from pathlib import Path
from typing import List, Optional
from models.data_models import MediaFile


class TrackEmbedder:
    """Embeds external tracks (audio, subtitles) into MKV"""

    def __init__(self):
        self.mkvmerge_path = 'mkvmerge'

    def has_external_tracks(
        self,
        audio_files: List[MediaFile],
        subtitle_files: List[MediaFile]
    ) -> bool:
        """
        Checks for external tracks

        Args:
            audio_files: List of external audio files
            subtitle_files: List of external subtitles

        Returns:
            True if external tracks exist
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
        Embeds external tracks into MKV file

        Args:
            mkv_file: Source MKV file
            audio_files: List of external audio files to embed
            subtitle_files: List of subtitles to embed
            output_file: Output file (if None, replaces original)

        Returns:
            Path to resulting file or None on error
        """
        if not self.has_external_tracks(audio_files, subtitle_files):
            return mkv_file  # Nothing to embed

        if output_file is None:
            output_file = mkv_file.parent / f"{mkv_file.stem}_embedded.mkv"

        print(f"\n📦 Встраивание внешних треков в {mkv_file.name}")
        print(f"   Аудио: {len(audio_files)}, Субтитры: {len(subtitle_files)}")

        try:
            # Build mkvmerge command
            cmd = [
                self.mkvmerge_path,
                '-o', str(output_file),
                str(mkv_file)
            ]

            # Add audio tracks
            for audio in audio_files:
                cmd.append(str(audio.path))
                print(f"   + Аудио: {audio.filename}")

            # Add subtitles with metadata
            for sub in subtitle_files:
                # Set language and track name
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
