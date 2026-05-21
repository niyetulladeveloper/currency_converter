"""Работа с ExchangeRate-API и конвертация валют."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from cache import get_cached_rates, set_cached_rates

# Загружаем .env из корня проекта
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

API_BASE = "https://v6.exchangerate-api.com/v6"
REQUEST_TIMEOUT = 15


class ConverterError(Exception):
    """Базовая ошибка конвертера."""


class ConfigError(ConverterError):
    """Ошибка конфигурации (API key)."""


class NetworkError(ConverterError):
    """Сетевая ошибка."""


class CurrencyError(ConverterError):
    """Неверный код валюты."""


def get_api_key() -> str:
    """Возвращает API-ключ из .env."""
    key = os.getenv("API_KEY", "").strip()
    if not key or key == "your_key_here":
        raise ConfigError(
            "API_KEY не задан. Скопируйте .env.example в .env и укажите ключ "
            "с https://www.exchangerate-api.com/"
        )
    return key


def _request_json(url: str) -> dict[str, Any]:
    """GET-запрос с обработкой ошибок."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.ConnectionError as e:
        raise NetworkError("Нет подключения к интернету.") from e
    except requests.Timeout as e:
        raise NetworkError("Превышено время ожидания ответа API.") from e
    except requests.RequestException as e:
        raise NetworkError(f"Ошибка запроса: {e}") from e

    if response.status_code == 401:
        raise ConfigError("Неверный API_KEY. Проверьте ключ в .env")
    if response.status_code == 403:
        raise ConfigError("Доступ запрещён. Проверьте лимиты или ключ API.")
    if response.status_code >= 500:
        raise NetworkError(f"Сервер API недоступен (HTTP {response.status_code}).")

    try:
        data = response.json()
    except ValueError as e:
        raise NetworkError("Некорректный ответ API (не JSON).") from e

    if data.get("result") == "error":
        error_type = data.get("error-type", "unknown")
        if error_type == "invalid-key":
            raise ConfigError("Неверный API_KEY.")
        if error_type in ("unsupported-code", "malformed-request"):
            raise CurrencyError(f"Ошибка API: {error_type}")
        raise ConverterError(f"Ошибка API: {error_type}")

    return data


def fetch_rates(base: str, use_cache: bool = True) -> dict[str, float]:
    """
    Получает курсы относительно base (1 base = X target).
    Использует cache.json при актуальном TTL.
    """
    base = base.upper()

    if use_cache:
        cached = get_cached_rates(base)
        if cached is not None:
            return cached

    api_key = get_api_key()
    url = f"{API_BASE}/{api_key}/latest/{base}"
    data = _request_json(url)

    rates_raw = data.get("conversion_rates")
    if not rates_raw:
        raise ConverterError("API не вернул курсы валют.")

    rates = {k.upper(): float(v) for k, v in rates_raw.items()}
    set_cached_rates(base, rates)
    return rates


def fetch_supported_codes() -> list[str]:
    """Список поддерживаемых кодов валют."""
    api_key = get_api_key()
    url = f"{API_BASE}/{api_key}/codes"
    data = _request_json(url)

    codes = data.get("supported_codes")
    if not codes:
        # fallback: ключи из latest USD
        rates = fetch_rates("USD")
        return sorted(rates.keys())

    # API возвращает [["USD", "US Dollar"], ...]
    return sorted(code[0].upper() for code in codes if code)


def validate_currency(code: str, available: dict[str, float] | list[str] | None = None) -> str:
    """Проверяет код валюты и возвращает его в верхнем регистре."""
    code = code.upper().strip()
    if len(code) != 3 or not code.isalpha():
        raise CurrencyError(f"Некорректный код валюты: {code}")

    if available is not None:
        if isinstance(available, dict):
            keys = available.keys()
        else:
            keys = available
        if code not in keys:
            raise CurrencyError(f"Валюта не поддерживается: {code}")

    return code


def convert_amount(
    amount: float,
    from_currency: str,
    to_currencies: list[str],
) -> dict[str, float]:
    """
    Конвертирует amount из from_currency в одну или несколько валют.
    Возвращает {TO: converted_amount}.
    """
    if amount < 0:
        raise ConverterError("Сумма не может быть отрицательной.")

    from_currency = from_currency.upper()
    to_list = [c.upper() for c in to_currencies]

    if from_currency in to_list and len(to_list) == 1:
        return {from_currency: amount}

    rates = fetch_rates(from_currency)

    for code in [from_currency, *to_list]:
        validate_currency(code, rates)

    results: dict[str, float] = {}
    for to_curr in to_list:
        if to_curr == from_currency:
            results[to_curr] = amount
            continue
        rate = rates.get(to_curr)
        if rate is None:
            raise CurrencyError(f"Курс для {to_curr} не найден.")
        results[to_curr] = amount * rate

    return results
