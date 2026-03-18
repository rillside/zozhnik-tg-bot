from datetime import datetime
from typing import Any

from database import (
    get_last_sleep_log,
    get_open_sleep_session,
    get_sleep_history,
    get_sleep_settings,
    get_sleep_week_stats,
    get_user_time_now,
    log_sleep_start,
    log_wake_up,
)
from keyboards import sleep_dashboard_keyboard, sleep_not_set_keyboard, sleep_history_keyboard
from messages import (
    sleep_dashboard_msg,
    sleep_history_msg,
    sleep_log_end_msg,
    sleep_log_start_msg,
    sleep_no_open_session_msg,
    sleep_not_set_msg,
    sleep_too_soon_msg,
)
from utils.xp_helper import award_xp

MIN_SLEEP_MINUTES = 30  # минимальное время сна перед пробуждением


async def sleeps_main(message: Any, bot: Any) -> None:
    """Отображает дашборд трекера сна: текущее состояние, последнюю сессию и среднюю продолжительность."""
    user_id = message.chat.id
    settings = await get_sleep_settings(user_id)
    if not settings or (settings[0] is None and settings[1] is None):
        await bot.send_message(user_id, sleep_not_set_msg, reply_markup=sleep_not_set_keyboard())
        return

    sleep_time, wake_time, reminders_enabled = settings
    open_session = await get_open_sleep_session(user_id)
    last_sleep = await get_last_sleep_log(user_id)
    week_stats = await get_sleep_week_stats(user_id)
    avg_duration = week_stats[1] if week_stats and week_stats[1] else None

    is_sleeping = open_session is not None
    sleep_start_str = None
    if is_sleeping:
        try:
            ss_dt = datetime.strptime(open_session[1][:16], '%Y-%m-%d %H:%M')
            sleep_start_str = ss_dt.strftime('%H:%M')
        except Exception:
            sleep_start_str = open_session[1]

    await bot.send_message(
        user_id,
        sleep_dashboard_msg(
            message.from_user.first_name,
            sleep_time, wake_time, last_sleep, avg_duration,
            is_sleeping, sleep_start_str
        ),
        reply_markup=sleep_dashboard_keyboard(is_sleeping)
    )


async def handle_sleep_log_start(call: Any, bot: Any) -> None:
    """Отмечает начало сна и обновляет дашборд с кнопкой пробуждения."""
    user_id = call.message.chat.id
    now = await get_user_time_now(user_id)
    time_str = now.strftime('%H:%M')
    await log_sleep_start(user_id)
    await bot.answer_callback_query(call.id, "Сон начат! Спокойной ночи 🌙", show_alert=False)
    await bot.edit_message_text(
        sleep_log_start_msg(time_str),
        user_id, call.message.message_id,
        reply_markup=sleep_dashboard_keyboard(True)
    )


async def handle_sleep_log_end(call: Any, bot: Any) -> None:
    """Отмечает пробуждение: проверяет минимальный срок сна и начисляет XP по качеству сна."""
    user_id = call.message.chat.id
    # Проверяем минимум 30 минут сна
    open_session = await get_open_sleep_session(user_id)
    if open_session:
        sleep_start_str = open_session[1]
        try:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M'):
                try:
                    sleep_start_dt = datetime.strptime(sleep_start_str[:26], fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Неизвестный формат: {sleep_start_str}")
            now_user = await get_user_time_now(user_id)
            elapsed = (now_user - sleep_start_dt).total_seconds() / 60
            if elapsed < MIN_SLEEP_MINUTES:
                wait_mins = int(MIN_SLEEP_MINUTES - elapsed) + 1
                await bot.answer_callback_query(
                    call.id,
                    sleep_too_soon_msg(wait_mins),
                    show_alert=True
                )
                return
        except Exception:
            pass
    duration = await log_wake_up(user_id)
    if duration is None:
        await bot.answer_callback_query(call.id, sleep_no_open_session_msg, show_alert=True)
        return
    await bot.answer_callback_query(call.id, "Пробуждение отмечено! ☀️", show_alert=False)
    await bot.edit_message_text(
        sleep_log_end_msg(duration),
        user_id, call.message.message_id,
        reply_markup=sleep_dashboard_keyboard(False)
    )
    # XP по качеству сна
    if duration >= 420:
        await award_xp(bot, user_id, 'sleep_good')
    elif duration >= 300:
        await award_xp(bot, user_id, 'sleep_ok')
    else:
        await award_xp(bot, user_id, 'sleep_short')


async def handle_sleep_history(call: Any, bot: Any) -> None:
    """Паказывает историю последних 7 сессий сна."""
    history = await get_sleep_history(call.message.chat.id, 7)
    await bot.edit_message_text(
        sleep_history_msg(history),
        call.message.chat.id, call.message.message_id,
        reply_markup=sleep_history_keyboard()
    )
