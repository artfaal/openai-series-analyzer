#!/usr/bin/env python3
"""
Media Organizer - автоматизация подготовки сериалов/аниме для Plex
Поддержка различных форматов релизов и структур директорий

v3.0 - Модульная архитектура с preprocessing
"""

import os
from pathlib import Path
from typing import Optional
from collections import defaultdict

# Import models
from models.data_models import SeriesInfo

# Import processors
from processors.scanner import FileScanner
from processors.ai_analyzer import AIAnalyzer
from processors.validator import MediaValidator
from processors.merger import MKVMerger
from processors.preprocessor import Preprocessor

# Import utils
from utils.patterns import parse_directory_name


class MediaOrganizer:
    """Главный orchestrator для обработки медиафайлов"""

    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.files = []
        self.series_info: Optional[SeriesInfo] = None
        self.episode_map = defaultdict(lambda: {
            'video': None,
            'audio': [],
            'subtitles': []
        })

        # Initialize processors
        self.scanner = FileScanner()
        self.ai_analyzer = AIAnalyzer()
        self.validator = MediaValidator()
        self.merger = MKVMerger()
        self.preprocessor = Preprocessor(self.directory)

    def extract_info_from_dirname(self) -> dict:
        """Извлекает информацию из названия директории"""
        dirname = self.directory.name
        print(f"📂 Анализ названия директории: {dirname}")

        info = parse_directory_name(dirname)

        if info['title']:
            print(f"✅ Распознано: {info['title']} (Сезон {info['season']}, Группа: {info['release_group']})")
        else:
            print(f"⚠️ Не удалось распознать паттерн директории")

        return info

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

    def confirm_series_info(self, ai_result: dict, dir_info: dict) -> SeriesInfo:
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
        print("\n🎬 MEDIA ORGANIZER ДЛЯ PLEX v3.0")
        print("="*60)

        # 1. Анализ названия директории
        dir_info = self.extract_info_from_dirname()

        # 2. Сканирование файлов
        self.files = self.scanner.scan_directory(self.directory)
        if not self.files:
            print("❌ Файлы не найдены")
            return

        # 3. Организация файлов по эпизодам
        self.organize_files()

        # 4. Preprocessing (AVI→MKV, EAC3→AAC, встраивание треков)
        if self.preprocessor.needs_preprocessing(self.files):
            self.preprocessor.preprocess_all_episodes(self.episode_map)

        # 5. Анализ через AI
        ai_result = self.ai_analyzer.analyze(self.files, dir_info, self.directory.name)

        # 6. Подтверждение информации
        self.series_info = self.confirm_series_info(ai_result, dir_info)

        # 7. План обработки
        self.show_processing_plan()

        # 8. Подтверждение
        confirm = input("\n▶️  Начать обработку? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено")
            self.preprocessor.cleanup()
            return

        # 9. Создание структуры
        output_path = self.create_output_structure()

        # 10. Обработка эпизодов (merge)
        print("\n" + "="*60)
        print("⚙️  ФИНАЛЬНОЕ ОБЪЕДИНЕНИЕ")
        print("="*60)

        success_count = 0
        for ep_num in sorted(self.episode_map.keys()):
            ep_data = self.episode_map[ep_num]
            output_file = output_path / self.generate_plex_filename(ep_num)

            if self.merger.merge_episode(
                ep_data['video'],
                ep_data['audio'],
                ep_data['subtitles'],
                output_file
            ):
                success_count += 1

        # 11. Валидация
        if success_count > 0:
            self.validator.validate_directory(output_path)

        # 12. Cleanup
        self.preprocessor.cleanup()

        # 13. Итог
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
