import logging
from typing import Any, Dict

import pandas as pd

from src.utils import (get_card_stats, get_exchange_rates, get_greeting, get_stock_prices, get_top_transactions,
                       load_user_settings)

# Логгер для этого модуля
logger = logging.getLogger(__name__)


def home_page(date_str: str) -> Dict[str, Any]:
    """
    Главная функция страницы.

    Args:
        date_str: Дата в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        Словарь с данными для отображения на главной странице
    """
    logger.info(f"=== Обработка запроса для даты: {date_str} ===")

    try:
        # Загружаем данные операций
        logger.info("Загрузка данных операций...")
        df = pd.read_excel("data/operations.xlsx")
        logger.info(f"Загружено {len(df)} записей")

        # Загружаем настройки
        logger.info("Загрузка пользовательских настроек...")
        settings = load_user_settings()

        # Формируем ответ
        logger.info("Формирование ответа...")
        response = {
            "greeting": get_greeting(date_str),
            "cards": get_card_stats(df, date_str),
            "top_transactions": get_top_transactions(df, date_str),
            "currency_rates": get_exchange_rates(settings.get("user_currencies", [])),
            "stock_prices": get_stock_prices(settings.get("user_stocks", [])),
        }

        logger.info("=== Запрос успешно обработан ===")
        return response

    except FileNotFoundError:
        logger.error("Файл operations.xlsx не найден!")
        return {"error": "Файл данных не найден"}
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return {"error": str(e)}
