import logging
import time
import asyncio
from config import owners
from database import get_id_by_username, get_all_admin, get_username_by_id
from keyboards import return_admin_rights, go_to_ticket_keyboard
from messages import adm_update_username_msg, censorship_violation_msg, remove_adm_censor_msg, broadcast_return_adm, \
    broadcast_add_adm_msg, broadcast_remove_adm_msg, admin_notify_new_ticket, admin_notify_new_message_in_ticket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

async def admin_update_notification(bot, user_id, old_username, new_username):
    for i in owners:
        await bot.send_message(
            i,
            adm_update_username_msg(user_id, old_username, new_username)
        )


async def admin_censorship_violation(bot, text_br, sender_id, sender_username,content_type):
    await bot.send_message(sender_id, remove_adm_censor_msg(content_type))
    for i in owners:
        await bot.send_message(
            i, censorship_violation_msg(sender_id, sender_username, text_br,content_type),
            reply_markup=return_admin_rights()
        )


async def return_admin_notify(bot, user_id, owner_id):
    owner_username = await get_username_by_id(owner_id)
    user_username = await get_username_by_id(user_id)
    for i in owners:
        if i == owner_id:
            continue
        await bot.send_message(i, broadcast_return_adm(owner_id,owner_username,user_username))


async def add_admin_notify(bot, owner_id, user_id):
    for i in owners:
        if i == owner_id:
            continue
        await bot.send_message(i, broadcast_add_adm_msg(user_id, owner_id))


async def remove_admin_notify(bot, owner_id, user_id):
    for i in owners:
        if i == owner_id:
            continue
        await bot.send_message(i, broadcast_remove_adm_msg(user_id, owner_id))
async def all_admin_notify(bot,text):
        for i in await get_all_admin(only_admin=True):
            try:
                await bot.send_message(i[0], text)
                await asyncio.sleep(0.07)
            except:
                logging.warn("Ошибка отправки сообщения администратору {i}")


async def new_ticket_notify(bot,id_ticket,user_id,type_ticket):
    for i in await get_all_admin(False):
        try:
            await bot.send_message(i[0], admin_notify_new_ticket(id_ticket,type_ticket),reply_markup=go_to_ticket_keyboard(id_ticket,'admin'))
            await asyncio.sleep(0.07)
        except:
            logging.warn("Ошибка отправки сообщения администратору {i}")


async def new_message_in_ticket_notify(bot,id_ticket,type_ticket):
    for i in await get_all_admin(only_admin=False):
        try:
            await bot.send_message(i[0], admin_notify_new_message_in_ticket(id_ticket,type_ticket),reply_markup=go_to_ticket_keyboard(id_ticket,'admin'))
            await asyncio.sleep(0.07)
        except:
            logging.warn("Ошибка отправки сообщения администратору {i}")
