import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator
import aiosqlite

_logger = logging.getLogger(__name__)

"""Инфраструктура и инициализация"""
@asynccontextmanager
async def get_connection() -> AsyncGenerator:
    """Асинхронный контекстный менеджер для получения соединения с базой данных с автоматическим commit/rollback транзакции."""
    conn = None
    try:
        conn = await aiosqlite.connect('database.db')
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.execute("PRAGMA busy_timeout = 10000")
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        await conn.commit()

    except Exception as e:
        if conn:
            await conn.rollback()
        raise e

    finally:
        if conn:
            await conn.close()

async def init_db() -> None:
    """Создаёт все необходимые таблицы базы данных, если они ещё не существуют."""
    async with get_connection() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                status TEXT,
                timezone INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_notification TIMESTAMP
            )
        ''')


        await conn.execute('''
                CREATE TABLE IF NOT EXISTS track_water (
                    user_id INTEGER PRIMARY KEY,
                    timezone INTEGER,
                    broadcast_type TEXT,
                    broadcast_interval INTEGER,
                    last_broadcast TIMESTAMP,
                    goal_ml TEXT,
                    Monday TEXT DEFAULT 0,
                    Tuesday TEXT DEFAULT 0,
                    Wednesday TEXT DEFAULT 0,
                    Thursday TEXT DEFAULT 0,
                    Friday TEXT DEFAULT 0,
                    Saturday TEXT DEFAULT 0,
                    Sunday TEXT DEFAULT 0,
                    Total TEXT DEFAULT 0,
                    last_update TIMESTAMP,
                    last_reset TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            week_start TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS track_activity (
            user_id INTEGER PRIMARY KEY,
            timezone INTEGER,
            goal_exercises INTEGER,
            broadcast_type TEXT,
            broadcast_interval INTEGER,
            last_broadcast TIMESTAMP,
            last_inactivity_reminder TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        ''')
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            difficulty TEXT,
            file_id TEXT,
            channel_message_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
            )
            ''')
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS exercises_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise_id INTEGER,
            date DATE DEFAULT CURRENT_DATE,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE SET NULL
            )
            ''')
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS exercises_user_favorites (
            user_id INTEGER,
            exercise_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, exercise_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
            )
            ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                status_for_user TEXT DEFAULT 'no_new',
                status_for_admin TEXT DEFAULT 'new',
                type TEXT,
                under_admin_review INTEGER DEFAULT 0,
                opened_by_admin_at TIME DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                text TEXT,
                is_from_user BOOLEAN,
                type_msg TEXT DEFAULT 'string',
                file_id TEXT DEFAULT NULL,
                channel_message_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            )
            ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS track_sleep (
                user_id INTEGER PRIMARY KEY,
                timezone INTEGER,
                sleep_time TEXT,
                wake_time TEXT,
                reminders_enabled INTEGER DEFAULT 1,
                last_sleep_reminder TIMESTAMP,
                last_wake_reminder TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sleep_start TIMESTAMP,
                wake_up TIMESTAMP,
                duration INTEGER,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS xp_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                xp_gained INTEGER NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

"""Пользователи и администрация"""
async def add_user(user_id: int, username: str | None, status: str) -> None:
    """Добавляет пользователя в БД или обновляет его username/status и время последней активности, если он уже существует."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        exists = await cursor.fetchone()
        if exists:
            await conn.execute('''
                UPDATE users
                SET username = ?, status = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (username, status, user_id))
        else:
            await conn.execute('''
                INSERT INTO users (user_id, username, status)
                VALUES (?, ?, ?)
            ''', (user_id, username, status))
            await conn.execute('''INSERT INTO track_water (user_id) VALUES (?)''', (user_id,))
            await conn.execute('''INSERT INTO track_activity (user_id) VALUES (?)''', (user_id,))
            await conn.execute('''INSERT INTO track_sleep (user_id) VALUES (?)''', (user_id,))
            await conn.execute('''INSERT INTO user_xp (user_id) VALUES (?)''', (user_id,))
            _logger.info(f"Added new user: {user_id} - {'@' + username} - {status}")

async def all_users() -> list[int]:
    """Возвращает список ID пользователей."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT * FROM users')
        users = await cursor.fetchall()
    return [user[0] for user in users]

async def get_new_users_count(days: int) -> int:
    """Возвращает количество новых пользователей, зарегистрировавшихся за последние N дней."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
        SELECT COUNT(*)
        FROM users
        WHERE created_date >= datetime('now', ?)
    ''', (f'-{days} days',))
        result = await cursor.fetchone()
    return result[0]

async def update_user_activity_smart(user_id: int) -> None:
    """Обновляет время последней активности пользователя, но не чаще одного раза в час."""
    async with get_connection() as conn:
        await conn.execute('''
        UPDATE users
        SET last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ? AND (
            last_activity IS NULL OR
            last_activity < datetime('now', '-1 hours')
        )
        ''', (user_id,))

async def get_active_users_count(days: int = 4) -> int:
    """Возвращает количество активных пользователей за последние N дней."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
        SELECT COUNT(*)
        FROM users
        WHERE last_activity >= datetime('now', ?)
        ''', (f'-{days} days',))
        result = await cursor.fetchone()
    return result[0]

async def get_user_status(user_id: int | None = None, username: str | None = None) -> str:
    """Возвращает статус пользователя: 'User', 'Admin' или 'Owner'."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if user_id:
            await cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()

        elif username:
            await cursor.execute('SELECT status FROM users WHERE username = ?', (username,))
            result = await cursor.fetchone()
    return result[0] if result else 'User'

async def get_all_admin(only_admin: bool = True) -> list[tuple]:
    """Возвращает список (ID пользователя, username) администраторов, при only_admin=False включая владельцев."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        status_list = ['Admin']
        if not only_admin:
            status_list.append('Owner')
        quoted_statuses = [f"'{status}'" for status in status_list]
        status_str = ','.join(quoted_statuses)
        await cursor.execute(f'''
                SELECT user_id,username
                FROM users
                WHERE status IN ({status_str})
            ''')
        result = await cursor.fetchall()
    return result

