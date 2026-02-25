import asyncio
import logging

"""
Утилита для rate-limited рассылки с использованием asyncio.gather и semaphore.
"""

# Ограничение параллельных отправок для соблюдения rate limit Telegram
SEMAPHORE_LIMIT = 15

_logger = logging.getLogger(__name__)


async def _send_with_semaphore(semaphore, coro):
    """Выполняет корутину отправки с учётом semaphore."""
    async with semaphore:
        try:
            await coro
            return True
        except Exception as e:
            _logger.warning("Ошибка отправки: %s", e)
            return False


async def rate_limited_gather(send_coroutines):
    """
    Выполняет список корутин отправки с ограничением через semaphore.

    Args:
        send_coroutines: список корутин (например, bot.send_message(...))

    Returns:
        (succ, unsucc): количество успешных и неуспешных отправок
    """
    if not send_coroutines:
        return 0, 0
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    tasks = [_send_with_semaphore(semaphore, coro) for coro in send_coroutines]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    succ = sum(1 for r in results if r is True)
    unsucc = len(results) - succ
    return succ, unsucc
