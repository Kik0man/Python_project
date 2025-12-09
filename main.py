import json

from src.reports import main_reports
from src.services import main_search
from src.views import home_page

if __name__ == "__main__":
    # Тестируем функцию
    result = home_page("2021-12-31 16:44:00")

    # Выводим результат
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    print("🚀 Запуск системы поиска по транзакциям...")
    main_search()

    print("🚀 Запуск системы поиска по категориям...")
    main_reports()
