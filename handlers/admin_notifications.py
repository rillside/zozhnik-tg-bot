from config import owners
from database import get_all_admin, get_username_by_id
from keyboards import return_admin_rights, go_to_ticket_keyboard
from messages import adm_update_username_msg, censorship_violation_msg, remove_adm_censor_msg, broadcast_return_adm, \
    broadcast_add_adm_msg, broadcast_remove_adm_msg, admin_notify_new_ticket, admin_notify_new_message_in_ticket
from typing import Any
from utils.rate_limit_send import rate_limited_gather


async def admin_update_notification(bot: Any, user_id: int, old_username: str | None, new_username: str | None) -> None:
    """Уведомляет всех владельцев об изменении юзернейма пользователя."""
    text = adm_update_username_msg(user_id, old_username, new_username)
    coros = [bot.send_message(owner_id, text) for owner_id in owners]
    await rate_limited_gather(coros)


async def admin_censorship_violation(bot: Any, text_br: Any, sender_id: int, sender_username: str | None, content_type: str) -> None:
    """Уведомляет владельцев о нарушении цензуры администратором и снимает его права."""
    text_to_owners = censorship_violation_msg(sender_id, sender_username, text_br, content_type)
    markup = return_admin_rights()
    coros = [bot.send_message(sender_id, remove_adm_censor_msg(content_type))]
    coros += [
        bot.send_message(owner_id, text_to_owners, reply_markup=markup)
        for owner_id in owners
    ]
    await rate_limited_gather(coros)


async def return_admin_notify(bot: Any, user_id: int, owner_id: int) -> None:
    """Уведомляет всех владельцев (кроме инициатора) о восстановлении прав админа."""
    owner_username = await get_username_by_id(owner_id)
    user_username = await get_username_by_id(user_id)
    text = broadcast_return_adm(owner_id, owner_username, user_username)
    coros = [
        bot.send_message(o_id, text) for o_id in owners if o_id != owner_id
    ]
    await rate_limited_gather(coros)


async def add_admin_notify(bot: Any, owner_id: int, user_id: int) -> None:
    """Уведомляет всех владельцев (кроме инициатора) о назначении нового администратора."""
    text = broadcast_add_adm_msg(user_id, owner_id)
    coros = [bot.send_message(o_id, text) for o_id in owners if o_id != owner_id]
    await rate_limited_gather(coros)


async def remove_admin_notify(bot: Any, owner_id: int, user_id: int) -> None:
    """Уведомляет всех владельцев (кроме инициатора) о снятии прав администратора."""
    text = broadcast_remove_adm_msg(user_id, owner_id)
    coros = [bot.send_message(o_id, text) for o_id in owners if o_id != owner_id]
    await rate_limited_gather(coros)


async def all_admin_notify(bot: Any, text: str) -> None:
    """Рассылает сообщение всем администраторам."""
    admins = await get_all_admin(only_admin=True)
    coros = [bot.send_message(admin_id, text) for admin_id, *_ in admins]
    await rate_limited_gather(coros)


async def new_ticket_notify(bot: Any, id_ticket: int, user_id: int, type_ticket: str) -> None:
    """Уведомляет всех администраторов о новом тикете поддержки."""
    admins = await get_all_admin(False)
    text = admin_notify_new_ticket(id_ticket, type_ticket)
    markup = go_to_ticket_keyboard(id_ticket, 'admin')
    coros = [
        bot.send_message(admin_id, text, reply_markup=markup)
        for admin_id, *_ in admins
    ]
    await rate_limited_gather(coros)


async def new_message_in_ticket_notify(bot: Any, id_ticket: int, type_ticket: str) -> None:
    """Уведомляет всех администраторов о новом сообщении в тикете."""
    admins = await get_all_admin(only_admin=False)
    text = admin_notify_new_message_in_ticket(id_ticket, type_ticket)
    markup = go_to_ticket_keyboard(id_ticket, 'admin')
    coros = [
        bot.send_message(admin_id, text, reply_markup=markup)
        for admin_id, *_ in admins
    ]
    await rate_limited_gather(coros)