async def is_user_valid(user_id: int | None = None, username: str | None = None) -> tuple | None:
    """Проверяет, существует ли пользователь в базе данных."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if user_id:
            await cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        elif username:
            clean_username = username.lstrip('@')
            await cursor.execute('SELECT 1 FROM users WHERE username = ?', (clean_username,))
        else:
            return False

        result = await cursor.fetchone()
    return result

async def replace_status(status: str, user_id: int | None = None, username: str | None = None) -> None:
    """Обновляет статус пользователя по ID пользователя или username."""
    async with get_connection() as conn:
        cursor = await conn.cursor()

        if user_id:
            await cursor.execute('UPDATE users SET status = ? WHERE user_id = ?',
                                 (status, user_id))
        elif username:
            await cursor.execute('UPDATE users SET status = ? WHERE username = ?',
                                 (status, username))

async def get_id_by_username(username: str) -> int | None:
    """Возвращает ID пользователя по username."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        result = await cursor.fetchone()
    return result[0]

async def get_username_by_id(user_id: int) -> str | None:
    """Возвращает username по ID пользователя."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
    return result[0]

async def update_username(user_id: int, username: str | None, bot) -> None:
    """Обновляет username пользователя и уведомляет админов, если он администратор."""
    old_username = await get_username_by_id(user_id)
    if old_username != username:
        async with get_connection() as conn:
            await conn.execute(
                'UPDATE users SET username = ? WHERE user_id = ?',
                (username, user_id)
            )

        if await get_user_status(user_id) == 'Admin':
            from handlers.admin_notifications import admin_update_notification
            await admin_update_notification(bot, user_id, old_username, username)

async def search_user(query: str) -> tuple | None:
    """Поиск пользователя по ID пользователя или username.
    Возвращает (ID пользователя, username, status, created_date, last_activity, timezone) или None."""
    async with get_connection() as conn:
        query = query.strip().lstrip('@')
        if query.isdigit():
            cursor = await conn.execute(
                'SELECT user_id, username, status, created_date, last_activity, timezone FROM users WHERE user_id = ?',
                (int(query),)
            )
        else:
            cursor = await conn.execute(
                'SELECT user_id, username, status, created_date, last_activity, timezone FROM users WHERE username = ?',
                (query,)
            )
        return await cursor.fetchone()

async def is_user_banned(user_id: int) -> bool:
    """Проверяет, забанен ли пользователь."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
    return row is not None and row[0] == 'BANNED'

"""Часовой пояс и время пользователя"""
async def set_timezone(user_id: int, new_timezone: int) -> None:
    """Устанавливает часовой пояс пользователя во всех связанных таблицах."""
    async with get_connection() as conn:
        await conn.execute('UPDATE users SET timezone = ? WHERE user_id = ? ', (new_timezone, user_id))
        await conn.execute('UPDATE track_water SET timezone = ? WHERE user_id = ?', (new_timezone, user_id))
        await conn.execute('UPDATE track_activity SET timezone = ? WHERE user_id = ?', (new_timezone, user_id))
        await conn.execute('UPDATE track_sleep SET timezone = ? WHERE user_id = ?', (new_timezone, user_id))

async def get_timezone(user_id: int) -> int | None:
    """Возвращает смещение часового пояса относительно МСК или None."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
    return result[0] if result else None

async def get_user_time_now(user_id: int) -> datetime:
    """Возвращает текущее локальное время пользователя с учётом его часового пояса."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
    tz = row[0] if row and row[0] is not None else 0
    return datetime.now() + timedelta(hours=tz)

"""Водный трекер"""
async def water_set_reminder_type(user_id: int, broadcast_type: str, broadcast_interval: int | None = None) -> None:
    """Устанавливает тип и интервал напоминаний о воде для пользователя."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if broadcast_type == "Smart":
            await cursor.execute(
                'UPDATE track_water SET broadcast_type = ?, broadcast_interval = NULL WHERE user_id = ?',
                (broadcast_type, user_id)
            )

        else:
            await cursor.execute('UPDATE track_water SET broadcast_type = ?, broadcast_interval = ? WHERE user_id = ?',
                                 (broadcast_type, broadcast_interval, user_id)
                                 )
        await cursor.execute('UPDATE track_water SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?',
                             (user_id,))

async def update_reminder_sent_time(user_id: int) -> None:
    """Обновляет время последней отправки напоминания о воде."""
    async with get_connection() as conn:
        await conn.execute('''UPDATE track_water SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?''',
                           (user_id,))

async def update_water_goal(user_id: int, new_goal: int) -> None:
    """Устанавливает дневную цель по воде в мл для пользователя."""
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET goal_ml = ? WHERE user_id = ?',
                           (new_goal, user_id)
                           )

async def count_users_trackers(db_table: str, column_name: str, user_id: int | None = None) -> int:
    """Считает количество записей, не равных NULL в column_name, опционально фильтруя по пользователю."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if user_id:
            await cursor.execute(f'''
                        SELECT COUNT(*)
                        FROM {db_table}
                        WHERE user_id = ?
                        AND {column_name} IS NOT NULL
                    ''', (user_id,))
            result = await cursor.fetchone()
        else:
            await cursor.execute(f'''SELECT COUNT(*)
            FROM {db_table}
            WHERE {column_name} IS NOT NULL ''')
            result = await cursor.fetchone()
    return result[0]

async def add_water_ml(user_id: int, volume_ml: int, add_total: bool = True) -> None:
    """Добавляет выпитый объём воды в статистику пользователя за текущий день недели."""
    today = await get_user_time_now(user_id)
    day_name = today.strftime('%A')
    now_user_date = today.date()
    days_since_monday = now_user_date.weekday()
    last_monday = now_user_date - timedelta(days=days_since_monday)
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(f'UPDATE track_water SET {day_name} ={day_name} + ? WHERE user_id = ?',
                             (volume_ml, user_id))
        if add_total:
            await cursor.execute('UPDATE track_water SET Total = Total + ? WHERE user_id = ?',
                                 (volume_ml, user_id))
        await cursor.execute('INSERT INTO water_logs (user_id, amount, week_start) VALUES (?, ?, ?) ',
                             (user_id, volume_ml, last_monday))

