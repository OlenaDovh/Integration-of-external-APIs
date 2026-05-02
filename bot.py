import asyncio
import os
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WEATHER_CITY = 1
FORECAST_CITY = 2

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

main_keyboard = ReplyKeyboardMarkup(
    [["Прогноз на сьогодні"], ["Прогноз на 5 днів"]],
    resize_keyboard=True
)


def get_weather(city: str) -> str:
    """Отримує поточну погоду для вказаного міста.

    Args:
        city: Назва міста.

    Returns:
        Рядок із інформацією про погоду або повідомлення про помилку.
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

            today = datetime.now().strftime("%d.%m.%Y")

            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            temp_min = data["main"]["temp_min"]
            temp_max = data["main"]["temp_max"]
            description = data["weather"][0]["description"]
            wind_speed = data.get("wind", {}).get("speed", 0)
            clouds = data.get("clouds", {}).get("all", 0)

            wind_text = f"{wind_speed} м/с" if wind_speed > 0 else "немає"
            clouds_text = f"{clouds}%" if clouds > 0 else "немає"

            logging.info(f"Успішний запит погоди для міста {city}. Час виконання: {execution_time} сек.")

            return (
                f"{city}. Погода на сьогодні ({today}):\n\n"
                f"Температура: {round(temperature)}°C\n"
                f"Відчувається як: {round(feels_like)}°C\n"
                f"Мінімальна температура: {round(temp_min)}°C\n"
                f"Максимальна температура: {round(temp_max)}°C\n"
                f"Стан погоди: {description}\n"
                f"Вітер: {wind_text}\n"
                f"Хмарність: {clouds_text}"
            )

        logging.error(
            f"Помилка запиту погоди для міста {city}. Код: {response.status_code}. Відповідь: {response.text}. Час виконання: {execution_time} сек.")
        return "Не вдалося отримати погоду. Перевірте назву міста, що вводите."

    except requests.RequestException as error:
        execution_time = round(time.time() - start_time, 3)
        logging.error(f"Помилка під час запиту погоди для міста {city}: {error}. Час виконання: {execution_time} сек.")
        return "Сталася помилка під час підключення до API."


def get_forecast(city: str) -> str:
    """Отримує прогноз погоди на 5 днів для міста.

    Args:
        city: Назва міста.

    Returns:
        Рядок із прогнозом або повідомлення про помилку.
    """

    start_time = time.time()

    url = "https://api.openweathermap.org/data/2.5/forecast"

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
            forecast_items = data["list"]

            result = f"{city}. Прогноз погоди на 5 днів:\n\n"
            used_dates = []

            for item in forecast_items:
                date_text = item["dt_txt"]
                date = date_text.split(" ")[0]
                time_text = date_text.split(" ")[1]

                formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")

                if time_text == "12:00:00" and date not in used_dates:
                    temperature = item["main"]["temp"]
                    feels_like = item["main"]["feels_like"]
                    description = item["weather"][0]["description"]
                    wind_speed = item.get("wind", {}).get("speed", 0)
                    clouds = item.get("clouds", {}).get("all", 0)

                    result += (
                        f"{formatted_date}:\n"
                        f"Температура: {round(temperature)}°C\n"
                        f"Відчувається як: {round(feels_like)}°C\n"
                        f"Стан погоди: {description}\n"
                        f"Вітер: {wind_speed} м/с\n"
                        f"Хмарність: {clouds}%\n\n"
                    )

                    used_dates.append(date)

                if len(used_dates) == 5:
                    break

            logging.info(f"Успішний запит прогнозу для міста {city}. Час виконання: {execution_time} сек.")

            return result

        logging.error(
            f"Помилка запиту прогнозу для міста {city}. Код: {response.status_code}. Відповідь: {response.text}. Час виконання: {execution_time} сек.")
        return "Не вдалося отримати прогноз. Перевірте назву міста, що вводите."

    except requests.RequestException as error:
        execution_time = round(time.time() - start_time, 3)
        logging.error(
            f"Помилка під час запиту прогнозу для міста {city}: {error}. Час виконання: {execution_time} сек.")
        return "Сталася помилка під час підключення до API."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /start.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        None.
    """

    await update.message.reply_text(
        "Привіт! Обери дію:",
        reply_markup=main_keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Виводить довідку з доступними можливостями бота.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        None.
    """

    text = (
        "🤖 Доступні можливості бота:\n\n"
        "📍 Прогноз на сьогодні - поточна погода\n"
        "📅 Прогноз на 5 днів - прогноз на кілька днів\n\n"
        "⚙️ Команди:\n"
        "/start - запуск бота\n"
        "/help - довідка\n"
        "/weather - прогноз на сьогодні\n"
        "/forecast - прогноз на 5 днів\n\n"
        "⬇️ Або просто натисни кнопку нижче"
    )

    await update.message.reply_text(text, reply_markup=main_keyboard)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запитує місто для отримання поточної погоди.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Стан очікування введення міста.
    """

    await update.message.reply_text("Вкажіть місто:")
    return WEATHER_CITY


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запитує місто для отримання прогнозу погоди.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Стан очікування введення міста для прогнозу.
    """

    await update.message.reply_text("Вкажіть місто для отримання прогнозу:")
    return FORECAST_CITY


async def weather_city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє введене місто та надсилає поточну погоду.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Завершення діалогу.
    """

    city = update.message.text.strip()
    result = get_weather(city)

    await update.message.reply_text(result)
    await update.message.reply_text(
        "Хочете обрати прогноз на сьогодні чи наступні кілька днів? Натисніть відповідну кнопку на клавіатурі.",
        reply_markup=main_keyboard
    )

    return ConversationHandler.END


async def forecast_city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє введене місто та надсилає прогноз погоди.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Завершення діалогу.
    """

    city = update.message.text.strip()
    result = get_forecast(city)

    await update.message.reply_text(result)
    await update.message.reply_text(
        "Хочете обрати прогноз на сьогодні чи наступні кілька днів? Натисніть відповідну кнопку на клавіатурі.",
        reply_markup=main_keyboard
    )

    return ConversationHandler.END


async def choose_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє кнопку прогнозу на сьогодні та запитує місто.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Стан очікування введення міста.
    """

    await update.message.reply_text("Вкажіть місто:")
    return WEATHER_CITY


async def forecast_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє кнопку прогнозу на 5 днів та запитує місто.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        Стан очікування введення міста для прогнозу.
    """

    await update.message.reply_text("Вкажіть місто для прогнозу:")
    return FORECAST_CITY


async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє довільний текст користувача поза діалогом.

    Args:
        update: Об'єкт оновлення Telegram.
        context: Контекст виконання.

    Returns:
        None.
    """

    await update.message.reply_text(
        "Хочете обрати прогноз на сьогодні чи наступні кілька днів? Натисніть відповідну кнопку на клавіатурі.",
        reply_markup=main_keyboard
    )


def main() -> None:
    """Запускає Telegram-бота для отримання прогнозу погоди.

    Returns:
        None.
    """

    if not OPENWEATHER_API_KEY:
        print("Помилка: OPENWEATHER_API_KEY не знайдено")
        return

    if not TELEGRAM_BOT_TOKEN:
        print("Помилка: TELEGRAM_BOT_TOKEN не знайдено")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    handler = ConversationHandler(
        entry_points=[
            CommandHandler("weather", weather_command),
            CommandHandler("forecast", forecast_command),
            MessageHandler(filters.Regex("^Прогноз на сьогодні$"), choose_city_button),
            MessageHandler(filters.Regex("^Прогноз на 5 днів$"), forecast_button)
        ],
        states={
            WEATHER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, weather_city_handler)],
            FORECAST_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, forecast_city_handler)]
        },
        fallbacks=[]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))

    application.run_polling()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()