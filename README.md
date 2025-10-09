# Media Organizer for Plex v3.0

Automated tool for preparing TV series and anime for Plex Media Server import with modular architecture and preprocessing pipeline.

## Features

### Preprocessing (NEW in v3.0)
- 🔄 **AVI → MKV conversion**: automatic .avi file conversion using ffmpeg
- 🔊 **EAC3 → AAC conversion**: detection and conversion of EAC3 audio (TV-compatible)
- 📦 **Track embedding**: automatic embedding of external .mka and .ass/.srt into MKV
- ⚡ **Conditional execution**: preprocessing runs only when needed

### Core Features
- 📂 **Automatic recognition** of series titles via OpenAI API
- 🎬 **Media file merging**: video + audio tracks + subtitles into one MKV
- 🏷️ **Plex-compatible names**: automatic renaming to standard `Series Title - S01E01.mkv`
- 📁 **Proper structure**: creates directories `Series Title (Year)/Season 01/`
- 🔍 **File validation**: checks created files using MediaInfo
- 🎭 **Subtitle support**: detection and marking of tracks (Animevod, Crunchyroll)
- ♻️ **Deduplication**: automatic removal of duplicate subtitles

### Architecture
- 🧩 **Modular structure**: separation into processors, models, utils
- 🧪 **Testability**: each processor is a separate module
- 🔧 **Extensibility**: easy to add new processors

## Requirements

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
OPENAI_API_KEY=your-api-key-here
```

## Usage

```bash
# Interactive mode
python media_organizer.py

# With directory specified
python media_organizer.py /path/to/series/directory
```

## Workflow

1. **Directory Analysis** - parse title and metadata from folder name
2. **File Scanning** - search for video, audio and subtitles
3. **Organization** - group files by episodes
4. **Preprocessing** (NEW) - conditional processing:
   - Convert AVI → MKV (if .avi files exist)
   - Convert EAC3 → AAC (if EAC3 detected)
   - Embed external tracks (if .mka/.ass/.srt exist)
5. **AI Recognition** - determine official series title
6. **Confirmation** - interactive correction if needed
7. **Final Merging** - create final MKV files
8. **Validation** - check created files (duration, tracks, codecs)
9. **Cleanup** - remove temporary files

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

## Validation

After processing, automatic validation of all created files runs:

- ✅ Check for video/audio tracks
- ⏱️ Duration check (protection from broken files)
- 📊 Display codecs and resolution
- 💾 File sizes
- ⚠️ Warnings about potential issues

## License

MIT
