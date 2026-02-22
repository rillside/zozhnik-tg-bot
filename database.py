import logging
import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime, timedelta


@asynccontextmanager
async def get_connection():
    conn = None
    try:
        conn = await aiosqlite.connect('database.db')
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.execute("PRAGMA busy_timeout = 10000")
        yield conn
        await conn.commit()

    except Exception as e:
        if conn:
            await conn.rollback()
        raise e

    finally:
        if conn:
            await conn.close()


async def init_db():
    async with get_connection() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                status TEXT,
                timezone INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await conn.execute('''
                CREATE TABLE IF NOT EXISTS track_water (
                    user_id INTEGER PRIMARY KEY,
                    timezone INTEGER,
                    broadcast_type TEXT,
                    broadcast_interval TIME,
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
                    last_reset TEXT
                )
            ''')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            week_start TEXT
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
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
            )
            ''')
        await conn.execute('''
                        CREATE TABLE IF NOT EXISTS exercises_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            exercise_id INTEGER,
                            date DATE DEFAULT CURRENT_DATE,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,    
                text TEXT,              
                is_from_user BOOLEAN,
                type_msg TEXT DEFAULT 'string',
                file_id TEXT DEFAULT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')


async def add_user(user_id, username, status):
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
            await conn.execute('''INSERT INTO track_water (user_id)
                              VALUES (?) '''
                               , (user_id,))
            logging.info(f"Added new user: {user_id} - {'@' + username} - {status}")


async def all_users():
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT * FROM users')
        users = await cursor.fetchall()
    return [user[0] for user in users]


async def get_new_users_count(days):
    async with get_connection() as conn:
        cursor = await conn.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE created_date >= datetime('now', ?)
    ''', (f'-{days} days',))
        result = await cursor.fetchone()
    return result[0]


async def update_user_activity_smart(user_id):
    async with get_connection() as conn:
        await conn.execute('''
        UPDATE users 
        SET last_activity = CURRENT_TIMESTAMP 
        WHERE user_id = ? AND (
            last_activity IS NULL OR 
            last_activity < datetime('now', '-1 hours')
        )
        ''', (user_id,))


async def get_active_users_count(days=4):
    async with get_connection() as conn:
        cursor = await conn.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE last_activity >= datetime('now', ?)
        ''', (f'-{days} days',))
        result = await cursor.fetchone()
    return result[0]


async def get_user_status(user_id=None, username=None):
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if user_id:
            await cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()

        elif username:
            await cursor.execute('SELECT status FROM users WHERE username = ?', (username,))
            result = await cursor.fetchone()
    return result[0] if result else 'User'


async def get_all_admin(only_admin=True):
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


async def is_user_valid(user_id=None, username=None):
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


async def replace_status(status, user_id=None, username=None):
    async with get_connection() as conn:
        cursor = await conn.cursor()

        if user_id:
            await cursor.execute('UPDATE users SET status = ? WHERE user_id = ?',
                                 (status, user_id))
        elif username:
            await cursor.execute('UPDATE users SET status = ? WHERE username = ?',
                                 (status, username))


async def get_id_by_username(username):
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        result = await cursor.fetchone()
    return result[0]


async def get_username_by_id(user_id):
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
    return result[0]


async def update_username(user_id, username, bot):
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


async def water_set_reminder_type(user_id, broadcast_type, broadcast_interval=None):
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


async def update_reminder_sent_time(user_id):
    async with get_connection() as conn:
        await conn.execute('''UPDATE track_water SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?''',
                           (user_id,))


async def update_water_goal(user_id, new_goal):
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET goal_ml = ? WHERE user_id = ?',
                           (new_goal, user_id)
                           )


async def count_users_trackers(db_table, column_name, user_id=None):
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


async def add_water_ml(user_id, volume_ml, add_total=True):
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


