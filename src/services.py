import json
import logging
from typing import Any, Dict, List

import pandas as pd

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def simple_search(search_query: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Поиск транзакций по запросу в описании или категории.
    """
    logger.info(f"Поиск: '{search_query}' в {len(transactions)} транзакциях")

    try:
        if not search_query:
            return {"status": "error", "message": "Запрос не может быть пустым"}

        if not transactions:
            return {"status": "error", "message": "Нет данных для поиска"}

        query_lower = search_query.lower()
        found = []

        for trans in transactions:
            desc = str(trans.get("Описание", "")).lower()
            cat = str(trans.get("Категория", "")).lower()

            if query_lower in desc or query_lower in cat:
                found.append(trans)

        return {
            "status": "success",
            "query": search_query,
            "found": len(found),
            "total": len(transactions),
            "transactions": found,
        }

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return {"status": "error", "message": str(e)}


def load_data(filepath: str = "data/operations.xlsx") -> Any:
    """Загружает данные из Excel файла."""
    try:
        logger.info(f"Загрузка данных из {filepath}")
        df = pd.read_excel(filepath)
        return df.to_dict("records")
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return []


def search_in_excel(search_query: str) -> str:
    """Поиск в Excel файле с возвратом JSON."""
    transactions = load_data()

    if not transactions:
        return json.dumps(
            {"status": "error", "message": "Не удалось загрузить данные. Проверьте файл data/operations.xlsx"},
            ensure_ascii=False,
        )

    result = simple_search(search_query, transactions)
    return json.dumps(result, ensure_ascii=False, default=str)


def show_results(result: Dict[str, Any]) -> Any:
    """Показывает результаты поиска."""
    if result["status"] != "success":
        print(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
        return

    query = result["query"]
    found = result["found"]
    total = result["total"]

    print(f"\n🔍 Результаты поиска '{query}':")
    print(f"✅ Найдено: {found} из {total}")

    if found == 0:
        print("😞 Ничего не найдено")
        return

    print("\n📋 Транзакции:")
    for i, trans in enumerate(result["transactions"][:10], 1):  # Показываем первые 10
        print(f"\n{i}. 📅 {trans.get('Дата операции', 'Нет даты')}")
        print(f"   📝 {trans.get('Описание', 'Нет описания')}")
        print(f"   💰 {trans.get('Сумма операции', 'Нет суммы'):.2f} руб.")
        print(f"   🏷️  {trans.get('Категория', 'Нет категории')}")

    if found > 10:
        print(f"\n... и еще {found - 10} транзакций")


def main_search() -> Any:
    """Главная функция для интерактивного поиска."""
    print("🔍 Сервис поиска по транзакциям")
    print("=" * 40)

    # Пробуем загрузить данные
    data = load_data()
    if not data:
        print("❌ Ошибка: не удалось загрузить данные")
        print("   Убедитесь что файл data/operations.xlsx существует")
        return

    print(f"✅ Загружено {len(data)} транзакций")
    print("\n💡 Примеры запросов: 'Колхоз', 'Магнит', 'Супермаркеты'")

    # Основной цикл
    while True:
        print("\n" + "-" * 40)
        query = input("Введите слово для поиска (или 'выход'): ").strip()

        if query.lower() in ["выход", "exit", "quit", "q"]:
            print("👋 До свидания!")
            break

        if not query:
            print("❌ Запрос не может быть пустым")
            continue

        # Выполняем поиск
        result = simple_search(query, data)
        show_results(result)
