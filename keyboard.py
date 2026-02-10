from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def regestration():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Реєстрація"), KeyboardButton(text="Авторизація")]
        ],
        resize_keyboard=True
    )

def main_menu_for_teacher():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показати всі візити")], 
            [KeyboardButton(text="Вивести список відсутніх учнів")]
        ],
        resize_keyboard=True
    )

def main_menu_for_student():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Прибув")],
            [KeyboardButton(text="В дорозі")],
            [KeyboardButton(text="В дома")]
        ],
        resize_keyboard=True
    )