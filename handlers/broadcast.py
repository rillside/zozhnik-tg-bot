import logging
import re
import time

from config import is_owner, owners, save_owners, censorship_threshold,ai_censor
from database import all_users, replace_status
from handlers.admin_notifications import admin_censorship_violation
from handlers.broadcast.filtres_censor import banned_phrases, banned_words
from keyboards import accept_send
from messages import broadcast_stats
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
if ai_censor:
    try:
        logging.info("Начата загрузка AI модели...")
        from detoxify import Detoxify
        toxicity_checker = Detoxify('original')  # Модель unitary/toxic-bert
        logging.info("AI Модель загружена")
    except Exception as e:
        logging.warn(f"Ошибка загрузки Detoxify. AI проверка в рассылке отключена\n{e}")
        toxicity_checker = None
else:
    toxicity_checker = None
    logging.info("AI проверка в рассылке отключена")

def ai_censor(text):
    if toxicity_checker is None:
        return False

    try:
        result = toxicity_checker.predict(text[:1024])
        print(result)
        return any(score > censorship_threshold for score in result.values())
    except Exception as e:
        print(f"Ошибка нейросети: {e}")
        return False


def censor_broadcast(text):
    words = set(re.sub(r'[^\w\s]', ' ', text.lower()).split())
    if any(i in words for i in banned_words):
        print('word')
        return False

    elif any(i in text.lower() for i in banned_phrases):
        print('pharses')
        return False
    elif ai_censor(text):
        print('ai')
        return False
    return True


def accept_broadcast(message, bot):
    if message.text.strip():
        bot.send_message(message.chat.id, f"📋 Предпросмотр:\n{message.text}", reply_markup=accept_send())


def broadcast_send(call, bot):
    message = call.message.text.split(':', 1)[1]
    sender_id = call.message.chat.id
    sender_username = call.from_user.username
    sender = '@' + sender_username if sender_username is not None else sender_id
    unsucc = 0
    succ = 0
    if censor_broadcast(message):
        for i in all_users():
            try:
                bot.send_message(
                    i, message +
                       f"\n\n📨 Отправитель: {sender}" if is_owner(i) else message
                )
                time.sleep(0.07)
                succ += 1
            except Exception as e:
                unsucc += 1
                print(f"Ошибка при отправке рассылки {i}:\n{e}")
        bot.send_message(call.message.chat.id, broadcast_stats(succ, unsucc))
    else:
        replace_status('User', user_id=sender_id)
        if is_owner(sender_id):
            owners.remove(sender_id)
            save_owners()
        admin_censorship_violation(bot, message, sender_id, sender_username)
