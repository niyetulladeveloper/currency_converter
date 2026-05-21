"""История конвертаций в history.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
HISTORY_FILE = PROJECT_ROOT / "history.json"
MAX_HISTORY_ENTRIES = 200


def _load() -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_entry(
    amount: float,
    from_currency: str,
    conversions: dict[str, float],
) -> dict[str, Any]:
    """Добавляет запись в историю и возвращает её."""
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "amount": amount,
        "from": from_currency.upper(),
        "conversions": {k.upper(): round(v, 4) for k, v in conversions.items()},
    }
    entries = _load()
    entries.insert(0, entry)
    _save(entries[:MAX_HISTORY_ENTRIES])
    return entry


def get_history(limit: int = 50) -> list[dict[str, Any]]:
    """Последние записи истории."""
    return _load()[:limit]


def clear_history() -> int:
    """Очищает историю. Возвращает число удалённых записей."""
    entries = _load()
    count = len(entries)
    _save([])
    return count
