import logging

import aiohttp

_logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:4b"
_TIMEOUT = aiohttp.ClientTimeout(total=120)


async def ask_ollama(system_prompt: str, user_message: str) -> str | None:
    """
    Отправляет запрос в локальный Ollama.
    Возвращает текст ответа или None при ошибке.
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    _logger.error(f"Ollama вернул {resp.status}: {body}")
                    return None
                data = await resp.json()
                return data["message"]["content"].strip()

    except aiohttp.ClientConnectorError:
        _logger.error("Ollama недоступна (соединение отклонено). Убедитесь, что запущен 'ollama serve'")
        return None
    except aiohttp.ServerTimeoutError:
        _logger.error("Ollama не ответила за 120 секунд")
        return None
    except Exception as e:
        _logger.error(f"Ошибка запроса к Ollama: {e}")
        return None
