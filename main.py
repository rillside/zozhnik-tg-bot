import asyncio
import logging
import signal
from functools import wraps
from typing import Any, Callable

import telebot
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.async_telebot import AsyncTeleBot

from config import is_admin, is_owner, token
from database import (
    add_user,
    count_users_trackers,
    get_all_admin,
    get_timezone,
    init_db,
    is_user_banned,
    load_tickets_info,
    tickets_by_user,
    update_user_activity_smart,
    update_username,
    water_stats,
)
from handlers.admin_users import (
    admin_ban_user,
    admin_unban_user,
    admin_user_search,
    admin_users_start,
    admin_xp_cancel,
    admin_xp_input,
    admin_xp_start,
)
from handlers.ai.analyzer import ai_analyze_profile
from handlers.broadcast import accept_broadcast, broadcast_send
from handlers.leaderboard import show_leaderboard, show_xp_profile
from handlers.owner_menu import add_admin, remove_admin, return_admin
from handlers.settings import (
    activity_goal_custom_stg,
    activity_goal_settings,
    activity_interval_open,
    activity_reminder_open,
    activity_setting_interval,
    activity_settings_open,
    activity_smart_type_install,
    activity_stg_cancel,
    select_timezone,
    set_reminder_type_water,
    sleep_custom_sleep_time_input,
    sleep_custom_time_cancel,
    sleep_custom_wake_time_input,
    sleep_request_custom_sleep_time,
    sleep_request_custom_wake_time,
    sleep_select_sleep_time,
    sleep_select_wake_time,
    sleep_settings_open,
    sleep_stg_cancel,
    sleep_stg_sleep_time_open,
    sleep_stg_wake_time_open,
    sleep_toggle_reminder,
    water_goal_custom_stg,
    water_goal_settings,
    water_setting_interval,
    water_smart_type_install,
)
from handlers.sleeps import (
    handle_sleep_history,
    handle_sleep_log_end,
    handle_sleep_log_start,
    sleeps_main,
)
from handlers.sports.admin_exercises import (
    accept_delete_exercise,
    cancel_delete_exercise,
    delete_exercise,
    edit_exercise_handle_category,
    edit_exercise_show_list,
    edit_exercise_start,
    exercise_go_back,
    exercise_management,
    handle_exercise_category,
    handle_exercise_description,
    handle_exercise_difficulty,
    handle_exercise_edit,
    handle_exercise_name,
    handle_exercise_video,
    open_exercise_for_edit,
    open_video,
    save_exercise,
    save_exercise_changes,
    skip_exercise_video,
    start_add_exercise,
    stats_exercise,
)
from handlers.sports.user_exercises import (
    sports_back_to_categories,
    sports_back_to_main,
    sports_cancel_done,
    sports_check_all_start,
    sports_check_favorites_start,
    sports_confirm_done,
    sports_handle_category,
    sports_mark_done,
    sports_show_exercise,
    sports_show_exercise_stats,
    sports_show_favorites_page,
    sports_show_list,
    sports_show_my_stats,
    sports_start,
    toggle_favorite,
)
from handlers.stats import adm_stats, owner_stats, user_stats
from handlers.support.support import (
    admin_look_tickets,
    create_ticket,
    handle_delete_ticket,
    handling_aggressive_content,
    look_ticket_page,
    opening_photo_in_ticket,
    opening_ticket,
    send_message_to_ticket,
    ticket_exit,
    tickets_exit,
)
from handlers.water import add_custom_water, handle_add_water
from keyboards import (
    activity_goal_keyboard,
    activity_goal_not_set_keyboard,
    activity_setup_keyboard,
    admin_exercise_keyboard,
    admin_menu,
    admin_ticket_section_keyboard,
    cancel_br_start,
    consultation_support_keyboard,
    get_water_interval_keyboard,
    main_menu,
    opening_ticket_keyboard,
    own_cancel,
    owner_menu,
    settings_keyboard,
    stats_keyboard,
    supp_ticket_cancel_keyboard,
    support_selection_keyboard,
    technical_support_keyboard,
    timezone_selection_keyboard,
    water_add_keyboard,
    water_goal_keyboard,
    water_goal_not_set_keyboard,
    water_setup_keyboard,
)
from messages import (
    activity_goal_selection_msg,
    activity_setup_required_msg,
    activity_tracker_setup_msg,
    add_new_adm_msg,
    adm_start_message,
    admin_ticket_section_msg,
    banned_msg,
    cancellation,
    create_ticket_msg,
    error_msg,
    example_broadcast,
    exercise_cancel_msg,
    exit_home,
    media_is_closed_msg,
    my_tickets_msg,
    nf_cmd,
    no_active_tickets_msg,
    opening_ticket_msg,
    remove_adm_msg,
    send_media_group_error_msg,
    settings_msg,
    start_message,
    support_consult_msg,
    support_selection_msg,
    support_tech_msg,
    timezone_selection_msg,
    water_goal_not_set_msg,
    water_goal_selection_msg,
    water_interval_setup_msg,
    water_tracker_dashboard_msg,
    water_tracker_setup_msg,
)
from utils.antispam import is_group_warned, mark_group_warned
from utils.censorship.checker import censor_load
from utils.fsm import State
from utils.scheduler import Scheduler

