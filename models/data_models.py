"""
Data models для Media Organizer
"""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field


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


@dataclass
class PreprocessingResult:
    """Результат preprocessing операций"""
    file_path: Path
    operations_applied: List[str] = field(default_factory=list)
    avi_converted: bool = False
    eac3_converted: bool = False
    tracks_embedded: bool = False
    success: bool = True
    error_message: Optional[str] = None
