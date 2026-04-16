import telebot
from telebot.async_telebot import AsyncTeleBot

from config import is_admin, is_owner
from database import count_users_trackers, get_all_admin, is_user_banned, water_stats
from handlers.admin_users import admin_users_start
from handlers.sleeps import sleeps_main
from handlers.sports.admin_exercises import exercise_management
from handlers.sports.user_exercises import sports_start
from handlers.stats import adm_stats, owner_stats, user_stats
from keyboards import (
    activity_goal_not_set_keyboard,
    admin_menu,
    admin_ticket_section_keyboard,
    cancel_br_start,
    main_menu,
    owner_menu,
    settings_keyboard,
    stats_keyboard,
    support_selection_keyboard,
    water_add_keyboard,
    water_goal_not_set_keyboard,
)
from messages import (
    activity_setup_required_msg,
    adm_start_message,
    admin_ticket_section_msg,
    banned_msg,
    example_broadcast,
    exit_home,
    nf_cmd,
    settings_msg,
    support_selection_msg,
    water_goal_not_set_msg,
    water_tracker_dashboard_msg,
)
from utils.fsm import State


async def handle_main_message(message: telebot.types.Message, bot: AsyncTeleBot) -> None:
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return

    match message.text:
        case "💧 Водный баланс":
            if await count_users_trackers("track_water", "goal_ml", message.chat.id):
                current_goal, water_drunk = await water_stats(message.chat.id)
                await bot.send_message(
                    message.chat.id,
                    water_tracker_dashboard_msg(message.from_user.first_name, current_goal, water_drunk),
                    reply_markup=water_add_keyboard(),
                )
            else:
                await bot.send_message(
                    message.chat.id,
                    water_goal_not_set_msg,
                    reply_markup=water_goal_not_set_keyboard(),
                )
        case "💪 Физ-активность":
            if await count_users_trackers("track_activity", "goal_exercises", message.chat.id):
                await sports_start(message, bot)
            else:
                await bot.send_message(
                    message.chat.id,
                    activity_setup_required_msg,
                    reply_markup=activity_goal_not_set_keyboard(),
                )
        case "😴 Сон":
            await sleeps_main(message, bot)
        case "📊 Статистика":
            stats_text = await user_stats(message.chat.id)
            if stats_text is None:
                stats_text = "Ошибка при загрузке статистики"
            await bot.send_message(message.chat.id, stats_text, reply_markup=stats_keyboard())
        case "⚙️ Настройки":
            await bot.send_message(
                message.chat.id,
                settings_msg(message.from_user.first_name),
                reply_markup=settings_keyboard(),
            )
        case "👨‍⚕️ Персональный специалист":
            await bot.send_message(
                message.chat.id,
                support_selection_msg(message.from_user.first_name),
                reply_markup=support_selection_keyboard(),
            )
        case "🛠️ Админ панель" if await is_admin(message.chat.id):
            await bot.send_message(
                message.chat.id,
                adm_start_message(message.from_user.first_name, message.chat.id),
                reply_markup=admin_menu(message.chat.id),
            )
        case "📊 Статистика пользователей" if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id, await adm_stats())
        case "📢 Рассылка" if await is_admin(message.chat.id):
            msg = await bot.send_message(message.chat.id, example_broadcast, reply_markup=cancel_br_start())
            State.set_state(message.chat.id, "waiting_broadcast_text", msg.message_id)
        case "🔍 Пользователи" if await is_admin(message.chat.id):
            await admin_users_start(message, bot)
        case "💪 Управление упражнениями" if await is_admin(message.chat.id):
            await exercise_management(message, bot)
        case "👨‍⚕️ Обращения" if await is_admin(message.chat.id):
            await bot.send_message(
                message.chat.id,
                admin_ticket_section_msg(message.from_user.first_name),
                reply_markup=admin_ticket_section_keyboard(),
            )
        case "👑 Управление администрацией" if is_owner(message.chat.id):
            await bot.send_message(
                message.chat.id,
                await owner_stats(),
                reply_markup=owner_menu(await get_all_admin()),
            )
        case "↩️ На главную":
            user_is_admin = await is_admin(message.chat.id)
            await bot.send_message(
                message.chat.id,
                exit_home(),
                reply_markup=main_menu(message.chat.id, user_is_admin),
            )
        case _:
            await bot.send_message(message.chat.id, nf_cmd)
