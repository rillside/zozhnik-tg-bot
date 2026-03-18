from database import get_leaderboard, get_user_rank, get_user_xp
from keyboards import leaderboard_keyboard, xp_profile_keyboard
from messages import leaderboard_msg, profile_xp_msg
from typing import Any


async def show_leaderboard(source: Any, bot: Any) -> None:
    """Показывает таблицу лидеров; source может быть message или call."""
    if hasattr(source, 'chat'):
        user_id = source.chat.id
        send = lambda text, kb: bot.send_message(user_id, text, reply_markup=kb)
    else:
        user_id = source.message.chat.id
        send = lambda text, kb: bot.edit_message_text(
            text, user_id, source.message.message_id, reply_markup=kb
        )

    rows = await get_leaderboard(20)
    user_rank = await get_user_rank(user_id)
    xp, level = await get_user_xp(user_id)
    text = leaderboard_msg(rows, user_rank, xp, level)
    await send(text, leaderboard_keyboard())


async def show_xp_profile(source: Any, bot: Any) -> None:
    """Показывает XP-профиль пользователя; source может быть message или call."""
    if hasattr(source, 'chat'):
        user_id = source.chat.id
        first_name = source.from_user.first_name
        send = lambda text, kb: bot.send_message(user_id, text, reply_markup=kb)
    else:
        user_id = source.message.chat.id
        first_name = source.from_user.first_name
        send = lambda text, kb: bot.edit_message_text(
            text, user_id, source.message.message_id, reply_markup=kb
        )

    xp, level = await get_user_xp(user_id)
    rank = await get_user_rank(user_id)
    text = profile_xp_msg(first_name, xp, level, rank)
    await send(text, xp_profile_keyboard())