async def water_stats(user_id: int) -> tuple:
    """Возвращает пару (goal_ml, выпито сегодня) для пользователя."""
    today = await get_user_time_now(user_id)
    day_name = today.strftime('%A')
    async with get_connection() as conn:
        cursor = await conn.execute(f'SELECT goal_ml,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
        result = map(int, await cursor.fetchone())
    return result

async def update_last_add_water_ml(user_id: int) -> None:
    """Обновляет время последнего добавления воды для пользователя."""
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET last_update = CURRENT_TIMESTAMP WHERE user_id = ?',
                           (user_id,))

async def get_water_stats_for_today(user_id: int) -> tuple:
    """Возвращает (last_update, выпито сегодня) для пользователя."""
    today = await get_user_time_now(user_id)
    day_name = today.strftime('%A')
    async with get_connection() as conn:
        cursor = await conn.execute(f'SELECT last_update,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
        update_time, cnt_water = await cursor.fetchone()
    return update_time, cnt_water

async def fetch_water_stats_all() -> list[tuple]:
    """Возвращает статистику водного трекера для всех пользователей."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''SELECT user_id,goal_ml,timezone,Monday,Tuesday,
        Wednesday,Thursday,Friday,Saturday,Sunday,last_reset
         FROM track_water''')
        return await cursor.fetchall()

async def set_last_reset_water(user_id: int, last_reset: str) -> None:
    """Сохраняет дату последнего сброса еженедельной статистики воды."""
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET last_reset = ? WHERE user_id = ?', (last_reset, user_id))

async def water_reset(user_id: int) -> None:
    """Сбрасывает ежедневные счётчики воды за все дни недели."""
    async with get_connection() as conn:
        await conn.execute('''UPDATE track_water SET Monday = 0,Tuesday = 0,
        Wednesday = 0,Thursday = 0,Friday = 0,Saturday = 0,Sunday = 0 WHERE USER_ID = ?''', (user_id,))

async def get_lost_records_of_water(user_id: int) -> list[tuple]:
    """Возвращает все записи в журнале воды пользователя."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT id,amount,week_start FROM water_logs WHERE user_id = ?''', (user_id,))
        return await cursor.fetchall()

async def delete_water_log(log_id: int) -> None:
    """Удаляет запись в журнале воды по её ID."""
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM water_logs WHERE id = ?''', (log_id,))

async def get_users_for_water_reminders() -> list[tuple]:
    """Возвращает пользователей с включенными напоминаниями о воде."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT user_id,broadcast_type,broadcast_interval,
        last_broadcast,last_update FROM track_water WHERE broadcast_type IS NOT NULL''')
        result = await cursor.fetchall()
    return result

"""Поддержка и тикеты"""
async def add_ticket(title: str, user_id: int, username: str | None, first_name: str, type_supp: str) -> int:
    """Создаёт новый тикет поддержки и возвращает его ID."""
    async with get_connection() as conn:
        cursor = await conn.execute('''INSERT INTO tickets (title,user_id,username,first_name,type)
                      VALUES (?,?,?,?,?)''',
                                    (title, user_id, username, first_name, type_supp))
        ticket_id = cursor.lastrowid
    return ticket_id

async def delete_ticket(ticket_id: int) -> None:
    """Удаляет тикет и всю его переписку из базы данных."""
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM tickets WHERE id = ?''',
                           (ticket_id,))

async def send_supp_msg(ticket_id: int, text: str | None, is_from_user: bool,
                        type_msg: str = 'string', file_id: str | None = None,
                        channel_message_id: int | None = None) -> None:
    """Добавляет сообщение в тикет и обновляет время последней активности тикета."""
    async with get_connection() as conn:
        if type_msg == 'string':
            await conn.execute('''INSERT INTO messages
                         (ticket_id, text, is_from_user)
                         VALUES (?, ?, ?)''',
                               (ticket_id, text, is_from_user))
        else:
            await conn.execute('''INSERT INTO messages
                                (ticket_id, text, is_from_user, type_msg, file_id, channel_message_id)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                               (ticket_id, text, is_from_user, type_msg, file_id, channel_message_id))
        await conn.execute('''UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                           (ticket_id,))

async def tickets_by_user(user_id: int) -> dict[str, Any] | None:
    """Возвращает первый тикет пользователя или None, если тикетовнет."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            'SELECT id,status_for_user,type,created_at,updated_at FROM tickets WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

async def count_tickets_for_admin(type_ticket: str) -> int:
    """Считает количество тикетов заданного типа."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM tickets
               WHERE type = ? AND (under_admin_review IS NULL OR under_admin_review = 0)''',
            (type_ticket,)
        )
        result = await cursor.fetchone()
    return result[0] if result else 0

