#!/usr/bin/env python3
"""
Media Organizer - automated preparation of series/anime for Plex
Support for various release formats and directory structures

v4.0 - AI-powered recognition with GPT-5 and web search
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
from processors.preview import PreviewGenerator

# Import utils
from utils.patterns import parse_directory_name
from utils.filename_normalizer import normalize_series_title


class MediaOrganizer:
    """Main orchestrator for processing media files"""

    def __init__(self, directory: str, auto_confirm: bool = False, delete_source: bool = False):
        self.directory = Path(directory)
        self.auto_confirm = auto_confirm
        self.delete_source = delete_source
        self.files = []
        self.series_info: Optional[SeriesInfo] = None
        self.episode_map = defaultdict(lambda: {
            'video': None,
            'audio': [],
            'subtitles': []
        })
        self.preprocessing_results = {}  # Store preprocessing results for preview

        # Initialize processors
        self.scanner = FileScanner()
        self.ai_analyzer = AIAnalyzer()
        self.validator = MediaValidator()
        self.merger = MKVMerger()
        self.preprocessor = Preprocessor(self.directory)
        self.preview_generator = PreviewGenerator()

    def extract_info_from_dirname(self) -> dict:
        """Extracts information from directory name"""
        dirname = self.directory.name
        print(f"📂 Анализ названия директории: {dirname}")

        info = parse_directory_name(dirname)

        if info['title']:
            print(f"✅ Распознано: {info['title']} (Сезон {info['season']}, Группа: {info['release_group']})")
        else:
            print(f"⚠️ Не удалось распознать паттерн директории")

        return info

    def organize_files(self):
        """Organizes files by episodes"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info("=== Организация файлов ===")
        print("\n📋 Организация файлов по эпизодам...")

        for file in self.files:
            if file.episode_number:
                ep = file.episode_number

                if file.file_type == 'video':
                    self.episode_map[ep]['video'] = file
                    logger.info(f"Эпизод {ep}: видео {file.path}")
                elif file.file_type == 'audio':
                    self.episode_map[ep]['audio'].append(file)
                    logger.info(f"Эпизод {ep}: аудио {file.path}")
                elif file.file_type == 'subtitle' and not file.is_duplicate:
                    self.episode_map[ep]['subtitles'].append(file)
                    logger.info(f"Эпизод {ep}: субтитры {file.path}")

        logger.info(f"Всего эпизодов организовано: {len(self.episode_map)}")
        print(f"✅ Организовано эпизодов: {len(self.episode_map)}")

    def confirm_series_info(self, ai_result: dict, dir_info: dict) -> SeriesInfo:
        """Confirm series information"""
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

        # Auto-confirm mode
        if self.auto_confirm:
            print("\n✅ Авто-подтверждение: информация принята")
            return SeriesInfo(
                title=ai_result['title'],
                year=ai_result.get('year'),
                season=ai_result['season'],
                total_episodes=ai_result['total_episodes'],
                release_group=dir_info.get('release_group')
            )

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
        """Generates filename according to Plex standard"""
        series = self.series_info
        normalized_title = normalize_series_title(series.title)
        season_str = f"S{series.season:02d}"
        episode_str = f"E{episode_num:02d}"

        filename = f"{normalized_title} - {season_str}{episode_str}.mkv"
        return filename

    def create_output_structure(self) -> Path:
        """Creates directory structure for Plex"""
        series = self.series_info
        normalized_title = normalize_series_title(series.title)

        series_folder = f"{normalized_title}"
        if series.year:
            series_folder += f" ({series.year})"

        season_folder = f"Season {series.season:02d}"

        output_path = self.directory.parent / series_folder / season_folder
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Создана структура: {output_path}")
        return output_path

    def show_processing_plan(self):
        """Displays detailed processing plan with preview"""
        # Generate detailed preview report
        series_dict = {
            'title': self.series_info.title,
            'year': self.series_info.year,
            'season': self.series_info.season,
            'total_episodes': self.series_info.total_episodes
        }

        preview_report = self.preview_generator.generate_preview(
            self.episode_map,
            series_dict,
            self.preprocessing_results
        )
        print(preview_report)

    def process(self):
        """Main processing workflow"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"=== НАЧАЛО ОБРАБОТКИ ===")
        logger.info(f"Директория: {self.directory}")
        logger.info(f"Авто-подтверждение: {self.auto_confirm}")
        logger.info(f"Удаление источника: {self.delete_source}")

        print("\n🎬 MEDIA ORGANIZER ДЛЯ PLEX v4.0")
        print("="*60)

        # 1. Analyze directory name
        logger.info("Этап 1: Анализ названия директории")
        dir_info = self.extract_info_from_dirname()
        logger.info(f"Результат анализа: {dir_info}")

        # 2. Scan files
        logger.info("Этап 2: Сканирование файлов")
        self.files = self.scanner.scan_directory(self.directory)
        if not self.files:
            print("❌ Файлы не найдены")
            logger.error("Файлы не найдены")
            return

        # 3. Organize files by episodes
        logger.info("Этап 3: Организация файлов по эпизодам")
        self.organize_files()

        # 4. Preprocessing (AVI→MKV, EAC3→AAC, embed tracks)
        # Always run preprocessing - it will check for EAC3, AVI, external tracks
        logger.info("Этап 4: Preprocessing")
        self.preprocessing_results = self.preprocessor.preprocess_all_episodes(self.episode_map)
        logger.info(f"Результаты preprocessing: {len(self.preprocessing_results)} эпизодов обработано")

        # 5. AI analysis
        logger.info("Этап 5: AI-анализ серии")
        ai_result = self.ai_analyzer.analyze(self.files, dir_info, self.directory.name)
        logger.info(f"AI результат: {ai_result}")

        # 6. Confirm information
        logger.info("Этап 6: Подтверждение информации")
        self.series_info = self.confirm_series_info(ai_result, dir_info)
        logger.info(f"Информация о серии: {self.series_info}")

        # 7. Processing plan
        logger.info("Этап 7: План обработки")
        self.show_processing_plan()

        # 8. Confirmation
        logger.info("Этап 8: Подтверждение пользователя")
        if self.auto_confirm:
            print("\n✅ Авто-подтверждение: начинаем обработку")
            logger.info("Автоматическое подтверждение активно")
        else:
            confirm = input("\n▶️  Начать обработку? (y/n): ").strip().lower()
            logger.info(f"Ответ пользователя: {confirm}")
            if confirm != 'y':
                print("❌ Отменено")
                logger.info("Обработка отменена пользователем")
                self.preprocessor.cleanup()
                return

        # 9. Create structure
        logger.info("Этап 9: Создание выходной структуры")
        output_path = self.create_output_structure()
        logger.info(f"Выходной путь: {output_path}")

        # 10. Process episodes (merge)
        logger.info("Этап 10: Финальное объединение")
        print("\n" + "="*60)
        print("⚙️  ФИНАЛЬНОЕ ОБЪЕДИНЕНИЕ")
        print("="*60)

        success_count = 0
        for ep_num in sorted(self.episode_map.keys()):
            ep_data = self.episode_map[ep_num]
            output_file = output_path / self.generate_plex_filename(ep_num)

            logger.info(f"Объединение эпизода {ep_num}: {output_file}")
            if self.merger.merge_episode(
                ep_data['video'],
                ep_data['audio'],
                ep_data['subtitles'],
                output_file
            ):
                success_count += 1
                logger.info(f"Эпизод {ep_num} успешно объединён")

        # 11. Validation
        logger.info("Этап 11: Валидация")
        if success_count > 0:
            self.validator.validate_directory(output_path)

        # 12. Cleanup
        logger.info("Этап 12: Очистка временных файлов")
        self.preprocessor.cleanup()

        # 13. Delete source directory if requested and all episodes succeeded
        if self.delete_source and success_count == len(self.episode_map) and success_count > 0:
            logger.info("Этап 13: Удаление исходной директории")
            print("\n🗑️  Удаление исходной директории...")
            try:
                import shutil
                import os

                # Error handler for macOS metadata files
                def onerror(func, path, exc_info):
                    """Error handler for shutil.rmtree - ignore macOS metadata file errors"""
                    if os.path.exists(path):
                        os.chmod(path, 0o777)
                        try:
                            func(path)
                        except:
                            # Ignore errors for ._ files
                            if not os.path.basename(path).startswith('._'):
                                print(f"⚠️  Не удалось удалить: {path}")
                                logger.warning(f"Не удалось удалить: {path}")

                shutil.rmtree(self.directory, onerror=onerror)
                print(f"✅ Исходная директория удалена: {self.directory}")
                logger.info(f"Исходная директория удалена: {self.directory}")
            except Exception as e:
                print(f"⚠️  Не удалось удалить исходную директорию: {e}")
                logger.error(f"Не удалось удалить исходную директорию: {e}", exc_info=True)

        # 14. Summary
        logger.info("=== ИТОГИ ===")
        logger.info(f"Успешно обработано: {success_count}/{len(self.episode_map)}")
        logger.info(f"Выходной путь: {output_path}")
        print("\n" + "="*60)
        print("🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
        print("="*60)
        print(f"✅ Успешно: {success_count}/{len(self.episode_map)} эпизодов")
        print(f"📁 Путь: {output_path}")
        if self.delete_source and success_count == len(self.episode_map):
            print(f"🗑️  Исходная директория удалена")
        print("="*60)


def setup_logging():
    """Setup logging to file and console"""
    import logging
    from datetime import datetime

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'media_organizer_{timestamp}.log'

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info(f"Лог-файл: {log_file}")
    return logging.getLogger(__name__)


def main():
    """Entry point"""
    import sys
    import argparse

    # Setup logging first
    logger = setup_logging()

    parser = argparse.ArgumentParser(
        description='Media Organizer для Plex v4.0 - автоматическая подготовка сериалов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Примеры использования:
  python media_organizer.py "/path/to/series"
  python media_organizer.py "/path/to/series1,/path/to/series2,/path/to/series3" -y
  python media_organizer.py "/path/to/series" --auto-confirm --delete-source
        """
    )
    parser.add_argument(
        'directories',
        nargs='?',
        help='Путь к директории с сериалом или несколько путей через запятую'
    )
    parser.add_argument(
        '--auto-confirm', '-y',
        action='store_true',
        help='Автоматическое подтверждение без интерактивного режима'
    )
    parser.add_argument(
        '--delete-source', '-d',
        action='store_true',
        help='Удалить исходную директорию после успешной обработки'
    )

    args = parser.parse_args()

    # Get directories
    if args.directories:
        # Split by comma and strip whitespace
        directories = [d.strip() for d in args.directories.split(',')]
    else:
        directory_input = input("Введите путь к директории (или несколько через запятую): ").strip()
        directories = [d.strip() for d in directory_input.split(',')]

    # Validate all directories exist
    invalid_dirs = [d for d in directories if not os.path.isdir(d)]
    if invalid_dirs:
        print("❌ Следующие директории не найдены:")
        for d in invalid_dirs:
            print(f"   - {d}")
        return

    # Process each directory
    total_dirs = len(directories)
    successful = 0
    failed = 0

    for idx, directory in enumerate(directories, 1):
        if total_dirs > 1:
            print("\n" + "="*60)
            print(f"📦 ОБРАБОТКА ДИРЕКТОРИИ {idx}/{total_dirs}")
            print(f"📂 {directory}")
            print("="*60)
            logger.info(f"Обработка директории {idx}/{total_dirs}: {directory}")

        try:
            logger.info(f"Создание MediaOrganizer для: {directory}")
            organizer = MediaOrganizer(
                directory,
                auto_confirm=args.auto_confirm,
                delete_source=args.delete_source
            )
            organizer.process()
            successful += 1
            logger.info(f"Успешно обработано: {directory}")
        except KeyboardInterrupt:
            print("\n\n❌ Прервано пользователем")
            logger.warning("Прервано пользователем")
            break
        except Exception as e:
            print(f"\n❌ Ошибка при обработке {directory}: {e}")
            logger.error(f"Ошибка при обработке {directory}: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            failed += 1

    # Final summary for multiple directories
    if total_dirs > 1:
        print("\n" + "="*60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("="*60)
        print(f"✅ Успешно обработано: {successful}/{total_dirs}")
        if failed > 0:
            print(f"❌ Ошибок: {failed}/{total_dirs}")
        print("="*60)


if __name__ == "__main__":
    main()
