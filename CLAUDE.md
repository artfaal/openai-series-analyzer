# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Organizer for Plex v3.0 - автоматизированный инструмент для подготовки сериалов и аниме для Plex Media Server.

**Основные возможности:**
- Автоматическое распознавание названий через OpenAI API
- **Preprocessing pipeline**: AVI→MKV, EAC3→AAC, встраивание треков
- Объединение медиафайлов в Plex-совместимую структуру
- Валидация с помощью MediaInfo
- Модульная архитектура для лёгкого расширения

## Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# External dependencies required
# macOS:
brew install mkvtoolnix mediainfo ffmpeg

# Linux:
apt-get install mkvtoolnix mediainfo ffmpeg
```

## Running the Script

```bash
# Interactive mode
python media_organizer.py

# With directory argument
python media_organizer.py /path/to/series/directory
```

## Architecture

### Модульная структура

```
openai-series-analizer/
├── media_organizer.py          # Main orchestrator (287 lines)
├── models/
│   └── data_models.py          # All dataclasses
├── processors/
│   ├── scanner.py              # File scanning
│   ├── ai_analyzer.py          # OpenAI integration
│   ├── preprocessor.py         # Preprocessing coordinator
│   ├── avi_converter.py        # AVI → MKV
│   ├── audio_converter.py      # EAC3 → AAC
│   ├── track_embedder.py       # Embed external tracks
│   ├── merger.py               # Final MKV merging
│   └── validator.py            # MediaInfo validation
└── utils/
    └── patterns.py             # Regex patterns
```

**Data models** (models/data_models.py):
- `MediaFile` - информация о файле
- `SeriesInfo` - метаданные сериала
- `MediaValidationResult` - результаты валидации
- `PreprocessingResult` - результаты preprocessing

**Main orchestrator** (media_organizer.py):
- Координирует все processors
- Управляет episode_map
- Обрабатывает пользовательский ввод

### Processing Workflow

1. **Directory Analysis** (utils/patterns.py):
   - Парсит название директории по паттерну `Название.S01.качество-ГРУППА`
   - Извлекает: название, сезон, релиз-группу

2. **File Scanning** (processors/scanner.py):
   - Рекурсивно сканирует директорию
   - Классифицирует файлы: video (.mkv, .mp4, .avi), audio (.mka, .aac), subtitle (.srt, .ass)
   - Извлекает номера эпизодов из имён файлов (паттерн S01E01)
   - Определяет треки субтитров (Анимевод, Crunchyroll)
   - Обнаруживает дубликаты субтитров

3. **File Organization** (media_organizer.py):
   - Группирует файлы в `episode_map` по номерам эпизодов
   - Фильтрует дубликаты субтитров

4. **Preprocessing** (processors/preprocessor.py) - **NEW**:
   - **Conditional**: запускается только если нужно
   - **AVI Conversion**: .avi → .mkv с помощью ffmpeg (remux)
   - **EAC3 Conversion**: обнаруживает EAC3, конвертирует в AAC
   - **Track Embedding**: встраивает внешние .mka и .ass/.srt в MKV
   - Создаёт временные файлы в `.preprocessing_temp/`

5. **AI Analysis** (processors/ai_analyzer.py):
   - Использует OpenAI GPT-4o для определения официального английского названия
   - Определяет год выхода и подтверждает сезон
   - Fallback на локальное распознавание при отсутствии API ключа

6. **User Confirmation** (media_organizer.py):
   - Интерактивное подтверждение/исправление метаданных
   - Опции: принять, исправить название, исправить всё

7. **Final Merging** (processors/merger.py):
   - Использует `mkvmerge` для финального объединения
   - Устанавливает правильные названия треков субтитров
   - Выходной формат: `Series Title - S01E01.mkv`

8. **Output Structure** (media_organizer.py):
   - Создаёт Plex-совместимую структуру: `Series Title (Year)/Season 01/`

9. **Validation** (processors/validator.py):
   - Анализирует созданные MKV файлы с помощью MediaInfo
   - Проверяет: длительность, количество треков, кодеки, разрешение
   - Выявляет ошибки и предупреждения

10. **Cleanup**:
    - Удаляет временные файлы preprocessing

## Important Notes

### External Dependencies

**Required:**
- **mkvmerge** (MKVToolNix) - для объединения медиафайлов
- **mediainfo** - для анализа и валидации
- **ffmpeg** - для AVI→MKV и EAC3→AAC конвертации

### File Pattern Recognition
- Эпизоды: `[Ss](\d+)[Ee](\d+)` (utils/patterns.py)
- Директории: `^(.+?)\.S(\d+).*?-(\w+)$` (utils/patterns.py)

### Preprocessing Features
- **AVI Detection**: по расширению `.avi` (processors/avi_converter.py)
- **EAC3 Detection**: через MediaInfo analysis (processors/audio_converter.py)
- **Track Embedding**: встраивание внешних .mka и .ass/.srt (processors/track_embedder.py)

### Key Modules
- `processors/preprocessor.py` - координатор preprocessing, управляет временными файлами
- `processors/audio_converter.py` - обнаруживает EAC3 треки, извлекает, конвертирует в AAC, заменяет
- `processors/avi_converter.py` - ffmpeg remux (без перекодирования видео)
- `processors/scanner.py` - сканирование с дедупликацией субтитров
- `processors/validator.py` - валидация через MediaInfo

## Development Guidelines

### Environment
- **ALWAYS** activate venv: `source venv/bin/activate`
- Never use global Python packages
- Future-proof for Docker deployment

### Configuration Management
- **API keys and secrets**: в `.env` file (никогда не коммитить)
- **AI prompts**: в `.env` file для гибкости
- **Important parameters**: в `.env` или config file (model name, bitrates, etc.)
- **Unimportant parameters**: можно хардкодить в коде
- `.env` is in `.gitignore` - never commit secrets

### Git Workflow
1. Make changes in small batches
2. Test changes immediately when possible
3. **Before committing:**
   - Check for unwanted files: `ls -la`
   - Add unwanted files to `.gitignore` if found
   - Remove temporary files: `rm -f`
   - Update CLAUDE.md if architecture/setup changed
   - Update README.md if new functionality added
4. Commit after each batch of related changes

### .gitignore Rules
- Add files that shouldn't be in git immediately
- Python compilation artifacts (`__pycache__/`, `*.pyc`) - OK to keep locally, must be in .gitignore
- Temporary files (`.preprocessing_temp/`, etc.)
- Environment files (`.env`)
- Virtual environments (`venv/`)

### Testing
- Keep all tests in separate `tests/` directory
- Do not mix tests with application code