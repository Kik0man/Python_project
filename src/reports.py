import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_spending_by_category(df: pd.DataFrame, category: str, date_str: str) -> Dict[str, Any]:
    """Отчет о тратах по категории за трехмесячный период.
    Args:
        df: DataFrame с транзакциями
        category: Категория для анализа
        date_str: Дата конца периода в формате 'YYYY-MM-DD HH:MM:SS'
    Returns:
        JSON с тратами по категории за 3 месяца"""
    logger.info("=== Отчет по категории '{category}' на дату {date_str} ===")

    try:
        # 1. Проверяем входные данные
        if df.empty:
            logger.error("DataFrame пустой")
            return {"status": "error", "message": "Нет данных для анализа"}

        if not category or not isinstance(category, str):
            logger.error("Некорректная категория")
            return {"status": "error", "message": "Укажите категорию для анализа"}

        # 2. Определяем период (3 месяца назад от указанной даты)
        try:
            end_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            start_date = end_date - timedelta(days=90)  # 3 месяца назад
            logger.info(f"Период анализа: {start_date.date()} - {end_date.date()}")
        except ValueError as e:
            logger.error(f"Ошибка в формате даты: {e}")
            return {"status": "error", "message": f"Некорректный формат даты: {e}"}

        # 3. Преобразуем даты в DataFrame
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        # 4. Фильтруем данные по периоду и категории
        period_mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
        category_mask = df["Категория"].str.contains(category, case=False, na=False)

        filtered_df = df[period_mask & category_mask].copy()

        # 5. Фильтруем только расходы (отрицательные суммы)
        expenses_df = filtered_df[filtered_df["Сумма операции"] < 0].copy()
        expenses_df["Абсолютная сумма"] = expenses_df["Сумма операции"].abs()

        logger.info(f"Найдено {len(expenses_df)} транзакций по категории '{category}'")

        # 6. Группируем по месяцам
        expenses_df["Месяц"] = expenses_df["Дата операции"].dt.to_period("M")
        monthly_data = (
            expenses_df.groupby("Месяц")
            .agg({"Абсолютная сумма": "sum", "Сумма операции": "count"})
            .rename(columns={"Абсолютная сумма": "total_spent", "Сумма операци": "transactions_count"})  # Исправлено
        )

        # Преобразуем Period в строку
        monthly_data.index = monthly_data.index.astype(str)

        # 7. Считаем общую статистику
        total_spent = expenses_df["Абсолютная сумма"].sum()
        avg_monthly = monthly_data["total_spent"].mean() if not monthly_data.empty else 0
        total_transactions = len(expenses_df)

        # 8. Топ-5 самых крупных трат
        top_expenses = expenses_df.nlargest(5, "Абсолютная сумма")[["Дата операции", "Описание", "Сумма операции"]]
        top_expenses_list = []

        for _, row in top_expenses.iterrows():
            top_expenses_list.append(
                {
                    "date": row["Дата операции"].strftime("%d.%m.%Y %H:%M:%S"),
                    "description": str(row["Описание"]),
                    "amount": float(round(abs(row["Сумма операции"]), 2)),
                }
            )

        # 9. Формируем результат
        result = {
            "status": "success",
            "category": category,
            "period": {"start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d"), "days": 90},
            "statistics": {
                "total_spent": float(round(total_spent, 2)),
                "avg_monthly": float(round(avg_monthly, 2)),
                "transactions_count": int(total_transactions),
                "monthly_breakdown": monthly_data.to_dict(orient="index"),
            },
            "top_expenses": top_expenses_list,
            "total_months": len(monthly_data),
        }

        logger.info(f"Отчет сформирован. Потрачено: {total_spent:.2f} руб.")
        return result

    except Exception as e:
        logger.error(f"Ошибка формирования отчета: {e}")
        return {"status": "error", "message": str(e)}


