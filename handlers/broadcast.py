import logging
import asyncio

from config import is_owner, owners, save_owners
from database import all_users, replace_status
from handlers.admin_notifications import admin_censorship_violation
from keyboards import accept_send
from messages import broadcast_stats
from utils.censorship.checker import censor_check, removal_of_admin_rights

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)





async def accept_broadcast(message, bot):
    if message.text.strip():
        await bot.send_message(message.chat.id, f"📋 Предпросмотр:\n{message.text}", reply_markup=accept_send())


async def broadcast_send(call, bot):
    message = call.message.text.split(':', 1)[1].strip()
    sender_id = call.message.chat.id
    sender_username = call.from_user.username
    sender = '@' + sender_username if sender_username is not None else sender_id
    unsucc = 0
    succ = 0
    if censor_check(message):
        for i in await all_users():
            try:
                await bot.send_message(
                    i, message +
                       f"\n\n📨 Отправитель: {sender}" if is_owner(i) else message
                )
                await asyncio.sleep(0.07)
                succ += 1
            except Exception as e:
                unsucc += 1
                print(f"Ошибка при отправке рассылки {i}:\n{e}")
        await bot.send_message(call.message.chat.id, broadcast_stats(succ, unsucc))
    else:
        await removal_of_admin_rights(bot,message,sender_id,sender_username,'br')
