from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import TEACHER_SECRET_CODE
from keyboard import regestration, main_menu_for_teacher, main_menu_for_student
import database as db  # Припустимо, файл з логікою БД називається database.py

router = Router()

# Визначаємо стани для FSM
class AuthState(StatesGroup):
    wait_for_email = State()        # Очікування пошти від учня
    wait_for_teacher_code = State()  # Очікування пароля від вчителя
    wait_for_name = State()         # Очікування ПІБ (спільний крок)

# --- Блок реєстрації та авторизації ---

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user_role = db.get_user_role(message.from_user.id)
    
    if user_role == "teacher":
        await message.answer("Вітаю, вчителю! Панель керування готова.", reply_markup=main_menu_for_teacher())
    elif user_role == "student":
        await message.answer("Привіт! Оберіть свій поточний статус:", reply_markup=main_menu_for_student())
    else:
        await message.answer(
            "Вітаємо у системі Visits! Будь ласка, оберіть варіант входу:", 
            reply_markup=regestration()
        )

@router.message(F.text == "Вхід для вчителя")
async def teacher_auth_start(message: Message, state: FSMContext):
    await message.answer("Введіть секретний код доступу:")
    await state.set_state(AuthState.wait_for_teacher_code)

@router.message(AuthState.wait_for_teacher_code)
async def check_teacher_code(message: Message, state: FSMContext):
    if message.text == TEACHER_SECRET_CODE:
        await state.update_data(role="teacher", email="admin@school.com")
        await message.answer("Код вірний! Тепер введіть ваше Прізвище та Ім'я:")
        await state.set_state(AuthState.wait_for_name)
    else:
        await message.answer("Невірний код. Спробуйте ще раз або натисніть /start")

@router.message(F.text == "Реєстрація") # Або "Учень: Реєстрація", залежно від тексту в keyboard.py
async def student_reg_start(message: Message, state: FSMContext):
    await message.answer("Введіть вашу електронну пошту (наприклад, student@example.com):")
    await state.set_state(AuthState.wait_for_email)

@router.message(AuthState.wait_for_email)
async def process_email(message: Message, state: FSMContext):
    # Тут можна додати перевірку валідності email
    await state.update_data(role="student", email=message.text.lower())
    await message.answer("Дякую! Тепер введіть ваше Прізвище та Ім'я:")
    await state.set_state(AuthState.wait_for_name)

@router.message(AuthState.wait_for_name)
async def finish_registration(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = message.text
    tg_id = message.from_user.id
    
    # Зберігаємо дані в базу
    db.register_user(tg_id, full_name, user_data['email'], user_data['role'])
    
    if user_data['role'] == "teacher":
        await message.answer(f"Реєстрація завершена. Вітаю, {full_name}!", reply_markup=main_menu_for_teacher())
    else:
        await message.answer(f"Реєстрація завершена. Привіт, {full_name}!", reply_markup=main_menu_for_student())
    
    await state.clear()

# --- Блок логіки для учнів ---

@router.message(F.text.in_(["Прибув", "В дорозі", "В дома"]))
async def handle_student_status(message: Message):
    user_role = db.get_user_role(message.from_user.id)
    if user_role == "student":
        status = message.text
        db.log_visit(message.from_user.id, status) # Запис відмітки в БД
        await message.answer(f"Ваш статус «{status}» збережено. Дякуємо!")
    else:
        await message.answer("Ця функція доступна тільки для учнів.")

# --- Блок логіки для вчителів ---

@router.message(F.text == "Показати всі візити")
async def show_all_visits(message: Message):
    if db.get_user_role(message.from_user.id) == "teacher":
        visits = db.get_all_today_visits()
        # Тут логіка формування тексту зі списком
        await message.answer(f"Список візитів на сьогодні:\n{visits}")
    else:
        await message.answer("Доступ заборонено.")

def register_handlers(dp):
    dp.include_router(router)