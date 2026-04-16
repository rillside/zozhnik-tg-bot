import asyncio

import telebot
from telebot.async_telebot import AsyncTeleBot

from config import is_admin
from database import is_user_banned
from handlers.admin_users import admin_user_search, admin_xp_input
from handlers.broadcast import accept_broadcast
from handlers.owner_menu import add_admin, remove_admin
from handlers.settings import (
    activity_goal_custom_stg,
    sleep_custom_sleep_time_input,
    sleep_custom_wake_time_input,
    water_goal_custom_stg,
)
from handlers.sports.admin_exercises import (
    handle_exercise_description,
    handle_exercise_name,
    handle_exercise_video,
    save_exercise_changes,
)
from handlers.support.support import create_ticket, send_message_to_ticket
from handlers.water import add_custom_water
from keyboards import cancel_br_start
from messages import admin_access_denied_msg, banned_msg, send_media_group_error_msg
from utils.antispam import is_group_warned, mark_group_warned
from utils.fsm import State

_locks = {}


async def handle_fsm_text(message: telebot.types.Message, bot: AsyncTeleBot) -> None:
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return

    state, data = State.get_state(message.chat.id)
    match state:
        case "waiting_broadcast_text":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            await accept_broadcast(message, bot)
        case "waiting_admin_id":
            mode = data.get("mode") if isinstance(data, dict) else data
            prompt_msg_id = data.get("prompt_msg_id") if isinstance(data, dict) else None
            if prompt_msg_id:
                try:
                    await bot.delete_message(message.chat.id, prompt_msg_id)
                except Exception:
                    pass
            if mode == "add":
                await add_admin(message, bot)
            elif mode == "remove":
                await remove_admin(message, bot)
        case "waiting_ticket_title":
            await create_ticket(message, bot, *data)
        case "waiting_send_msg_to_ticket":
            await send_message_to_ticket(message, bot, *data)
        case "waiting_add_water":
            await add_custom_water(message, bot)
        case "waiting_custom_water_goal":
            await water_goal_custom_stg(bot, message, *data)
        case "waiting_custom_activity_goal":
            await activity_goal_custom_stg(bot, message, *data)
        case "waiting_custom_sleep_time":
            await sleep_custom_sleep_time_input(bot, message, *data)
        case "waiting_custom_wake_time":
            await sleep_custom_wake_time_input(bot, message, *data)
        case "waiting_user_search":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            await admin_user_search(message, bot)
        case "waiting_admin_xp":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            await admin_xp_input(message, bot)
        case "adding_exercise":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            if data == {}:
                await handle_exercise_name(message, bot)
            elif "name" in data and "description" not in data:
                await handle_exercise_description(message, bot)
        case "waiting_new_exercise_field":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            if "action" in data and "ex_id" in data:
                await save_exercise_changes(bot, message=message)


async def handle_fsm_photo(message: telebot.types.Message, bot: AsyncTeleBot) -> None:
    state, data = State.get_state(message.chat.id)

    async with _locks.setdefault(message.chat.id, asyncio.Lock()):
        if message.media_group_id:
            group_id = message.media_group_id
            if not is_group_warned(group_id):
                await bot.send_message(
                    message.chat.id,
                    send_media_group_error_msg,
                    reply_markup=cancel_br_start(),
                )
                mark_group_warned(group_id)
            return

    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption if message.caption else None

    match state:
        case "waiting_broadcast_text":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            await accept_broadcast(message, bot, "photo", file_id, caption)
        case "waiting_send_msg_to_ticket":
            await send_message_to_ticket(
                message,
                bot,
                *data,
                type_msg="photo",
                file_id=file_id,
                caption=caption,
            )


async def handle_fsm_video(message: telebot.types.Message, bot: AsyncTeleBot) -> None:
    state, data = State.get_state(message.chat.id)
    match state:
        case "adding_exercise":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            if "difficulty" in data:
                await handle_exercise_video(message, bot)
        case "waiting_new_exercise_field":
            if not await is_admin(message.chat.id):
                await bot.send_message(message.chat.id, admin_access_denied_msg)
                State.clear_state(message.chat.id)
                return
            if "action" in data and "ex_id" in data:
                await save_exercise_changes(bot, message=message)
