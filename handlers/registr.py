from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import TEACHER_SECRET_CODE
from keyboard import class_selection_menu, regestration, main_menu_for_teacher, main_menu_for_student
import database as db 

router = Router()

class AuthState(StatesGroup):
    wait_for_class = State()
    wait_for_email = State()
    wait_for_teacher_code = State()
    wait_for_teacher_email = State()
    wait_for_absent_class = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    # Додано await
    user_role = await db.get_user_role(message.from_user.id) 
    
    if user_role == "teacher":
        await message.answer("Вітаю, вчителю!", reply_markup=main_menu_for_teacher())
    elif user_role == "student":
        await message.answer("Привіт! Оберіть статус:", reply_markup=main_menu_for_student())
    else:
        await message.answer(
            "Вітаємо у системі Visits! Оберіть варіант входу:", 
            reply_markup=regestration()
        )

@router.message(F.text == "Учень: Реєстрація за email")
async def student_reg_start(message: Message, state: FSMContext):
    await state.clear() 
    await message.answer("Оберіть ваш клас:", reply_markup=class_selection_menu())
    await state.set_state(AuthState.wait_for_class)

@router.message(AuthState.wait_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.lower()
    data = await state.get_data()
    class_name = data.get('class_name')
    
    # Додано await
    user_data = await db.get_allowed_user_data(email)
    
    if user_data and user_data['class_name'] == class_name:
        full_name = user_data['full_name']
        # Додано await
        await db.register_user(message.from_user.id, full_name, email, "student", class_name)
        await message.answer(f"Привіт, {full_name}! Реєстрація успішна.", reply_markup=main_menu_for_student())
        await state.clear()
    else:
        await message.answer(
            f"Пошти {email} немає у списках {class_name}.\nСпробуйте ще раз або /start",
            reply_markup=class_selection_menu()
        )

@router.message(AuthState.wait_for_teacher_email)
async def process_teacher_email(message: Message, state: FSMContext):
    email = message.text.lower()
    # Додано await
    user_data = await db.get_allowed_user_data(email)
    
    if user_data and user_data['class_name'] == 'teacher':
        full_name = user_data['full_name']
        # Додано await
        await db.register_user(message.from_user.id, full_name, email, "teacher")
        await message.answer(f"Вітаю, {full_name}!", reply_markup=main_menu_for_teacher())
        await state.clear()
    else:
        await message.answer("Цієї пошти немає в списку вчителів.")

@router.message(F.text.in_(["Прибув✅", "В дорозі🚗", "В дома🏠"]))
async def handle_student_status(message: Message):
    # Додано await
    user_role = await db.get_user_role(message.from_user.id)
    if user_role == "student":
        # Додано await
        await db.log_visit(message.from_user.id, message.text)
        await message.answer(f"Статус «{message.text}» успішно змінено! ✅")

@router.message(F.text == "Показати всі візити")
async def show_all_visits(message: Message):
    # Додано await
    if await db.get_user_role(message.from_user.id) == "teacher":
        # Додано await
        visits = await db.get_all_today_visits()
        await message.answer(f"Журнал за сьогодні:\n{visits}")

def register_handlers(dp):
    dp.include_router(router)