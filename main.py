#!/usr/bin/env python3
"""CLI конвертер валют — ExchangeRate-API + кэш + история."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

import converter
import history as history_module
from converter import (
    ConfigError,
    ConverterError,
    CurrencyError,
    NetworkError,
    convert_amount,
    fetch_supported_codes,
)

# Вывод в stdout — иначе в части терминалов Windows видна только строка "Python" от py.exe
console = Console()


def cmd_convert(args: argparse.Namespace) -> int:
    """Команда convert: сумма, исходная валюта, целевые валюты."""
    try:
        amount = float(args.amount.replace(",", "."))
    except ValueError:
        console.print("[red]Ошибка:[/] сумма должна быть числом.")
        return 1

    from_curr = args.from_currency.upper()
    to_currencies = [c.upper() for c in args.to_currencies]

    try:
        results = convert_amount(amount, from_curr, to_currencies)
    except (ConfigError, NetworkError, CurrencyError, ConverterError) as e:
        console.print(f"[red]Ошибка:[/] {e}")
        return 1

    # Таблица результатов
    table = Table(title="Конвертация валют", show_header=True, header_style="bold magenta")
    table.add_column("Из", style="cyan")
    table.add_column("В", style="green")
    table.add_column("Сумма", justify="right", style="bold yellow")
    table.add_column("Курс (1 →)", justify="right", style="dim")

    rates = None
    try:
        rates = converter.fetch_rates(from_curr)
    except ConverterError:
        pass

    for to_curr, converted in results.items():
        rate_str = "—"
        if rates and to_curr != from_curr and to_curr in rates:
            rate_str = f"{rates[to_curr]:,.6f}".rstrip("0").rstrip(".")
        elif to_curr == from_curr:
            rate_str = "1"

        table.add_row(
            from_curr,
            to_curr,
            f"{converted:,.2f}",
            rate_str,
        )

    console.print(table)
    console.print(
        f"\n[dim]Исходная сумма: {amount:,.2f} {from_curr}[/]"
    )

    history_module.add_entry(amount, from_curr, results)
    console.print("[dim]Запись добавлена в историю.[/]")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Список доступных валют."""
    try:
        codes = fetch_supported_codes()
    except (ConfigError, NetworkError, ConverterError) as e:
        console.print(f"[red]Ошибка:[/] {e}")
        return 1

    # Вывод в колонках по 8 кодов
    table = Table(
        title=f"Доступные валюты ({len(codes)})",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Код", style="green")

    for i, code in enumerate(codes, 1):
        table.add_row(str(i), code)

    console.print(table)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """Показать или очистить историю."""
    if args.clear:
        count = history_module.clear_history()
        console.print(f"[green]История очищена[/] ({count} записей удалено).")
        return 0

    entries = history_module.get_history()
    if not entries:
        console.print(Panel("[dim]История пуста. Выполните convert для добавления записей.[/]", title="История"))
        return 0

    table = Table(title="История конвертаций", show_lines=True)
    table.add_column("Дата", style="dim")
    table.add_column("Сумма", justify="right", style="yellow")
    table.add_column("Из", style="cyan")
    table.add_column("Результаты", overflow="fold")

    for entry in entries:
        conv_parts = [
            f"{curr} {val:,.2f}" for curr, val in entry.get("conversions", {}).items()
        ]
        table.add_row(
            entry.get("timestamp", "—"),
            f"{entry.get('amount', 0):,.2f}",
            entry.get("from", "—"),
            ", ".join(conv_parts),
        )

    console.print(table)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Конвертер валют (ExchangeRate-API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py convert 100 USD UZS
  python main.py convert 50 EUR USD RUB UZS
  python main.py list
  python main.py history
  python main.py history --clear
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="Конвертировать сумму")
    p_convert.add_argument("amount", help="Сумма (например 100)")
    p_convert.add_argument("from_currency", help="Исходная валюта (USD)")
    p_convert.add_argument(
        "to_currencies",
        nargs="+",
        help="Целевая валюта или несколько (UZS или USD RUB UZS)",
    )
    p_convert.set_defaults(func=cmd_convert)

    p_list = sub.add_parser("list", help="Список валют")
    p_list.set_defaults(func=cmd_list)

    p_hist = sub.add_parser("history", help="История конвертаций")
    p_hist.add_argument(
        "--clear",
        action="store_true",
        help="Очистить историю",
    )
    p_hist.set_defaults(func=cmd_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
