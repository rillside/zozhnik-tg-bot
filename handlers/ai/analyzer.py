import logging
from datetime import datetime
from typing import Any

from database import get_user_full_stats
from .client import ask_ollama
from .promts import SYSTEM_PROMPT
from config import ai_analyzer_enabled
from messages import ai_analyze_off_msg

_logger = logging.getLogger(__name__)


def _build_profile_text(stats: dict, first_name: str) -> str:
    """Конвертирует словарь статистики в читаемый текст для AI."""
    lines = [f"Пользователь: {first_name}"]

    try:
        reg_date = datetime.strptime(stats['created_date'], '%Y-%m-%d %H:%M:%S')
        days = (datetime.now() - reg_date).days
        lines.append(f"Дней на платформе: {days}")
    except Exception:
        pass

    # Вода
    water = stats.get('water', {})
    if water.get('goal'):
        goal = water['goal']
        today = water.get('today', 0)
        pct = round(today / goal * 100) if goal else 0
        weekly = water.get('total', 0)
        lines.append("\nВодный баланс:")
        lines.append(f"  Дневная цель: {goal} мл")
        lines.append(f"  Выпито сегодня: {today} мл ({pct}% от цели)")
        lines.append(f"  За последнюю неделю: {weekly} мл")
    else:
        lines.append("\nВодный баланс: трекер не настроен")

    # Активность
    activity = stats.get('activity', {})
    if activity.get('goal'):
        goal_a = activity['goal']
        today_a = activity.get('today', 0)
        weekly_a = activity.get('weekly', 0)
        pct_a = round(today_a / goal_a * 100) if goal_a else 0
        lines.append("\nФизическая активность:")
        lines.append(f"  Дневная цель: {goal_a} упражнений")
        lines.append(f"  Выполнено сегодня: {today_a} ({pct_a}% от цели)")
        lines.append(f"  За последнюю неделю: {weekly_a} упражнений")
    else:
        lines.append("\nФизическая активность: трекер не настроен")

    # Сон
    sleep = stats.get('sleep', {})
    if sleep.get('sleep_time') and sleep.get('wake_time'):
        avg = sleep.get('avg_duration')
        week_count = sleep.get('week_count', 0)
        lines.append("\nСон:")
        lines.append(f"  Режим: отбой в {sleep['sleep_time']}, подъём в {sleep['wake_time']}")
        lines.append(f"  Сессий за неделю: {week_count}")
        if avg:
            h, m = divmod(int(avg), 60)
            lines.append(f"  Среднее время сна: {h}ч {m}мин")
        else:
            lines.append("  Данных о продолжительности пока нет")
    else:
        lines.append("\nСон: трекер не настроен")

    return "\n".join(lines)


async def ai_analyze_profile(call: Any, bot: Any) -> None:
    """Обрабатывает нажатие кнопки «ИИ-анализ профиля»: собирает статистику, вызывает Ollama и отправляет анализ."""
    if not ai_analyzer_enabled:
        await bot.answer_callback_query(call.id, ai_analyze_off_msg, show_alert=True)
        return
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "Пользователь"

    await bot.answer_callback_query(call.id)
    # Показываем индикатор ожидания
    try:
        await bot.edit_message_text(
            "⏳ Анализирую профиль...\n\nЭто займёт несколько секунд — модель думает 🤔",
            call.message.chat.id,
            call.message.message_id,
        )
    except Exception:
        pass

    # Загружаем данные
    stats = await get_user_full_stats(user_id)
    if not stats:
        await bot.send_message(user_id, "❌ Не удалось загрузить данные профиля.")
        return

    # Формируем профиль и вызываем Ollama
    profile_text = _build_profile_text(stats, first_name)
    _logger.info(f"AI-анализ запрошен для ID пользователя={user_id}")

    result = await ask_ollama(SYSTEM_PROMPT, profile_text)

    if result is None:
        await bot.send_message(call.message.chat.id, ai_analyze_off_msg, show_alert=True)
    else:
        _logger.info(f"AI-анализ успешно выполнен для ID пользователя={user_id}, символов: {len(result)}")
        await bot.send_message(user_id, result, parse_mode=None)