bot = AsyncTeleBot(token, parse_mode='HTML' )
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

class FakeMessage:
    def __init__(self, message: telebot.types.Message, chat: telebot.types.Chat, from_user: telebot.types.User) -> None:
        """Обёртка-заглушка для message, используемая внутри callback-контекста."""
        self.message = message
        self.chat = chat
        self.from_user = from_user


def error_handler(func: Callable) -> Callable:
    """Декоратор для перехвата и логирования исключений в хэндлерах с отправкой пользователю сообщения об ошибке."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        """Внутренняя обёрточная функция декоратора: вызывает хэндлер и обрабатывает исключения."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Ошибка в {func.__name__}: {e}")
            chat_id = None
            if len(args) > 0:
                if hasattr(args[0], 'chat'):
                    chat_id = args[0].chat.id
                elif hasattr(args[0], 'message') and hasattr(args[0].message, 'chat'):
                    chat_id = args[0].message.chat.id

            if chat_id:
                try:
                    await bot.send_message(chat_id, error_msg)
                except:
                    pass

    return wrapper


@bot.message_handler(commands=['start'])
# @error_handler
async def start(message: telebot.types.Message) -> None:
    """Обрабатывает команду /start: регистрирует пользователя и показывает главное меню или выбор часового пояса."""
    State.clear_state(message.chat.id)
    user_is_admin = await is_admin(message.chat.id)
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return
    logging.info(f"Пользователь {message.chat.id} запустил бота")
    if is_owner(message.chat.id):
        await add_user(message.chat.id, message.from_user.username,
                       'Owner')

    else:

        await add_user(message.chat.id, message.from_user.username,
                       f"{'Admin' if user_is_admin else 'User'}")
    if await get_timezone(message.chat.id) is not None:
        await bot.send_message(
            message.chat.id,
            start_message(message.from_user.first_name),
            reply_markup=main_menu(message.chat.id, user_is_admin)
        )
    else:
        await bot.send_message(message.chat.id,
                               timezone_selection_msg(
                                   message.from_user.first_name),
                               reply_markup=timezone_selection_keyboard()
                               )


@bot.message_handler(content_types=['text'], func=lambda msg: State.user_states.get(msg.chat.id) is not None)
async def state_handler(message: telebot.types.Message) -> None:
    """Диспетчер текстовых сообщений в FSM-режиме: направляет входящий текст в нужный хэндлер по текущему состоянию."""
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return
    state, data = State.get_state(message.chat.id)
    match state:
        case 'waiting_broadcast_text':
            await accept_broadcast(message, bot)
        case 'waiting_admin_id':
            if data == 'add':
                await add_admin(message, bot)
            elif data == 'remove':
                await remove_admin(message, bot)
        case 'waiting_ticket_title':
            await create_ticket(message, bot, data)
        case 'waiting_send_msg_to_ticket':
            await send_message_to_ticket(message, bot, *data)
        case 'waiting_add_water':
            await add_custom_water(message, bot)
        case 'waiting_custom_water_goal':
            await water_goal_custom_stg(bot, message, *data)
        case 'waiting_custom_activity_goal':
            await activity_goal_custom_stg(bot, message, *data)
        case 'waiting_custom_sleep_time':
            await sleep_custom_sleep_time_input(bot, message, *data)
        case 'waiting_custom_wake_time':
            await sleep_custom_wake_time_input(bot, message, *data)
        case 'waiting_user_search':
            await admin_user_search(message, bot)
        case 'waiting_admin_xp':
            await admin_xp_input(message, bot)
        case 'adding_exercise':
            if data == {}:
                await handle_exercise_name(message, bot)
            elif 'name' in data and 'description' not in data:
                await handle_exercise_description(message, bot)
        case 'waiting_new_exercise_field':
            if 'action' in data and 'ex_id' in data:
                await save_exercise_changes(bot, message=message)


