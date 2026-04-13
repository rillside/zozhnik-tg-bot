import asyncio
from datetime import datetime, timedelta
from typing import Any

from database import (
    add_ticket,
    clear_ticket_lock,
    count_tickets_for_admin,
    delete_ticket,
    get_ticket_id_by_message_id,
    get_message_media_info,
    get_photo_ids_by_ticket,
    get_ticket_status,
    is_ticket_locked_for_admin,
    load_info_by_ticket,
    load_tickets_info,
    replace_ticket_status,
    send_supp_msg,
    tickets_by_user,
    try_lock_ticket_for_admin,
    update_message_file_id,
)
from handlers.admin_notifications import new_message_in_ticket_notify, new_ticket_notify
from keyboards import (
    accept_aggressive_msg_keyboard,
    accept_aggressive_title_keyboard,
    accept_delete_ticket_keyboard,
    admin_ticket_section_keyboard,
    cancel_media_keyboard,
    go_to_ticket_keyboard,
    opening_ticket_keyboard,
    supp_ticket_draft_keyboard,
    support_selection_keyboard,
    ticket_actions_keyboard,
)
from messages import (
    admin_open_ticket_msg,
    admin_ticket_section_msg,
    admin_tickets_msg,
    aggressive_content_warning_msg,
    cancellation,
    confirm_delete_ticket_msg,
    error_ticket_opening_msg,
    my_tickets_msg,
    no_active_tickets_msg,
    notify_new_message_in_ticket,
    open_ticket_msg,
    succ_ticket_title_msg,
    support_selection_msg,
    ticket_closed_msg,
    ticket_locked_by_other_admin_msg,
    ticket_limit_error_msg,
)
from utils.censorship.checker import censor_check, removal_of_admin_rights
from utils.fsm import State
from utils.media_storage import save_media_to_channel, send_media_with_fallback


async def _deny_locked_admin_action(call: Any, bot: Any) -> None:
    await bot.answer_callback_query(call.id, ticket_locked_by_other_admin_msg, show_alert=True)
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


async def _ensure_admin_ticket_access(call: Any, bot: Any, ticket_id: int) -> bool:
    if await is_ticket_locked_for_admin(ticket_id, call.message.chat.id):
        await _deny_locked_admin_action(call, bot)
        return False
    return True


