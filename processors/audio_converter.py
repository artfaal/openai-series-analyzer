"""
EAC3 Audio Converter
Обнаруживает и конвертирует EAC3 (E-AC-3) аудиотреки в AAC используя ffmpeg
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from pymediainfo import MediaInfo


class AudioConverter:
    """Конвертер EAC3 аудио в AAC"""

    def __init__(self):
        self.ffmpeg_path = 'ffmpeg'
        self.mkvmerge_path = 'mkvmerge'

    def detect_eac3_tracks(self, mkv_file: Path) -> List[int]:
        """
        Определяет индексы EAC3 аудиотреков в MKV файле

        Args:
            mkv_file: Путь к MKV файлу

        Returns:
            List индексов треков с EAC3 кодеком
        """
        eac3_tracks = []

        try:
            media_info = MediaInfo.parse(str(mkv_file))

            for track in media_info.tracks:
                if track.track_type == 'Audio':
                    codec = (track.codec_id or track.format or '').upper()
                    # EAC3 может быть представлен как: E-AC-3, EAC3, A_EAC3
                    if 'EAC3' in codec or 'E-AC-3' in codec or 'A_EAC3' in codec:
                        # track_id в MediaInfo начинается с 1, нам нужен 0-based index
                        track_index = track.track_id - 1 if track.track_id else 0
                        eac3_tracks.append(track_index)

        except Exception as e:
            print(f"⚠️  Ошибка при анализе {mkv_file.name}: {e}")

        return eac3_tracks

    def extract_audio_track(self, mkv_file: Path, track_index: int, output_file: Path) -> bool:
        """
        Извлекает аудиотрек из MKV

        Args:
            mkv_file: Путь к MKV файлу
            track_index: Индекс трека для извлечения
            output_file: Путь для сохранения извлечённого трека

        Returns:
            True если успешно, False при ошибке
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
        Конвертирует аудио в AAC

        Args:
            input_audio: Путь к входному аудиофайлу
            output_audio: Путь для выходного AAC файла

        Returns:
            True если успешно, False при ошибке
        """
        try:
            # ffmpeg -i input.eac3 -c:a aac -b:a 192k output.aac
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_audio),
                '-c:a', 'aac',
                '-b:a', '192k',  # битрейт 192 kbps
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
        Заменяет аудиотрек в MKV файле

        Args:
            mkv_file: Исходный MKV файл
            track_index: Индекс трека для замены
            new_audio: Новый аудиофайл (AAC)
            output_mkv: Выходной MKV файл

        Returns:
            True если успешно, False при ошибке
        """
        try:
            # mkvmerge -o output.mkv input.mkv --audio-tracks !track_index new_audio.aac
            # Удаляем старый трек и добавляем новый
            cmd = [
                self.mkvmerge_path,
                '-o', str(output_mkv),
                '--audio-tracks', f'!{track_index}',  # Исключаем старый трек
                str(mkv_file),
                str(new_audio)  # Добавляем новый трек
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка замены трека в MKV: {e.stderr}")
            return False

    def process_file(self, mkv_file: Path, temp_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Полный цикл обработки: обнаружение EAC3, конвертация, замена

        Args:
            mkv_file: Путь к MKV файлу
            temp_dir: Директория для временных файлов (если None, используется parent файла)

        Returns:
            Path к обработанному файлу или None если обработка не требовалась/неудачна
        """
        eac3_tracks = self.detect_eac3_tracks(mkv_file)

        if not eac3_tracks:
            return None  # Нет EAC3 треков, обработка не нужна

        print(f"\n🔊 Обнаружено EAC3 треков: {len(eac3_tracks)} в {mkv_file.name}")

        if temp_dir is None:
            temp_dir = mkv_file.parent

        # Обрабатываем только первый EAC3 трек для упрощения
        # TODO: в будущем можно обрабатывать все треки
        track_index = eac3_tracks[0]
        print(f"   Конвертация трека #{track_index}...")

        # Временные файлы
        temp_eac3 = temp_dir / f"{mkv_file.stem}_temp.eac3"
        temp_aac = temp_dir / f"{mkv_file.stem}_temp.aac"
        output_mkv = temp_dir / f"{mkv_file.stem}_converted.mkv"

        try:
            # 1. Извлекаем EAC3 трек
            if not self.extract_audio_track(mkv_file, track_index, temp_eac3):
                return None

            # 2. Конвертируем в AAC
            if not self.convert_to_aac(temp_eac3, temp_aac):
                return None

            # 3. Заменяем трек в MKV
            if not self.replace_audio_in_mkv(mkv_file, track_index, temp_aac, output_mkv):
                return None

            print(f"✅ EAC3 → AAC конвертация завершена: {output_mkv.name}")
            return output_mkv

        finally:
            # Очистка временных файлов
            for temp_file in [temp_eac3, temp_aac]:
                if temp_file.exists():
                    temp_file.unlink()
