import logging
import sqlite3
import time
from datetime import datetime, timedelta


def get_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")  # Для лучшей производительности
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            status TEXT,
            timezone INTEGER,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS track_water (
                user_id INTEGER PRIMARY KEY,
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
                last_update TIMESTAMP
            )
        ''')
    cursor.execute('''
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,    
            text TEXT,              
            is_from_user BOOLEAN,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    conn.commit()
    conn.close()


def add_user(user_id, username, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute('''
            UPDATE users 
            SET username = ?, status = ?, last_activity = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (username, status, user_id))
    else:
        cursor.execute('''
            INSERT INTO users (user_id, username, status) 
            VALUES (?, ?, ?)
        ''', (user_id, username, status))
        cursor.execute('''INSERT INTO track_water (user_id)
                          VALUES (?) '''
                       , (user_id,))
        logging.info(f"Added new user: {user_id} - {'@' + username} - {status}")
    conn.commit()
    conn.close()


def all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users]


def get_new_users_count(days):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE created_date >= datetime('now', ?)
    ''', (f'-{days} days',))
    result = cursor.fetchone()
    conn.close()
    return result[0]


def update_user_activity_smart(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET last_activity = CURRENT_TIMESTAMP 
        WHERE user_id = ? AND (
            last_activity IS NULL OR 
            last_activity < datetime('now', '-1 hours')
        )
    ''', (user_id,))
    conn.commit()
    conn.close()


def get_active_users_count(days=4):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE last_activity >= datetime('now', ?)
    ''', (f'-{days} days',))
    result = cursor.fetchone()
    conn.close()
    return result[0]


def get_user_status(user_id=None, username=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute('SELECT status FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
    elif username:
        cursor.execute('SELECT status FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
    return result[0] if result else 'User'


def get_all_admin(only_admin=True):
    conn = get_connection()
    cursor = conn.cursor()
    status_list = ['Admin']
    if not only_admin:
        status_list.append('Owner')
    quoted_statuses = [f"'{status}'" for status in status_list]
    status_str = ','.join(quoted_statuses)
    cursor.execute(f'''
            SELECT user_id,username
            FROM users 
            WHERE status IN ({status_str})
        ''')
    result = cursor.fetchall()
    print(result)
    conn.close()
    return result


def is_user_valid(user_id=None, username=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    elif username:
        clean_username = username.lstrip('@')
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (clean_username,))
    else:
        return False

    result = cursor.fetchone()
    conn.close()
    return result


def replace_status(status, user_id=None, username=None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute('UPDATE users SET status = ? WHERE user_id = ?',
                       (status, user_id))
    elif username:
        cursor.execute('UPDATE users SET status = ? WHERE username = ?',
                       (status, username))

    conn.commit()
    conn.close()


def get_id_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0]


def get_username_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0]


def update_username(user_id, username, bot):
    old_username = get_username_by_id(user_id)
    if old_username != username:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET username = ? WHERE user_id = ?',
            (username, user_id)

        )
        conn.commit()
        conn.close()
        if get_user_status(user_id) == 'Admin':
            from handlers.admin_notifications import admin_update_notification
            admin_update_notification(bot, user_id, old_username, username)


def water_set_reminder_type(user_id, broadcast_type, broadcast_interval=None):
    conn = get_connection()
    cursor = conn.cursor()
    if broadcast_type == "Smart":
        cursor.execute('UPDATE track_water SET broadcast_type = ?, broadcast_interval = NULL WHERE user_id = ?',
                       (broadcast_type, user_id)
                       )

    else:
        cursor.execute('UPDATE track_water SET broadcast_type = ?, broadcast_interval = ? WHERE user_id = ?',
                       (broadcast_type, broadcast_interval, user_id)
                       )
    cursor.execute('UPDATE track_water SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?',
                   (user_id, ))
    conn.commit()
    conn.close()
def update_reminder_sent_time(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE track_water SET last_broadcast = CURRENT_TIMESTAMP WHERE user_id = ?''',
                   (user_id, ))
    conn.commit()
    conn.close()

def update_water_goal(user_id, new_goal):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE track_water SET goal_ml = ? WHERE user_id = ?',
                   (new_goal, user_id)
                   )
    conn.commit()
    conn.close()


def count_users_trackers(db_table, column_name, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute(f'''
                    SELECT COUNT(*) 
                    FROM {db_table} 
                    WHERE user_id = ? 
                    AND {column_name} IS NOT NULL
                ''', (user_id,))
        result = cursor.fetchone()[0]
    else:
        cursor.execute(f'''SELECT COUNT(*) 
        FROM {db_table} 
        WHERE {column_name} IS NOT NULL ''')
        result = cursor.fetchone()[0]
    conn.close()
    return result


def add_water_ml(user_id, volume_ml):
    today = get_user_time_now(user_id)
    day_name = today.strftime('%A')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'UPDATE track_water SET {day_name} ={day_name} + ? WHERE user_id = ?',
                   (volume_ml, user_id))
    conn.commit()
    conn.close()


def water_stats(user_id):
    today = get_user_time_now(user_id)
    day_name = today.strftime('%A')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT goal_ml,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
    result = map(int, cursor.fetchone())

    conn.close()
    return result


def set_timezone(user_id, new_timezone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET timezone = ? WHERE user_id = ? ', (new_timezone, user_id))
    conn.commit()
    conn.close()


def get_timezone(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_user_time_now(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
    hours_diff = cursor.fetchone()[0]
    conn.close()
    return datetime.now() + timedelta(hours=hours_diff)


def update_last_add_water_ml(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE track_water SET last_update = CURRENT_TIMESTAMP WHERE user_id = ?',
                   (user_id,))
    conn.commit()
    conn.close()


def get_water_stats_for_today(user_id):
    today = get_user_time_now(user_id)
    day_name = today.strftime('%A')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT last_update,{day_name} FROM track_water WHERE user_id = ?', (user_id,))
    update_time, cnt_water = cursor.fetchone()
    conn.close()
    return update_time, cnt_water



def add_ticket(title, user_id, username, first_name, type_supp):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tickets (title,user_id,username,first_name,type)
                      VALUES (?,?,?,?,?)''',
                   (title, user_id, username, first_name, type_supp))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def delete_ticket(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM tickets WHERE id = ?''',
                   (ticket_id,))
    conn.commit()
    conn.close()


def send_supp_msg(ticket_id, text, is_from_user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO messages
                     (ticket_id, text, is_from_user)
                     VALUES ( ?, ?, ?)''',
                   (ticket_id, text, is_from_user))
    cursor.execute('''UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                   (ticket_id,))
    conn.commit()
    conn.close()


def tickets_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id,status_for_user,type,created_at,updated_at FROM tickets WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def count_tickets_for_admin(type_ticket):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(*) FROM tickets WHERE type = ?''',(type_ticket,))
    result = cursor.fetchone()
    return result[0] if result else 0

def load_info_by_ticket(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM tickets WHERE id = ?''', (ticket_id,))
    ticket_info = cursor.fetchone()
    cursor.execute('''SELECT is_from_user,text FROM messages WHERE ticket_id = ?''', (ticket_id,))
    message_info = cursor.fetchall()
    conn.close()
    return ticket_info, message_info


def load_tickets_info(user_id=None, role='user',type=None):
    conn = get_connection()
    cursor = conn.cursor()
    if role == 'user':
        cursor.execute('''SELECT title,id,status_for_user,updated_at FROM tickets WHERE user_id = ?''', (user_id,))
    elif role == 'admin':
        cursor.execute('''SELECT title,id,status_for_admin,updated_at FROM tickets WHERE type = ?''', (type,) )
    ticket_list = [list(row) for row in cursor.fetchall()]
    conn.close()
    return type,ticket_list


def get_ticket_status(ticket_id, role):
    conn = get_connection()
    cursor = conn.cursor()
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    cursor.execute(f'''SELECT {status_column} FROM tickets WHERE id = ?''', (ticket_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0]


def replace_ticket_status(ticket_id, status, role):
    conn = get_connection()
    cursor = conn.cursor()
    status_column = 'status_for_user' if role == 'user' else 'status_for_admin'
    cursor.execute(f'''UPDATE tickets SET {status_column} = ? WHERE id = ?''', (status, ticket_id))
    conn.commit()
    conn.close()
def get_users_for_water_reminders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT user_id,broadcast_type,broadcast_interval,
    last_broadcast,last_update FROM track_water WHERE broadcast_type IS NOT NULL''')
    result = cursor.fetchall()
    conn.close()
    return result
