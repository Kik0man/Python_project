import json
from typing import Any
from unittest.mock import patch

import pandas as pd

from src.services import load_data, main_search, search_in_excel, show_results, simple_search


def test_simple_search_found() -> None:
    """Тест успешного поиска транзакций."""
    transactions = [{"Описание": "Магнит", "Категория": "Супермаркеты", "Сумма операции": -1000}]

    result = simple_search("магнит", transactions)
    assert result["status"] == "success"
    assert result["found"] == 1


def test_simple_search_not_found() -> None:
    """Тест поиска без результатов."""
    transactions = [{"Описание": "Пятерочка", "Категория": "Супермаркеты", "Сумма операции": -1000}]

    result = simple_search("магнит", transactions)
    assert result["status"] == "success"
    assert result["found"] == 0


def test_simple_search_empty_query() -> None:
    """Тест поиска с пустым запросом."""
    result = simple_search("", [])
    assert result["status"] == "error"


def test_simple_search_no_data() -> None:
    """Тест поиска без данных."""
    result = simple_search("магнит", [])
    assert result["status"] == "error"


def test_load_data_success() -> None:
    """Тест успешной загрузки данных."""
    with patch("src.services.pd.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame({"Описание": ["Тест"]})
        result = load_data()
        assert len(result) == 1


def test_load_data_error() -> None:
    """Тест ошибки при загрузке данных."""
    with patch("src.services.pd.read_excel", side_effect=Exception("Error")):
        result = load_data()
        assert result == []


def test_search_in_excel() -> None:
    """Тест поиска в Excel файле."""
    with patch("src.services.load_data") as mock_load:
        mock_load.return_value = [{"Описание": "Магнит", "Категория": "Супермаркеты"}]

        result_json = search_in_excel("магнит")
        result = json.loads(result_json)
        assert result["status"] == "success"


def test_load_data_filepath() -> None:
    """Тест загрузки данных с указанием пути к файлу."""
    with patch("src.services.pd.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame({"Описание": ["Тест"]})
        result = load_data("custom/path/file.xlsx")
        assert len(result) == 1


def test_search_in_excel_no_data() -> None:
    """Тест поиска в Excel без данных."""
    with patch("src.services.load_data", return_value=[]):
        result_json = search_in_excel("тест")
        result = json.loads(result_json)
        assert result["status"] == "error"


def test_show_results_error() -> None:
    """Тест отображения результатов с ошибкой."""
    result = {"status": "error", "message": "Тестовая ошибка"}
    show_results(result)


def test_show_results_no_transactions() -> None:
    """Тест отображения результатов без транзакций."""
    result = {"status": "success", "query": "тест", "found": 0, "total": 100, "transactions": []}
    show_results(result)


def test_show_results_many_transactions() -> None:
    """Тест отображения большого количества транзакций."""
    transactions = []
    for i in range(15):  # Больше 10
        transactions.append(
            {
                "Дата операции": f"2024-01-{i + 1:02d}",
                "Описание": f"Транзакция {i}",
                "Сумма операции": -100 * (i + 1),
                "Категория": "Тест",
            }
        )

    result = {"status": "success", "query": "тест", "found": 15, "total": 100, "transactions": transactions}

    show_results(result)


def test_main_search_exit(monkeypatch: Any) -> None:
    """Тест выхода из main_search."""
    inputs = ["выход"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    with patch("src.services.load_data", return_value=[{"Описание": "Тест"}]):
        main_search()


def test_main_search_empty_query(monkeypatch: Any) -> None:
    """Тест main_search с пустым запросом."""
    inputs = ["", "выход"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    with patch("src.services.load_data", return_value=[{"Описание": "Тест"}]):
        main_search()


def test_main_search_no_data() -> None:
    """Тест main_search без данных."""
    with patch("src.services.load_data", return_value=[]):
        # Просто проверяем, что функция не падает
        try:
            main_search()
        except SystemExit:
            pass
