"""
Preprocessor Coordinator
Координирует все preprocessing операции: AVI→MKV, EAC3→AAC, встраивание треков
"""

from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from models.data_models import MediaFile, PreprocessingResult
from processors.avi_converter import AVIConverter
from processors.audio_converter import AudioConverter
from processors.track_embedder import TrackEmbedder


class Preprocessor:
    """Координатор preprocessing операций"""

    def __init__(self, work_dir: Path):
        """
        Args:
            work_dir: Рабочая директория для временных файлов
        """
        self.work_dir = work_dir
        self.temp_dir = work_dir / ".preprocessing_temp"
        self.temp_dir.mkdir(exist_ok=True)

        self.avi_converter = AVIConverter()
        self.audio_converter = AudioConverter()
        self.track_embedder = TrackEmbedder()

    def needs_preprocessing(self, files: List[MediaFile]) -> bool:
        """
        Проверяет, нужен ли preprocessing

        Args:
            files: Список файлов

        Returns:
            True если нужен preprocessing
        """
        # Проверяем наличие AVI файлов
        has_avi = any(f.file_type == 'video' and f.path.suffix.lower() == '.avi' for f in files)

        # Проверяем наличие внешних треков
        has_external_tracks = any(f.file_type in ['audio', 'subtitle'] for f in files)

        # TODO: Проверка EAC3 требует анализа MKV файлов

        return has_avi or has_external_tracks

    def preprocess_episode(
        self,
        episode_num: int,
        video: MediaFile,
        audio_tracks: List[MediaFile],
        subtitles: List[MediaFile]
    ) -> Optional[PreprocessingResult]:
        """
        Выполняет preprocessing для одного эпизода

        Args:
            episode_num: Номер эпизода
            video: Видеофайл
            audio_tracks: Внешние аудиотреки
            subtitles: Внешние субтитры

        Returns:
            PreprocessingResult или None если preprocessing не нужен
        """
        if not video:
            return None

        result = PreprocessingResult(
            file_path=video.path,
            operations_applied=[],
            success=True
        )

        current_file = video.path
        print(f"\n🔄 Preprocessing эпизода {episode_num}: {video.filename}")

        # 1. Конвертация AVI → MKV
        if self.avi_converter.needs_conversion(current_file):
            print("   ├─ AVI → MKV конвертация...")
            temp_mkv = self.temp_dir / f"ep{episode_num:02d}_from_avi.mkv"
            converted = self.avi_converter.convert(current_file, temp_mkv)

            if converted:
                current_file = converted
                result.avi_converted = True
                result.operations_applied.append("AVI→MKV")
            else:
                result.success = False
                result.error_message = "Failed to convert AVI"
                return result

        # 2. Обнаружение и конвертация EAC3
        if current_file.suffix.lower() == '.mkv':
            print("   ├─ Проверка EAC3 аудио...")
            eac3_result = self.audio_converter.process_file(current_file, self.temp_dir)

            if eac3_result:
                current_file = eac3_result
                result.eac3_converted = True
                result.operations_applied.append("EAC3→AAC")

        # 3. Встраивание внешних треков
        if audio_tracks or subtitles:
            print("   └─ Встраивание внешних треков...")
            temp_embedded = self.temp_dir / f"ep{episode_num:02d}_embedded.mkv"
            embedded = self.track_embedder.embed_tracks(
                current_file,
                audio_tracks,
                subtitles,
                temp_embedded
            )

            if embedded:
                current_file = embedded
                result.tracks_embedded = True
                result.operations_applied.append("Embed tracks")
            else:
                result.success = False
                result.error_message = "Failed to embed tracks"
                return result

        # Обновляем путь к файлу
        result.file_path = current_file

        if result.operations_applied:
            print(f"✅ Preprocessing завершён: {', '.join(result.operations_applied)}")
        else:
            print(f"ℹ️  Preprocessing не требовался")

        return result

    def preprocess_all_episodes(
        self,
        episode_map: Dict[int, Dict]
    ) -> Dict[int, PreprocessingResult]:
        """
        Выполняет preprocessing для всех эпизодов

        Args:
            episode_map: Словарь {episode_num: {'video': MediaFile, 'audio': [...], 'subtitles': [...]}}

        Returns:
            Словарь {episode_num: PreprocessingResult}
        """
        print("\n" + "="*60)
        print("🔄 PREPROCESSING")
        print("="*60)

        results = {}

        for ep_num in sorted(episode_map.keys()):
            ep_data = episode_map[ep_num]

            result = self.preprocess_episode(
                ep_num,
                ep_data.get('video'),
                ep_data.get('audio', []),
                ep_data.get('subtitles', [])
            )

            if result:
                results[ep_num] = result

                # Обновляем episode_map с новым путём к файлу
                if result.success and result.file_path != ep_data['video'].path:
                    ep_data['video'].path = result.file_path
                    ep_data['video'].filename = result.file_path.name

                    # Очищаем внешние треки если они были встроены
                    if result.tracks_embedded:
                        ep_data['audio'] = []
                        ep_data['subtitles'] = []

        print("\n" + "="*60)
        print(f"📊 Preprocessing завершён: {len(results)} эпизодов обработано")
        print("="*60)

        return results

    def cleanup(self):
        """Очищает временные файлы"""
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Временные файлы очищены")
