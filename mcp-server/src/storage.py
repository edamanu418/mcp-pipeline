from pathlib import Path
from typing import Any

from .core.json_storage import JsonStorage

DATA_FILE = Path("pipeline_data.json")


def _get_storage() -> JsonStorage:
    return JsonStorage(DATA_FILE, "pipelines")


def load() -> dict[str, Any]:
    return _get_storage().load()


def save(data: dict[str, Any]) -> None:
    _get_storage().save(data)
