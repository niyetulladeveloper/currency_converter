# Currency Converter CLI

Конвертер валют в командной строке на базе [ExchangeRate-API](https://www.exchangerate-api.com/) (бесплатный тариф).

## Возможности

- Конвертация между любыми поддерживаемыми валютами (USD, EUR, UZS, RUB, GBP, JPY и др.)
- Конвертация одной суммы сразу в несколько валют
- Список всех доступных кодов валют
- История операций в `history.json`
- Кэш курсов в `cache.json` на 1 час (меньше запросов к API)

## Требования

- Python 3.10+
- Ключ API (бесплатно, без карты): https://www.exchangerate-api.com/

## Установка

```bash
cd currency_converter
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Скопируйте файл окружения и укажите ключ:

```bash
copy .env.example .env
```

Откройте `.env` и замените значение:

```env
API_KEY=ваш_ключ_с_exchangerate-api.com
```

## Использование

```bash
# 100 USD → UZS
python main.py convert 100 USD UZS

# 50 EUR → USD, RUB, UZS, GBP одновременно
python main.py convert 50 EUR USD RUB UZS GBP

# Список валют
python main.py list

# История
python main.py history

# Очистить историю
python main.py history --clear
```

## Структура проекта

```
currency_converter/
├── main.py          # CLI (argparse + rich)
├── converter.py     # API и логика конвертации
├── cache.py         # Кэш курсов (1 час)
├── history.py       # История в JSON
├── .env             # API_KEY (не коммитить)
├── .env.example
├── .gitignore
├── cache.json       # создаётся автоматически
├── history.json     # создаётся автоматически
└── requirements.txt
```

## Обработка ошибок

Приложение сообщает понятные ошибки при:

- отсутствии или неверном `API_KEY`
- отсутствии интернета
- неверном коде валюты (не 3 буквы или не в списке API)
- недоступности сервера API

## Лицензия

Учебный проект. Используйте API в соответствии с условиями ExchangeRate-API.
