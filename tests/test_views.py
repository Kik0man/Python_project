from unittest.mock import patch

import pandas as pd

from src.views import home_page


def test_home_page_success() -> None:
    """Тест успешного выполнения главной страницы."""
    test_data = pd.DataFrame(
        {"Номер карты": ["1111222233334444"], "Дата операции": ["01.01.2024 10:00:00"], "Сумма операции": [-1000]}
    )

    with patch("src.views.pd.read_excel", return_value=test_data):
        with patch("src.views.load_user_settings", return_value={"user_currencies": [], "user_stocks": []}):
            with patch("src.views.get_greeting", return_value="Привет"):
                with patch("src.views.get_card_stats", return_value=[{"last_digits": "4444"}]):
                    with patch("src.views.get_top_transactions", return_value=[]):
                        with patch("src.views.get_exchange_rates", return_value=[]):
                            with patch("src.views.get_stock_prices", return_value=[]):
                                result = home_page("2024-01-15 12:00:00")
                                assert "greeting" in result


def test_home_page_file_not_found() -> None:
    """Тест обработки ошибки при отсутствии файла."""
    with patch("src.views.pd.read_excel", side_effect=FileNotFoundError):
        result = home_page("2024-01-15 12:00:00")
        assert "error" in result


def test_home_page_general_error() -> None:
    """Тест обработки общей ошибки."""
    with patch("src.views.pd.read_excel", side_effect=Exception("Test error")):
        result = home_page("2024-01-15 12:00:00")
        assert "error" in result


def test_home_page_empty_data() -> None:
    """Тест главной страницы с пустыми данными."""
    df = pd.DataFrame(columns=["Номер карты", "Дата операции", "Сумма операции"])

    with patch("src.views.pd.read_excel", return_value=df):
        with patch("src.views.load_user_settings", return_value={}):
            result = home_page("2024-01-15 12:00:00")
            assert "greeting" in result


def test_home_page_with_currencies() -> None:
    """Тест главной страницы с валютами."""
    df = pd.DataFrame(
        {"Номер карты": ["1111222233334444"], "Дата операции": ["01.01.2024 10:00:00"], "Сумма операции": [-1000]}
    )

    with patch("src.views.pd.read_excel", return_value=df):
        with patch("src.views.load_user_settings", return_value={"user_currencies": ["USD"], "user_stocks": ["AAPL"]}):
            with patch("src.views.get_greeting", return_value="Привет"):
                with patch("src.views.get_card_stats", return_value=[]):
                    with patch("src.views.get_top_transactions", return_value=[]):
                        with patch("src.views.get_exchange_rates", return_value=[{"currency": "USD", "rate": 90.5}]):
                            with patch("src.views.get_stock_prices", return_value=[{"stock": "AAPL", "price": 150.0}]):
                                result = home_page("2024-01-15 12:00:00")
                                assert "currency_rates" in result
                                assert "stock_prices" in result
