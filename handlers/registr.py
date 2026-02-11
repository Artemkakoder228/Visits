from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import TEACHER_SECRET_CODE, ALLOWED_TEACHER_EMAIL
from keyboard import class_selection_menu, regestration, main_menu_for_teacher, main_menu_for_student
import database as db 

router = Router()

# Визначаємо стани для FSM
class AuthState(StatesGroup):
    wait_for_class = State()        # Вибір класу (для учня)
    wait_for_email = State()        # Введення пошти (для учня)
    wait_for_teacher_code = State() # Введення секретного коду (для вчителя)
    wait_for_teacher_email = State() # Введення перевірочної пошти (для вчителя)
    wait_for_name = State()
    wait_for_absent_class = State() # Новий стан      # Введення ПІБ (спільне)

# --- Головне меню та вхід ---

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user_role = db.get_user_role(message.from_user.id)
    
    if user_role == "teacher":
        await message.answer("Вітаю, вчителю!", reply_markup=main_menu_for_teacher())
    elif user_role == "student":
        await message.answer("Привіт! Оберіть статус:", reply_markup=main_menu_for_student())
    else:
        await message.answer(
            "Вітаємо у системі Visits! Оберіть варіант входу:", 
            reply_markup=regestration()
        )

# --- Логіка Учня (Навігація: Клас -> Пошта -> ПІБ) ---

@router.message(F.text == "Учень: Реєстрація за email")
async def student_reg_start(message: Message, state: FSMContext):
    await state.clear() 
    await message.answer("Оберіть ваш клас:", reply_markup=class_selection_menu())
    await state.set_state(AuthState.wait_for_class)

@router.message(AuthState.wait_for_class, F.text == "⬅️ Назад")
async def back_from_class(message: Message, state: FSMContext):
    await state.clear()
    await cmd_start(message)

@router.message(AuthState.wait_for_class)
async def process_class_selection(message: Message, state: FSMContext):
    selected_class = message.text
    await state.update_data(class_name=selected_class)
    await message.answer(
        f"Ви обрали клас: {selected_class}.\nТепер введіть вашу пошту:",
        reply_markup=class_selection_menu() 
    )
    await state.set_state(AuthState.wait_for_email)

@router.message(AuthState.wait_for_email, F.text == "⬅️ Назад")
async def back_from_email(message: Message, state: FSMContext):
    await message.answer("Оберіть ваш клас заново:", reply_markup=class_selection_menu())
    await state.set_state(AuthState.wait_for_class)

@router.message(AuthState.wait_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.lower()
    data = await state.get_data()
    class_name = data.get('class_name')
    
    if db.is_email_in_class(email, class_name):
        await state.update_data(role="student", email=email)
        await message.answer("Пошта підтверджена! Введіть ПІБ:", reply_markup=None)
        await state.set_state(AuthState.wait_for_name)
    else:
        await message.answer(
            f"Пошти {email} немає у списках {class_name}.\nОберіть клас знову:",
            reply_markup=class_selection_menu()
        )
        await state.set_state(AuthState.wait_for_class)

# --- Логіка Вчителя (Код -> Пошта -> ПІБ) ---

@router.message(F.text == "Вхід для вчителя")
async def teacher_auth_start(message: Message, state: FSMContext):
    await message.answer("Введіть секретний код доступу:", reply_markup=None)
    await state.set_state(AuthState.wait_for_teacher_code)

@router.message(AuthState.wait_for_teacher_code)
async def check_teacher_code(message: Message, state: FSMContext):
    if message.text == TEACHER_SECRET_CODE:
        await message.answer("Код вірний! Тепер введіть вашу вчительську пошту:")
        await state.set_state(AuthState.wait_for_teacher_email) # Переходимо до нового стану
    else:
        await message.answer("Невірний код. Спробуйте ще раз або /start")

@router.message(AuthState.wait_for_teacher_email)
async def check_teacher_email(message: Message, state: FSMContext):
    input_email = message.text.lower()
    
    # Шукаємо дані в таблиці allowed_emails
    user_data = db.get_allowed_user_data(input_email)
    
    # Перевіряємо, чи є така пошта і чи належить вона вчителю
    if user_data and user_data[1] == 'teacher':
        full_name = user_data[0]
        
        # Відразу реєструємо користувача в основній таблиці users
        db.register_user(
            tg_id=message.from_user.id,
            full_name=full_name,
            email=input_email,
            role="teacher",
            class_name=None
        )
        
        await message.answer(f"Авторизація успішна! Вітаю, {full_name}!", reply_markup=main_menu_for_teacher())
        await state.clear()
    else:
        await message.answer(f"Помилка! Пошта {input_email} не знайдена в списку вчителів. Спробуйте ще раз або /start")

@router.message(AuthState.wait_for_name)
async def finish_registration(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = message.text
    
    db.register_user(
        message.from_user.id, 
        full_name, 
        user_data['email'], 
        user_data['role'], 
        user_data.get('class_name')
    )
    
    if user_data['role'] == "teacher":
        await message.answer(f"Вітаю, {full_name}!", reply_markup=main_menu_for_teacher())
    else:
        await message.answer(f"Привіт, {full_name}!", reply_markup=main_menu_for_student())
    
    await state.clear()

# --- Статуси та Вихід ---
@router.message(F.text == "Хто відсутній?")
async def ask_class_for_absent(message: Message, state: FSMContext):
    if db.get_user_role(message.from_user.id) == "teacher":
        await message.answer("Оберіть клас для перевірки відсутніх:", reply_markup=class_selection_menu())
        await state.set_state(AuthState.wait_for_absent_class)

@router.message(AuthState.wait_for_absent_class)
async def show_absent_students(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await cmd_start(message)
        return

    selected_class = message.text
    absent_list = db.get_absent_students(selected_class)
    
    if not absent_list:
        text = f"У класі {selected_class} всі присутні! ✅"
    else:
        text = f"Відсутні у {selected_class} ({len(absent_list)} чол.):\n"
        text += "\n".join([f"❌ {name}" for name in absent_list])
    
    await message.answer(text, reply_markup=main_menu_for_teacher())
    await state.clear()

@router.message(F.text.in_(["Прибув", "В дорозі", "В дома"]))
async def handle_student_status(message: Message):
    user_role = db.get_user_role(message.from_user.id)
    if user_role == "student":
        db.log_visit(message.from_user.id, message.text)
        await message.answer(f"Статус «{message.text}» збережено!")
    else:
        await message.answer("Доступно тільки для учнів.")

@router.message(F.text == "Показати всі візити")
async def show_all_visits(message: Message):
    if db.get_user_role(message.from_user.id) == "teacher":
        visits = db.get_all_today_visits()
        await message.answer(f"Візити за сьогодні:\n{visits}")

@router.message(F.text == "Вийти з акаунта")
async def logout_to_test(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Оберіть режим для входу:", reply_markup=regestration())

def register_handlers(dp):
    dp.include_router(router)