from config import is_admin
from typing import Any
from database import count_users_trackers, update_activity_goal, \
    activity_set_reminder_type, water_set_reminder_type, get_timezone, \
    set_timezone, update_water_goal, \
    get_sleep_settings, update_sleep_time, update_wake_time, toggle_sleep_reminders
from keyboards import activity_setup_keyboard, activity_goal_keyboard, \
    activity_goal_custom_cancel, activity_reminder_type_keyboard, \
    activity_interval_keyboard, settings_keyboard, water_goal_keyboard, \
    water_setup_keyboard, get_water_reminder_type_keyboard, main_menu, water_goal_custom_cancel, \
    sleep_setup_keyboard, sleep_time_keyboard, wake_time_keyboard, sleep_cancel_custom_keyboard
from messages import activity_tracker_setup_msg, activity_goal_selection_msg, \
    activity_setup_required_msg, activity_goal_success_msg, \
    activity_reminder_type_selection_msg, activity_interval_setup_msg, \
    activity_reminder_type_smart_msg, activity_interval_selected_msg, \
    activity_goal_custom_msg, activity_goal_limit_msg, \
    activity_goal_incorrect_format_msg, water_goal_limit_msg, \
    water_goal_success_msg, water_goal_selection_msg, water_tracker_setup_msg, \
    water_goal_incorrect_format_msg, water_reminder_type_selection_msg, \
    water_setup_required_msg, water_reminder_type_smart_msg, \
    water_interval_selected_short_msg, water_goal_custom_msg, cancellation, \
    timezone_suc_msg, start_message, settings_msg, \
    sleep_tracker_setup_msg, sleep_time_selection_msg, wake_time_selection_msg, \
    sleep_time_set_msg, wake_time_set_msg, sleep_time_format_error_msg, \
    sleep_reminder_toggle_msg, sleep_custom_time_input_msg
from utils.fsm import State


async def select_timezone(call: Any, bot: Any) -> None:
    """Сохраняет выбранный часовой пояс и переводит на главное меню или приветственное сообщение."""
    timezone_offset = int(call.data.split('_')[1])
    old_timezone = await get_timezone(call.message.chat.id)
    await set_timezone(call.message.chat.id, timezone_offset)
    await bot.answer_callback_query(call.id, timezone_suc_msg, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if old_timezone is None:
        user_is_admin = await is_admin(call.message.chat.id)
        await bot.send_message(
            call.message.chat.id,
            start_message(call.from_user.first_name),
            reply_markup=main_menu(call.message.chat.id,user_is_admin)
        )
    else:
        await bot.send_message(
            call.message.chat.id,
            settings_msg(call.from_user.first_name),
            reply_markup=settings_keyboard()
        )


async def set_reminder_type_water(call: Any, bot: Any) -> None:
    """Открывает выбор типа напоминаний о воде (требует установленной цели)."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if await count_users_trackers('track_water', 'goal_ml', call.message.chat.id):
        await bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        await bot.send_message(call.message.chat.id,
                         water_setup_required_msg,
                         reply_markup=water_goal_keyboard())


async def water_smart_type_install(call: Any, bot: Any) -> None:
    """Устанавливает умный режим напоминаний о воде."""
    await bot.answer_callback_query(call.id, water_reminder_type_smart_msg, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await water_set_reminder_type(call.message.chat.id, 'Smart')
    await bot.send_message(
        call.message.chat.id,
        water_tracker_setup_msg(call.from_user.first_name),
        reply_markup=water_setup_keyboard()
    )


async def water_setting_interval(call: Any, bot: Any, step: str) -> None:
    """Устанавливает интервал напоминаний о воде или возвращается назад (шаг: `install` / `exit`)."""
    if step == 'exit':
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        interval = int(call.data[-2])
        await bot.answer_callback_query(call.id, water_interval_selected_short_msg(interval), show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
        await water_set_reminder_type(call.message.chat.id, 'Interval', interval)


async def water_goal_custom_stg(bot: Any, message: Any, call: Any, send_msg: Any) -> None:
    """Обрабатывает ввод произвольной цели по воде и сохраняет её."""
    ml = message.text.strip()
    if ml.replace('.', '', 1).isdigit():
        if 500 <= float(ml) <= 8000:
            State.clear_state(call.message.chat.id)
            await update_water_goal(call.from_user.id, ml)
            await bot.send_message(call.message.chat.id, water_goal_success_msg(ml))
            await bot.delete_message(message.chat.id, send_msg.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )


        else:
            await bot.delete_message(message.chat.id, send_msg.message_id)
            send_msg = await bot.send_message(message.chat.id, water_goal_limit_msg,
                                        reply_markup=water_goal_custom_cancel())
            State.set_state(call.message.chat.id,'waiting_custom_water_goal',[call,send_msg])
    else:
        await bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = await bot.send_message(message.chat.id, water_goal_incorrect_format_msg,
                                    reply_markup=water_goal_custom_cancel())
        State.set_state(call.message.chat.id,'waiting_custom_water_goal',[call,send_msg])


async def water_goal_settings(call: Any, bot: Any, step: str) -> None:
    """Диспетчер действий с целью воды: установка, произвольный ввод, выход или отмена (шаг)."""
    if step == 'set_goal':
        goal_ml = int(call.data.split('_')[-1])
        await update_water_goal(call.from_user.id, goal_ml)
        await bot.answer_callback_query(call.id, water_goal_success_msg(goal_ml))
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
    elif step == 'set_goal_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        send_custom_selection_msg = await bot.send_message(
            call.message.chat.id,
            water_goal_custom_msg, reply_markup=water_goal_custom_cancel()
        )
        State.set_state(call.message.chat.id, 'waiting_custom_water_goal', [call, send_custom_selection_msg])
    elif step == 'exit':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name)
            , reply_markup=water_setup_keyboard()
        )
    elif step == 'cancel_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        State.clear_state(call.message.chat.id)
        await bot.send_message(call.message.chat.id,
                         water_goal_selection_msg(call.from_user.first_name),
                         reply_markup=water_goal_keyboard()
                         )
async def activity_settings_open(call: Any, bot: Any) -> None:
    """Открывает настройки трекера активности."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        activity_tracker_setup_msg(call.from_user.first_name),
        reply_markup=activity_setup_keyboard()
    )


