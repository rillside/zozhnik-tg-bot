import asyncio
from datetime import datetime, timedelta

from utils.censorship.checker import censor_check, removal_of_admin_rights
from database import add_ticket, load_info_by_ticket, get_ticket_status, replace_ticket_status, send_supp_msg, \
    delete_ticket, tickets_by_user, load_tickets_info, count_tickets_for_admin
from handlers.admin_notifications import new_ticket_notify, new_message_in_ticket_notify
from keyboards import supp_ticket_draft_keyboard, ticket_exit_keyboard, go_to_ticket_keyboard, \
    accept_aggressive_msg_keyboard, accept_aggressive_title_keyboard, accept_delete_ticket_keyboard, \
    opening_ticket_keyboard, support_selection_keyboard, admin_ticket_section_keyboard
from messages import aggressive_content_warning_msg, succ_ticket_title_msg, open_ticket_msg, \
    admin_open_ticket_msg, ticket_limit_error_msg, upload_photo_error, notify_new_message_in_ticket, \
    error_ticket_opening_msg, ticket_closed_msg, confirm_delete_ticket_msg, cancellation, my_tickets_msg, \
    no_active_tickets_msg, admin_tickets_msg, support_selection_msg, admin_ticket_section_msg
from utils.fsm import clear_state, set_state


async def opening_ticket(message, bot, id_ticket, role):
    max_char = 3800
    ticket_info, message_history = await load_info_by_ticket(id_ticket)
    id_ticket, title, user_id, username, first_name, status_for_user, status_for_admin, type_ticket, created_date, update_date = ticket_info
    if not ticket_info:
        await bot.send_message(message.chat.id, error_ticket_opening_msg)
        return
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
                                    reply_markup=ticket_exit_keyboard(role=role, type=type_ticket, id_ticket=id_ticket)
                                    )
    else:
        messages_id = []
        count_msg = -(-len(text_msg) // max_char)  # к большему
        for i in range(1, count_msg + 1):
            if i == count_msg:
                last_msg = await bot.send_message(message.chat.id,
                                            text_msg[max_char * (i - 1):max_char * i + 1],
                                            reply_markup=ticket_exit_keyboard(messages_id, role, type=type_ticket,
                                                                              id_ticket=id_ticket)
                                            )
            else:
                messages_id.append(await bot.send_message(
                    message.chat.id,
                    text_msg[max_char * (i - 1):max_char * i + 1]
                ))
                await asyncio.sleep(0.05)

    if await get_ticket_status(id_ticket, role) == 'new':
        await replace_ticket_status(id_ticket, 'no_new', role)
    set_state(message.chat.id,'waiting_send_msg_to_ticket',[id_ticket,role,last_msg,type_ticket,user_id])

async def handle_delete_ticket(call, bot, type_handle):
    await bot.delete_message(call.message.chat.id, call.message_id)
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
        await bot.answer_callback_query(call.id, cancellation)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await opening_ticket(call.message, bot, id_ticket, 'user')
        clear_state(call.message.chat.id)


async def handling_aggressive_content(call, bot, content_type):
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


async def create_ticket(message, bot, type_ticket):
    if len(message.text) > 50:
        await bot.send_message(message.chat.id, ticket_limit_error_msg())
    else:
        if await censor_check(message.text):
            id_ticket = await add_ticket(message.text, message.chat.id,
                                   message.from_user.username,
                                   message.from_user.first_name, type_ticket)
            await bot.send_message(message.chat.id, succ_ticket_title_msg,
                             reply_markup=supp_ticket_draft_keyboard(id_ticket))
            await new_ticket_notify(bot, id_ticket, message.chat.id, type_ticket)

        else:
            await bot.send_message(
                message.chat.id,
                aggressive_content_warning_msg('заголовке'),
                reply_markup=accept_aggressive_title_keyboard(message.text, type_ticket)
            )



async def send_message_to_ticket(message, bot, ticket_id, role, last_msg, type_ticket, user_id):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, last_msg.message_id)
    except Exception:
        pass
    if type(message.text) == str:
        if len(message.text) <= 1000:
            if await censor_check(message.text):
                is_from_user = 1 if role == 'user' else 0
                await send_supp_msg(ticket_id, message.text, is_from_user)
                info = await load_info_by_ticket(ticket_id)
                last_update = info[0][-1]
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
                                         ticket_id, message.text)
                                     )
                    return
                else:
                    await removal_of_admin_rights(bot, message.text,
                                            message.chat.id,
                                            message.from_user.username,
                                            'supp'
                                            )
                    return
        else:
            await bot.send_message(message.chat.id, ticket_limit_error_msg(1000, 'сообщение'))
    else:
        await bot.send_message(message.chat.id, upload_photo_error)
    await opening_ticket(message, bot, ticket_id, role)


async def ticket_exit(call, bot):
    clear_state(call.message.chat.id)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    role = 'admin' if call.data.split('_')[-2] == 'admin' else 'user'
    try:
        limit = -2 if role == 'admin' else -1
        for i in call.data.split('_')[2:limit]:
            await bot.delete_message(call.message.chat.id, int(i))
    except:
        pass
    if role == 'user':
        if await tickets_by_user(call.message.chat.id):
            await bot.send_message(
                call.message.chat.id,
                my_tickets_msg,
                reply_markup=opening_ticket_keyboard('user',
                                                     await load_tickets_info(call.message.chat.id))
            )
        else:
            await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
    else:
        type_supp = call.data.split('_')[-1]
        if await count_tickets_for_admin(type_supp):
            await bot.send_message(call.message.chat.id
                             , admin_tickets_msg(type_supp),
                             reply_markup=
                             opening_ticket_keyboard('admin', await load_tickets_info(role='admin', type=type_supp)
                                                     ))
        else:
            await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)


async def tickets_exit(call, bot):
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


async def look_ticket_page(call, bot):
    page, role = call.data.split('_')[2], call.data.split('_')[3]
    if role == 'admin':
        type = call.data.split('_')[4]
        text = admin_tickets_msg(type)
    else:
        type = None
        text = my_tickets_msg
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(call.message.chat.id, text,
                     reply_markup=opening_ticket_keyboard(
                         role, await load_tickets_info(call.message.chat.id, role=role, type=type),
                         int(page))
                     )


async def admin_look_tickets(call, bot):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    type_supp = call.data.split('_')[2]
    if await count_tickets_for_admin(type_supp):
        await bot.send_message(call.message.chat.id
                         , admin_tickets_msg(type_supp),
                         reply_markup=
                         opening_ticket_keyboard('admin', await load_tickets_info(role='admin', type=type_supp)
                                                 ))
    else:
        await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
