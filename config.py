import json
from database import get_user_status
from dotenv import load_dotenv
import os

def load_owners():
    try:
        with open('owners.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ Ошибка загрузки owners.json: {e}. Создаю файл с пустым списком.")
        with open('owners.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []

load_dotenv()
token = os.getenv('token_bot')  # Токен бота
if not token:
    raise ValueError("BOT_TOKEN не найден в .env файле!")
owners = load_owners()
owners_copy = owners[:]
ai_censor_enabled = False
censorship_threshold = 0.5 #Порог срабатывания AI цензуры

def save_owners():
    with open('owners.json', 'w', encoding='utf-8') as f:
        json.dump(owners, f, indent=2)


async def is_admin(user_id=None, username=None):
    if user_id:
        return await get_user_status(user_id=user_id) in ['Admin', 'Owner']
    elif username:
        return await get_user_status(username=username) in ['Admin', 'Owner']
    return None


def is_owner(user_id):
    return user_id in owners