async def activity_reminder_open(call: Any, bot: Any) -> None:
    """Открывает выбор типа напоминаний об активности (требует установленной цели)."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if await count_users_trackers('track_activity', 'goal_exercises', call.message.chat.id):
        await bot.send_message(
            call.message.chat.id,
            activity_reminder_type_selection_msg(call.from_user.first_name),
            reply_markup=activity_reminder_type_keyboard()
        )
    else:
        await bot.send_message(
            call.message.chat.id,
            activity_setup_required_msg,
            reply_markup=activity_goal_keyboard()
        )


async def activity_smart_type_install(call: Any, bot: Any) -> None:
    """Устанавливает умный режим напоминаний об активности."""
    await bot.answer_callback_query(call.id, activity_reminder_type_smart_msg, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await activity_set_reminder_type(call.message.chat.id, 'Smart')
    await bot.send_message(
        call.message.chat.id,
        activity_tracker_setup_msg(call.from_user.first_name),
        reply_markup=activity_setup_keyboard()
    )


async def activity_interval_open(call: Any, bot: Any) -> None:
    """Открывает выбор интервала напоминаний об активности."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        activity_interval_setup_msg(call.from_user.first_name),
        reply_markup=activity_interval_keyboard()
    )


async def activity_setting_interval(call: Any, bot: Any, step: str) -> None:
    """Устанавливает интервал напоминаний об активности или возвращается назад (шаг: `install` / `exit`)."""
    if step == 'exit':
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            activity_reminder_type_selection_msg(call.from_user.first_name),
            reply_markup=activity_reminder_type_keyboard()
        )
    else:
        interval = int(call.data.split('_')[-1])
        await bot.answer_callback_query(call.id, activity_interval_selected_msg(interval), show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await activity_set_reminder_type(call.message.chat.id, 'Interval', interval)
        await bot.send_message(
            call.message.chat.id,
            activity_tracker_setup_msg(call.from_user.first_name),
            reply_markup=activity_setup_keyboard()
        )


async def activity_goal_settings(call: Any, bot: Any, step: str) -> None:
    """Диспетчер действий с целью активности: установка, произвольный ввод, выход или отмена (шаг)."""
    if step == 'set_goal':
        goal = int(call.data.split('_')[-1])
        await update_activity_goal(call.from_user.id, goal)
        await bot.answer_callback_query(call.id, activity_goal_success_msg(goal))
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            activity_tracker_setup_msg(call.from_user.first_name),
            reply_markup=activity_setup_keyboard()
        )
    elif step == 'set_goal_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        send_msg = await bot.send_message(
            call.message.chat.id,
            activity_goal_custom_msg,
            reply_markup=activity_goal_custom_cancel()
        )
        State.set_state(call.message.chat.id, 'waiting_custom_activity_goal', [call, send_msg])
    elif step == 'exit':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.send_message(
            call.message.chat.id,
            activity_tracker_setup_msg(call.from_user.first_name),
            reply_markup=activity_setup_keyboard()
        )
    elif step == 'cancel_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        State.clear_state(call.message.chat.id)
        await bot.send_message(
            call.message.chat.id,
            activity_goal_selection_msg(call.from_user.first_name),
            reply_markup=activity_goal_keyboard()
        )


