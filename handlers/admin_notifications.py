import logging
import time

from config import owners
from database import get_id_by_username, get_all_admin
from keyboards import return_admin_rights, go_to_ticket_keyboard
from messages import adm_update_username_msg, censorship_violation_msg, remove_adm_censor_msg, broadcast_return_adm, \
    broadcast_add_adm_msg, broadcast_remove_adm_msg, admin_notify_new_ticket, admin_notify_new_message_in_ticket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

def admin_update_notification(bot, user_id, old_username, new_username):
    for i in owners:
        bot.send_message(
            i,
            adm_update_username_msg(user_id, old_username, new_username)
        )


def admin_censorship_violation(bot, text_br, sender_id, sender_username,content_type):
    bot.send_message(sender_id, remove_adm_censor_msg(content_type))
    for i in owners:
        bot.send_message(
            i, censorship_violation_msg(sender_id, sender_username, text_br,content_type),
            reply_markup=return_admin_rights()
        )


def return_admin_notify(bot, user_id, owner_id):
    for i in owners:
        if i == owner_id:
            continue
        bot.send_message(i, broadcast_return_adm(user_id, owner_id))


def add_admin_notify(bot, owner_id, user_id):
    for i in owners:
        if i == owner_id:
            continue
        bot.send_message(i, broadcast_add_adm_msg(user_id, owner_id))


def remove_admin_notify(bot, owner_id, user_id):
    for i in owners:
        if i == owner_id:
            continue
        bot.send_message(i, broadcast_remove_adm_msg(user_id, owner_id))
def all_admin_notify(bot,text):
        for i in get_all_admin(only_admin=True):
            try:
                bot.send_message(i[0], text)
                time.sleep(0.07)
            except:
                logging.warn("Ошибка отправки сообщения администратору {i}")


def new_ticket_notify(bot,id_ticket,user_id,type_ticket):
    for i in get_all_admin(False):
        try:
            bot.send_message(i[0], admin_notify_new_ticket(id_ticket,type_ticket),reply_markup=go_to_ticket_keyboard(id_ticket,'admin'))
            time.sleep(0.07)
        except:
            logging.warn("Ошибка отправки сообщения администратору {i}")


def new_message_in_ticket_notify(bot,id_ticket,type_ticket):
    for i in get_all_admin(only_admin=False):
        try:
            bot.send_message(i[0], admin_notify_new_message_in_ticket(id_ticket,type_ticket),reply_markup=go_to_ticket_keyboard(id_ticket,'admin'))
            time.sleep(0.07)
        except:
            logging.warn("Ошибка отправки сообщения администратору {i}")
