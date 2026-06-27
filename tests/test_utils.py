from unittest.mock import mock_open, patch

import pandas as pd

from src.utils import (get_card_stats, get_exchange_rates, get_greeting, get_stock_prices, get_top_transactions,
                       load_user_settings)


def test_load_user_settings_success() -> None:
    """Тест успешной загрузки настроек пользователя."""
    with patch("builtins.open", mock_open(read_data='{"user_currencies": ["USD"]}')):
        result = load_user_settings()
        assert "user_currencies" in result
        assert result["user_currencies"] == ["USD"]


def test_load_user_settings_error() -> None:
    """Тест ошибки при загрузке настроек пользователя."""
    with patch("builtins.open", side_effect=Exception("File error")):
        result = load_user_settings()
        assert result == {"user_currencies": [], "user_stocks": []}


def test_get_greeting_morning() -> None:
    """Тест приветствия для утреннего времени."""
    result = get_greeting("2024-01-15 08:00:00")
    assert result == "Доброе утро"


def test_get_greeting_day() -> None:
    """Тест приветствия для дневного времени."""
    result = get_greeting("2024-01-15 14:00:00")
    assert result == "Добрый день"


def test_get_greeting_evening() -> None:
    """Тест приветствия для вечернего времени."""
    result = get_greeting("2024-01-15 20:00:00")
    assert result == "Добрый вечер"


def test_get_greeting_night() -> None:
    """Тест приветствия для ночного времени."""
    result = get_greeting("2024-01-15 02:00:00")
    assert result == "Доброй ночи"


def test_get_greeting_error() -> None:
    """Тест приветствия при ошибке в дате."""
    result = get_greeting("неправильная дата")
    assert result == "Добрый день"


def test_get_card_stats() -> None:
    """Тест расчета статистики по картам."""
    df = pd.DataFrame(
        {"Номер карты": ["1111222233334444"], "Дата операции": ["01.01.2024 10:00:00"], "Сумма операции": [-1000]}
    )

    result = get_card_stats(df, "2024-01-15 12:00:00")
    assert len(result) > 0


def test_get_top_transactions() -> None:
    """Тест получения топовых транзакций."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.01.2024 10:00:00"],
            "Сумма операции": [-1000],
            "Категория": ["Еда"],
            "Описание": ["Магазин"],
        }
    )

    result = get_top_transactions(df, "2024-01-15 12:00:00")
    assert len(result) == 1


def test_get_exchange_rates_empty() -> None:
    """Тест получения курсов валют с пустым списком."""
    result = get_exchange_rates([])
    assert result == []


def test_get_stock_prices_empty() -> None:
    """Тест получения цен акций с пустым списком."""
    result = get_stock_prices([])
    assert result == []


def test_get_exchange_rates_api_error() -> None:
    """Тест получения курсов валют при ошибке API."""
    with patch("src.utils.requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        result = get_exchange_rates(["USD", "EUR"])
        assert result == []


def test_get_exchange_rates_timeout() -> None:
    """Тест таймаута при получении курсов валют."""
    with patch("src.utils.requests.get", side_effect=Exception("Timeout")):
        result = get_exchange_rates(["USD"])
        assert result == []


def test_get_stock_prices_api_error() -> None:
    """Тест получения цен акций при ошибке API."""
    with patch("src.utils.requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        result = get_stock_prices(["AAPL"])
        assert result == []


def test_get_stock_prices_timeout() -> None:
    """Тест таймаута при получении цен акций."""
    with patch("src.utils.requests.get", side_effect=Exception("Timeout")):
        result = get_stock_prices(["AAPL"])
        assert result == []


def test_get_card_stats_empty() -> None:
    """Тест статистики по картам с пустыми данными."""
    df = pd.DataFrame(columns=["Номер карты", "Дата операции", "Сумма операции"])
    result = get_card_stats(df, "2024-01-15 12:00:00")
    assert result == []


def test_get_card_stats_error() -> None:
    """Тест статистики по картам с ошибкой."""
    df = pd.DataFrame({"Номер карты": ["1111"], "Дата операции": ["неправильная дата"]})
    result = get_card_stats(df, "2024-01-15 12:00:00")
    assert result == []


def test_get_top_transactions_empty() -> None:
    """Тест топ транзакций с пустыми данными."""
    df = pd.DataFrame(columns=["Дата операции", "Сумма операции", "Категория", "Описание"])
    result = get_top_transactions(df, "2024-01-15 12:00:00")
    assert result == []


def test_get_top_transactions_error() -> None:
    """Тест топ транзакций с ошибкой."""
    df = pd.DataFrame({"Дата операции": ["неправильная дата"]})
    result = get_top_transactions(df, "2024-01-15 12:00:00")
    assert result == []
