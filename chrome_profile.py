"""Recoverable maintenance helpers for the Selenium Chrome profile."""

from datetime import datetime
from pathlib import Path


CACHE_DIR_NAMES = {"Cache", "Code Cache", "GPUCache"}


def quarantine_cache_dirs(profile_dir: Path) -> Path | None:
    """Move Chrome cache directories aside while preserving profile data."""
    profile_dir = Path(profile_dir)
    cache_dirs = [
        child
        for path in profile_dir.glob("*")
        if path.is_dir()
        for child in path.glob("*")
        if child.is_dir() and child.name in CACHE_DIR_NAMES
    ]
    if not cache_dirs:
        return None

    backup_dir = profile_dir.parent / (
        f"{profile_dir.name}.cache-backup-"
        f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    backup_dir.mkdir(parents=True, exist_ok=False)
    for cache_dir in cache_dirs:
        destination = backup_dir / cache_dir.relative_to(profile_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        cache_dir.rename(destination)
    return backup_dir
