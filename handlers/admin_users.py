"""Управление пользователями для администраторов."""
from typing import Any
from database import search_user, replace_status, admin_set_xp, get_user_xp, get_user_rank
from keyboards import user_profile_admin_keyboard, admin_search_cancel, admin_xp_cancel_keyboard
from messages import (
    user_profile_admin_msg, admin_xp_change_success_msg,
    user_search_not_found_msg, user_banned_notify_msg, user_unbanned_notify_msg,
)
from utils.fsm import set_state, get_state, clear_state


async def _safe_delete(bot: Any, chat_id: int, msg_id: int | None) -> None:
    """Удаляет сообщение без исключений, игнорируя ошибки (msg_id None-safe)."""
    if not msg_id:
        return
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


async def _send_search_prompt(chat_id: int, bot: Any) -> None:
    """Отправляет строку поиска и сохраняет msg_id в FSM."""
    sent = await bot.send_message(
        chat_id,
        "🔍 <b>Поиск пользователя</b>\n\nВведите ID или @username:",
        reply_markup=admin_search_cancel()
    )
    set_state(chat_id, 'waiting_user_search', {'prompt_msg_id': sent.message_id})


async def _show_user_profile_by_id(chat_id: int, user_id: int, bot: Any) -> None:
    """Загружает и отправляет карточку профиля по user_id."""
    row = await search_user(str(user_id))
    if not row:
        await bot.send_message(chat_id, user_search_not_found_msg(str(user_id)))
        return
    uid, username, status, created_date, last_activity, timezone = row
    xp, level = await get_user_xp(uid)
    rank = await get_user_rank(uid)
    text = user_profile_admin_msg(uid, username, status, created_date, last_activity, timezone, xp, level, rank)
    await bot.send_message(chat_id, text, reply_markup=user_profile_admin_keyboard(uid, status))


async def _show_user_profile_by_query(chat_id: int, query: str, bot: Any) -> None:
    """Ищет пользователя по запросу и показывает профиль. Если не найден — снова показывает поиск."""
    row = await search_user(query)
    if not row:
        await bot.send_message(chat_id, user_search_not_found_msg(query))
        await _send_search_prompt(chat_id, bot)
        return
    uid, username, status, created_date, last_activity, timezone = row
    xp, level = await get_user_xp(uid)
    rank = await get_user_rank(uid)
    text = user_profile_admin_msg(uid, username, status, created_date, last_activity, timezone, xp, level, rank)
    await bot.send_message(chat_id, text, reply_markup=user_profile_admin_keyboard(uid, status))


# ── Точки входа ──────────────────────────────────────────────────────────────

async def admin_users_start(message: Any, bot: Any) -> None:
    """Кнопка «🔍 Пользователи» — показывает строку поиска."""
    await _send_search_prompt(message.chat.id, bot)


async def admin_go_to_search(chat_id: int, bot: Any, msg_to_delete_id: int | None = None) -> None:
    """Удаляет сообщение (если указано) и возвращает к строке поиска."""
    await _safe_delete(bot, chat_id, msg_to_delete_id)
    await _send_search_prompt(chat_id, bot)


async def admin_user_search(message: Any, bot: Any) -> None:
    """Обрабатывает введённый запрос и показывает профиль найденного пользователя."""
    _, data = get_state(message.chat.id)
    prompt_msg_id = data.get('prompt_msg_id') if data else None
    query = message.text.strip()
    clear_state(message.chat.id)
    # удаляем промпт поиска (бот-сообщение — можно удалить)
    await _safe_delete(bot, message.chat.id, prompt_msg_id)
    await _show_user_profile_by_query(message.chat.id, query, bot)


# ── Бан / Разбан ─────────────────────────────────────────────────────────────

