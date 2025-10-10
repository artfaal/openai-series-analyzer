# Media Organizer for Plex v4.0

AI-powered tool for preparing TV series and anime for Plex Media Server import with advanced preprocessing and intelligent recognition.

## Features

### AI-Powered Recognition (NEW in v4.0)
- 🤖 **GPT-5 with web search**: accurate series title and year detection
- 🌐 **Database search**: automatic lookup in TVDB, TMDB, IMDb, MyAnimeList
- 🧠 **Smart parsing**: AI-based directory and file name recognition (no regex limitations)
- 🎯 **Adaptive subtitle detection**: recognizes any studio or track name
- 🎵 **Audio studio detection**: automatically identifies dubbing studios (AniLibria, Studio Band, etc.)
- 📺 **Episode recognition**: handles any naming format (S01E01, "01. Title", etc.)

### Preprocessing
- 🔄 **AVI → MKV conversion**: automatic .avi file conversion using ffmpeg
- 🔊 **EAC3 → AAC conversion**: detection and conversion of EAC3 audio (TV-compatible)
- 📦 **Track embedding**: automatic embedding of external .mka and .ass/.srt into MKV
- ⚡ **Conditional execution**: preprocessing runs only when needed
- 💾 **Smart temp files**: created in working directory (same disk)

### Core Features
- 🎬 **Media file merging**: video + audio tracks + subtitles into one MKV
- 🏷️ **Plex-compatible names**: automatic renaming to standard `Series Title - S01E01.mkv`
- 📁 **Proper structure**: creates directories `Series Title (Year)/Season 01/`
- 🔍 **File validation**: checks created files using MediaInfo
- 🎭 **Subtitle support**: AI-powered track detection and naming
- ♻️ **Deduplication**: automatic removal of duplicate subtitles

### Automation
- 🚀 **Batch processing**: process multiple directories in one command
- ⚡ **Auto-confirmation mode**: fully automated processing without user interaction
- 🗑️ **Source deletion**: optional automatic cleanup of source directories after success
- 📊 **Progress tracking**: clear status for multi-directory processing

### Architecture
- 🧩 **Modular structure**: separation into processors, models, utils
- 🤖 **AI-first approach**: leverages OpenAI API for complex logic
- 🧪 **Testability**: each processor is a separate module
- 🔧 **Extensibility**: easy to add new processors

## Requirements

### OpenAI API Key
**Required**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

The tool uses:
- **GPT-5** with web search for series title recognition
- **GPT-4o-mini** for pattern recognition tasks

### System Dependencies

```bash
# macOS
brew install mkvtoolnix mediainfo ffmpeg

# Linux
apt-get install mkvtoolnix mediainfo ffmpeg
```

### Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
# OpenAI API Configuration (required)
OPENAI_API_KEY=your-api-key-here

# Model Configuration (optional, defaults shown)
OPENAI_MODEL=gpt-5
OPENAI_REASONING_EFFORT=medium
OPENAI_SIMPLE_MODEL=gpt-4o-mini

# Audio Conversion (optional)
AAC_BITRATE=192k
```

**Reasoning effort levels:**
- `minimal`/`low` - faster, good for simple series
- `medium` - balanced (recommended)
- `high` - thorough research, slower, for complex/ambiguous titles

## Usage

### Basic Usage

```bash
# Interactive mode
python media_organizer.py

# Single directory
python media_organizer.py /path/to/series/directory

# Auto-confirmation (no prompts)
python media_organizer.py /path/to/series -y

# View help
python media_organizer.py --help
```

### Batch Processing

```bash
# Multiple directories (comma-separated)
python media_organizer.py "/path/series1,/path/series2,/path/series3"

# Multiple directories with auto-confirmation
python media_organizer.py "/path/series1,/path/series2,/path/series3" -y

# Batch with source deletion
python media_organizer.py "/path/series1,/path/series2" -y -d
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--auto-confirm` | `-y` | Skip all confirmation prompts (fully automated) |
| `--delete-source` | `-d` | Delete source directory after successful processing |
| `--help` | `-h` | Show help message with examples |

### Full Automation Example

```bash
# Process 3 series automatically and delete sources
python media_organizer.py "/downloads/Anime S1,/downloads/Anime S2,/downloads/Anime S3" --auto-confirm --delete-source
```

This will:
1. Process all 3 directories sequentially
2. Use AI to determine titles automatically
3. Process without any user prompts
4. Delete source directories after successful processing
5. Show final statistics (e.g., "✅ Успешно обработано: 3/3")

## Workflow

1. **Directory Analysis** - AI-powered parsing of folder name (GPT-4o-mini)
2. **File Scanning** - search for video, audio and subtitles
   - AI-powered episode number extraction (any format)
   - AI-powered subtitle track detection
   - AI-powered audio studio detection
3. **Organization** - group files by episodes
4. **Preprocessing** - conditional processing:
   - Convert AVI → MKV (if .avi files exist)
   - Convert EAC3 → AAC (if EAC3 detected)
   - Embed external tracks (if .mka/.ass/.srt exist)
5. **AI Recognition** - GPT-5 with web search:
   - Searches TVDB, TMDB, IMDb, MyAnimeList
   - Determines official English title
   - Finds release year and confirms season
6. **Confirmation** - interactive correction if needed (skipped with `--auto-confirm`)
7. **Preview** - detailed plan showing all operations
8. **Final Merging** - create final MKV files with proper track names
9. **Validation** - check created files (duration, tracks, codecs)
10. **Cleanup** - remove temporary files
11. **Source Deletion** - optional removal of source directory (with `--delete-source`)

## Example

**Input structure:**
```
Frieren.S01.1080p-GRUPPE/
├── Frieren.S01E01.mkv
├── Frieren.S01E01.ru.mka
├── Subtitles/
│   ├── Animevod/
│   │   └── Frieren.S01E01.ru_Animevod.ass
│   └── CR/
│       └── Frieren.S01E01.ru_CR.ass
```

**Output structure:**
```
Frieren Beyond Journey's End (2023)/
└── Season 01/
    └── Frieren Beyond Journey's End - S01E01.mkv
        ├── Video: H.264
        ├── Audio: AAC (Russian)
        ├── Subtitle: Russian [Animevod]
        └── Subtitle: Russian [Crunchyroll]
```

**AI Recognition in action:**
- 🔍 Input: `Frieren.S01.1080p-GRUPPE`
- 🌐 Web search: Searches for "Frieren anime TVDB IMDb"
- ✅ Found: "Frieren: Beyond Journey's End" (2023)
- 📝 Plex-compatible: `Frieren Beyond Journey's End (2023)`

## Validation

After processing, automatic validation of all created files runs:

- ✅ Check for video/audio tracks
- ⏱️ Duration check (protection from broken files)
- 📊 Display codecs and resolution
- 💾 File sizes
- ⚠️ Warnings about potential issues

## License

MIT
