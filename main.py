import asyncio
import logging
import database as db
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
# Виправляємо імпорт: імпортуємо саму функцію реєстрації
from handlers import registr

logging.basicConfig(level=logging.INFO)

# Ініціалізуємо бота за токеном з конфігу
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Створюємо таблиці в visits.db
    db.init_db()
    
    # Викликаємо функцію безпосередньо
    registr(dp)

    print("Бот запущений і готовий до роботи...")
    
    # Запускаємо поллінг, передаючи об'єкт бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")