async def admin_ban_user(call: Any, bot: Any) -> None:
    """Банит пользователя — обновляет карточку на месте."""
    user_id = int(call.data.split('_')[-1])
    row = await search_user(str(user_id))
    if not row:
        await bot.answer_callback_query(call.id, "Пользователь не найден", show_alert=True)
        return
    uid, username, status, created_date, last_activity, timezone = row
    if status == 'Owner':
        await bot.answer_callback_query(call.id, "Нельзя забанить владельца.", show_alert=True)
        return
    await replace_status('BANNED', user_id=uid)
    try:
        await bot.send_message(uid, user_banned_notify_msg(call.from_user.username))
    except Exception:
        pass
    xp, level = await get_user_xp(uid)
    rank = await get_user_rank(uid)
    text = user_profile_admin_msg(uid, username, 'BANNED', created_date, last_activity, timezone, xp, level, rank)
    try:
        await bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            reply_markup=user_profile_admin_keyboard(uid, 'BANNED')
        )
    except Exception:
        await bot.send_message(
            call.message.chat.id, text,
            reply_markup=user_profile_admin_keyboard(uid, 'BANNED')
        )
    await bot.answer_callback_query(call.id, f"✅ {uid} заблокирован")


async def admin_unban_user(call: Any, bot: Any) -> None:
    """Разбанивает пользователя — обновляет карточку на месте."""
    user_id = int(call.data.split('_')[-1])
    row = await search_user(str(user_id))
    if not row:
        await bot.answer_callback_query(call.id, "Пользователь не найден", show_alert=True)
        return
    uid, username, status, created_date, last_activity, timezone = row
    await replace_status('User', user_id=uid)
    try:
        await bot.send_message(uid, user_unbanned_notify_msg(call.from_user.username))
    except Exception:
        pass
    xp, level = await get_user_xp(uid)
    rank = await get_user_rank(uid)
    text = user_profile_admin_msg(uid, username, 'User', created_date, last_activity, timezone, xp, level, rank)
    try:
        await bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            reply_markup=user_profile_admin_keyboard(uid, 'User')
        )
    except Exception:
        await bot.send_message(
            call.message.chat.id, text,
            reply_markup=user_profile_admin_keyboard(uid, 'User')
        )
    await bot.answer_callback_query(call.id, f"✅ {uid} разблокирован")


# ── XP ───────────────────────────────────────────────────────────────────────

async def admin_xp_start(call: Any, bot: Any, action: str) -> None:
    """Удаляет карточку профиля и запрашивает кол-во XP."""
    user_id = int(call.data.split('_')[-1])
    verb = "прибавить" if action == 'add' else "вычесть"
    await _safe_delete(bot, call.message.chat.id, call.message.message_id)
    sent = await bot.send_message(
        call.message.chat.id,
        f"✏️ Введите количество XP, которое нужно <b>{verb}</b> пользователю <code>{user_id}</code>:",
        reply_markup=admin_xp_cancel_keyboard(user_id)
    )
    set_state(call.message.chat.id, 'waiting_admin_xp', {
        'user_id': user_id,
        'action': action,
        'prompt_msg_id': sent.message_id,
    })
    await bot.answer_callback_query(call.id)


async def admin_xp_cancel(call: Any, bot: Any) -> None:
    """Отмена ввода XP — удаляет промпт и возвращает профиль пользователя."""
    user_id = int(call.data.split('_')[-1])
    clear_state(call.message.chat.id)
    await _safe_delete(bot, call.message.chat.id, call.message.message_id)
    await bot.answer_callback_query(call.id)
    await _show_user_profile_by_id(call.message.chat.id, user_id, bot)


async def admin_xp_input(message: Any, bot: Any) -> None:
    """Обрабатывает введённое количество XP."""
    _, data = get_state(message.chat.id)
    user_id = data['user_id']
    action = data['action']
    prompt_msg_id = data.get('prompt_msg_id')

    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await bot.send_message(message.chat.id, "❌ Введите положительное целое число.")
        return

    clear_state(message.chat.id)
    amount = int(text)
    delta = amount if action == 'add' else -amount
    new_xp = await admin_set_xp(user_id, delta)

    # удаляем промпт ввода (бот-сообщение)
    await _safe_delete(bot, message.chat.id, prompt_msg_id)

    await bot.send_message(message.chat.id, admin_xp_change_success_msg(user_id, delta, new_xp))
    await _show_user_profile_by_id(message.chat.id, user_id, bot)
