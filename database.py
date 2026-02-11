import asyncpg
from datetime import datetime
from config import DATABASE_URL
async def get_connection():
    """Створює підключення до Neon."""
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    """Ініціалізація бази даних у Neon: створення таблиць (PostgreSQL синтаксис)."""
    conn = await get_connection()
    
    # Таблиця користувачів (BIGINT для Telegram ID)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id BIGINT PRIMARY KEY,
            full_name TEXT,
            email TEXT,
            role TEXT,
            class_name TEXT
        )
    ''')

    # Таблиця дозволених пошт
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS allowed_emails (
            email TEXT PRIMARY KEY,
            class_name TEXT,
            full_name TEXT
        )
    ''')
    
    # Таблиця візитів (SERIAL для автоінкременту)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            tg_id BIGINT,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tg_id) REFERENCES users (tg_id)
        )
    ''')
    
    await conn.close()

async def register_user(tg_id, full_name, email, role, class_name=None):
    """Реєстрація або оновлення користувача (синтаксис PostgreSQL ON CONFLICT)."""
    conn = await get_connection()
    await conn.execute('''
        INSERT INTO users (tg_id, full_name, email, role, class_name)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (tg_id) DO UPDATE 
        SET full_name = EXCLUDED.full_name, email = EXCLUDED.email, 
            role = EXCLUDED.role, class_name = EXCLUDED.class_name
    ''', tg_id, full_name, email, role, class_name)
    await conn.close()

async def get_user_role(tg_id):
    """Отримання ролі за Telegram ID."""
    conn = await get_connection()
    role = await conn.fetchval('SELECT role FROM users WHERE tg_id = $1', tg_id)
    await conn.close()
    return role

async def log_visit(tg_id, status):
    """Запис статусу відвідування."""
    conn = await get_connection()
    # PostgreSQL автоматично підставить час через DEFAULT CURRENT_TIMESTAMP, 
    # але ми можемо передати свій для точності
    now = datetime.now()
    await conn.execute('''
        INSERT INTO visits (tg_id, status, timestamp)
        VALUES ($1, $2, $3)
    ''', tg_id, status, now)
    await conn.close()

async def get_allowed_user_data(email):
    """Отримання даних користувача за поштою."""
    conn = await get_connection()
    row = await conn.fetchrow('SELECT full_name, class_name FROM allowed_emails WHERE email = $1', email.lower())
    await conn.close()
    return row # Поверне об'єкт Record (можна звертатися як row['full_name'])

async def get_absent_students(class_name):
    """Список студентів, які не відмітилися сьогодні."""
    conn = await get_connection()
    today = datetime.now().date()
    
    # PostgreSQL використовує синтаксис ::date для порівняння дат
    rows = await conn.fetch('''
        SELECT DISTINCT full_name FROM allowed_emails 
        WHERE class_name = $1 AND email NOT IN (
            SELECT users.email FROM visits 
            JOIN users ON visits.tg_id = users.tg_id 
            WHERE visits.timestamp::date = $2
        )
    ''', class_name, today)
    await conn.close()
    
    if not rows:
        return []

    formatted_list = []
    separator = "------------------------"
    for row in rows:
        formatted_list.append(separator)
        formatted_list.append(f"{row[0]}❌")
    
    return formatted_list

async def get_all_student_ids():
    """Список всіх ID учнів для розсилки."""
    conn = await get_connection()
    rows = await conn.fetch('SELECT tg_id FROM users WHERE role = $1', 'student')
    await conn.close()
    return [row['tg_id'] for row in rows]

async def get_all_today_visits():
    """Журнал відвідувань за сьогодні."""
    conn = await get_connection()
    today = datetime.now().date()
    
    rows = await conn.fetch('''
        SELECT users.full_name, visits.status, visits.timestamp
        FROM visits
        JOIN users ON visits.tg_id = users.tg_id
        WHERE visits.timestamp::date = $1
        ORDER BY visits.timestamp DESC
    ''', today)
    await conn.close()
    
    if not rows:
        return "Сьогодні ще ніхто не відмічався."
    
    report = ""
    for row in rows:
        time_str = row['timestamp'].strftime("%H:%M:%S")
        report += f"📍 {row['full_name']}: {row['status']} ({time_str})\n"
    return report

async def clear_old_visits():
    """Очищення старих записів (крім сьогоднішніх)."""
    conn = await get_connection()
    today = datetime.now().date()
    await conn.execute('DELETE FROM visits WHERE timestamp::date < $1', today)
    await conn.close()