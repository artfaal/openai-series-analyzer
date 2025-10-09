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

# External dependency required: MKVToolNix (для mkvmerge)
# macOS: brew install mkvtoolnix
# Linux: apt-get install mkvtoolnix
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

## Important Notes

### API Key Management
**CRITICAL**: Строка 18 содержит hardcoded OpenAI API key. При работе с кодом:
- Никогда не коммитить изменения с реальным API ключом
- Использовать переменные окружения: `os.getenv('OPENAI_API_KEY')`
- API ключ нужно удалить и заменить на env var

### External Dependencies
- **mkvmerge** (из пакета MKVToolNix) - обязателен для объединения медиафайлов
- Проверка наличия: `which mkvmerge`

### File Pattern Recognition
- Эпизоды: регулярное выражение `[Ss](\d+)[Ee](\d+)` (media_organizer.py:83)
- Директории: регулярное выражение `^(.+?)\.S(\d+).*?-(\w+)$` (media_organizer.py:66)

### Subtitle Track Detection
- Логика в `detect_subtitle_track()` (media_organizer.py:93)
- Проверяет имена файлов и родительские директории на ключевые слова (Анимевод, CR)
- Всегда делай коммит после пачки изменений
- Запомни, что наш проект активируется через activate. Не пытайся использовать глобальные пакеты и питон