async def opening_ticket(message: Any, bot: Any, id_ticket: int | str, role: str, call: Any | None = None) -> None:
    """Открывает тикет для пользователя или админа: формирует историю сообщений и отправляет с клавиатурой действий."""
    max_char = 3800
    id_ticket = int(id_ticket)
    ticket_info, message_history = await load_info_by_ticket(id_ticket)
    if not ticket_info:
        await bot.send_message(message.chat.id, error_ticket_opening_msg)
        return
    id_ticket = ticket_info['id']
    title = ticket_info['title']
    user_id = ticket_info['user_id']
    username = ticket_info['username']
    first_name = ticket_info['first_name']
    status_for_admin = ticket_info['status_for_admin']
    type_ticket = ticket_info['type']
    created_date = ticket_info['created_at']
    update_date = ticket_info['updated_at']

    if role == 'admin':
        if not await try_lock_ticket_for_admin(id_ticket, message.chat.id):
            if call:
                await _deny_locked_admin_action(call, bot)
            else:
                await bot.send_message(message.chat.id, ticket_locked_by_other_admin_msg)
            return

    photos_id = await get_photo_ids_by_ticket(id_ticket)
    if role == 'user':
        text_msg = open_ticket_msg(id_ticket, title, type_ticket, created_date, update_date,
                                   message_history)

    else:
        text_msg = admin_open_ticket_msg(id_ticket, title, user_id, username, first_name,
                                         status_for_admin,
                                         type_ticket, created_date,
                                         update_date, message_history)

    if len(text_msg) <= max_char:
        last_msg = await bot.send_message(message.chat.id,
                                          text_msg,
                                          reply_markup=ticket_actions_keyboard(role=role, type=type_ticket,
                                                                            id_ticket=id_ticket,
                                                                            photos_id=photos_id)
                                          )
    else:
        messages_id = []
        count_msg = -(-len(text_msg) // max_char)  # к большему
        for i in range(1, count_msg + 1):
            if i == count_msg:
                last_msg = await bot.send_message(message.chat.id,
                                                  text_msg[max_char * (i - 1):max_char * i + 1],
                                                  reply_markup=ticket_actions_keyboard(messages_id, role, type=type_ticket,
                                                                                    id_ticket=id_ticket,
                                                                                    photos_id=photos_id)
                                                  )
            else:
                messages_id.append(await bot.send_message(
                    message.chat.id,
                    text_msg[max_char * (i - 1):max_char * i + 1]
                ))
                await asyncio.sleep(0.05)

    if await get_ticket_status(id_ticket, role) == 'new':
        await replace_ticket_status(id_ticket, 'no_new', role)
    State.set_state(message.chat.id, 'waiting_send_msg_to_ticket', [id_ticket, role, last_msg, type_ticket, user_id])

async def opening_photo_in_ticket(call: Any, bot: Any, msg_id: str) -> None:
    """Отправляет фото из тикета с fallback-механизмом через канал хранения."""
    state, state_data = State.get_state(call.message.chat.id)
    role = state_data[1] if state == 'waiting_send_msg_to_ticket' and state_data else None
    if role == 'admin':
        ticket_id = await get_ticket_id_by_message_id(int(msg_id))
        if ticket_id and await is_ticket_locked_for_admin(ticket_id, call.message.chat.id):
            await _deny_locked_admin_action(call, bot)
            return

    file_id, channel_message_id = await get_message_media_info(msg_id)
    if not file_id:
        await bot.answer_callback_query(call.id, 'Фото не найдено', show_alert=True)
        return

    # Используем fallback механизм
    async def update_callback(new_file_id: str) -> None:
        """Обновляет file_id сообщения тикета в БД после пересылки через канал."""
        await update_message_file_id(msg_id, new_file_id)

    await send_media_with_fallback(
        bot=bot,
        chat_id=call.message.chat.id,
        file_id=file_id,
        channel_message_id=channel_message_id,
        media_type='photo',
        reply_markup=cancel_media_keyboard(),
        update_callback=update_callback if channel_message_id else None
    )
async def handle_delete_ticket(call: Any, bot: Any, type_handle: str) -> None:
    """Диспетчер удаления тикета: запрос подтверждения, подтверждение или отмена."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if type_handle == 'delete':
        id_ticket = call.data.split('_')[2]
        await delete_ticket(id_ticket)
        await bot.send_message(call.message.chat.id, ticket_closed_msg(id_ticket))
    elif type_handle == 'confirm':
        ticket_id = call.data.split('_')[3]
        await bot.send_message(
            call.message.chat.id,
            confirm_delete_ticket_msg(ticket_id),
            reply_markup=accept_delete_ticket_keyboard(ticket_id)
        )
    elif type_handle == 'cancel':
        id_ticket = call.data.split('_')[3]
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await opening_ticket(call.message, bot, id_ticket, 'user')
        State.clear_state(call.message.chat.id)


async def handling_aggressive_content(call: Any, bot: Any, content_type: str) -> None:
    """Обрабатывает подтверждение / отмену агрессивного заголовка или сообщения в тикете."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if content_type == 'title':
        if call.data.split('_')[2] == 'accept':
            title, type_ticket = call.data.split('_')[3], call.data.split('_')[4]
            id_ticket = await add_ticket(title, call.message.chat.id,
                                         call.message.from_user.username,
                                         call.message.from_user.first_name,
                                         type_ticket
                                         )
            await bot.send_message(call.message.chat.id, succ_ticket_title_msg,
                                   reply_markup=supp_ticket_draft_keyboard(id_ticket))
            await new_ticket_notify(bot, id_ticket, call.message.chat.id, type_ticket)
        else:
            await bot.send_message(call.message.chat.id, ticket_closed_msg())
    else:
        ticket_id = call.data.split('_')[4]
        if call.data.split('_')[3] == 'accept':
            text = call.data.split('_')[5]
            await send_supp_msg(ticket_id, text, 1)
            await opening_ticket(call.message, bot, ticket_id, 'user')
        else:
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await opening_ticket(call.message, bot, ticket_id, 'user')


async def create_ticket(message: Any, bot: Any, type_ticket: str) -> None:
    """Создаёт новый тикет поддержки по заголовку из сообщения с проверкой цензуры."""
    if len(message.text) > 50:
        await bot.send_message(message.chat.id, ticket_limit_error_msg())
    else:
        if await censor_check(message.text):
            id_ticket = await add_ticket(message.text, message.chat.id,
                                         message.from_user.username,
                                         message.from_user.first_name, type_ticket)
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.send_message(message.chat.id, succ_ticket_title_msg,
                                   reply_markup=supp_ticket_draft_keyboard(id_ticket))
            await new_ticket_notify(bot, id_ticket, message.chat.id, type_ticket)

        else:
            await bot.send_message(
                message.chat.id,
                aggressive_content_warning_msg('заголовке'),
                reply_markup=accept_aggressive_title_keyboard(message.text, type_ticket)
            )


async def send_message_to_ticket(message: Any, bot: Any, ticket_id: int | str, role: str, last_msg: Any,
                                 type_ticket: str, user_id: int, type_msg: str = 'message',
                                 file_id: str | None = None, caption: str | None = None) -> None:
    """Отправляет сообщение или фото в тикет: проверяет цензуру, сохраняет в БД и уведомляет собеседника."""
    ticket_id = int(ticket_id)
    if role == 'admin' and await is_ticket_locked_for_admin(ticket_id, message.chat.id):
        await bot.send_message(message.chat.id, ticket_locked_by_other_admin_msg)
        State.clear_state(message.chat.id)
        return

    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, last_msg.message_id)
    except Exception:
        pass
    if type_msg == 'message':
        text = message.text
    else:
        text = caption if caption else ''
    if len(text) <= 1000:
        if await censor_check(text):
            # Если это фото, сохраняем его в канал
            channel_message_id = None
            if type_msg == 'photo' and file_id:
                channel_message_id, new_file_id = await save_media_to_channel(bot, file_id, 'photo')
                # Используем новый file_id из канала, если сохранение прошло успешно
                if channel_message_id and new_file_id:
                    file_id = new_file_id

            is_from_user = 1 if role == 'user' else 0
            await send_supp_msg(ticket_id, text, is_from_user, type_msg, file_id, channel_message_id)
            info = await load_info_by_ticket(ticket_id)
            last_update = info[0]['updated_at']
            server_time = datetime.fromisoformat(last_update) + timedelta(hours=3)
            if datetime.now() - server_time >= timedelta(hours=1):
                if role == 'user':
                    await new_message_in_ticket_notify(bot, ticket_id, type_ticket)
                else:
                    await bot.send_message(user_id,
                                           notify_new_message_in_ticket(ticket_id),
                                           reply_markup=go_to_ticket_keyboard(ticket_id, 'user')
                                           )
            role_recipient = 'user' if role == 'admin' else 'admin'
            if await get_ticket_status(ticket_id, role_recipient) == 'no_new':
                await replace_ticket_status(ticket_id, 'new', role_recipient)
        else:
            if role == 'user':
                await bot.send_message(message.chat.id,
                                       aggressive_content_warning_msg('сообщении'),
                                       reply_markup=
                                       accept_aggressive_msg_keyboard(
                                           ticket_id, text)
                                       )
                return
            else:
                await removal_of_admin_rights(bot, text,
                                              message.chat.id,
                                              message.from_user.username,
                                              'supp'
                                              )
                State.clear_state(message.chat.id)
                return
    else:
        await bot.send_message(message.chat.id, ticket_limit_error_msg(1000, 'сообщение'))

    await opening_ticket(message, bot, ticket_id, role)