async def load_info_by_ticket(ticket_id: int) -> tuple[dict[str, Any] | None, list]:
    """Возвращает (ticket_info, messages) для тикета.

    `ticket_info` is returned as a dict with named columns from `tickets`.
    """
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''SELECT * FROM tickets WHERE id = ?''', (ticket_id,))
        ticket_row = await cursor.fetchone()
        ticket_info = None
        if ticket_row:
            columns = [column[0] for column in cursor.description]
            ticket_info = dict(zip(columns, ticket_row))
        await cursor.execute('''SELECT is_from_user,text,type_msg,file_id FROM messages WHERE ticket_id = ?''',
                             (ticket_id,))
        message_rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
        message_info = [dict(zip(columns, row)) for row in message_rows]
    return ticket_info, message_info

async def get_photo_ids_by_ticket(ticket_id: int) -> list[int]:
    """Возвращает список ID фотосообщений в тикете."""
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT id FROM messages WHERE ticket_id = ? AND type_msg = 'photo'", (ticket_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_photo_file_id(msg_id: int) -> str | None:
    """Возвращает file_id фотосообщения по ID записи в истории."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT file_id FROM messages WHERE id = ?', (msg_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def load_tickets_info(user_id: int | None = None, role: str = 'user',
                            type: str | None = None) -> tuple[str | None, list[dict[str, Any]]]:
    """Возвращает (type, список тикетов) для пользователя или админа."""
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if role == 'user':
            await cursor.execute('''SELECT title,id,status_for_user,updated_at FROM tickets WHERE user_id = ?''',
                                 (user_id,))
        elif role == 'admin':
            await cursor.execute(
                '''SELECT title,id,status_for_admin,updated_at FROM tickets
                   WHERE type = ? AND (under_admin_review IS NULL OR under_admin_review = 0)''',
                (type,)
            )
        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
        ticket_list = [dict(zip(columns, row)) for row in rows]

    return type, ticket_list

async def get_ticket_status(ticket_id: int, role: str) -> str | None:
    """Возвращает статус тикета для указанной роли ('user' или 'admin')."""
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    async with get_connection() as conn:
        cursor = await conn.execute(f'''SELECT {status_column} FROM tickets WHERE id = ?''', (ticket_id,))
        result = await cursor.fetchone()
    return result[0]

async def replace_ticket_status(ticket_id: int, status: str, role: str) -> None:
    """Обновляет статус тикета для указанной роли."""
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    async with get_connection() as conn:
        await conn.execute(f'''UPDATE tickets SET {status_column} = ? WHERE id = ?''', (status, ticket_id))

async def try_lock_ticket_for_admin(ticket_id: int, user_id: int) -> bool:
    """Пытается установить lock на тикет для администратора. Возвращает True при успехе."""
    async with get_connection() as conn:
        await conn.execute(
            '''UPDATE tickets
               SET under_admin_review = ?, opened_by_admin_at = CURRENT_TIMESTAMP
               WHERE id = ?
                 AND (under_admin_review IS NULL OR under_admin_review = 0 OR under_admin_review = ?)''',
            (user_id, ticket_id, user_id)
        )
        changes_cursor = await conn.execute('SELECT changes()')
        changes = await changes_cursor.fetchone()
    return bool(changes and changes[0] > 0)

async def clear_ticket_lock(ticket_id: int) -> None:
    """Сбрасывает lock тикета."""
    async with get_connection() as conn:
        await conn.execute(
            '''UPDATE tickets
               SET under_admin_review = NULL, opened_by_admin_at = NULL
               WHERE id = ?''',
            (ticket_id,)
        )

async def is_ticket_locked_for_admin(ticket_id: int, user_id: int) -> bool:
    """Проверяет, закреплён ли тикет за другим администратором."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT under_admin_review
               FROM tickets
               WHERE id = ?''',
            (ticket_id,)
        )
        row = await cursor.fetchone()
    if not row:
        return True
    lock_owner = row[0]
    return lock_owner not in (None, 0, user_id)

async def get_ticket_id_by_message_id(message_id: int) -> int | None:
    """Возвращает ticket_id по id сообщения в таблице messages."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT ticket_id FROM messages WHERE id = ?', (message_id,))
        row = await cursor.fetchone()
    return row[0] if row else None

async def clear_stale_ticket_locks(max_age_hours: int = 1) -> int:
    """Очищает lock у тикетов, открытых более max_age_hours назад."""
    async with get_connection() as conn:
        await conn.execute(
            '''UPDATE tickets
               SET under_admin_review = NULL, opened_by_admin_at = NULL
               WHERE under_admin_review IS NOT NULL
                 AND under_admin_review != 0
                 AND opened_by_admin_at IS NOT NULL
                 AND opened_by_admin_at <= datetime('now', ?)''',
            (f'-{max_age_hours} hours',)
        )
        changes_cursor = await conn.execute('SELECT changes()')
        changes = await changes_cursor.fetchone()
    return changes[0] if changes else 0

"""Трекер активности и напоминания"""
async def get_activity_goal_and_today_count(user_id: int) -> tuple:
    """Возвращает (goal_exercises, today_count) или (None, 0) если цель не задана."""
    today = await get_user_time_now(user_id)
    today_str = today.strftime('%Y-%m-%d')
    async with get_connection() as conn:
        cursor = await conn.execute(
            'SELECT goal_exercises FROM track_activity WHERE user_id = ?', (user_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] is None:
            return None, 0
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM exercises_logs WHERE user_id = ? AND date = ?''',
            (user_id, today_str)
        )
        count = (await cursor.fetchone())[0]
    return row[0], count

async def update_activity_goal(user_id: int, goal: int) -> None:
    """Устанавливает дневную цель по упражнениям."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_activity SET goal_exercises = ? WHERE user_id = ?',
            (goal, user_id)
        )

async def activity_set_reminder_type(user_id: int, broadcast_type: str, broadcast_interval: int | None = None) -> None:
    """Устанавливает тип и интервал напоминаний об активности."""
    async with get_connection() as conn:
        if broadcast_type == 'Smart':
            await conn.execute(
                '''UPDATE track_activity SET broadcast_type = ?, broadcast_interval = NULL,
                   last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?''',
                (broadcast_type, user_id)
            )
        else:
            await conn.execute(
                '''UPDATE track_activity SET broadcast_type = ?, broadcast_interval = ?,
                   last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?''',
                (broadcast_type, broadcast_interval, user_id)
            )

