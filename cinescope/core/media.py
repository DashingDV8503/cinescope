from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class MediaStatus(Enum):
    """Enumeration for the user's watch status."""
    WATCHING = 'Watching'
    COMPLETED = 'Completed'
    PLAN_TO_WATCH = 'Plan to Watch'
    DROPPED = 'Dropped'

@dataclass
class Episode:
    episode_number: int
    name: str
    vote_average: float

@dataclass
class SeasonProgress:
    episodesWatched: int
    totalEpisodes: int
    vote_average: Optional[float] = None
    episodes: Optional[List[Episode]] = field(default_factory=list)

@dataclass
class Media:
    """The core data class for a movie or TV show."""
    # Core attributes from the documentation
    id: int
    title: str
    year: str
    type: str  # 'movie' or 'series'
    poster_path: Optional[str]
    plot: str
    vote_average: float
    status: MediaStatus
    genres: List[Dict[str, Any]] = field(default_factory=list)

    # Optional IDs
    imdb_id: Optional[str] = None
    tvdb_id: Optional[int] = None
    
    # Movie-specific attributes
    runtime: Optional[int] = None

    # Series-specific attributes
    episode_run_time: Optional[List[int]] = field(default_factory=list)
    number_of_seasons: Optional[int] = None
    production_status: Optional[str] = None
    seasons: Optional[Dict[str, SeasonProgress]] = field(default_factory=dict)