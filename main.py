import asyncio
import logging
import database as db
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import registr

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    db.init_db()
    
    registr.register_handlers(dp)

    print("Бот запущений і готовий до роботи...")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")