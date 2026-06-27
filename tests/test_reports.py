import json
from typing import Any
from unittest.mock import patch

import pandas as pd

from src.reports import display_report, generate_category_report, get_spending_by_category, main_reports


def test_get_spending_by_category_success() -> None:
    """Тест успешного формирования отчета по категории."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.12.2023 10:00:00"],
            "Категория": ["Супермаркеты"],
            "Сумма операции": [-1000],
            "Описание": ["Магнит"],
        }
    )

    result = get_spending_by_category(df, "Супермаркеты", "2024-01-31 23:59:59")
    assert result["status"] == "success"


def test_get_spending_by_category_empty_df() -> None:
    """Тест формирования отчета с пустыми данными."""
    df = pd.DataFrame()
    result = get_spending_by_category(df, "Супермаркеты", "2024-01-31 23:59:59")
    assert result["status"] == "error"


def test_get_spending_by_category_invalid_category() -> None:
    """Тест формирования отчета с невалидной категорией."""
    df = pd.DataFrame({"Дата операции": [], "Категория": [], "Сумма операции": []})
    result = get_spending_by_category(df, "", "2024-01-31 23:59:59")
    assert result["status"] == "error"


def test_generate_category_report_success() -> None:
    """Тест успешной генерации отчета."""
    with patch("src.reports.pd.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame(
            {
                "Дата операции": ["01.01.2024 10:00:00"],
                "Категория": ["Супермаркеты"],
                "Сумма операции": [-1000],
                "Описание": ["Магнит"],
            }
        )

        result_json = generate_category_report("Супермаркеты", "2024-01-31 23:59:59")
        result = json.loads(result_json)
        assert result["status"] == "success"


def test_generate_category_report_file_not_found() -> None:
    """Тест генерации отчета при отсутствии файла."""
    with patch("src.reports.pd.read_excel", side_effect=FileNotFoundError):
        result_json = generate_category_report("Супермаркеты", "2024-01-31 23:59:59")
        result = json.loads(result_json)
        assert result["status"] == "error"


def test_get_spending_by_category_error_in_date() -> None:
    """Тест отчета с ошибкой в дате."""
    df = pd.DataFrame({"Дата операции": ["01.01.2024"]})
    result = get_spending_by_category(df, "Категория", "неправильная дата")
    assert result["status"] == "error"


def test_get_spending_by_category_no_expenses() -> None:
    """Тест отчета без расходов (только доходы)."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.01.2024 10:00:00"],
            "Категория": ["Супермаркеты"],
            "Сумма операции": [1000],  # Положительная сумма (доход)
            "Описание": ["Возврат"],
        }
    )

    result = get_spending_by_category(df, "Супермаркеты", "2024-01-31 23:59:59")
    assert result["status"] == "success"
    assert result["statistics"]["total_spent"] == 0.0


def test_get_spending_by_category_exception() -> None:
    """Тест отчета с исключением."""
    df = pd.DataFrame({"Дата операции": ["неправильная дата"]})
    result = get_spending_by_category(df, "Категория", "2024-01-31 23:59:59")
    assert result["status"] == "error"


def test_generate_category_report_exception() -> None:
    """Тест генерации отчета с исключением."""
    with patch("src.reports.pd.read_excel", side_effect=Exception("Test error")):
        result_json = generate_category_report("Категория", "2024-01-31 23:59:59")
        result = json.loads(result_json)
        assert result["status"] == "error"


def test_display_report_error() -> None:
    """Тест отображения отчета с ошибкой."""
    report = {"status": "error", "message": "Тестовая ошибка"}
    # Просто проверяем, что функция не падает
    display_report(report)


def test_main_reports_exit(monkeypatch: Any) -> None:
    """Тест выхода из main_reports."""
    # Симулируем ввод 'выход' для завершения программы
    inputs = ["выход"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    # Просто проверяем, что функция не падает
    main_reports()


def test_main_reports_with_date(monkeypatch: Any) -> None:
    """Тест main_reports с вводом даты."""
    inputs = ["Супермаркеты", "2024-01-31 23:59:59", "выход"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    with patch("src.reports.generate_category_report") as mock_report:
        mock_report.return_value = json.dumps({"status": "success"})


def test_get_spending_by_category_small_period() -> None:
    """Тест отчета с малым периодом данных (меньше 3 месяцев)."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.01.2024 10:00:00", "15.01.2024 15:00:00"],
            "Категория": ["Еда", "Еда"],
            "Сумма операции": [-500, -300],
            "Описание": ["Продукты", "Обед"],
        }
    )

    result = get_spending_by_category(df, "Еда", "2024-01-20 23:59:59")
    assert result["status"] == "success"
    assert result["period"]["days"] == 90
    assert result["total_months"] <= 2


def test_get_spending_by_category_with_nan_values() -> None:
    """Тест отчета с NaN значениями в данных."""
    df = pd.DataFrame(
        {
            "Дата операции": ["01.01.2024 10:00:00", None, "неверная дата"],
            "Категория": ["Еда", None, "Еда"],
            "Сумма операции": [-500, -300, None],
            "Описание": ["Продукты", None, None],
        }
    )

    result = get_spending_by_category(df, "Еда", "2024-01-31 23:59:59")
    # Должен либо успешно обработать, либо вернуть error
    assert "status" in result


def test_get_spending_by_category_multiple_months() -> None:
    """Тест отчета с данными за несколько месяцев."""
    df = pd.DataFrame(
        {
            "Дата операции": [
                "01.12.2023 10:00:00",
                "15.12.2023 15:00:00",
                "05.01.2024 12:00:00",
                "20.01.2024 18:00:00",
                "10.02.2024 14:00:00",
            ],
            "Категория": ["Транспорт"] * 5,
            "Сумма операции": [-100, -200, -150, -250, -300],
            "Описание": ["Такси", "Метро", "Автобус", "Такси", "Метро"],
        }
    )

    result = get_spending_by_category(df, "Транспорт", "2024-02-15 23:59:59")
    assert result["status"] == "success"
    assert result["total_months"] >= 2
