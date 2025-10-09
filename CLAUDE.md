# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Organizer for Plex - автоматизированный инструмент для подготовки сериалов и аниме для Plex Media Server. Использует OpenAI API для распознавания названий сериалов и организует медиафайлы в структуру, совместимую с Plex.

## Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# External dependencies required
# macOS:
brew install mkvtoolnix mediainfo

# Linux:
apt-get install mkvtoolnix mediainfo
```

## Configuration

Create `.env` file in project root:
```env
OPENAI_API_KEY=your-api-key-here
```

## Running the Script

```bash
# Interactive mode
python media_organizer.py

# With directory argument
python media_organizer.py /path/to/series/directory
```

## Architecture

### Main Class: `MediaOrganizer`

Центральный класс, управляющий всем процессом обработки медиафайлов.

**Key data structures:**
- `MediaFile` - dataclass для хранения информации о файле (путь, тип, номер эпизода, язык, субтитры)
- `SeriesInfo` - dataclass для метаданных сериала (название, год, сезон, количество эпизодов)
- `MediaValidationResult` - dataclass для результатов валидации (треки, кодеки, ошибки)
- `episode_map` - словарь, группирующий видео/аудио/субтитры по номерам эпизодов

### Processing Workflow

1. **Directory Analysis** (`extract_info_from_dirname`):
   - Парсит название директории по паттерну `Название.S01.качество-ГРУППА`
   - Извлекает: название, сезон, релиз-группу

2. **File Scanning** (`scan_directory`):
   - Рекурсивно сканирует директорию
   - Классифицирует файлы: video (.mkv, .mp4), audio (.mka, .aac), subtitle (.srt, .ass)
   - Извлекает номера эпизодов из имён файлов (паттерн S01E01)
   - Определяет треки субтитров (Анимевод, Crunchyroll)
   - Обнаруживает дубликаты субтитров по размеру и треку

3. **AI Analysis** (`analyze_with_ai`):
   - Использует OpenAI GPT-4o для определения официального английского названия сериала
   - Определяет год выхода и подтверждает сезон
   - Fallback на локальное распознавание при отсутствии API ключа

4. **User Confirmation** (`confirm_series_info`):
   - Интерактивное подтверждение/исправление метаданных
   - Опции: принять, исправить название, исправить всё

5. **File Organization** (`organize_files`):
   - Группирует файлы в `episode_map` по номерам эпизодов
   - Фильтрует дубликаты субтитров

6. **Merging** (`merge_episode`):
   - Использует `mkvmerge` для объединения видео + аудиодорожки + субтитры
   - Устанавливает правильные названия треков субтитров
   - Выходной формат: `Series Title - S01E01.mkv`

7. **Output Structure** (`create_output_structure`):
   - Создаёт Plex-совместимую структуру: `Series Title (Year)/Season 01/`
   - Именует файлы по стандарту Plex: `Series Title - S01E01.mkv`

8. **Validation** (`validate_output_files`):
   - Анализирует созданные MKV файлы с помощью MediaInfo
   - Проверяет: длительность, количество треков, кодеки, разрешение
   - Выявляет ошибки (нет видео, слишком короткое) и предупреждения
   - Выводит детальную статистику по каждому файлу

## Important Notes

### External Dependencies

**Required:**
- **mkvmerge** (MKVToolNix) - для объединения медиафайлов
  - macOS: `brew install mkvtoolnix`
  - Linux: `apt-get install mkvtoolnix`

**Optional (for validation):**
- **mediainfo** - для анализа и валидации медиафайлов
  - macOS: `brew install mediainfo`
  - Linux: `apt-get install mediainfo`

### File Pattern Recognition
- Эпизоды: регулярное выражение `[Ss](\d+)[Ee](\d+)` (media_organizer.py:83)
- Директории: регулярное выражение `^(.+?)\.S(\d+).*?-(\w+)$` (media_organizer.py:66)

### Subtitle Track Detection
- Логика в `detect_subtitle_track()` (media_organizer.py:93)
- Проверяет имена файлов и родительские директории на ключевые слова (Анимевод, CR)

## Development Guidelines

### Environment
- **ALWAYS** activate venv: `source venv/bin/activate`
- Never use global Python packages
- Future-proof for Docker deployment

### Workflow
1. Make changes in small batches
2. Test changes immediately when possible
3. Before committing:
   - Update CLAUDE.md if architecture/setup changed
   - Update README.md if new functionality added
4. Commit after each batch of related changes

### Testing
- Keep all tests in separate `tests/` directory
- Do not mix tests with application code

### Configuration
- API keys and secrets in `.env` file (media_organizer.py:22)
- `.env` is in `.gitignore` - never commit secrets