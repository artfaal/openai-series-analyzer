"""
EAC3 Audio Converter
Detects and converts EAC3 (E-AC-3) audio tracks to AAC using ffmpeg
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from pymediainfo import MediaInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AudioConverter:
    """EAC3 to AAC audio converter"""

    def __init__(self):
        self.ffmpeg_path = 'ffmpeg'
        self.mkvmerge_path = 'mkvmerge'
        self.aac_bitrate = os.getenv('AAC_BITRATE', '192k')

    def detect_eac3_tracks(self, mkv_file: Path) -> List[int]:
        """
        Detects EAC3 audio track indexes in MKV file

        Args:
            mkv_file: Path to MKV file

        Returns:
            List of audio track indexes (0-based, relative to audio tracks only)
        """
        eac3_tracks = []

        try:
            media_info = MediaInfo.parse(str(mkv_file))

            # Count only audio tracks to get proper index for ffmpeg (0:a:N)
            audio_track_index = 0
            for track in media_info.tracks:
                if track.track_type == 'Audio':
                    codec = (track.codec_id or track.format or '').upper()
                    # EAC3 can be represented as: E-AC-3, EAC3, A_EAC3
                    if 'EAC3' in codec or 'E-AC-3' in codec or 'A_EAC3' in codec:
                        eac3_tracks.append(audio_track_index)
                    audio_track_index += 1

        except Exception as e:
            print(f"⚠️  Ошибка при анализе {mkv_file.name}: {e}")

        return eac3_tracks

    def extract_audio_track(self, mkv_file: Path, track_index: int, output_file: Path) -> bool:
        """
        Extracts audio track from MKV

        Args:
            mkv_file: Path to MKV file
            track_index: Track index to extract
            output_file: Path to save extracted track

        Returns:
            True if successful, False on error
        """
        try:
            # ffmpeg -i input.mkv -map 0:a:0 -c copy output.eac3
            cmd = [
                self.ffmpeg_path,
                '-i', str(mkv_file),
                '-map', f'0:a:{track_index}',
                '-c', 'copy',
                '-y',
                str(output_file)
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка извлечения трека: {e.stderr}")
            return False

    def convert_to_aac(self, input_audio: Path, output_audio: Path) -> bool:
        """
        Converts audio to AAC

        Args:
            input_audio: Path to input audio file
            output_audio: Path for output AAC file

        Returns:
            True if successful, False on error
        """
        try:
            # ffmpeg -i input.eac3 -c:a aac -b:a 192k output.aac
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_audio),
                '-c:a', 'aac',
                '-b:a', self.aac_bitrate,
                '-y',
                str(output_audio)
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка конвертации в AAC: {e.stderr}")
            return False

    def replace_audio_in_mkv(
        self,
        mkv_file: Path,
        track_index: int,
        new_audio: Path,
        output_mkv: Path
    ) -> bool:
        """
        Replaces audio track in MKV file

        Args:
            mkv_file: Source MKV file
            track_index: Audio track index (0-based, relative to audio tracks)
            new_audio: New audio file (AAC)
            output_mkv: Output MKV file

        Returns:
            True if successful, False on error
        """
        try:
            # Get total number of audio tracks to build proper track selection
            media_info = MediaInfo.parse(str(mkv_file))
            audio_count = sum(1 for t in media_info.tracks if t.track_type == 'Audio')

            # Build list of audio tracks to keep (all except the one we're replacing)
            audio_tracks_to_keep = [str(i) for i in range(audio_count) if i != track_index]
            audio_selection = ','.join(audio_tracks_to_keep) if audio_tracks_to_keep else ''

            # mkvmerge -o output.mkv --audio-tracks 1,2 input.mkv new_audio.aac
            # Keep specified audio tracks and add new one
            cmd = [
                self.mkvmerge_path,
                '-o', str(output_mkv),
            ]

            if audio_selection:
                cmd.extend(['--audio-tracks', audio_selection])
            else:
                # If no tracks to keep, exclude all audio
                cmd.extend(['--no-audio'])

            cmd.append(str(mkv_file))
            cmd.append(str(new_audio))  # Add new track

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка замены трека в MKV: {e.stderr}")
            return False

    def convert_all_eac3_ffmpeg(self, mkv_file: Path, output_mkv: Path) -> bool:
        """
        Converts all EAC3 tracks to AAC in one pass using ffmpeg

        Args:
            mkv_file: Input MKV file
            output_mkv: Output MKV file

        Returns:
            True if successful, False on error
        """
        try:
            # Build ffmpeg command that converts all EAC3 audio to AAC
            # -c copy: copy all streams by default
            # -c:a:N aac -b:a:N 192k: for each audio track, if EAC3, convert to AAC
            cmd = [
                self.ffmpeg_path,
                '-i', str(mkv_file),
                '-map', '0',  # Copy all streams
                '-c', 'copy',  # Copy by default
                '-c:a', 'aac',  # Convert all audio to AAC
                '-b:a', self.aac_bitrate,  # AAC bitrate
                '-y',
                str(output_mkv)
            ]

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка конвертации через ffmpeg: {e.stderr}")
            return False

    def process_file(self, mkv_file: Path, temp_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Full processing cycle: EAC3 detection, conversion, replacement

        Args:
            mkv_file: Path to MKV file
            temp_dir: Directory for temporary files (if None, uses file's parent)

        Returns:
            Path to processed file or None if processing was not needed/unsuccessful
        """
        eac3_tracks = self.detect_eac3_tracks(mkv_file)

        if not eac3_tracks:
            return None  # No EAC3 tracks, processing not needed

        print(f"\n🔊 Обнаружено EAC3 треков: {len(eac3_tracks)} в {mkv_file.name}")

        if temp_dir is None:
            temp_dir = mkv_file.parent

        output_mkv = temp_dir / f"{mkv_file.stem}_converted.mkv"

        print(f"   Конвертация всех EAC3 треков в AAC...")

        # Convert all EAC3 to AAC in one pass using ffmpeg
        if not self.convert_all_eac3_ffmpeg(mkv_file, output_mkv):
            return None

        print(f"✅ EAC3 → AAC конвертация завершена: {len(eac3_tracks)} треков обработано")
        return output_mkv
