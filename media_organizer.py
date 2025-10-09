#!/usr/bin/env python3
"""
Media Organizer - автоматизация подготовки сериалов/аниме для Plex
Поддержка различных форматов релизов и структур директорий
"""

import os
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import openai
from dotenv import load_dotenv
from pymediainfo import MediaInfo

# Загрузка переменных окружения из .env
load_dotenv()

# Настройки
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

@dataclass
class MediaFile:
    """Класс для хранения информации о медиафайле"""
    path: Path
    filename: str
    file_type: str  # 'video', 'audio', 'subtitle', 'unknown'
    language: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    subtitle_track: Optional[str] = None  # Название трека субтитров (Анимевод, CR и т.д.)
    is_duplicate: bool = False

@dataclass
class SeriesInfo:
    """Информация о сериале"""
    title: str
    year: Optional[int]
    season: int
    total_episodes: int
    release_group: Optional[str] = None

@dataclass
class MediaValidationResult:
    """Результат валидации медиафайла"""
    file_path: Path
    is_valid: bool
    duration: Optional[float] = None  # в секундах
    video_tracks: int = 0
    audio_tracks: int = 0
    subtitle_tracks: int = 0
    video_codec: Optional[str] = None
    audio_codecs: List[str] = field(default_factory=list)
    resolution: Optional[str] = None
    file_size_mb: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class MediaOrganizer:
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.files: List[MediaFile] = []
        self.series_info: Optional[SeriesInfo] = None
        self.episode_map: Dict[int, Dict] = defaultdict(lambda: {
            'video': None,
            'audio': [],
            'subtitles': []
        })

    def extract_info_from_dirname(self) -> Dict:
        """Извлекает информацию из названия директории"""
        dirname = self.directory.name
        print(f"📂 Анализ названия директории: {dirname}")

        info = {
            'title': None,
            'season': None,
            'year': None,
            'release_group': None
        }

        # Паттерн: Название.S01.качество-ГРУППА
        pattern = r'^(.+?)\.S(\d+).*?-(\w+)$'
        match = re.match(pattern, dirname)

        if match:
            title = match.group(1).replace('.', ' ')
            info['title'] = title
            info['season'] = int(match.group(2))
            info['release_group'] = match.group(3)
            print(f"✅ Распознано: {title} (Сезон {info['season']}, Группа: {info['release_group']})")
        else:
            print(f"⚠️ Не удалось распознать паттерн директории")

        return info

    def extract_episode_info(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        """Извлекает номер сезона и эпизода из имени файла"""
        # Паттерн: S01E01 или s01e01
        pattern = r'[Ss](\d+)[Ee](\d+)'
        match = re.search(pattern, filename)

        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode

        return None, None

    def detect_subtitle_track(self, filename: str, parent_dir: str) -> Optional[str]:
        """Определяет тип субтитров (по названию или директории)"""
        # Из имени файла
        if 'Анимевод' in filename or 'анимевод' in filename.lower():
            return 'Анимевод'
        if 'CR' in filename or filename.endswith('.ru_CR.ass'):
            return 'Crunchyroll'

        # Из родительской директории
        if 'Анимевод' in parent_dir:
            return 'Анимевод'
        if 'CR' in parent_dir:
            return 'Crunchyroll'

        return None

    def scan_directory(self) -> List[MediaFile]:
        """Сканирует директорию и классифицирует файлы"""
        print(f"\n🔍 Сканирование директории: {self.directory}")

        media_extensions = {
            'video': ['.mkv', '.mp4', '.avi', '.m4v', '.ts'],
            'audio': ['.mka', '.aac', '.mp3', '.flac', '.ac3', '.dts'],
            'subtitle': ['.srt', '.ass', '.ssa', '.sub', '.sup']
        }

        files = []
        subtitle_hashes = {}  # Для обнаружения дубликатов

        for item in self.directory.rglob('*'):
            if item.is_file() and item.name != 'Комментарий.txt':
                ext = item.suffix.lower()

                # Определяем тип файла
                file_type = None
                for ftype, extensions in media_extensions.items():
                    if ext in extensions:
                        file_type = ftype
                        break

                if file_type:
                    season, episode = self.extract_episode_info(item.name)

                    media_file = MediaFile(
                        path=item,
                        filename=item.name,
                        file_type=file_type,
                        season_number=season,
                        episode_number=episode
                    )

                    # Для субтитров
                    if file_type == 'subtitle':
                        media_file.subtitle_track = self.detect_subtitle_track(
                            item.name,
                            item.parent.name
                        )

                        # Проверка на дубликаты субтитров
                        file_size = item.stat().st_size
                        hash_key = (episode, media_file.subtitle_track, file_size)

                        if hash_key in subtitle_hashes:
                            media_file.is_duplicate = True
                            print(f"🔄 Дубликат субтитров: {item.name}")
                        else:
                            subtitle_hashes[hash_key] = item

                    files.append(media_file)

        print(f"✅ Найдено файлов: {len(files)}")
        print(f"   - Видео: {sum(1 for f in files if f.file_type == 'video')}")
        print(f"   - Аудио: {sum(1 for f in files if f.file_type == 'audio')}")
        print(f"   - Субтитры: {sum(1 for f in files if f.file_type == 'subtitle')}")

        return files

    def analyze_with_ai(self, files: List[MediaFile], dir_info: Dict) -> Dict:
        """Анализирует файлы с помощью OpenAI API"""

        # Проверяем наличие API ключа
        if not OPENAI_API_KEY:
            print("\n⚠️  OpenAI API ключ не найден в .env файле, используем локальное распознавание")
            return {
                'title': dir_info.get('title', 'Unknown'),
                'year': None,
                'season': dir_info.get('season', 1),
                'total_episodes': len([f for f in files if f.file_type == 'video']),
                'needs_confirmation': True
            }

        print("\n🤖 Анализ через OpenAI API...")

        # Группируем файлы для лучшего представления
        video_files = [f for f in files if f.file_type == 'video']
        subtitle_tracks = set(f.subtitle_track for f in files
                             if f.file_type == 'subtitle' and f.subtitle_track)

        file_summary = f"""
Директория: {self.directory.name}

Видео файлы ({len(video_files)} шт):
{chr(10).join([f"- {f.filename}" for f in video_files[:3]])}
{"..." if len(video_files) > 3 else ""}

Субтитры (треки): {', '.join(subtitle_tracks) if subtitle_tracks else 'не найдены'}

Информация из названия директории:
- Возможное название: {dir_info.get('title', 'не определено')}
- Сезон: {dir_info.get('season', 'не определён')}
- Релиз-группа: {dir_info.get('release_group', 'не определена')}
"""

        prompt = f"""Проанализируй информацию о сериале/аниме:

{file_summary}

Задачи:
1. Определи правильное название сериала на английском (для Plex)
2. Определи год выхода (если возможно)
3. Подтверди или исправь номер сезона
4. Укажи общее количество эпизодов

Ответь ТОЛЬКО валидным JSON без дополнительного текста:
{{
  "title": "название на английском (без точек, через пробелы)",
  "year": год или null,
  "season": номер_сезона,
  "total_episodes": количество,
  "needs_confirmation": true/false (если не уверен в названии)
}}

Примечания:
- Название должно быть официальным английским названием для баз данных типа TVDB/TMDB
- Если это аниме, используй ромадзи латиницей
- Год - это год выхода сериала, не год релиза"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты эксперт по аниме и сериалам. Отвечай ТОЛЬКО валидным JSON без markdown блоков."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()

            # Убираем markdown блоки если есть
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            print("✅ Анализ завершён")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"   Ответ API: {content[:200]}...")
            return self._get_fallback_result(dir_info, files)
        except Exception as e:
            print(f"❌ Ошибка при анализе: {e}")
            return self._get_fallback_result(dir_info, files)

    def _get_fallback_result(self, dir_info: Dict, files: List[MediaFile]) -> Dict:
        """Возвращает результат на основе локального анализа"""
        return {
            'title': dir_info.get('title', 'Unknown'),
            'year': None,
            'season': dir_info.get('season', 1),
            'total_episodes': len([f for f in files if f.file_type == 'video']),
            'needs_confirmation': True
        }

    def confirm_series_info(self, ai_result: Dict, dir_info: Dict) -> SeriesInfo:
        """Подтверждение информации о сериале"""
        print("\n" + "="*60)
        print("📺 ИНФОРМАЦИЯ О СЕРИАЛЕ")
        print("="*60)
        print(f"Название:      {ai_result['title']}")
        print(f"Год:           {ai_result.get('year', 'не определён')}")
        print(f"Сезон:         {ai_result['season']}")
        print(f"Эпизодов:      {ai_result['total_episodes']}")
        print(f"Релиз-группа:  {dir_info.get('release_group', 'не определена')}")

        if ai_result.get('needs_confirmation'):
            print("\n⚠️  AI не уверен в правильности названия")

        print("="*60)

        while True:
            choice = input("\n[1] Всё верно\n[2] Исправить название\n[3] Исправить всё\nВыбор: ").strip()

            if choice == '1':
                return SeriesInfo(
                    title=ai_result['title'],
                    year=ai_result.get('year'),
                    season=ai_result['season'],
                    total_episodes=ai_result['total_episodes'],
                    release_group=dir_info.get('release_group')
                )

            elif choice == '2':
                title = input("Введите правильное название (англ.): ").strip()
                return SeriesInfo(
                    title=title,
                    year=ai_result.get('year'),
                    season=ai_result['season'],
                    total_episodes=ai_result['total_episodes'],
                    release_group=dir_info.get('release_group')
                )

            elif choice == '3':
                title = input("Название (англ.): ").strip()
                year_input = input("Год (Enter для пропуска): ").strip()
                year = int(year_input) if year_input else None
                season = int(input("Номер сезона: ").strip())

                return SeriesInfo(
                    title=title,
                    year=year,
                    season=season,
                    total_episodes=ai_result['total_episodes'],
                    release_group=dir_info.get('release_group')
                )
            else:
                print("❌ Неверный выбор")

    def organize_files(self):
        """Организует файлы по эпизодам"""
        print("\n📋 Организация файлов по эпизодам...")

        for file in self.files:
            if file.episode_number:
                ep = file.episode_number

                if file.file_type == 'video':
                    self.episode_map[ep]['video'] = file
                elif file.file_type == 'audio':
                    self.episode_map[ep]['audio'].append(file)
                elif file.file_type == 'subtitle' and not file.is_duplicate:
                    self.episode_map[ep]['subtitles'].append(file)

        print(f"✅ Организовано эпизодов: {len(self.episode_map)}")

    def generate_plex_filename(self, episode_num: int) -> str:
        """Генерирует имя файла по стандарту Plex"""
        series = self.series_info
        season_str = f"S{series.season:02d}"
        episode_str = f"E{episode_num:02d}"

        filename = f"{series.title} - {season_str}{episode_str}.mkv"
        return filename

    def create_output_structure(self) -> Path:
        """Создаёт структуру директорий для Plex"""
        series = self.series_info

        series_folder = f"{series.title}"
        if series.year:
            series_folder += f" ({series.year})"

        season_folder = f"Season {series.season:02d}"

        output_path = self.directory.parent / series_folder / season_folder
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Создана структура: {output_path}")
        return output_path

    def merge_episode(self, episode_num: int, output_file: Path):
        """Объединяет видео, аудио и субтитры в один MKV"""
        ep_data = self.episode_map[episode_num]

        if not ep_data['video']:
            print(f"⚠️  Эпизод {episode_num}: видео не найдено")
            return False

        print(f"\n🔧 Обработка эпизода {episode_num}:")
        print(f"   Видео: {ep_data['video'].filename}")
        print(f"   Аудио: {len(ep_data['audio'])} треков")
        print(f"   Субтитры: {len(ep_data['subtitles'])} треков")

        # Формируем команду mkvmerge
        cmd = ['mkvmerge', '-o', str(output_file)]

        # Добавляем видео
        cmd.extend([str(ep_data['video'].path)])

        # Добавляем аудио дорожки
        for audio in ep_data['audio']:
            cmd.extend([str(audio.path)])

        # Добавляем субтитры с правильными названиями треков
        for sub in ep_data['subtitles']:
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

    def validate_media_file(self, file_path: Path) -> MediaValidationResult:
        """Валидирует медиафайл с помощью MediaInfo"""
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

    def validate_output_files(self, output_path: Path):
        """Валидирует все созданные файлы"""
        print("\n" + "="*60)
        print("🔍 ВАЛИДАЦИЯ ВЫХОДНЫХ ФАЙЛОВ")
        print("="*60)

        mkv_files = sorted(output_path.glob("*.mkv"))

        if not mkv_files:
            print("⚠️  MKV файлы не найдены")
            return

        valid_count = 0
        invalid_count = 0

        for mkv_file in mkv_files:
            validation = self.validate_media_file(mkv_file)
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

    def show_processing_plan(self):
        """Отображает план обработки"""
        print("\n" + "="*60)
        print("📋 ПЛАН ОБРАБОТКИ")
        print("="*60)

        for ep_num in sorted(self.episode_map.keys()):
            new_name = self.generate_plex_filename(ep_num)
            ep_data = self.episode_map[ep_num]

            print(f"\nЭпизод {ep_num:02d}:")
            print(f"  → {new_name}")

            if ep_data['video']:
                print(f"  📹 Видео: {ep_data['video'].filename}")

            if ep_data['audio']:
                print(f"  🔊 Аудио: {len(ep_data['audio'])} треков")
                for audio in ep_data['audio']:
                    print(f"      - {audio.filename}")

            if ep_data['subtitles']:
                print(f"  💬 Субтитры:")
                for sub in ep_data['subtitles']:
                    track = sub.subtitle_track or "Unknown"
                    print(f"      - {track}")

        print("="*60)

    def process(self):
        """Основной процесс обработки"""
        print("\n🎬 MEDIA ORGANIZER ДЛЯ PLEX v2.0")
        print("="*60)

        # 1. Анализ названия директории
        dir_info = self.extract_info_from_dirname()

        # 2. Сканирование файлов
        self.files = self.scan_directory()
        if not self.files:
            print("❌ Файлы не найдены")
            return

        # 3. Анализ через AI
        ai_result = self.analyze_with_ai(self.files, dir_info)

        # 4. Подтверждение информации
        self.series_info = self.confirm_series_info(ai_result, dir_info)

        # 5. Организация файлов
        self.organize_files()

        # 6. План обработки
        self.show_processing_plan()

        # 7. Подтверждение
        confirm = input("\n▶️  Начать обработку? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено")
            return

        # 8. Создание структуры
        output_path = self.create_output_structure()

        # 9. Обработка эпизодов
        print("\n" + "="*60)
        print("⚙️  ОБРАБОТКА")
        print("="*60)

        success_count = 0
        for ep_num in sorted(self.episode_map.keys()):
            output_file = output_path / self.generate_plex_filename(ep_num)
            if self.merge_episode(ep_num, output_file):
                success_count += 1

        # 10. Валидация
        if success_count > 0:
            self.validate_output_files(output_path)

        # 11. Итог
        print("\n" + "="*60)
        print("🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
        print("="*60)
        print(f"✅ Успешно: {success_count}/{len(self.episode_map)} эпизодов")
        print(f"📁 Путь: {output_path}")
        print("="*60)


def main():
    """Точка входа"""
    import sys

    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Введите путь к директории с сериалом: ").strip()

    if not os.path.isdir(directory):
        print("❌ Директория не найдена")
        return

    try:
        organizer = MediaOrganizer(directory)
        organizer.process()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