async def water_stats(user_id):
    today = await get_user_time_now(user_id)
    day_name = today.strftime('%A')
    async with get_connection() as conn:
        cursor = await conn.execute(f'SELECT goal_ml,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
        result = map(int, await cursor.fetchone())
    return result


async def set_timezone(user_id, new_timezone):
    async with get_connection() as conn:
        await conn.execute('UPDATE users SET timezone = ? WHERE user_id = ? ', (new_timezone, user_id))
        await conn.execute('UPDATE track_water SET timezone = ? WHERE user_id = ?', (new_timezone, user_id))


async def get_timezone(user_id):
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
    return result[0] if result else None


async def get_user_time_now(user_id):
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        hours_diff = await cursor.fetchone()
    return datetime.now() + timedelta(hours=hours_diff[0])


async def update_last_add_water_ml(user_id):
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET last_update = CURRENT_TIMESTAMP WHERE user_id = ?',
                           (user_id,))


async def get_water_stats_for_today(user_id):
    today = await get_user_time_now(user_id)
    day_name = today.strftime('%A')
    async with get_connection() as conn:
        cursor = await conn.execute(f'SELECT last_update,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
        update_time, cnt_water = await cursor.fetchone()
    return update_time, cnt_water


async def fetch_water_stats_all():
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''SELECT user_id,goal_ml,timezone,Monday,Tuesday,
        Wednesday,Thursday,Friday,Saturday,Sunday,last_reset
         FROM track_water''')
        return await cursor.fetchall()


async def set_last_reset_water(user_id, last_reset):
    async with get_connection() as conn:
        await conn.execute('UPDATE track_water SET last_reset = ? WHERE user_id = ?', (last_reset, user_id))


async def water_reset(user_id):
    async with get_connection() as conn:
        await conn.execute('''UPDATE track_water SET Monday = 0,Tuesday = 0,
        Wednesday = 0,Thursday = 0,Friday = 0,Saturday = 0,Sunday = 0 WHERE USER_ID = ?''', (user_id,))


async def get_lost_records_of_water(user_id):
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT id,amount,week_start FROM water_logs WHERE user_id = ?''', (user_id,))
        return await cursor.fetchall()


async def delete_water_log(log_id):
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM water_logs WHERE id = ?''', (log_id,))


async def add_ticket(title, user_id, username, first_name, type_supp):
    async with get_connection() as conn:
        cursor = await conn.execute('''INSERT INTO tickets (title,user_id,username,first_name,type)
                      VALUES (?,?,?,?,?)''',
                                    (title, user_id, username, first_name, type_supp))
        ticket_id = cursor.lastrowid
    return ticket_id


async def delete_ticket(ticket_id):
    async with get_connection() as conn:
        await conn.execute('''DELETE FROM tickets WHERE id = ?''',
                           (ticket_id,))


async def send_supp_msg(ticket_id, text, is_from_user, type_msg='string', file_id=None):
    async with get_connection() as conn:
        if type_msg == 'string':
            await conn.execute('''INSERT INTO messages
                         (ticket_id, text, is_from_user)
                         VALUES ( ?, ?, ?,?)''',
                               (ticket_id, text, is_from_user))
        else:
            await conn.execute('''INSERT INTO messages 
                                (ticket_id, text, is_from_user,type_msg,file_id)
                                VALUES ( ?, ?, ?,?,?)''',
                               (ticket_id, text, is_from_user, type_msg, file_id))
        await conn.execute('''UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                           (ticket_id,))


async def tickets_by_user(user_id):
    async with get_connection() as conn:
        cursor = await conn.execute(
            'SELECT id,status_for_user,type,created_at,updated_at FROM tickets WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
    return result


async def count_tickets_for_admin(type_ticket):
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT COUNT(*) FROM tickets WHERE type = ?''', (type_ticket,))
        result = await cursor.fetchone()
    return result[0] if result else 0


async def load_info_by_ticket(ticket_id):
    async with get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''SELECT * FROM tickets WHERE id = ?''', (ticket_id,))
        ticket_info = await cursor.fetchone()
        await cursor.execute('''SELECT is_from_user,text,type_msg,file_id FROM messages WHERE ticket_id = ?''',
                             (ticket_id,))
        message_info = await cursor.fetchall()
    return ticket_info, message_info


async def get_photo_ids_by_ticket(ticket_id):
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT id FROM messages WHERE ticket_id = ? AND type_msg = 'photo'", (ticket_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_photo_file_id(msg_id):
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT file_id FROM messages WHERE id = ?', (msg_id,))
        result = await cursor.fetchone()
        return result[0] if result else None


