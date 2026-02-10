import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from keyboard import regestration, main_menu_for_teacher, main_menu_for_student 
from handlers import register_handlers

logging.basicConfig(level=logging.INFO)