async def update_activity_reminder_sent_time(user_id: int) -> None:
    """Обновляет время последней отправки напоминания об активности."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_activity SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

async def get_users_for_activity_reminders() -> list[tuple]:
    """Возвращает пользователей с настроенными напоминаниями об активности."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
            SELECT user_id, broadcast_type, broadcast_interval, last_broadcast
            FROM track_activity
            WHERE broadcast_type IS NOT NULL AND goal_exercises IS NOT NULL
        ''')
        return await cursor.fetchall()

async def get_inactive_users_for_reminder() -> list[int]:
    """Пользователи: последняя активность > 4 дней, и last_inactivity_reminder NULL или > 4 дней."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
            SELECT u.user_id
            FROM users u
            LEFT JOIN track_activity a ON u.user_id = a.user_id
            WHERE u.last_activity < datetime('now', '-4 days')
              AND (a.last_inactivity_reminder IS NULL
                   OR a.last_inactivity_reminder < datetime('now', '-4 days'))
        ''')
        return [row[0] for row in await cursor.fetchall()]

async def update_last_inactivity_reminder(user_id: int) -> None:
    """Обновляет время последнего напоминания о неактивности."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_activity SET last_inactivity_reminder = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

"""Упражнения и спортивная статистика"""
async def is_exercise_name_exists(name: str) -> bool:
    """Проверяет, есть ли уже активное упражнение с таким названием."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT 1 FROM exercises WHERE name = ? AND is_active = 1', (name,))
        result = await cursor.fetchone()
        return result is not None

async def add_exercise_to_db(name: str, description: str, category: str, difficulty: str,
                             file_id: str | None, created_by: int,
                             channel_message_id: int | None = None) -> None:
    """Добавляет новое упражнение в базу данных."""
    async with get_connection() as conn:
        await conn.execute('''INSERT INTO exercises (name, description,
         category, difficulty, file_id, channel_message_id, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?) ''',
                           (name, description, category, difficulty, file_id, channel_message_id, created_by)
                           )

async def get_exercises_id_name(category: str, difficulty: str) -> list[tuple]:
    """Возвращает (id, name) всех упражнений (в том числе неактивных) по категории и сложности."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT id,name FROM exercises WHERE category = ? AND difficulty = ?''',
                                    (category, difficulty))
        res = await cursor.fetchall()
    return res

async def get_active_exercises(category: str, difficulty: str) -> list[tuple]:
    """Возвращает (id, name) активных упражнений по категории и сложности."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT id,name FROM exercises WHERE category = ? AND difficulty = ? AND is_active = 1''',
            (category, difficulty))
        res = await cursor.fetchall()
    return res

async def get_exercise_by_id(exercise_id: int) -> tuple | None:
    """Возвращает все поля упражнения по его ID."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT * FROM exercises WHERE id = ?''', (exercise_id,))
        res = await cursor.fetchone()
    return res

async def get_file_id_by_ex_id(ex_id: int) -> str | None:
    """Возвращает file_id прикреплённого видео для упражнения."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT file_id FROM exercises WHERE id = ?''', (ex_id,))
        res = await cursor.fetchone()
    return res[0]

async def get_exercise_media_info(ex_id: int) -> tuple:
    """Возвращает (file_id, channel_message_id) для упражнения."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT file_id, channel_message_id FROM exercises WHERE id = ?''',
            (ex_id,)
        )
        res = await cursor.fetchone()
    return res if res else (None, None)

async def update_exercise_file_id(ex_id: int, new_file_id: str) -> None:
    """Обновляет file_id для упражнения."""
    async with get_connection() as conn:
        await conn.execute(
            '''UPDATE exercises SET file_id = ? WHERE id = ?''',
            (new_file_id, ex_id)
        )
    _logger.info(f"Обновлен file_id для упражнения {ex_id}")

async def update_message_file_id(msg_id: int, new_file_id: str) -> None:
    """Обновляет file_id для фотосообщения в тикете."""
    async with get_connection() as conn:
        await conn.execute(
            '''UPDATE messages SET file_id = ? WHERE id = ?''',
            (new_file_id, msg_id)
        )
    _logger.info(f"Обновлен file_id для сообщения {msg_id}")

async def get_message_media_info(msg_id: int) -> tuple:
    """Возвращает (file_id, channel_message_id) для сообщения в тикете."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT file_id, channel_message_id FROM messages WHERE id = ?''',
            (msg_id,)
        )
        res = await cursor.fetchone()
    return res if res else (None, None)

