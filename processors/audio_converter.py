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
            List of track indexes with EAC3 codec
        """
        eac3_tracks = []

        try:
            media_info = MediaInfo.parse(str(mkv_file))

            for track in media_info.tracks:
                if track.track_type == 'Audio':
                    codec = (track.codec_id or track.format or '').upper()
                    # EAC3 can be represented as: E-AC-3, EAC3, A_EAC3
                    if 'EAC3' in codec or 'E-AC-3' in codec or 'A_EAC3' in codec:
                        # track_id in MediaInfo starts from 1, we need 0-based index
                        track_index = track.track_id - 1 if track.track_id else 0
                        eac3_tracks.append(track_index)

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
            track_index: Track index to replace
            new_audio: New audio file (AAC)
            output_mkv: Output MKV file

        Returns:
            True if successful, False on error
        """
        try:
            # mkvmerge -o output.mkv input.mkv --audio-tracks !track_index new_audio.aac
            # Remove old track and add new one
            cmd = [
                self.mkvmerge_path,
                '-o', str(output_mkv),
                '--audio-tracks', f'!{track_index}',  # Exclude old track
                str(mkv_file),
                str(new_audio)  # Add new track
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка замены трека в MKV: {e.stderr}")
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

        # Process only the first EAC3 track for simplicity
        # TODO: in the future, can process all tracks
        track_index = eac3_tracks[0]
        print(f"   Конвертация трека #{track_index}...")

        # Temporary files
        temp_eac3 = temp_dir / f"{mkv_file.stem}_temp.eac3"
        temp_aac = temp_dir / f"{mkv_file.stem}_temp.aac"
        output_mkv = temp_dir / f"{mkv_file.stem}_converted.mkv"

        try:
            # 1. Extract EAC3 track
            if not self.extract_audio_track(mkv_file, track_index, temp_eac3):
                return None

            # 2. Convert to AAC
            if not self.convert_to_aac(temp_eac3, temp_aac):
                return None

            # 3. Replace track in MKV
            if not self.replace_audio_in_mkv(mkv_file, track_index, temp_aac, output_mkv):
                return None

            print(f"✅ EAC3 → AAC конвертация завершена: {output_mkv.name}")
            return output_mkv

        finally:
            # Cleanup temporary files
            for temp_file in [temp_eac3, temp_aac]:
                if temp_file.exists():
                    temp_file.unlink()
