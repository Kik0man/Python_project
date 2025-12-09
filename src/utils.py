import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_user_settings() -> Any:
    """Загружает настройки пользователя из JSON файла."""
    try:
        with open("user_settings.json", "r") as f:
            settings = json.load(f)
        logger.info(f"Настройки загружены: {settings}")
        return settings
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        return {"user_currencies": [], "user_stocks": []}


def get_greeting(date_str: str) -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    try:
        hour = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").hour
        if 5 <= hour < 12:
            return "Доброе утро"
        elif 12 <= hour < 18:
            return "Добрый день"
        elif 18 <= hour < 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"
    except Exception as e:
        logger.error(f"Ошибка в определении приветствия: {e}")
        return "Добрый день"


def get_card_stats(df: pd.DataFrame, date_str: str) -> List[Dict[str, Any]]:
    """Считает статистику по картам за период с начала месяца."""
    logger.info(f"Рассчет статистики по картам для даты: {date_str}")
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_of_month = target_date.replace(day=1, hour=0, minute=0, second=0)

        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        filtered = df[(df["Дата операции"] >= start_of_month) & (df["Дата операции"] <= target_date)]

        card_stats = []
        for card in filtered["Номер карты"].dropna().unique():
            card_df = filtered[filtered["Номер карты"] == card]
            expenses = card_df[card_df["Сумма операции"] < 0]["Сумма операции"].sum()
            total_spent = round(abs(expenses), 2)
            cashback = round(total_spent / 100, 2)  # 1 рубль на каждые 100 рублей

            card_stats.append({"last_digits": str(card)[-4:], "total_spent": total_spent, "cashback": cashback})

        logger.info(f"Найдено {len(card_stats)} карт")
        return card_stats

    except Exception as e:
        logger.error(f"Ошибка расчета статистики карт: {e}")
        return []


def get_top_transactions(df: pd.DataFrame, date_str: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """Находит топ-N транзакций по абсолютной сумме платежа."""
    logger.info(f"Поиск топ-{top_n} транзакций для даты: {date_str}")
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_of_month = target_date.replace(day=1, hour=0, minute=0, second=0)

        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        filtered = df[(df["Дата операции"] >= start_of_month) & (df["Дата операции"] <= target_date)].copy()

        # Добавляем абсолютную сумму для сортировки
        filtered["abs_amount"] = filtered["Сумма операции"].abs()

        # Сортируем по абсолютной сумме (по убыванию)
        top = filtered.nlargest(top_n, "abs_amount")

        result = []
        for _, row in top.iterrows():
            result.append(
                {
                    "date": row["Дата операции"].strftime("%d.%m.%Y"),
                    "amount": row["Сумма операции"],
                    "category": str(row.get("Категория", "Не указана")),
                    "description": str(row.get("Описание", "Без описания")),
                }
            )

        logger.info(f"Найдено {len(result)} транзакций")
        return result

    except Exception as e:
        logger.error(f"Ошибка поиска топовых транзакций: {e}")
        return []


def get_exchange_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """Получает курсы валют через API."""
    logger.info(f"Получение курсов валют: {currencies}")
    rates = []

    for currency in currencies:
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/RUB", timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data["rates"].get(currency)
                if rate:
                    rates.append({"currency": currency, "rate": round(rate, 2)})
                    logger.info(f"Курс {currency}: {rate}")
                else:
                    logger.warning(f"Курс {currency} не найден в ответе")
            else:
                logger.warning(f"Ошибка API для валюты {currency}: статус {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка получения курса {currency}: {e}")

    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """Получает цены акций через API."""
    logger.info(f"Получение цен акций: {stocks}")
    prices = []
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    for stock in stocks:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={api_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price_str = data.get("Global Quote", {}).get("05. price")
                if price_str:
                    prices.append({"stock": stock, "price": round(float(price_str), 2)})
                    logger.info(f"Цена {stock}: {price_str}")
                else:
                    logger.warning(f"Цена для {stock} не найдена")
            else:
                logger.warning(f"Ошибка API для акции {stock}: статус {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка получения цены {stock}: {e}")

    return prices