async def get_exercise_status(ex_id: int) -> int:
    """Возвращает статус активности упражнения: 1 — активно, 0 — неактивно."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT is_active FROM exercises WHERE id = ?''',
                                    (ex_id,))
        res = await cursor.fetchone()
        return int(res[0])

async def update_exercise_in_db(ex_id: int, db_field: str, new_value: Any) -> None:
    """Обновляет указанное поле упражнения в базе данных."""
    async with get_connection() as conn:
        await conn.execute(f'''UPDATE exercises SET {db_field} = ? WHERE id = ?''',
                           (new_value, ex_id))

async def delete_exercise_in_db(ex_id: int) -> None:
    """Удаляет упражнение и все связанные записи в журнале выполнений."""
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM exercises WHERE id = ?''',
                           (ex_id,))
        await conn.execute('''DELETE FROM exercises_logs WHERE exercise_id = ?''',
                           (ex_id,))

async def get_exercise_stats() -> dict:
    """
    Собирает статистику по упражнениям:
    - общее количество
    - количество выполнений
    - популярные упражнения
    - статистика за неделю
    """
    async with get_connection() as conn:
        # Общее количество упражнений
        cursor = await conn.execute('SELECT COUNT(*) FROM exercises WHERE is_active = 1')
        total = (await cursor.fetchone())[0]

        # Общее количество выполнений
        cursor = await conn.execute('SELECT COUNT(*) FROM exercises_logs')
        total_completions = (await cursor.fetchone())[0]

        # Самые популярные упражнения
        cursor = await conn.execute('''
            SELECT e.name, COUNT(el.id) as count
            FROM exercises e
            LEFT JOIN exercises_logs el ON e.id = el.exercise_id
            WHERE e.is_active = 1
            GROUP BY e.id
            ORDER BY count DESC
            LIMIT 5
        ''')
        popular = await cursor.fetchall()

        # Статистика за последние 7 дней
        cursor = await conn.execute('''
            SELECT COUNT(*) FROM exercises_logs
            WHERE date >= DATE('now', '-7 days')
        ''')
        weekly = (await cursor.fetchone())[0]

        return {
            'total': total,
            'total_completions': total_completions,
            'popular': popular,
            'weekly': weekly
        }

async def check_ex_is_favorite(ex_id: int, user_id: int) -> bool:
    """Проверяет, находится ли упражнение в избранном у пользователя."""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT * FROM exercises_user_favorites WHERE exercise_id = ? AND user_id = ?''',
                                    (ex_id, user_id))
        res = await cursor.fetchone()
        return bool(res)

async def add_ex_to_favorite(user_id: int, ex_id: int) -> None:
    """Добавляет упражнение в избранное пользователя."""
    async with get_connection() as conn:
        await conn.execute('''INSERT INTO exercises_user_favorites (user_id,exercise_id) VALUES (?,?)''',
                           (user_id, ex_id))

async def remove_ex_from_favorite(user_id: int, ex_id: int) -> None:
    """Удаляет упражнение из избранного пользователя."""
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM exercises_user_favorites WHERE exercise_id = ? AND user_id = ?''',
                           (ex_id, user_id))

async def get_favorite_exercises(user_id: int) -> list[tuple]:
    """Возвращает список (id, name) избранных активных упражнений пользователя."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
            SELECT e.id, e.name FROM exercises e
            INNER JOIN exercises_user_favorites f ON e.id = f.exercise_id
            WHERE f.user_id = ? AND e.is_active = 1
            ORDER BY f.added_at DESC
        ''', (user_id,))
        return await cursor.fetchall()

async def add_exercise_log(user_id: int, exercise_id: int) -> None:
    """Добавляет запись о выполнении упражнения."""
    async with get_connection() as conn:
        await conn.execute(
            '''INSERT INTO exercises_logs (user_id, exercise_id) VALUES (?, ?)''',
            (user_id, exercise_id)
        )

async def get_last_exercise_log(user_id: int) -> tuple | None:
    """Возвращает (exercise_id, time) последней записи о выполнении пользователем или None."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT exercise_id, time FROM exercises_logs
               WHERE user_id = ? ORDER BY time DESC LIMIT 1''',
            (user_id,)
        )
        return await cursor.fetchone()

async def get_user_exercise_stats(user_id: int) -> dict:
    """Статистика выполнения упражнений пользователем."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM exercises_logs WHERE user_id = ?''',
            (user_id,)
        )
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute('''
            SELECT COUNT(*) FROM exercises_logs
            WHERE user_id = ? AND date >= DATE('now', '-7 days')
        ''', (user_id,))
        weekly = (await cursor.fetchone())[0]

        cursor = await conn.execute('''
            SELECT e.name, COUNT(el.id) as cnt FROM exercises_logs el
            JOIN exercises e ON e.id = el.exercise_id
            WHERE el.user_id = ?
            GROUP BY el.exercise_id
            ORDER BY cnt DESC
            LIMIT 5
        ''', (user_id,))
        top = await cursor.fetchall()

        return {'total': total, 'weekly': weekly, 'top': top}

async def get_user_exercise_stats_for_exercise(user_id: int, exercise_id: int) -> dict:
    """Статистика выполнения конкретного упражнения пользователем."""
    async with get_connection() as conn:
        cursor = await conn.execute('''
            SELECT COUNT(*) FROM exercises_logs
            WHERE user_id = ? AND exercise_id = ?
        ''', (user_id, exercise_id))
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute('''
            SELECT COUNT(*) FROM exercises_logs
            WHERE user_id = ? AND exercise_id = ? AND date >= DATE('now', '-7 days')
        ''', (user_id, exercise_id))
        weekly = (await cursor.fetchone())[0]

        return {'total': total, 'weekly': weekly}

async def get_user_full_stats(user_id: int) -> dict | None:
    """Получает полную статистику пользователя для главного меню."""
    async with get_connection() as conn:
        # Информация о пользователе
        cursor = await conn.execute(
            'SELECT username, status, created_date FROM users WHERE user_id = ?',
            (user_id,)
        )
        user_info = await cursor.fetchone()
        if not user_info:
            return None

        username, status, created_date = user_info

        # Статистика по воде
        cursor = await conn.execute(
            'SELECT goal_ml FROM track_water WHERE user_id = ?',
            (user_id,)
        )
        water_goal_row = await cursor.fetchone()
        water_goal = int(water_goal_row[0]) if water_goal_row and water_goal_row[0] else None

        # Текущее количество выпитой воды за сегодня
        today = await get_user_time_now(user_id)
        day_name = today.strftime('%A')
        cursor = await conn.execute(
            f'SELECT {day_name} FROM track_water WHERE user_id = ?',
            (user_id,)
        )
        water_today_row = await cursor.fetchone()
        water_today = int(water_today_row[0]) if water_today_row and water_today_row[0] else 0

        # Вода за неделю
        cursor = await conn.execute(
            '''SELECT COALESCE(SUM(amount), 0) FROM water_logs
               WHERE user_id = ? AND date(added_at) >= date('now', '-7 days')''',
            (user_id,)
        )
        water_total = (await cursor.fetchone())[0]

        # Статистика по активности
        cursor = await conn.execute(
            'SELECT goal_exercises FROM track_activity WHERE user_id = ?',
            (user_id,)
        )
        activity_goal_row = await cursor.fetchone()
        activity_goal = activity_goal_row[0] if activity_goal_row and activity_goal_row[0] else None

        # Упражнения выполненные сегодня
        user_time = await get_user_time_now(user_id)
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM exercises_logs WHERE user_id = ? AND date = ?''',
            (user_id, user_time.strftime('%Y-%m-%d'))
        )
        activity_today = (await cursor.fetchone())[0]

        # Упражнения за неделю
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM exercises_logs
               WHERE user_id = ? AND date >= DATE('now', '-7 days')''',
            (user_id,)
        )
        activity_weekly = (await cursor.fetchone())[0]

        # Статистика по сну
        cursor = await conn.execute(
            'SELECT sleep_time, wake_time FROM track_sleep WHERE user_id = ?', (user_id,)
        )
        sleep_row = await cursor.fetchone()
        sleep_time_val = sleep_row[0] if sleep_row else None
        wake_time_val = sleep_row[1] if sleep_row else None

        cursor = await conn.execute(
            '''SELECT AVG(duration), COUNT(*) FROM sleep_logs
               WHERE user_id = ? AND wake_up IS NOT NULL AND wake_up >= datetime('now', '-7 days')''',
            (user_id,)
        )
        sleep_week_row = await cursor.fetchone()
        sleep_avg = int(sleep_week_row[0]) if sleep_week_row and sleep_week_row[0] else None
        sleep_week_count = sleep_week_row[1] if sleep_week_row else 0

        return {
            'username': username,
            'status': status,
            'created_date': created_date,
            'water': {
                'goal': water_goal,
                'today': water_today,
                'total': water_total
            },
            'activity': {
                'goal': activity_goal,
                'today': activity_today,
                'weekly': activity_weekly
            },
            'sleep': {
                'sleep_time': sleep_time_val,
                'wake_time': wake_time_val,
                'avg_duration': sleep_avg,
                'week_count': sleep_week_count
            }
        }

"""Сон и напоминания о сне"""
async def get_sleep_settings(user_id: int) -> tuple | None:
    """Возвращает (sleep_time, wake_time, reminders_enabled) или None."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            'SELECT sleep_time, wake_time, reminders_enabled FROM track_sleep WHERE user_id = ?',
            (user_id,)
        )
        return await cursor.fetchone()