_locks = {}


@bot.message_handler(content_types=['photo'], func=lambda msg: State.user_states.get(msg.chat.id))
async def handle_photo_with_state(message: telebot.types.Message) -> None:
    """Обрабатывает входящие фото в FSM-контексте: защищает от медиагрупп и направляет в нужный хэндлер."""
    state, data = State.get_state(message.chat.id)
    async with _locks.setdefault(message.chat.id, asyncio.Lock()):
        if message.media_group_id:
            group_id = message.media_group_id
            if not is_group_warned(group_id):
                await bot.send_message(
                    message.chat.id,
                    send_media_group_error_msg,
                    reply_markup=cancel_br_start()
                )
                mark_group_warned(group_id)

            return
    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption if message.caption else None
    match state:
        case 'waiting_broadcast_text':
            await accept_broadcast(message, bot, 'photo', file_id, caption)
        case 'waiting_send_msg_to_ticket':
            await send_message_to_ticket(message, bot, *data, type_msg='photo', file_id=file_id, caption=caption)


@bot.message_handler(content_types=['video', 'animation'], func=lambda msg: State.user_states.get(msg.chat.id))
async def handle_video_with_state(message: telebot.types.Message) -> None:
    """Обрабатывает входящие видео и анимации в FSM-контексте: передаёт файл в хэндлер добавления/редактирования упражнений."""
    state, data = State.get_state(message.chat.id)
    match state:
        case 'adding_exercise':
            if 'difficulty' in data:
                await handle_exercise_video(message, bot)
        case 'waiting_new_exercise_field':
            if 'action' in data and 'ex_id' in data:
                await save_exercise_changes(bot, message=message)


@bot.message_handler(content_types=['text'])
# @error_handler
async def msg(message: telebot.types.Message) -> None:
    """Основной диспетчер текстовых команд главного и админского меню."""
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return
    await update_username(message.chat.id, message.from_user.username, bot)
    await update_user_activity_smart(message.chat.id)
    match message.text:
        case "💧 Водный баланс":
            if await count_users_trackers('track_water', 'goal_ml', message.chat.id):
                current_goal, water_drunk = await water_stats(message.chat.id)
                await bot.send_message(message.chat.id,
                                       water_tracker_dashboard_msg(
                                           message.from_user.first_name,
                                           current_goal, water_drunk),
                                       reply_markup=water_add_keyboard()
                                       )
            else:
                await bot.send_message(message.chat.id,
                                       water_goal_not_set_msg,
                                       reply_markup=water_goal_not_set_keyboard())
        case "💪 Физ-активность":
            if await count_users_trackers('track_activity', 'goal_exercises', message.chat.id):
                await sports_start(message, bot)
            else:
                await bot.send_message(
                    message.chat.id,
                    activity_setup_required_msg,
                    reply_markup=activity_goal_not_set_keyboard()
                )

        case "😴 Сон":
            await sleeps_main(message, bot)

        case "📊 Статистика":
            stats_text = await user_stats(message.chat.id)
            if stats_text is None:
                stats_text = "Ошибка при загрузке статистики"
            await bot.send_message(
                message.chat.id,
                stats_text,
                reply_markup=stats_keyboard()
            )

        case "⚙️ Настройки":
            await bot.send_message(
                message.chat.id,
                settings_msg(message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case "👨‍⚕️ Персональный специалист":
            await bot.send_message(message.chat.id, support_selection_msg(
                message.from_user.first_name),
                                   reply_markup=support_selection_keyboard()
                                   )

        case '🛠️ Админ панель' if await is_admin(message.chat.id):
            await bot.send_message(
                message.chat.id,
                adm_start_message(message.from_user.first_name,
                                  message.chat.id),
                reply_markup=admin_menu(message.chat.id)
            )

        case "📊 Статистика пользователей" if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id, await adm_stats())
        case '📢 Рассылка' if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                                   example_broadcast, reply_markup=cancel_br_start())
            State.set_state(message.chat.id, 'waiting_broadcast_text', None)
        case '🔍 Пользователи' if await is_admin(message.chat.id):
            await admin_users_start(message, bot)
        case '💪 Управление упражнениями' if await is_admin(message.chat.id):
            await exercise_management(message, bot)
        case '👨‍⚕️ Обращения' if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                                   admin_ticket_section_msg(
                                       message.from_user.first_name),
                                   reply_markup=admin_ticket_section_keyboard()
                                   )
        case "👑 Управление администрацией" if is_owner(message.chat.id):
            await bot.send_message(message.chat.id, await owner_stats(), reply_markup=owner_menu(await get_all_admin()))
        case "↩️ На главную":
            user_is_admin = await is_admin(message.chat.id)
            await bot.send_message(
                message.chat.id, exit_home(),
                reply_markup=main_menu(message.chat.id, user_is_admin)
            )
        case _:
            await bot.send_message(message.chat.id, nf_cmd)


