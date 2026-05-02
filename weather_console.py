import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def get_weather(city: str) -> str:
    """Отримує поточну погоду для вказаного міста.

    Args:
        city: Назва міста.

    Returns:
        Рядок із погодою або повідомленням про помилку.
    """

    start_time = time.time()

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ua"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        execution_time = round(time.time() - start_time, 3)

        if response.status_code == 200:
            data = response.json()
            temperature = data["main"]["temp"]
            description = data["weather"][0]["description"]

            logging.info(f"Успішний запит для міста {city}. Час виконання: {execution_time} сек.")

            return f"{city}: {round(temperature)}°C, {description}."

        logging.error(
            f"Помилка запиту для міста {city}. Код: {response.status_code}. Відповідь: {response.text}. Час виконання: {execution_time} сек."
        )

        return "Не вдалося отримати погоду. Перевірте назву міста або API-ключ."

    except requests.RequestException as error:
        execution_time = round(time.time() - start_time, 3)
        logging.error(
            f"Помилка під час запиту для міста {city}: {error}. Час виконання: {execution_time} сек."
        )
        return "Сталася помилка під час підключення до API."


def main() -> None:
    """Запускає консольну програму для отримання погоди.

    Returns:
        None.
    """

    if not OPENWEATHER_API_KEY:
        print("Помилка: OPENWEATHER_API_KEY не знайдено у файлі .env")
        return

    while True:
        city = input("Введіть місто (або 'exit' для виходу): ")

        if city.lower() == "exit":
            print("Вихід...")
            break

        result = get_weather(city)
        print(result)


if __name__ == "__main__":
    main()