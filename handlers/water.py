from datetime import datetime, timedelta
from typing import Any

from database import (
    add_water_ml,
    get_water_stats_for_today,
    update_last_add_water_ml,
    water_stats,
)
from keyboards import (
    accept_custom_add_water_keyboard,
    cancel_custom_add_water_keyboard,
    water_add_keyboard,
)
from messages import (
    add_water_msg,
    cancellation,
    water_add_custom_input_msg,
    water_add_hard_limit_msg,
    water_add_reasonable_limit_msg,
    water_add_time_limit_msg,
    water_custom_input_accept_msg,
    water_custom_input_format_error_msg,
    water_custom_input_limit_msg,
    water_tracker_dashboard_msg,
)
from utils.fsm import State
from utils.xp_helper import award_xp


async def validate_water_addition(info: tuple, added_water_ml: int | str) -> tuple[bool, str | None]:
    """Проверяет возможность добавить воду: интервал между записями и дневные лимиты. Возвращает `(успех, сообщение_об_ошибке_или_None)`."""
    # Константы
    min_interval = 15  # минут между записями
    daily_reasonable_limit = 5000  # мл за день (5 литров) - разумный максимум
    daily_hard_limit = 8000  # мл за день (8 литров) - абсолютный максимум
    update_time, cnt_water = info
    utc_time = datetime.now() - timedelta(hours=3)
    if update_time:
        update_time = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
        time_diff = (utc_time - update_time).total_seconds() / 60
        if time_diff < min_interval:
            wait_time = min_interval - int(time_diff)
            return False, water_add_time_limit_msg(wait_time)

    daily_total = int(cnt_water) + int(added_water_ml)
    if daily_total > daily_hard_limit:
        return False, water_add_hard_limit_msg(daily_hard_limit)
    elif daily_total > daily_reasonable_limit:
        over_amount = daily_total - daily_reasonable_limit
        return True, water_add_reasonable_limit_msg(over_amount)
    return True, None


async def handle_add_water(call: Any, bot: Any, step: str) -> None:
    """Диспетчер добавления воды: обрабатывает добавление порции, запрос произвольного значения или отмену."""
    if step == 'addition':
        water_add = call.data.split('_')[2]
        accept, msg = await validate_water_addition(await get_water_stats_for_today(call.message.chat.id), water_add)

        if accept:
            await update_last_add_water_ml(call.message.chat.id)
            await add_water_ml(call.message.chat.id, water_add)
            await bot.answer_callback_query(call.id, add_water_msg)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            current_goal, water_drunk = await water_stats(call.message.chat.id)
            await bot.send_message(call.message.chat.id,
                             water_tracker_dashboard_msg(
                                 call.from_user.first_name,
                                 current_goal, water_drunk),
                             reply_markup=water_add_keyboard()
                             )
            # XP за добавление воды
            await award_xp(bot, call.message.chat.id, 'water_add')
            # XP за достижение дневной цели
            if water_drunk >= current_goal:
                await award_xp(bot, call.message.chat.id, 'water_goal')
        if msg:
            await bot.send_message(call.message.chat.id, msg)
    elif step == 'request_value':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(call.message.chat.id,
                         water_add_custom_input_msg(
                             call.message.from_user.first_name),
                         reply_markup=cancel_custom_add_water_keyboard()
                         )
        State.set_state(call.message.chat.id,'waiting_add_water',None)
    elif step == 'custom_cancel':
        State.clear_state(call.message.chat.id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        current_goal, water_drunk = await water_stats(call.message.chat.id)
        await bot.send_message(call.message.chat.id,
                         water_tracker_dashboard_msg(
                             call.message.from_user.first_name,
                             current_goal, water_drunk),
                         reply_markup=water_add_keyboard()
                         )


async def add_custom_water(message: Any, bot: Any) -> None:
    """Обрабатывает ввод произвольного объёма воды в мл: валидирует диапазон и запрашивает подтверждение."""
    ml = message.text.strip()
    if ml.isdigit():
        if 50 <= int(ml) <= 1500:
            await bot.send_message(message.chat.id,
                             water_custom_input_accept_msg(ml),
                             reply_markup=
                             accept_custom_add_water_keyboard(ml)
                             )
            State.clear_state(message.chat.id)
            return
        else:
            await bot.send_message(message.chat.id, water_custom_input_limit_msg(ml),
                             reply_markup=cancel_custom_add_water_keyboard()
                             )
    else:
        await bot.send_message(message.chat.id, water_custom_input_format_error_msg,
                         reply_markup=cancel_custom_add_water_keyboard()
                         )