@bot.callback_query_handler(func=lambda call: True)
@error_handler
async def callback_inline(call: telebot.types.CallbackQuery) -> None:
    """Диспетчер всех callback-запросов бота: разбирает call.data и вызывает соответствующий хэндлер."""
    if await is_user_banned(call.message.chat.id):
        await bot.answer_callback_query(call.id, "🚫 Ваш аккаунт заблокирован.", show_alert=True)
        return
    match call.data:
        case data if data.startswith('timezone_') and 'settings' not in data:
            await select_timezone(call, bot)
        case data if data.startswith('br_accept_'):
            type_broadcast = data.split('_')[2]
            if type_broadcast == 'msg':
                await broadcast_send(call, bot)
            elif type_broadcast == 'photo':
                file_id, caption = State.get_state(call.message.chat.id)[1]
                await broadcast_send(call, bot, 'photo', file_id, caption)
            elif type_broadcast == 'media_group':
                pass
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'br_cancel':
            await bot.send_message(call.message.chat.id, cancellation)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
        case 'add_adm':
            await bot.send_message(call.message.chat.id, add_new_adm_msg, reply_markup=own_cancel())
            State.set_state(call.message.chat.id, 'waiting_admin_id', 'add')
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'remove_adm':
            await bot.send_message(call.message.chat.id, remove_adm_msg, reply_markup=own_cancel())
            State.set_state(call.message.chat.id, 'waiting_admin_id', 'remove')
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'own_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(call.message.chat.id, await owner_stats(),
                                   reply_markup=owner_menu(await get_all_admin()))
        case 'br_start_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
            await bot.send_message(call.message.chat.id, cancellation)
        case 'return_adm':
            await return_admin(call, bot)

        case 'water_settings':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )
        case 'activity_settings':
            await activity_settings_open(call, bot)
        case 'dream_settings':
            await sleep_settings_open(call, bot)

        case 'review_settings':
            pass
        case 'timezone_settings':
            await bot.answer_callback_query(call.id, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   timezone_selection_msg(
                                       call.from_user.first_name),
                                   reply_markup=timezone_selection_keyboard()
                                   )

        case 'water_reminder':
            await set_reminder_type_water(call, bot)
        case 'type_smart':
            await water_smart_type_install(call, bot)
        case 'type_interval':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id, water_interval_setup_msg(call.from_user.first_name),
                reply_markup=get_water_interval_keyboard()
            )
        case data if data.startswith('water_interval_'):
            step = 'exit' if data.split('_')[-1] == 'exit' else 'install'
            await water_setting_interval(call, bot, step)
        case 'water_goal':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   water_goal_selection_msg(call.from_user.first_name),
                                   reply_markup=water_goal_keyboard()
                                   )
        case data if data.startswith('water_goal_') or data == 'water_reminder_exit':
            action = (call.data.split('_')[-1])
            match action:
                case '1500' | '2000' | '2500' | '3000':
                    step = 'set_goal'
                case 'custom':
                    step = 'set_goal_custom'
                case 'exit':
                    step = 'exit'
                case 'cancel':
                    step = 'cancel_custom'
            await water_goal_settings(call, bot, step)

        case 'water_stg_cancel':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                settings_msg(call.message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case 'activity_goal':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                activity_goal_selection_msg(call.from_user.first_name),
                reply_markup=activity_goal_keyboard()
            )
        case 'activity_reminder':
            await activity_reminder_open(call, bot)
        case 'activity_type_smart':
            await activity_smart_type_install(call, bot)
        case 'activity_type_interval':
            await activity_interval_open(call, bot)
        case data if data.startswith('activity_interval_'):
            last = data.split('_')[-1]
            step = 'exit' if last == 'exit' else 'install'
            await activity_setting_interval(call, bot, step)
        case 'activity_reminder_exit':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(
                call.message.chat.id,
                activity_tracker_setup_msg(call.from_user.first_name),
                reply_markup=activity_setup_keyboard()
            )
        case data if data.startswith('activity_goal_'):
            last = data.split('_')[-1]
            if last == 'custom':
                step = 'set_goal_custom'
            elif last == 'exit':
                step = 'exit'
            elif last == 'cancel':
                step = 'cancel_custom'
            else:
                step = 'set_goal'
            await activity_goal_settings(call, bot, step)
        case 'activity_stg_cancel':
            await activity_stg_cancel(call, bot)
        # ── SLEEP ──────────────────────────────────────────────────────────────
        case 'sleep_stg_sleep_time':
            await sleep_stg_sleep_time_open(call, bot)
        case 'sleep_stg_wake_time':
            await sleep_stg_wake_time_open(call, bot)
        case data if data.startswith('select_sleep_time_'):
            await sleep_select_sleep_time(call, bot)
        case data if data.startswith('select_wake_time_'):
            await sleep_select_wake_time(call, bot)
        case 'sleep_time_custom':
            await sleep_request_custom_sleep_time(call, bot)
        case 'wake_time_custom':
            await sleep_request_custom_wake_time(call, bot)
        case 'sleep_time_exit':
            await sleep_settings_open(call, bot)
        case 'wake_time_exit':
            await sleep_settings_open(call, bot)
        case 'sleep_stg_toggle_reminder':
            await sleep_toggle_reminder(call, bot)
        case 'sleep_stg_cancel':
            await sleep_stg_cancel(call, bot)
        case 'sleep_custom_time_cancel':
            await sleep_custom_time_cancel(call, bot)
        case 'sleep_log_start':
            await handle_sleep_log_start(call, bot)
        case 'sleep_log_end':
            await handle_sleep_log_end(call, bot)
        case 'sleep_history':
            await handle_sleep_history(call, bot)

        case 'cancel_settings' | 'water_add_exit':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id, user_is_admin)
            )
        case data if ((data == 'water_add_custom'
                       or data == 'water_add_custom_cancel')
                      or (data.startswith('water_add')
                          and len(data.split('_')) == 3
                          and data.split('_')[-1].isdigit())):
            match data.split('_')[-1]:
                case 'custom':
                    step = 'request_value'
                case 'cancel':
                    step = 'custom_cancel'
                case _:
                    step = 'addition'
            await handle_add_water(call, bot, step)
        case 'technical_support' | 'personal_consultation':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   support_tech_msg if call.data == 'technical_support'
                                   else support_consult_msg,
                                   reply_markup=technical_support_keyboard()
                                   if call.data == 'technical_support'
                                   else consultation_support_keyboard()
                                   )
        case 'tech_supp_open_ticket' | 'consult_supp_open_ticket':
            type_supp = call.data.split('_')[0]
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, create_ticket_msg(type_supp),
                                   reply_markup=supp_ticket_cancel_keyboard())
            State.set_state(call.message.chat.id, 'waiting_ticket_title', type_supp)
        case 'back_to_main':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(call.message.chat.id, exit_home(),
                                   reply_markup=main_menu(call.message.chat.id, user_is_admin))
        case data if data.startswith('accept_ticket_'):
            id_ticket = data.split('_')[2]
            await bot.answer_callback_query(call.id, opening_ticket_msg, show_alert=True)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await opening_ticket(call.message, bot, id_ticket, 'user')
        case data if data.startswith(('delete_ticket_',
                                      'confirm_delete_ticket_',
                                      'cancel_delete_ticket_')
                                     ):
            type_handle = data.split('_')[0]
            await handle_delete_ticket(call, bot, type_handle)

        case data if data.startswith(('aggressive_title_', 'aggressive_msg_to_ticket_')):
            content_type = 'msg' if data.split('_')[1] == 'msg' else 'title'
            await handling_aggressive_content(call, bot, content_type)
        case 'my_tickets':
            if await tickets_by_user(call.message.chat.id):
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.send_message(
                    call.message.chat.id,
                    my_tickets_msg,
                    reply_markup=opening_ticket_keyboard('user',
                                                         await load_tickets_info(call.message.chat.id))
                )
            else:
                await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=True)
        case data if data.startswith('opening_photo_'):
            msg_id = data.split('_')[2]
            await opening_photo_in_ticket(call, bot, msg_id)
        case data if data.startswith('ticket_exit'):
            await ticket_exit(call, bot)
        case 'adm_tickets_tech' | 'adm_tickets_consult':
            await admin_look_tickets(call, bot)
        case data if data.startswith('tickets_exit'):
            await tickets_exit(call, bot)
        case 'adm_back_main':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   exit_home('Админ'),
                                   reply_markup=admin_menu(call.message.chat.id)
                                   )
        case data if data.startswith('tickets_page_'):
            await look_ticket_page(call, bot)
        case data if data.startswith('open_ticket_'):
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            ticket_id, role = data.split('_')[2], data.split('_')[3]
            await opening_ticket(call.message, bot, ticket_id, role, call=call)

        case 'supp_cancel_opening' | 'supp_ticket_exit':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, support_selection_msg(
                call.message.from_user.first_name),
                                   reply_markup=support_selection_keyboard()
                                   )
        case 'cancel_media':
            await bot.answer_callback_query(call.id, media_is_closed_msg, show_alert=True)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'admin_exercise_add':
            await start_add_exercise(call, bot)
        case data if data.startswith('add_exercise_category_'):
            await handle_exercise_category(call, bot)
        case data if data.startswith('add_exercise_difficulty_'):
            await handle_exercise_difficulty(call, bot)
        case 'exercise_confirm_open_video':
            await open_video(call, bot)
        case 'add_exercise_skip_video':
            await skip_exercise_video(call, bot)
        case 'exercise_confirm_save':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await save_exercise(call.message.chat.id, call.message.from_user.username, bot)
            State.clear_state(call.message.chat.id)
        case 'add_exercise_back':
            await exercise_go_back(call, bot)
        case 'add_exercise_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, exercise_cancel_msg,
                                   reply_markup=admin_exercise_keyboard())
            State.clear_state(call.message.chat.id)
        case 'admin_exercise_edit' | 'edit_exercise_back_to_categories':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await edit_exercise_start(call, bot)
        case data if data.startswith('filter_edit_exercise_category_'):
            await edit_exercise_handle_category(call, bot)
        case data if (data.startswith('filter_edit_exercise_difficulty_')  # Первое открытие списка
                      or data.startswith('edit_exercises_page_')  # Переход между страницами
                      or data.startswith('edit_exercise_back_to_list_')):  # После закрытия др. Упражнения
            await edit_exercise_show_list(call, bot)
        case data if data.startswith('edit_exercise_select_'):
            await open_exercise_for_edit(call=call, bot=bot)
        case 'edit_exercise_cancel':
            State.clear_state(call.message.chat.id)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await exercise_management(call.message, bot, call.from_user.first_name)
        case data if data.startswith('ex_edit_open_video_'):
            await open_video(call, bot, is_moment_of_creation=False)
        case data if data.startswith('ex_edit_field_'):
            await handle_exercise_edit(call, bot)
        case data if data.startswith('edit_exercise_category') or data.startswith('edit_exercise_difficulty'):
            await save_exercise_changes(bot, call=call)
        case data if data.startswith('ex_edit_delete_'):
            await accept_delete_exercise(call, bot)
        case data if data.startswith('confirm_delete_ex_'):
            await delete_exercise(call, bot)
        case data if data.startswith('cancel_delete_ex_'):
            await cancel_delete_exercise(call, bot)
        case 'admin_exercise_stats':
            await stats_exercise(call, bot)
        case 'ai_analyze':
            await ai_analyze_profile(call, bot)
        case data if data.startswith('adm_ban_'):
            await admin_ban_user(call, bot)
        case data if data.startswith('adm_unban_'):
            await admin_unban_user(call, bot)
        case data if data.startswith('adm_xp_add_'):
            await admin_xp_start(call, bot, 'add')
        case data if data.startswith('adm_xp_sub_'):
            await admin_xp_start(call, bot, 'sub')
        case data if data.startswith('adm_xp_cancel_'):
            await admin_xp_cancel(call, bot)
        case 'adm_search_cancel':
            State.clear_state(call.message.chat.id)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'cancel_any':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'back_to_stats':
            stats_text = await user_stats(call.message.chat.id)
            if stats_text is None:
                stats_text = "Ошибка при загрузке статистики"
            try:
                await bot.edit_message_text(
                    stats_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=stats_keyboard()
                )
            except Exception:
                await bot.send_message(call.message.chat.id, stats_text, reply_markup=stats_keyboard())
        case 'leaderboard_open' | 'leaderboard_refresh':
            await show_leaderboard(call, bot)
        case 'xp_profile':
            await show_xp_profile(call, bot)
        case 'sports_check_all':
            await sports_check_all_start(call, bot)
        case 'sports_check_favorites':
            await sports_check_favorites_start(call, bot)
        case 'sports_check_my_stats':
            await sports_show_my_stats(call, bot)
        case 'sports_close':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await sports_start(call.message, bot,
                               first_name=call.message.from_user.first_name
                               )
        case 'sports_back_to_main':
            await sports_back_to_main(call, bot)
        case 'sports_back_to_categories':
            await sports_back_to_categories(call, bot)
        case data if data.startswith('sport_ex_fav_page_'):
            await sports_show_favorites_page(call, bot)
        case data if data.startswith('sports_category_'):
            await sports_handle_category(call, bot)
        case data if data.startswith('sports_difficulty_') \
                     or data.startswith('sport_ex_all_page_') \
                     or data.startswith('sports_back_to_list_'):
            await sports_show_list(call, bot)
        case data if data.startswith('sports_open_ex_'):
            await sports_show_exercise(call, bot)
        case data if data.startswith('sports_fav_'):
            await toggle_favorite(call, bot)
        case data if data.startswith('sports_do_'):
            await sports_mark_done(call, bot)
        case data if data.startswith('sports_confirm_do_'):
            await sports_confirm_done(call, bot)
        case data if data.startswith('sports_cancel_do_'):
            await sports_cancel_done(call, bot)
        case data if data.startswith('sports_my_stats_'):
            await sports_show_exercise_stats(call, bot)
        case data if data.startswith('cancel_sleep_history'):
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await sleeps_main(FakeMessage(call.message,call.message.chat,call.from_user), bot)


