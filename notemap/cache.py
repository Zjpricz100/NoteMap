import hashlib
from pathlib import Path


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_path(data_dir: Path, subdir: str, hash: str, suffix: str) -> Path:
    return data_dir / subdir / f"{hash}{suffix}"