async def activity_goal_custom_stg(bot: Any, message: Any, call: Any, send_msg: Any) -> None:
    """Обрабатывает ввод произвольной цели активности и сохраняет её."""
    text = message.text.strip()
    if text.isdigit():
        goal = int(text)
        if 1 <= goal <= 30:
            State.clear_state(call.message.chat.id)
            await update_activity_goal(call.from_user.id, goal)
            await bot.send_message(call.message.chat.id, activity_goal_success_msg(goal))
            await bot.delete_message(message.chat.id, send_msg.message_id)
            await bot.send_message(
                call.message.chat.id,
                activity_tracker_setup_msg(call.from_user.first_name),
                reply_markup=activity_setup_keyboard()
            )
        else:
            await bot.delete_message(message.chat.id, send_msg.message_id)
            send_msg = await bot.send_message(
                message.chat.id,
                activity_goal_limit_msg,
                reply_markup=activity_goal_custom_cancel()
            )
            State.set_state(call.message.chat.id, 'waiting_custom_activity_goal', [call, send_msg])
    else:
        await bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = await bot.send_message(
            message.chat.id,
            activity_goal_incorrect_format_msg,
            reply_markup=activity_goal_custom_cancel()
        )
        State.set_state(call.message.chat.id, 'waiting_custom_activity_goal', [call, send_msg])


async def activity_stg_cancel(call: Any, bot: Any) -> None:
    """Узакрывает настройки активности и возвращается на главный экран настроек."""
    await bot.answer_callback_query(call.id, cancellation, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        settings_msg(call.from_user.first_name),
        reply_markup=settings_keyboard()
    )


# Настройки трекера сна

def _parse_time(text: str) -> str | None:
    """Проверяет и возвращает время в формате HH:MM или `None`."""
    text = text.strip()
    parts = text.split(':')
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    except ValueError:
        pass
    return None


async def sleep_settings_open(call: Any, bot: Any) -> None:
    """Открывает настройки трекера сна."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    settings = await get_sleep_settings(call.message.chat.id)
    sleep_time = settings[0] if settings else None
    wake_time = settings[1] if settings else None
    reminders_enabled = bool(settings[2]) if settings else True
    await bot.send_message(
        call.message.chat.id,
        sleep_tracker_setup_msg(call.from_user.first_name, sleep_time, wake_time, reminders_enabled),
        reply_markup=sleep_setup_keyboard(reminders_enabled)
    )


async def sleep_stg_sleep_time_open(call: Any, bot: Any) -> None:
    """Открывает выбор времени отбоя."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        sleep_time_selection_msg(call.from_user.first_name),
        reply_markup=sleep_time_keyboard()
    )


async def sleep_stg_wake_time_open(call: Any, bot: Any) -> None:
    """Открывает выбор времени подъёма."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        wake_time_selection_msg(call.from_user.first_name),
        reply_markup=wake_time_keyboard()
    )


async def sleep_select_sleep_time(call: Any, bot: Any) -> None:
    """Обрабатывает выбор времени отбоя из кнопок или кастомный ввод."""
    time_str = call.data.replace('select_sleep_time_', '')
    await update_sleep_time(call.message.chat.id, time_str)
    await bot.answer_callback_query(call.id, sleep_time_set_msg(time_str), show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    settings = await get_sleep_settings(call.message.chat.id)
    reminders_enabled = bool(settings[2]) if settings else True
    await bot.send_message(
        call.message.chat.id,
        sleep_tracker_setup_msg(call.from_user.first_name, time_str,
                                settings[1] if settings else None, reminders_enabled),
        reply_markup=sleep_setup_keyboard(reminders_enabled)
    )


async def sleep_select_wake_time(call: Any, bot: Any) -> None:
    """Обрабатывает выбор времени подъёма из кнопок."""
    time_str = call.data.replace('select_wake_time_', '')
    await update_wake_time(call.message.chat.id, time_str)
    await bot.answer_callback_query(call.id, wake_time_set_msg(time_str), show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    settings = await get_sleep_settings(call.message.chat.id)
    reminders_enabled = bool(settings[2]) if settings else True
    await bot.send_message(
        call.message.chat.id,
        sleep_tracker_setup_msg(call.from_user.first_name,
                                settings[0] if settings else None, time_str, reminders_enabled),
        reply_markup=sleep_setup_keyboard(reminders_enabled)
    )


async def sleep_request_custom_sleep_time(call: Any, bot: Any) -> None:
    """Запрашивает ручной ввод произвольного времени отбоя."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    send_msg = await bot.send_message(
        call.message.chat.id, sleep_custom_time_input_msg,
        reply_markup=sleep_cancel_custom_keyboard()
    )
    State.set_state(call.message.chat.id, 'waiting_custom_sleep_time', [call, send_msg])


