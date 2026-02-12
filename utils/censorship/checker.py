import logging
import re

from database import replace_status
from handlers.admin_notifications import admin_censorship_violation
from utils.censorship.word_filter import banned_words, banned_phrases
from config import ai_censor, censorship_threshold, is_owner, owners, save_owners

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
        logging.warn(f"Ошибка загрузки Detoxify. AI цензура отключена\n{e}")
        toxicity_checker = None
else:
    toxicity_checker = None
    logging.info("AI цензура отключена")

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


def censor_check(text):
    words = set(re.sub(r'[^\w\s]', ' ', text.lower()).split())
    if any(i in words for i in banned_words):
        return False

    elif any(i in text.lower() for i in banned_phrases):
        return False
    elif ai_censor(text):
        return False
    return True
def removal_of_admin_rights(bot,message,sender_id,sender_username,content_type):
    replace_status('User', user_id=sender_id)
    if is_owner(sender_id):
        owners.remove(sender_id)
        save_owners()
    admin_censorship_violation(bot, message, sender_id, sender_username,content_type)