async def update_sleep_time(user_id: int, sleep_time: str) -> None:
    """Устанавливает время отбоя для пользователя."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_sleep SET sleep_time = ? WHERE user_id = ?',
            (sleep_time, user_id)
        )

async def update_wake_time(user_id: int, wake_time: str) -> None:
    """Устанавливает время подъёма для пользователя."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_sleep SET wake_time = ? WHERE user_id = ?',
            (wake_time, user_id)
        )

async def toggle_sleep_reminders(user_id: int) -> bool:
    """Переключает состояние напоминаний сна и возвращает новое значение."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_sleep SET reminders_enabled = 1 - reminders_enabled WHERE user_id = ?',
            (user_id,)
        )
        cursor = await conn.execute(
            'SELECT reminders_enabled FROM track_sleep WHERE user_id = ?', (user_id,)
        )
        result = await cursor.fetchone()
    return bool(result[0])

async def log_sleep_start(user_id: int) -> None:
    """Начинает новую сессию сна, закрывая незакрытые."""
    now_user = await get_user_time_now(user_id)
    now_str = now_user.strftime('%Y-%m-%d %H:%M:%S')
    async with get_connection() as conn:
        # Закрываем незакрытые сессии
        await conn.execute(
            '''UPDATE sleep_logs SET wake_up = ?,
               duration = CAST((julianday(?) - julianday(sleep_start)) * 1440 AS INTEGER)
               WHERE user_id = ? AND wake_up IS NULL''',
            (now_str, now_str, user_id)
        )
        await conn.execute(
            'INSERT INTO sleep_logs (user_id, sleep_start) VALUES (?, ?)',
            (user_id, now_str)
        )

async def log_wake_up(user_id: int, max_sleep_minutes: int) -> tuple[int, bool] | None:
    """Закрывает активную сессию сна. Возвращает (длительность в минутах, был_ли_лимит_18ч) или None."""
    now_user = await get_user_time_now(user_id)
    now_str = now_user.strftime('%Y-%m-%d %H:%M:%S')
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT id, sleep_start FROM sleep_logs
               WHERE user_id = ? AND wake_up IS NULL ORDER BY logged_at DESC LIMIT 1''',
            (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        log_id, sleep_start = row
        # Парсим с запасным форматом для старых записей с микросекундами
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
            try:
                sleep_start_dt = datetime.strptime(sleep_start[:26], fmt)
                break
            except ValueError:
                continue
        else:
            _logger.error(f"log_wake_up: не удалось распарсить sleep_start='{sleep_start}', сессия удалена")
            await conn.execute('DELETE FROM sleep_logs WHERE id = ?', (log_id,))
            return None
        duration = int((now_user - sleep_start_dt).total_seconds() / 60)
        capped = False
        if duration > max_sleep_minutes:
            duration = max_sleep_minutes
            capped = True
        await conn.execute(
            'UPDATE sleep_logs SET wake_up = ?, duration = ? WHERE id = ?',
            (now_str, duration, log_id)
        )
    return duration, capped

async def get_open_sleep_session(user_id: int) -> tuple | None:
    """Возвращает активную (незакрытую) сессию сна (id, sleep_start) или None."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT id, sleep_start FROM sleep_logs
               WHERE user_id = ? AND wake_up IS NULL ORDER BY logged_at DESC LIMIT 1''',
            (user_id,)
        )
        return await cursor.fetchone()

async def get_last_sleep_log(user_id: int) -> tuple | None:
    """Возвращает последнюю завершённую запись (id, sleep_start, wake_up, duration)."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT id, sleep_start, wake_up, duration FROM sleep_logs
               WHERE user_id = ? AND wake_up IS NOT NULL ORDER BY wake_up DESC LIMIT 1''',
            (user_id,)
        )
        return await cursor.fetchone()