async def sleep_request_custom_wake_time(call: Any, bot: Any) -> None:
    """Запрашивает ручной ввод произвольного времени подъёма."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    send_msg = await bot.send_message(
        call.message.chat.id, sleep_custom_time_input_msg,
        reply_markup=sleep_cancel_custom_keyboard()
    )
    State.set_state(call.message.chat.id, 'waiting_custom_wake_time', [call, send_msg])


async def sleep_custom_sleep_time_input(bot: Any, message: Any, call: Any, send_msg: Any) -> None:
    """Обрабатывает кастомный ввод времени отбоя."""
    time_str = _parse_time(message.text)
    if time_str:
        State.clear_state(message.chat.id)
        await update_sleep_time(message.chat.id, time_str)
        await bot.delete_message(message.chat.id, send_msg.message_id)
        settings = await get_sleep_settings(message.chat.id)
        reminders_enabled = bool(settings[2]) if settings else True
        await bot.send_message(message.chat.id, sleep_time_set_msg(time_str))
        await bot.send_message(
            message.chat.id,
            sleep_tracker_setup_msg(call.from_user.first_name, time_str,
                                    settings[1] if settings else None, reminders_enabled),
            reply_markup=sleep_setup_keyboard(reminders_enabled)
        )
    else:
        await bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = await bot.send_message(
            message.chat.id, sleep_time_format_error_msg,
            reply_markup=sleep_cancel_custom_keyboard()
        )
        State.set_state(message.chat.id, 'waiting_custom_sleep_time', [call, send_msg])


async def sleep_custom_wake_time_input(bot: Any, message: Any, call: Any, send_msg: Any) -> None:
    """Обрабатывает кастомный ввод времени подъёма."""
    time_str = _parse_time(message.text)
    if time_str:
        State.clear_state(message.chat.id)
        await update_wake_time(message.chat.id, time_str)
        await bot.delete_message(message.chat.id, send_msg.message_id)
        settings = await get_sleep_settings(message.chat.id)
        reminders_enabled = bool(settings[2]) if settings else True
        await bot.send_message(message.chat.id, wake_time_set_msg(time_str))
        await bot.send_message(
            message.chat.id,
            sleep_tracker_setup_msg(call.from_user.first_name,
                                    settings[0] if settings else None, time_str, reminders_enabled),
            reply_markup=sleep_setup_keyboard(reminders_enabled)
        )
    else:
        await bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = await bot.send_message(
            message.chat.id, sleep_time_format_error_msg,
            reply_markup=sleep_cancel_custom_keyboard()
        )
        State.set_state(message.chat.id, 'waiting_custom_wake_time', [call, send_msg])


async def sleep_toggle_reminder(call: Any, bot: Any) -> None:
    """Переключает напоминания сна и обновляет страницу настроек."""
    enabled = await toggle_sleep_reminders(call.message.chat.id)
    await bot.answer_callback_query(call.id, sleep_reminder_toggle_msg(enabled), show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    settings = await get_sleep_settings(call.message.chat.id)
    sleep_time = settings[0] if settings else None
    wake_time = settings[1] if settings else None
    await bot.send_message(
        call.message.chat.id,
        sleep_tracker_setup_msg(call.from_user.first_name, sleep_time, wake_time, enabled),
        reply_markup=sleep_setup_keyboard(enabled)
    )


async def sleep_stg_cancel(call: Any, bot: Any) -> None:
    """Закрывает настройки сна и возвращается на главный экран настроек."""
    await bot.answer_callback_query(call.id, cancellation, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        settings_msg(call.from_user.first_name),
        reply_markup=settings_keyboard()
    )


async def sleep_custom_time_cancel(call: Any, bot: Any) -> None:
    """Отменяет ввод пользовательского времени сна и возвращает в настройки трекера."""
    State.clear_state(call.message.chat.id)
    await bot.answer_callback_query(call.id, cancellation, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    settings = await get_sleep_settings(call.message.chat.id)
    sleep_time = settings[0] if settings else None
    wake_time = settings[1] if settings else None
    reminders_enabled = bool(settings[2]) if settings else True
    await bot.send_message(
        call.message.chat.id,
        sleep_tracker_setup_msg(call.from_user.first_name, sleep_time, wake_time, reminders_enabled),
        reply_markup=sleep_setup_keyboard(reminders_enabled)
    )

