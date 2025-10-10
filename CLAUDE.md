# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Organizer for Plex v4.0 - AI-powered tool for preparing TV series and anime for Plex Media Server.

**Key Features:**
- **AI-powered recognition**: GPT-5 with web search for accurate title/year detection
- **Smart pattern recognition**: AI-based file and directory parsing (no regex limitations)
- **Preprocessing pipeline**: AVI→MKV, EAC3→AAC, track embedding
- Media file merging into Plex-compatible structure
- Validation with MediaInfo
- Modular architecture for easy extension

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

### Modular Structure

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
├── config/
│   └── prompts.py              # AI prompt templates
└── utils/
    └── patterns.py             # AI-powered pattern recognition
```

**Data Models** (models/data_models.py):
- `MediaFile` - file information
- `SeriesInfo` - series metadata
- `MediaValidationResult` - validation results
- `PreprocessingResult` - preprocessing results

**Main Orchestrator** (media_organizer.py):
- Coordinates all processors
- Manages episode_map
- Handles user input

**AI Integration** (processors/ai_analyzer.py, utils/patterns.py):
- GPT-5 with web search for main analysis
- GPT-4o-mini for simple pattern recognition
- No fallback to regex - OpenAI required

### Processing Workflow

1. **Directory Analysis** (utils/patterns.py):
   - AI-powered parsing of directory name
   - Extracts: title, season, release group, year
   - Uses GPT-4o-mini for fast, accurate parsing

2. **File Scanning** (processors/scanner.py):
   - Recursively scans directory
   - Classifies files: video (.mkv, .mp4, .avi), audio (.mka, .aac), subtitle (.srt, .ass)
   - Extracts episode numbers from filenames (S01E01 pattern - regex kept for reliability)
   - AI-powered subtitle track detection (utils/patterns.py)
   - Identifies duplicate subtitles

3. **File Organization** (media_organizer.py):
   - Groups files into `episode_map` by episode numbers
   - Filters duplicate subtitles

4. **Preprocessing** (processors/preprocessor.py):
   - **Conditional**: runs only when needed
   - **AVI Conversion**: .avi → .mkv using ffmpeg (remux)
   - **EAC3 Conversion**: detects EAC3, converts to AAC
   - **Track Embedding**: embeds external .mka and .ass/.srt into MKV
   - Creates temporary files in `.preprocessing_temp/` (inside working directory)

5. **AI Analysis** (processors/ai_analyzer.py):
   - Uses OpenAI **GPT-5 with web search** for accurate title/year recognition
   - Searches TVDB/TMDB/IMDb/MyAnimeList for official titles
   - Confirms season number and episode count
   - **No fallback** - requires OpenAI API key

6. **User Confirmation** (media_organizer.py):
   - Interactive confirmation/correction of metadata
   - Options: accept, correct title, correct all

7. **Final Merging** (processors/merger.py):
   - Uses `mkvmerge` for final merging
   - Sets correct subtitle track names
   - Output format: `Series Title - S01E01.mkv`

8. **Output Structure** (media_organizer.py):
   - Creates Plex-compatible structure: `Series Title (Year)/Season 01/`

9. **Validation** (processors/validator.py):
   - Analyzes created MKV files with MediaInfo
   - Checks: duration, track count, codecs, resolution
   - Identifies errors and warnings

10. **Cleanup**:
    - Removes temporary preprocessing files

## Important Notes

### External Dependencies

**Required:**
- **OpenAI API key** - for AI-powered recognition (GPT-5, GPT-4o-mini)
- **mkvmerge** (MKVToolNix) - for merging media files
- **mediainfo** - for analysis and validation
- **ffmpeg** - for AVI→MKV and EAC3→AAC conversion

### AI-Powered Pattern Recognition
- **Directory parsing**: AI-based (GPT-4o-mini) - handles any format
- **Subtitle detection**: AI-based (GPT-4o-mini) - recognizes any studio/track name
- **Episode numbers**: Regex `[Ss](\d+)[Ee](\d+)` - kept for reliability
- **Series analysis**: GPT-5 with web search - searches TVDB/TMDB/IMDb/MyAnimeList

### Preprocessing Features
- **AVI Detection**: by `.avi` extension (processors/avi_converter.py)
- **EAC3 Detection**: via MediaInfo analysis (processors/audio_converter.py)
- **Track Embedding**: embeds external .mka and .ass/.srt (processors/track_embedder.py)
- **Temp files location**: `.preprocessing_temp/` inside working directory (same disk)

### Key Modules
- `processors/ai_analyzer.py` - GPT-5 with web search for series recognition
- `utils/patterns.py` - AI-powered pattern recognition (directory, subtitles)
- `config/prompts.py` - centralized AI prompt templates
- `processors/preprocessor.py` - preprocessing coordinator, manages temp files
- `processors/audio_converter.py` - detects EAC3 tracks, extracts, converts to AAC, replaces
- `processors/avi_converter.py` - ffmpeg remux (no video re-encoding)
- `processors/scanner.py` - scanning with subtitle deduplication
- `processors/validator.py` - validation via MediaInfo

## Development Guidelines

### Environment
- **ALWAYS** activate venv: `source venv/bin/activate`
- Never use global Python packages
- Future-proof for Docker deployment

### Configuration Management
- **API keys and secrets**: in `.env` file (never commit)
- **AI prompts**: in `config/prompts.py` for flexibility (multiline prompts don't work well in .env)
- **Important parameters**: in `.env` file:
  - `OPENAI_MODEL` - main model (gpt-5 recommended)
  - `OPENAI_REASONING_EFFORT` - GPT-5 reasoning level (minimal/low/medium/high)
  - `OPENAI_SIMPLE_MODEL` - for pattern recognition (gpt-4o-mini recommended)
  - `AAC_BITRATE` - audio conversion quality
- **Unimportant parameters**: can be hardcoded in code
- `.env` is in `.gitignore` - never commit secrets
- **Always add comments** to `.env` file explaining each parameter

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

### Code Organization Principles
- **Organize for maintainability**: Structure the project to make it easy for Claude to navigate and maintain
- **Only Claude writes code**: Design code to be comfortable for AI-assisted development
- **Leverage AI analysis**: Use OpenAI API extensively for complex pattern recognition and data extraction
  - Title recognition with web search (GPT-5)
  - Directory/file parsing (GPT-4o-mini)
  - Subtitle track detection (GPT-4o-mini)
  - Any complex logic where AI can outperform regex
- **No regex fallbacks**: OpenAI API is required - if unavailable, process stops with clear error
- **Self-documenting code**: Write clear, self-explanatory code that's easy to understand later

### Language Policy

**Communication with User:**
- **Always communicate in Russian** when talking to the user
- Use Russian for explanations, questions, status updates, and all user interaction
- This applies regardless of documentation language

**Documentation and Code:**
- **CLAUDE.md**: Must be in English (for Claude Code compatibility)
- **README.md**: Must be in English (for open-source accessibility)
- **Code comments**: Must be in English (docstrings, inline comments)
- **User-facing messages**: Should be in Russian (print statements, interactive prompts, error messages)
- **AI prompts**: Should be in Russian (better understanding by Russian-speaking AI models)