async def get_sleep_week_stats(user_id: int) -> tuple:
    """Возвращает (count, avg_duration, min_duration, max_duration) за 7 дней."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT COUNT(*), AVG(duration), MIN(duration), MAX(duration)
               FROM sleep_logs WHERE user_id = ? AND wake_up IS NOT NULL
               AND wake_up >= datetime('now', '-7 days')''',
            (user_id,)
        )
        return await cursor.fetchone()

async def get_sleep_history(user_id: int, limit: int = 7) -> list[tuple]:
    """Возвращает последние завершённые записи (sleep_start, wake_up, duration)."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT sleep_start, wake_up, duration FROM sleep_logs
               WHERE user_id = ? AND wake_up IS NOT NULL ORDER BY wake_up DESC LIMIT ?''',
            (user_id, limit)
        )
        return await cursor.fetchall()

async def get_users_for_sleep_reminders() -> list[tuple]:
    """Пользователи с настроенными временами и включёнными напоминаниями.
    Возвращает: (ID пользователя, sleep_time, wake_time, timezone, last_sleep_reminder, last_wake_reminder, last_notification)"""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT ts.user_id, ts.sleep_time, ts.wake_time, ts.timezone,
               ts.last_sleep_reminder, ts.last_wake_reminder, u.last_notification
               FROM track_sleep ts
               JOIN users u ON ts.user_id = u.user_id
               WHERE ts.sleep_time IS NOT NULL AND ts.wake_time IS NOT NULL
               AND ts.reminders_enabled = 1'''
        )
        return await cursor.fetchall()

async def get_last_notification(user_id: int) -> datetime | None:
    """Возвращает время последнего уведомления пользователю или None."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            'SELECT last_notification FROM users WHERE user_id = ?', (user_id,)
        )
        row = await cursor.fetchone()
    if row and row[0]:
        try:
            return datetime.fromisoformat(row[0][:19])
        except Exception:
            return None
    return None

async def update_last_notification(user_id: int) -> None:
    """Обновляет время последнего уведомления пользователю."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE users SET last_notification = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

async def update_sleep_last_sleep_reminder(user_id: int) -> None:
    """Обновляет время последнего напоминания об отбое."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_sleep SET last_sleep_reminder = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

async def update_sleep_last_wake_reminder(user_id: int) -> None:
    """Обновляет время последнего напоминания о подъёме."""
    async with get_connection() as conn:
        await conn.execute(
            'UPDATE track_sleep SET last_wake_reminder = CURRENT_TIMESTAMP WHERE user_id = ?',
            (user_id,)
        )

async def get_all_sleep_settings_for_quiet_hours() -> dict:
    """Возвращает {ID пользователя: (sleep_time, wake_time, timezone)} для тихих часов."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT user_id, sleep_time, wake_time, timezone
               FROM track_sleep WHERE sleep_time IS NOT NULL AND wake_time IS NOT NULL'''
        )
        rows = await cursor.fetchall()
    return {row[0]: (row[1], row[2], row[3] or 0) for row in rows}

"""XP, рейтинг и административные действия"""
def xp_to_level(xp: int, xp_per_level: int) -> int:
    """Вычисляет уровень по количеству XP."""
    return 1 + xp // xp_per_level

def xp_for_next_level(xp: int, xp_per_level: int) -> int:
    """XP нужно до следующего уровня."""
    return xp_per_level - (xp % xp_per_level)

async def add_xp(user_id: int, action: str, xp_rewards: dict[str, int], xp_per_level: int) -> dict:
    """
    Начисляет очки пользователю и обновляет уровень.
    Возвращает dict: {xp_gained, old_level, new_level, total_xp, leveled_up}.
    """
    gained = xp_rewards.get(action, 0)
    if gained == 0:
        return {'xp_gained': 0, 'leveled_up': False, 'new_level': 1, 'total_xp': 0, 'old_level': 1}
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT xp, level FROM user_xp WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        if not row:
            await conn.execute('INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, ?)',
                               (user_id, 0, 1))
            old_xp, old_level = 0, 1
        else:
            old_xp, old_level = row
        new_xp = old_xp + gained
        new_level = xp_to_level(new_xp, xp_per_level)
        await conn.execute('UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ?',
                           (new_xp, new_level, user_id))
        await conn.execute('INSERT INTO xp_log (user_id, action, xp_gained) VALUES (?, ?, ?)',
                           (user_id, action, gained))
    return {
        'xp_gained': gained,
        'old_level': old_level,
        'new_level': new_level,
        'total_xp': new_xp,
        'leveled_up': new_level > old_level,
    }

async def get_user_xp(user_id: int) -> tuple:
    """Возвращает (xp, level)."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT xp, level FROM user_xp WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
    return (row[0], row[1]) if row else (0, 1)

async def get_leaderboard(limit: int = 20) -> list:
    """
    Возвращает топ-N: [(rank, user_id, username, xp, level), ...]
    Только пользователи с xp > 0.
    """
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT u.user_id, u.username, x.xp, x.level
               FROM user_xp x
               JOIN users u ON u.user_id = x.user_id
               WHERE x.xp > 0
               ORDER BY x.xp DESC
               LIMIT ?''',
            (limit,)
        )
        rows = await cursor.fetchall()
    return [(i + 1, row[0], row[1], row[2], row[3]) for i, row in enumerate(rows)]

async def get_user_rank(user_id: int) -> int | None:
    """Возвращает позицию пользователя в глобальном топе или None."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            '''SELECT COUNT(*) FROM user_xp
               WHERE xp > (SELECT xp FROM user_xp WHERE user_id = ?)''',
            (user_id,)
        )
        row = await cursor.fetchone()
    return (row[0] + 1) if row else None

async def admin_set_xp(user_id: int, delta: int, xp_per_level: int) -> int:
    """Прибавляет (или вычитает при delta < 0) XP пользователю.
    Возвращает новое значение XP."""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT xp, level FROM user_xp WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        if not row:
            await conn.execute('INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, ?)', (user_id, 0, 1))
            current_xp = 0
        else:
            current_xp = row[0]
        new_xp = max(0, current_xp + delta)
        new_level = xp_to_level(new_xp, xp_per_level)
        await conn.execute('UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ?', (new_xp, new_level, user_id))
    return new_xp