def generate_category_report(category: str, date_str: str) -> Any:
    """
    Генерирует отчет по категории из файла данных.

    Args:
        category: Категория для анализа
        date_str: Дата конца периода (по умолчанию текущая)

    Returns:
        JSON строка с отчетом
    """
    try:
        # Если дата не указана, берем текущую
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d 23:59:59")

        # Загружаем данные
        filepath = "data/operations.xlsx"
        logger.info(f"Загрузка данных из {filepath}")
        df = pd.read_excel(filepath)

        # Генерируем отчет
        report = get_spending_by_category(df, category, date_str)

        # Возвращаем JSON
        return json.dumps(report, indent=2, ensure_ascii=False, default=str)

    except FileNotFoundError:
        logger.error("Файл data/operations.xlsx не найден")
        return json.dumps({"status": "error", "message": "Файл с данными не найден"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def main_reports() -> Any:
    """Интерактивный режим работы с отчетами."""
    print("📊 ОТЧЕТ 'ТРАТЫ ПО КАТЕГОРИИ'")
    print("=" * 50)

    # Примеры категорий из данных
    example_categories = [
        "Супермаркеты",
        "Фастфуд",
        "Транспорт",
        "Дом и ремонт",
        "Развлечения",
        "Связь",
        "Здоровье",
        "Одежда",
    ]

    print(f"\n💡 Примеры категорий: {', '.join(example_categories[:5])}...")
    print("   Или введите свою категорию")

    while True:
        print("\n" + "-" * 50)
        category = input("Введите категорию (или 'выход'): ").strip()

        if category.lower() in ["выход", "exit", "quit", "q"]:
            print("👋 До свидания!")
            break

        if not category:
            print("❌ Категория не может быть пустой")
            continue

        date_input = input("Введите дату конца периода [ГГГГ-ММ-ДД ЧЧ:ММ:СС] (Enter для текущей): ").strip()

        if not date_input:
            date_str = datetime.now().strftime("%Y-%m-%d 23:59:59")
            print(f"📅 Используется текущая дата: {date_str}")
        else:
            date_str = date_input

        print(f"\n📈 Формирую отчет по категории '{category}'...")

        # Генерируем отчет
        report_json = generate_category_report(category, date_str)

        try:
            report = json.loads(report_json)
            display_report(report)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print(f"Ответ: {report_json[:200]}...")


def display_report(report: Dict[str, Any]) -> Any:
    """Красиво отображает отчет."""
    if report.get("status") != "success":
        print(f"❌ Ошибка: {report.get('message', 'Неизвестная ошибка')}")
        return

    category = report["category"]
    period = report["period"]
    stats = report["statistics"]

    print(f"\n{'=' * 60}")
    print(f"📊 ОТЧЕТ ПО КАТЕГОРИИ: {category}")
    print(f"{'=' * 60}")
    print(f"📅 Период: {period['start']} - {period['end']} ({period['days']} дней)")
    print(f"{'-' * 60}")

    print("\n📈 СТАТИСТИКА:")
    print(f"   💰 Всего потрачено: {stats['total_spent']:,.2f} руб.")
    print(f"   📆 В среднем в месяц: {stats['avg_monthly']:,.2f} руб.")
    print(f"   🔢 Количество транзакций: {stats['transactions_count']}")
    print(f"   📅 Охвачено месяцев: {report['total_months']}")

    # Месячная разбивка
    if stats["monthly_breakdown"]:
        print("\n📅 ПОМЕСЯЧНАЯ СТАТИСТИКА:")
        for month, data in stats["monthly_breakdown"].items():
            print(
                f"   • {month}: {data.get('total_spent', 0):,.2f} руб. "
                f"({data.get('transactions_count', 0)} транзакций)"
            )

    # Топ трат
    if report["top_expenses"]:
        print("\n🏆 ТОП-5 САМЫХ КРУПНЫХ ТРАТ:")
        for i, expense in enumerate(report["top_expenses"], 1):
            print(f"   {i}. {expense['date']}")
            print(f"      📝 {expense['description'][:50]}...")
            print(f"      💰 {expense['amount']:,.2f} руб.")

    print(f"\n{'=' * 60}")
    print("✅ Отчет сформирован успешно")