async def load_tickets_info(user_id=None, role='user', type=None):
    async with get_connection() as conn:
        cursor = await conn.cursor()
        if role == 'user':
            await cursor.execute('''SELECT title,id,status_for_user,updated_at FROM tickets WHERE user_id = ?''',
                                 (user_id,))
        elif role == 'admin':
            await cursor.execute('''SELECT title,id,status_for_admin,updated_at FROM tickets WHERE type = ?''', (type,))
        ticket_list = [list(row) for row in await cursor.fetchall()]

    return type, ticket_list


async def get_ticket_status(ticket_id, role):
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    async with get_connection() as conn:
        cursor = await conn.execute(f'''SELECT {status_column} FROM tickets WHERE id = ?''', (ticket_id,))
        result = await cursor.fetchone()
    return result[0]


async def replace_ticket_status(ticket_id, status, role):
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    async with get_connection() as conn:
        await conn.execute(f'''UPDATE tickets SET {status_column} = ? WHERE id = ?''', (status, ticket_id))


async def get_users_for_water_reminders():
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT user_id,broadcast_type,broadcast_interval,
        last_broadcast,last_update FROM track_water WHERE broadcast_type IS NOT NULL''')
        result = await cursor.fetchall()
    return result


async def is_exercise_name_exists(name):
    """Проверяет, есть ли уже упражнение с таким названием"""
    async with get_connection() as conn:
        cursor = await conn.execute('SELECT 1 FROM exercises WHERE name = ? AND is_active = 1', (name,))
        result = await cursor.fetchone()
        return result is not None


async def add_exercise_to_db(name, description, category, difficulty, file_id, created_by):
    async with get_connection() as conn:
        await conn.execute('''INSERT INTO exercises (name, description,
         category, difficulty, file_id, created_by) 
                VALUES (?, ?, ?, ?, ?, ?) ''',
                           (name, description, category, difficulty, file_id, created_by)
                           )


async def get_exercises_id_name(category, difficulty):
    """Возвращает список кортежей (id, name)
    всех упражнений(даже неактивных) по заданным фильтрам"""
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT id,name FROM exercises WHERE category = ? AND difficulty = ?''',
                                    (category, difficulty))
        res = await cursor.fetchall()
    return res


async def get_exercise_by_id(exercise_id):
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT * FROM exercises WHERE id = ?''', (exercise_id,))
        res = await cursor.fetchone()
    return res


async def get_file_id_by_ex_id(ex_id):
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT file_id FROM exercises WHERE id = ?''', (ex_id,))
        res = await cursor.fetchone()
    return res[0]


async def get_exercise_status(ex_id):
    async with get_connection() as conn:
        cursor = await conn.execute('''SELECT is_active FROM exercises WHERE id = ?''',
                                    (ex_id,))
        res = await cursor.fetchone()
        return int(res[0])


async def update_exercise_in_db(ex_id, db_field, new_value):
    async with get_connection() as conn:
        await conn.execute(f'''UPDATE exercises SET {db_field} = ? WHERE id = ?''',
                           (new_value, ex_id))
async def delete_exercise_in_db (ex_id):
    async with get_connection() as conn:
        await conn.execute(f'''DELETE FROM exercises WHERE id = ?''',
                           (ex_id,))
        await conn.execute(f'''DELETE FROM exercises_logs WHERE exercise_id = ?''',
                           (ex_id,))


async def get_exercise_stats():
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
        cursor = await conn.execute('SELECT COUNT(*) FROM user_exercises')
        total_completions = (await cursor.fetchone())[0]

        # Самые популярные упражнения
        cursor = await conn.execute('''
            SELECT e.name, COUNT(ue.id) as count 
            FROM exercises e
            LEFT JOIN user_exercises ue ON e.id = ue.exercise_id
            WHERE e.is_active = 1
            GROUP BY e.id
            ORDER BY count DESC
            LIMIT 5
        ''')
        popular = await cursor.fetchall()

        # Статистика за последние 7 дней
        cursor = await conn.execute('''
            SELECT COUNT(*) FROM user_exercises 
            WHERE date >= DATE('now', '-7 days')
        ''')
        weekly = (await cursor.fetchone())[0]

        return {
            'total': total,
            'total_completions': total_completions,
            'popular': popular,
            'weekly': weekly
        }