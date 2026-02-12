import time

from config import is_owner, owners, save_owners
from database import all_users, replace_status
from handlers.admin_notifications import admin_censorship_violation
from utils.censorship.checker import censor_check, removal_of_admin_rights
from keyboards import accept_send
from messages import broadcast_stats



def accept_broadcast(message, bot):
    if message.text.strip():
        bot.send_message(message.chat.id, f"📋 Предпросмотр:\n{message.text}", reply_markup=accept_send())


def broadcast_send(call, bot):
    message = call.message.text.split(':', 1)[1]
    sender_id = call.message.chat.id
    sender_username = call.from_user.username
    sender = '@' + sender_username if sender_username is not None else sender_id
    unsucc = 0
    succ = 0
    if censor_check(message):
        for i in all_users():
            try:
                bot.send_message(
                    i, message +
                       f"\n\n📨 Отправитель: {sender}" if is_owner(i) else message
                )
                time.sleep(0.07)
                succ += 1
            except Exception as e:
                unsucc += 1
                print(f"Ошибка при отправке рассылки {i}:\n{e}")
        bot.send_message(call.message.chat.id, broadcast_stats(succ, unsucc))
    else:
        removal_of_admin_rights(bot, message, sender_id, sender_username,'broadcast')