async def ticket_exit(call: Any, bot: Any) -> None:
    """Closes the ticket view and returns user to the tickets list."""
    role = 'admin' if call.data.split('_')[-2] == 'admin' else 'user'
    state, state_data = State.get_state(call.message.chat.id)
    ticket_id = None
    if state == 'waiting_send_msg_to_ticket' and state_data:
        try:
            ticket_id = int(state_data[0])
        except Exception:
            ticket_id = None

    if role == 'admin' and ticket_id is not None and not await _ensure_admin_ticket_access(call, bot, ticket_id):
        State.clear_state(call.message.chat.id)
        return

    State.clear_state(call.message.chat.id)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    try:
        limit = -2 if role == 'admin' else -1
        for i in call.data.split('_')[2:limit]:
            await bot.delete_message(call.message.chat.id, int(i))
    except Exception:
        pass

    if role == 'admin' and ticket_id is not None:
        await clear_ticket_lock(ticket_id)

    if role == 'user':
        if await tickets_by_user(call.message.chat.id):
            await bot.send_message(
                call.message.chat.id,
                my_tickets_msg,
                reply_markup=opening_ticket_keyboard('user',
                                                     await load_tickets_info(call.message.chat.id))
            )
        else:
            await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=True)
    else:
        type_supp = call.data.split('_')[-1]
        if await count_tickets_for_admin(type_supp):
            await bot.send_message(call.message.chat.id
                                   , admin_tickets_msg(type_supp),
                                   reply_markup=
                                   opening_ticket_keyboard('admin',
                                                           await load_tickets_info(role='admin', type=type_supp)
                                                           ))
        else:
            await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=True)

async def tickets_exit(call: Any, bot: Any) -> None:
    """Закрывает список тикетов и возвращает на главный экран поддержки."""
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data.split('_')[2] == 'user':
        await bot.send_message(call.message.chat.id, support_selection_msg(
            call.message.from_user.first_name),
                               reply_markup=support_selection_keyboard()
                               )
    else:
        await bot.send_message(call.message.chat.id,
                               admin_ticket_section_msg(
                                   call.message.from_user.first_name),
                               reply_markup=admin_ticket_section_keyboard()
                               )


async def look_ticket_page(call: Any, bot: Any) -> None:
    """Переходит на указанную страницу списка тикетов."""
    page, role = call.data.split('_')[2], call.data.split('_')[3]
    if role == 'admin':
        type = call.data.split('_')[4]
        text = admin_tickets_msg(type)
    else:
        type = None
        text = my_tickets_msg
    try:
        await bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=opening_ticket_keyboard(
                               role, await load_tickets_info(call.message.chat.id, role=role, type=type),
                               int(page))
        )
    except:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(call.message.chat.id, text,
                               reply_markup=opening_ticket_keyboard(
                                   role, await load_tickets_info(call.message.chat.id, role=role, type=type),
                                   int(page))
                               )


async def admin_look_tickets(call: Any, bot: Any) -> None:
    """Отображает список тикетов выбранного типа для админа."""
    type_supp = call.data.split('_')[2]
    if await count_tickets_for_admin(type_supp):
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(call.message.chat.id
                               , admin_tickets_msg(type_supp),
                               reply_markup=
                               opening_ticket_keyboard('admin', await load_tickets_info(role='admin', type=type_supp)
                                                       ))
    else:
        await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=True)


