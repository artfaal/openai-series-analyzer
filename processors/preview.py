"""
Preview Generator
Creates detailed preview report before processing
"""

from typing import Dict, List
from collections import defaultdict
from models.data_models import MediaFile
from utils.filename_normalizer import normalize_series_title


class PreviewGenerator:
    """Generates preview report before processing"""

    def generate_preview(self, episode_map: Dict[int, Dict], series_info: Dict, preprocessing_results: Dict = None) -> str:
        """
        Generates detailed preview report

        Args:
            episode_map: Dictionary {episode_num: {'video': MediaFile, 'audio': [...], 'subtitles': [...]}}
            series_info: Series information dict
            preprocessing_results: Optional dict of preprocessing results {episode_num: PreprocessingResult}

        Returns:
            str: Formatted preview report
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("📋 ДЕТАЛЬНЫЙ ПЛАН ОБРАБОТКИ")
        lines.append("=" * 60)

        # Series info
        lines.append(f"\n📺 Сериал: {series_info.get('title', 'Unknown')}")
        lines.append(f"   Год: {series_info.get('year', 'не определён')}")
        lines.append(f"   Сезон: {series_info.get('season', '?')}")
        lines.append(f"   Эпизодов: {len(episode_map)}")

        # Statistics - use preprocessing results if available
        total_videos = sum(1 for ep in episode_map.values() if ep.get('video'))

        if preprocessing_results:
            # Use counts from preprocessing (before embedding)
            total_audio = sum(r.audio_tracks_count for r in preprocessing_results.values())
            total_subs = sum(r.subtitle_tracks_count for r in preprocessing_results.values())
        else:
            # Use current counts from episode_map
            total_audio = sum(len(ep.get('audio', [])) for ep in episode_map.values())
            total_subs = sum(len(ep.get('subtitles', [])) for ep in episode_map.values())

        lines.append(f"\n📊 Статистика файлов:")
        lines.append(f"   • Видео: {total_videos}")
        lines.append(f"   • Аудио дорожек: {total_audio}")
        lines.append(f"   • Субтитров: {total_subs}")

        # Preprocessing analysis
        needs_avi = False
        needs_eac3 = False
        needs_embedding = False

        for ep_data in episode_map.values():
            video = ep_data.get('video')
            if video and video.path.suffix.lower() == '.avi':
                needs_avi = True
            if ep_data.get('audio') or ep_data.get('subtitles'):
                needs_embedding = True

        lines.append(f"\n🔄 Preprocessing:")
        if needs_avi:
            lines.append(f"   ✅ AVI → MKV конвертация требуется")
        else:
            lines.append(f"   ⊘ AVI файлов не найдено")

        lines.append(f"   ⚠️  EAC3 проверка (будет выполнена во время обработки)")

        if needs_embedding:
            lines.append(f"   ✅ Встраивание треков требуется ({total_audio} аудио, {total_subs} субтитров)")
        else:
            lines.append(f"   ⊘ Внешних треков не найдено")

        # Subtitle analysis
        if total_subs > 0:
            subtitle_tracks = defaultdict(int)
            subtitle_languages = defaultdict(int)

            for ep_data in episode_map.values():
                for sub in ep_data.get('subtitles', []):
                    if sub.subtitle_track:
                        subtitle_tracks[sub.subtitle_track] += 1
                    if sub.language:
                        lang_name = sub.language if isinstance(sub.language, str) else 'Unknown'
                        subtitle_languages[lang_name] += 1

            lines.append(f"\n📝 Субтитры по студиям:")
            for track, count in sorted(subtitle_tracks.items()):
                lines.append(f"   • {track}: {count} файлов")

            if subtitle_languages:
                lines.append(f"\n🌐 Субтитры по языкам:")
                for lang, count in sorted(subtitle_languages.items()):
                    lines.append(f"   • {lang}: {count} файлов")

        # Sample episodes
        lines.append(f"\n📂 Примеры эпизодов:")
        sample_episodes = sorted(episode_map.keys())[:3]

        for ep_num in sample_episodes:
            ep_data = episode_map[ep_num]
            video = ep_data.get('video')
            audio = ep_data.get('audio', [])
            subs = ep_data.get('subtitles', [])

            lines.append(f"\n   Эпизод {ep_num}:")
            if video:
                lines.append(f"      Видео: {video.filename}")
            if audio:
                lines.append(f"      Аудио: {len(audio)} дорожек")
            if subs:
                sub_info = []
                for sub in subs:
                    track = sub.subtitle_track or '?'
                    lang = f" ({sub.language})" if sub.language else ""
                    sub_info.append(f"{track}{lang}")
                lines.append(f"      Субтитры: {', '.join(sub_info)}")

        if len(episode_map) > 3:
            lines.append(f"   ... и ещё {len(episode_map) - 3} эпизодов")

        # Final output structure
        lines.append(f"\n📁 Итоговая структура:")
        series_title = series_info.get('title', 'Unknown')
        normalized_title = normalize_series_title(series_title)
        year = series_info.get('year')
        season = series_info.get('season', 1)

        if year:
            lines.append(f"   {normalized_title} ({year})/")
        else:
            lines.append(f"   {normalized_title}/")

        lines.append(f"   └── Season {season:02d}/")
        lines.append(f"       ├── {normalized_title} - S{season:02d}E01.mkv")
        if len(episode_map) > 1:
            lines.append(f"       ├── {normalized_title} - S{season:02d}E02.mkv")
        if len(episode_map) > 2:
            lines.append(f"       ├── ...")
            lines.append(f"       └── {normalized_title} - S{season:02d}E{len(episode_map):02d}.mkv")

        lines.append("\n" + "=" * 60)

        return '\n'.join(lines)
