"""
Preprocessor Coordinator
Coordinates all preprocessing operations: AVI→MKV, EAC3→AAC, track embedding
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from models.data_models import MediaFile, PreprocessingResult
from processors.avi_converter import AVIConverter
from processors.audio_converter import AudioConverter
from processors.track_embedder import TrackEmbedder

logger = logging.getLogger(__name__)


class Preprocessor:
    """Preprocessing operations coordinator"""

    def __init__(self, work_dir: Path):
        """
        Args:
            work_dir: Working directory for temporary files
        """
        self.work_dir = work_dir
        self.temp_dir = work_dir / ".preprocessing_temp"
        self.temp_dir.mkdir(exist_ok=True)

        self.avi_converter = AVIConverter()
        self.audio_converter = AudioConverter()
        self.track_embedder = TrackEmbedder()

    def preprocess_episode(
        self,
        episode_num: int,
        video: MediaFile,
        audio_tracks: List[MediaFile],
        subtitles: List[MediaFile]
    ) -> Optional[PreprocessingResult]:
        """
        Performs preprocessing for one episode

        Args:
            episode_num: Episode number
            video: Video file
            audio_tracks: External audio tracks
            subtitles: External subtitles

        Returns:
            PreprocessingResult or None if preprocessing is not needed
        """
        if not video:
            return None

        result = PreprocessingResult(
            file_path=video.path,
            operations_applied=[],
            success=True,
            audio_tracks_count=len(audio_tracks),
            subtitle_tracks_count=len(subtitles)
        )

        current_file = video.path
        print(f"\n🔄 Preprocessing эпизода {episode_num}: {video.filename}")
        logger.info(f"=== Preprocessing эпизода {episode_num} ===")
        logger.info(f"Исходный файл: {video.path}")
        logger.info(f"Внешних аудио: {len(audio_tracks)}, субтитров: {len(subtitles)}")

        # 1. AVI → MKV conversion
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

        # 2. EAC3 detection and conversion
        if current_file.suffix.lower() == '.mkv':
            print("   ├─ Проверка EAC3 аудио...")
            eac3_result = self.audio_converter.process_file(current_file, self.temp_dir)

            if eac3_result:
                current_file = eac3_result
                result.eac3_converted = True
                result.operations_applied.append("EAC3→AAC")

        # 3. Embed external tracks
        if audio_tracks or subtitles:
            print("   └─ Встраивание внешних треков...")
            logger.info(f"Встраивание треков: {len(audio_tracks)} аудио, {len(subtitles)} субтитров")
            for aud in audio_tracks:
                logger.debug(f"  Аудио: {aud.path}")
            for sub in subtitles:
                logger.debug(f"  Субтитры: {sub.path} (трек: {sub.subtitle_track})")

            temp_embedded = self.temp_dir / f"ep{episode_num:02d}_embedded.mkv"
            logger.info(f"Выходной файл встраивания: {temp_embedded}")

            embedded = self.track_embedder.embed_tracks(
                current_file,
                audio_tracks,
                subtitles,
                temp_embedded
            )

            if embedded:
                logger.info(f"Треки встроены успешно: {embedded}")
                current_file = embedded
                result.tracks_embedded = True
                result.operations_applied.append("Embed tracks")
            else:
                logger.error("Не удалось встроить треки")
                result.success = False
                result.error_message = "Failed to embed tracks"
                return result

        # Update file path
        result.file_path = current_file
        logger.info(f"Финальный файл preprocessing: {current_file}")

        if result.operations_applied:
            print(f"✅ Preprocessing завершён: {', '.join(result.operations_applied)}")
            logger.info(f"Операции: {', '.join(result.operations_applied)}")
        else:
            print(f"ℹ️  Preprocessing не требовался")
            logger.info("Preprocessing не требовался")

        return result

    def preprocess_all_episodes(
        self,
        episode_map: Dict[int, Dict]
    ) -> Dict[int, PreprocessingResult]:
        """
        Performs preprocessing for all episodes

        Args:
            episode_map: Dictionary {episode_num: {'video': MediaFile, 'audio': [...], 'subtitles': [...]}}

        Returns:
            Dictionary {episode_num: PreprocessingResult}
        """
        if not episode_map:
            return {}

        print("\n" + "="*60)
        print("🔄 PREPROCESSING")
        print("="*60)

        results = {}
        operations_count = 0

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
                if result.operations_applied:
                    operations_count += 1

                # Update episode_map with new file path
                if result.success and result.file_path != ep_data['video'].path:
                    ep_data['video'].path = result.file_path
                    ep_data['video'].filename = result.file_path.name

                    # Clear external tracks if they were embedded
                    if result.tracks_embedded:
                        ep_data['audio'] = []
                        ep_data['subtitles'] = []

        print("\n" + "="*60)
        print(f"📊 Preprocessing завершён: {operations_count} эпизодов обработано")
        print("="*60)

        return results

    def cleanup(self):
        """Cleans up temporary files"""
        if self.temp_dir.exists():
            import shutil

            # Use ignore_errors to handle macOS metadata files (._*)
            def onerror(func, path, exc_info):
                """Error handler for shutil.rmtree - ignore macOS metadata file errors"""
                import os
                # Try to remove read-only flag and retry
                if os.path.exists(path):
                    os.chmod(path, 0o777)
                    try:
                        func(path)
                    except:
                        # Ignore errors for ._ files
                        if not os.path.basename(path).startswith('._'):
                            print(f"⚠️  Не удалось удалить: {path}")

            shutil.rmtree(self.temp_dir, onerror=onerror)
            print(f"🧹 Временные файлы очищены")
