"""
Media Validator
Валидация медиафайлов с помощью MediaInfo
"""

from pathlib import Path
from typing import List
from pymediainfo import MediaInfo
from models.data_models import MediaValidationResult


class MediaValidator:
    """Валидатор медиафайлов"""

    def validate_file(self, file_path: Path) -> MediaValidationResult:
        """
        Валидирует медиафайл с помощью MediaInfo

        Args:
            file_path: Путь к файлу

        Returns:
            MediaValidationResult с результатами валидации
        """
        result = MediaValidationResult(file_path=file_path, is_valid=False)

        try:
            # Получаем размер файла
            result.file_size_mb = file_path.stat().st_size / (1024 * 1024)

            # Анализируем с помощью MediaInfo
            media_info = MediaInfo.parse(str(file_path))

            # Собираем информацию о треках
            for track in media_info.tracks:
                if track.track_type == 'General':
                    if track.duration:
                        result.duration = track.duration / 1000  # конвертируем из мс в секунды

                elif track.track_type == 'Video':
                    result.video_tracks += 1
                    if not result.video_codec:
                        result.video_codec = track.codec_id or track.format
                    if track.width and track.height:
                        result.resolution = f"{track.width}x{track.height}"

                elif track.track_type == 'Audio':
                    result.audio_tracks += 1
                    codec = track.codec_id or track.format
                    if codec and codec not in result.audio_codecs:
                        result.audio_codecs.append(codec)

                elif track.track_type == 'Text':
                    result.subtitle_tracks += 1

            # Валидация
            if result.video_tracks == 0:
                result.errors.append("Нет видеодорожки")
            elif result.video_tracks > 1:
                result.warnings.append(f"Несколько видеодорожек: {result.video_tracks}")

            if result.audio_tracks == 0:
                result.warnings.append("Нет аудиодорожек")

            if not result.duration or result.duration < 60:
                result.errors.append(f"Слишком короткое видео: {result.duration:.1f}s")

            # Файл считается валидным если нет критичных ошибок
            result.is_valid = len(result.errors) == 0

        except Exception as e:
            result.errors.append(f"Ошибка анализа: {str(e)}")
            result.is_valid = False

        return result

    def print_validation_result(self, validation: MediaValidationResult):
        """Выводит результат валидации в читаемом виде"""
        status = "✅" if validation.is_valid else "❌"
        print(f"\n{status} {validation.file_path.name}")
        print(f"   Размер: {validation.file_size_mb:.1f} MB")

        if validation.duration:
            minutes = int(validation.duration // 60)
            seconds = int(validation.duration % 60)
            print(f"   Длительность: {minutes}m {seconds}s")

        print(f"   Видео: {validation.video_tracks} трек(ов)", end="")
        if validation.video_codec:
            print(f" [{validation.video_codec}]", end="")
        if validation.resolution:
            print(f" {validation.resolution}", end="")
        print()

        print(f"   Аудио: {validation.audio_tracks} трек(ов)", end="")
        if validation.audio_codecs:
            print(f" [{', '.join(validation.audio_codecs)}]", end="")
        print()

        print(f"   Субтитры: {validation.subtitle_tracks} трек(ов)")

        if validation.errors:
            for error in validation.errors:
                print(f"   ❌ {error}")

        if validation.warnings:
            for warning in validation.warnings:
                print(f"   ⚠️  {warning}")

    def validate_directory(self, output_path: Path) -> tuple[int, int]:
        """
        Валидирует все MKV файлы в директории

        Args:
            output_path: Путь к директории с файлами

        Returns:
            Tuple (valid_count, invalid_count)
        """
        print("\n" + "="*60)
        print("🔍 ВАЛИДАЦИЯ ВЫХОДНЫХ ФАЙЛОВ")
        print("="*60)

        mkv_files = sorted(output_path.glob("*.mkv"))

        if not mkv_files:
            print("⚠️  MKV файлы не найдены")
            return 0, 0

        valid_count = 0
        invalid_count = 0

        for mkv_file in mkv_files:
            validation = self.validate_file(mkv_file)
            self.print_validation_result(validation)

            if validation.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        print("\n" + "="*60)
        print(f"📊 Результаты валидации:")
        print(f"   ✅ Валидных: {valid_count}")
        print(f"   ❌ С ошибками: {invalid_count}")
        print(f"   📁 Всего файлов: {len(mkv_files)}")
        print("="*60)

        return valid_count, invalid_count
