"""Локальный кэш курсов валют (TTL 1 час)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent
CACHE_FILE = PROJECT_ROOT / "cache.json"
CACHE_TTL_SECONDS = 3600  # 1 час


def _load_cache_file() -> dict[str, Any]:
    """Читает cache.json или возвращает пустую структуру."""
    if not CACHE_FILE.exists():
        return {"entries": {}}
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if "entries" not in data:
            return {"entries": {}}
        return data
    except (json.JSONDecodeError, OSError):
        return {"entries": {}}


def _save_cache_file(data: dict[str, Any]) -> None:
    """Сохраняет cache.json."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_cached_rates(base: str) -> dict[str, float] | None:
    """
    Возвращает словарь курсов для базовой валюты, если кэш актуален.
    Иначе None.
    """
    base = base.upper()
    data = _load_cache_file()
    entry = data["entries"].get(base)
    if not entry:
        return None

    fetched_at = entry.get("fetched_at", 0)
    if time.time() - fetched_at > CACHE_TTL_SECONDS:
        return None

    rates = entry.get("rates")
    if not isinstance(rates, dict):
        return None

    return {k.upper(): float(v) for k, v in rates.items()}


def set_cached_rates(base: str, rates: dict[str, float]) -> None:
    """Записывает курсы в кэш с меткой времени."""
    base = base.upper()
    data = _load_cache_file()
    data["entries"][base] = {
        "fetched_at": time.time(),
        "rates": rates,
    }
    _save_cache_file(data)


def clear_cache() -> None:
    """Удаляет файл кэша."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
