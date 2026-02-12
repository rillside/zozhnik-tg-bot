import time
from datetime import datetime, timedelta

from utils.censorship.checker import censor_check, removal_of_admin_rights
from database import add_ticket, load_info_by_ticket, get_ticket_status, replace_ticket_status, send_supp_msg
from handlers.admin_notifications import new_ticket_notify, new_message_in_ticket_notify
from keyboards import supp_ticket_draft_keyboard, ticket_exit_keyboard, go_to_ticket_keyboard, \
    accept_aggressive_msg_keyboard, accept_aggressive_title_keyboard
from messages import aggressive_content_warning_msg, succ_ticket_title_msg, open_ticket_msg, \
    admin_open_ticket_msg, ticket_limit_error_msg, upload_photo_error, notify_new_message_in_ticket, \
    error_ticket_opening_msg


def create_ticket(message, bot, type_ticket):
    if len(message.text) > 50:
        bot.send_message(message.chat.id, ticket_limit_error_msg())
        bot.register_next_step_handler_by_chat_id(
            message.chat.id,
            lambda msg: create_ticket(msg, bot, type_ticket)
        )
    else:
        if censor_check(message.text):
            id_ticket = add_ticket(message.text, message.chat.id,
                                   message.from_user.username,
                                   message.from_user.first_name, type_ticket)
            bot.send_message(message.chat.id, succ_ticket_title_msg,
                             reply_markup=supp_ticket_draft_keyboard(id_ticket))
            new_ticket_notify(bot, id_ticket, message.chat.id, type_ticket)

        else:
            bot.send_message(
                message.chat.id,
                aggressive_content_warning_msg('заголовке'),
            reply_markup=accept_aggressive_title_keyboard(message.text,type_ticket)
            )


def opening_ticket(message, bot, id_ticket, role):
    max_char = 3800
    ticket_info, message_history = load_info_by_ticket(id_ticket)
    id_ticket, title, user_id, username, first_name, status_for_user, status_for_admin, type_ticket, created_date, update_date = ticket_info
    if not ticket_info:
        bot.send_message(message.chat.id,error_ticket_opening_msg)
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
        last_msg = bot.send_message(message.chat.id,
                                    text_msg,
                                    reply_markup=ticket_exit_keyboard(role=role, type=type_ticket,id_ticket=id_ticket)
                                    )
    else:
        messages_id = []
        count_msg = -(-len(text_msg) // max_char)  # к большему
        for i in range(1, count_msg + 1):
            if i == count_msg:
                last_msg = bot.send_message(message.chat.id,
                                            text_msg[max_char * (i - 1):max_char * i + 1],
                                            reply_markup=ticket_exit_keyboard(messages_id, role, type=type_ticket,
                                                                              id_ticket=id_ticket)
                                            )
            else:
                messages_id.append(bot.send_message(
                    message.chat.id,
                    text_msg[max_char * (i - 1):max_char * i + 1]
                ))
                time.sleep(0.05)

    if get_ticket_status(id_ticket, role) == 'new':
        replace_ticket_status(id_ticket, 'no_new', role)
    bot.register_next_step_handler_by_chat_id(message.chat.id,
                                              lambda msg: send_message_to_ticket(msg, bot, id_ticket, role, last_msg,
                                                                                 type_ticket, user_id)
                                              )


def send_message_to_ticket(message, bot, ticket_id, role, last_msg, type_ticket, user_id):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, last_msg.message_id)
    except Exception:
        pass
    if type(message.text) == str:
        if len(message.text) <= 1000:
            if censor_check(message.text):
                is_from_user = 1 if role == 'user' else 0
                send_supp_msg(ticket_id, message.text, is_from_user)
                last_update = load_info_by_ticket(ticket_id)[0][-1]
                server_time = datetime.fromisoformat(last_update) + timedelta(hours=3)
                if datetime.now() - server_time >= timedelta(hours=1):
                    if role == 'user':
                        new_message_in_ticket_notify(bot, ticket_id, type_ticket)
                    else:
                        bot.send_message(user_id,
                                         notify_new_message_in_ticket(ticket_id),
                                         reply_markup=go_to_ticket_keyboard(ticket_id, 'user')
                                         )
                role_recipient = 'user' if role == 'admin' else 'admin'
                if get_ticket_status(ticket_id, role_recipient) == 'no_new':
                    replace_ticket_status(ticket_id, 'new', role_recipient)
            else:
                if role == 'user':
                    bot.send_message(message.chat.id,
                                     aggressive_content_warning_msg('сообщении'),
                                     reply_markup=
                                     accept_aggressive_msg_keyboard(
                                         ticket_id, message.text)
                                     )
                    return
                else:
                    removal_of_admin_rights(bot, message.text,
                                            message.chat.id,
                                            message.from_user.username,
                                            'supp'
                                            )
                    return
        else:
            bot.send_message(message.chat.id, ticket_limit_error_msg(1000, 'сообщение'))
    else:
        bot.send_message(message.chat.id, upload_photo_error)
    opening_ticket(message, bot, ticket_id, role)
