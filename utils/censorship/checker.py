import logging
import re
import asyncio
from typing import Any
from database import replace_status
from handlers.admin_notifications import admin_censorship_violation
from utils.censorship.word_filter import banned_words, banned_phrases
from config import ai_censor_enabled, censorship_threshold, is_owner, owners, save_owners

_logger = logging.getLogger(__name__)
toxicity_checker = None
async def censor_load() -> None:
    """Загружает ИИ-модель цензуры (Detoxify), если она включена в конфигурации."""
    global toxicity_checker
    if ai_censor_enabled:
        try:
            _logger.info("Начата загрузка ИИ-модели...")
            from detoxify import Detoxify
            toxicity_checker = Detoxify('original')  # Модель unitary/toxic-bert
            _logger.info("ИИ-модель загружена")
        except Exception as e:
            _logger.warn(f"Ошибка загрузки Detoxify. ИИ-цензура отключена\n{e}")
            toxicity_checker = None
    else:
        toxicity_checker = None
        _logger.info("ИИ-цензура отключена")

async def ai_censor(text: str) -> bool:
    """Проверяет текст через ИИ-модель. Возвращает `True`, если текст превышает порог токсичности."""

    if toxicity_checker is None:
        return False

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            toxicity_checker.predict,
            text[:1024]
        )
        return any(score > censorship_threshold for score in result.values())
    except Exception as e:
        _logger.warn(f"Ошибка при работе ИИ-цензуры: {e}")
        return False


async def censor_check(text: str) -> bool:
    """Проверяет текст на наличие запрещённых слов, фраз и ИИ-токсичности. Возвращает `True`, если текст прошёл проверку."""
    words = set(re.sub(r'[^\w\s]', ' ', text.lower()).split())
    if any(i in words for i in banned_words):
        return False

    elif any(i in text.lower() for i in banned_phrases):
        return False
    elif await ai_censor(text):
        return False
    return True
async def removal_of_admin_rights(bot: Any, message: Any, sender_id: int, sender_username: str | None, content_type: str) -> None:
    """Снимает права администратора за нарушение цензуры и уведомляет владельцев."""
    await replace_status('User', user_id=sender_id)
    if is_owner(sender_id):
        owners.remove(sender_id)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, save_owners)
    await admin_censorship_violation(bot, message, sender_id, sender_username,content_type)