async def start_bot() -> None:
    """Инициализирует базу данных, запускает планировщик напоминаний и запускает polling бота."""
    await init_db()
    reminder_service = Scheduler(bot)
    await reminder_service.start()
    await censor_load()

    # Получаем текущий event loop для регистрации signal handler
    loop = asyncio.get_event_loop()

    # Функция для остановки бота
    def stop_bot_handler():
        logging.info('Получен сигнал выключения, завершаю работу бота...')
        bot.stop_polling()

    # Регистрируем обработчик сигналов через asyncio
    try:
        loop.add_signal_handler(signal.SIGINT, stop_bot_handler)
        loop.add_signal_handler(signal.SIGTERM, stop_bot_handler)
    except:
        pass

    try:
        while True:
            try:
                logging.info("Бот запущен")
                await bot.infinity_polling()
                # Если polling завершился нормально (после stop_polling), выходим
                break
            except (ReadTimeout, ConnectionError, telebot.apihelper.ApiException) as e:
                logging.error(f"Произошла ошибка: {e}. Перезапуск через 15 секунд...")
                await asyncio.sleep(15)
            except KeyboardInterrupt:
                logging.info('Получен сигнал прерывания (KeyboardInterrupt)')
                bot.stop_polling()
                break
    finally:
        # Гарантированное закрытие ресурсов
        logging.info('Остановка напоминаний...')
        try:
            await reminder_service.stop()
        except Exception as e:
            logging.error(f"Ошибка при остановке напоминаний: {e}")

        logging.info('Закрытие сессии бота...')
        try:
            # Закрыть aiohttp сессию
            if hasattr(bot, 'session_manager') and bot.session_manager:
                await bot.session_manager.session.close()
        except Exception as e:
            logging.error(f"Ошибка при закрытии сессии: {e}")

        logging.info('Бот успешно остановлен')


if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info('Главный процесс прерван')
    except Exception as e:
        logging.error(f"Критическая ошибка при запуске: {e}", exc_info=True)

