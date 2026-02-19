import logging
import asyncio
from config import is_owner
from database import all_users
from keyboards import accept_send
from messages import broadcast_stats
from utils.censorship.checker import censor_check, removal_of_admin_rights
from utils.fsm import clear_state, set_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)





async def accept_broadcast(message, bot,type_broadcast='msg',photo_id=None,caption=None,media_group=None):
    if type_broadcast == 'msg':
        if message.text.strip():
            await bot.send_message(message.chat.id, f"📋 Предпросмотр:\n{message.text}", reply_markup=accept_send())
    elif type_broadcast == 'photo':
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_id,
            caption=f"📋 Предпросмотр:\n{caption}",reply_markup=accept_send('photo')
        )
        set_state(message.chat.id,'waiting_broadcast_accept',[photo_id,caption])




async def broadcast_send(call, bot,type_broadcast='msg',photo_id=None,caption=None):
    sender_id = call.message.chat.id
    sender_username = call.from_user.username
    sender = '@' + sender_username if sender_username is not None else sender_id
    unsucc = 0
    succ = 0
    if type_broadcast == 'msg':
        message = call.message.text.split(':', 1)[1].strip()
    else:
        message = caption.strip()

    if await censor_check(message):
        clear_state(call.message.chat.id)
        for i in await all_users():
            try:
                if type_broadcast == 'msg':
                    await bot.send_message(
                        i, message +
                           f"\n\n📨 Отправитель: {sender}" if is_owner(i) else message
                    )
                else:
                    await bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=photo_id,
                        caption=message + f"\n\n📨 Отправитель: {sender}" if is_owner(i) else ''
                    )
                await asyncio.sleep(0.07)
                succ += 1
            except Exception as e:
                unsucc += 1
                print(f"Ошибка при отправке рассылки {i}:\n{e}")
        await bot.send_message(call.message.chat.id, broadcast_stats(succ, unsucc))
    else:
        await removal_of_admin_rights(bot,message,sender_id,sender_username,'br')
