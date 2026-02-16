import re
from config import is_admin, owners_copy
from database import is_user_valid, get_all_admin, get_user_status, \
    get_id_by_username, replace_status
from handlers.admin_notifications import add_admin_notify, remove_admin_notify, return_admin_notify
from handlers.stats import owner_stats
from keyboards import owner_menu
from messages import incorrect_format, user_nf, user_already_admin, success_new_admin, owner_demotion_error, \
    attempt_demote_owner, user_not_admin, success_remove_admin, user_removed_admin, user_now_admin, owner_unban, \
    already_return_adm_msg, user_return_admin_msg, succ_return_adm


async def add_admin(msg, bot):
    if msg.text.strip().isdigit():
        clean_user_id = msg.text.strip()
        if await is_user_valid(user_id=clean_user_id):
            if not await is_admin(user_id=clean_user_id):
                await replace_status('Admin', user_id=clean_user_id)
                await bot.send_message(msg.chat.id, success_new_admin(msg.text))
                await bot.send_message(clean_user_id, user_now_admin)
                await add_admin_notify(bot, msg.chat.id, clean_user_id)
            else:
                await bot.send_message(msg.chat.id, user_already_admin)
        else:
            await bot.send_message(msg.chat.id, user_nf)
    elif '@' in msg.text:
        clean_username = msg.text.lstrip('@')
        if await is_user_valid(username=clean_username):
            user_id = await get_id_by_username(clean_username)
            if not await is_admin(username=clean_username):
                await replace_status('Admin', username=clean_username)
                await bot.send_message(msg.chat.id, success_new_admin(msg.text))
                await bot.send_message(
                    user_id,
                    user_now_admin
                )
                await add_admin_notify(bot, msg.chat.id, user_id)
            else:
                await bot.send_message(msg.chat.id, user_already_admin)
        else:
            await bot.send_message(msg.chat.id, user_nf)
    else:
        await bot.send_message(msg.chat.id, incorrect_format)
    await bot.send_message(msg.chat.id, owner_stats(), reply_markup=owner_menu())


async def remove_admin(msg, bot):
    if msg.text.strip().isdigit():
        clean_user_id = msg.text.strip()
        if await is_user_valid(user_id=clean_user_id):
            if await get_user_status(user_id=clean_user_id) != 'Owner':
                if await is_admin(user_id=clean_user_id):
                    await replace_status('User', user_id=clean_user_id)
                    await bot.send_message(msg.chat.id, success_remove_admin(msg.text))
                    await bot.send_message(clean_user_id, user_removed_admin)
                    await remove_admin_notify(bot, msg.chat.id, clean_user_id)
                else:
                    await bot.send_message(msg.chat.id, user_not_admin)
            else:
                await bot.send_message(clean_user_id, attempt_demote_owner(msg.chat.id,msg.from_user.username))
                await bot.send_message(msg.chat.id, owner_demotion_error)
        else:
            await bot.send_message(msg.chat.id, user_nf)
    elif '@' in msg.text:
        clean_username = msg.text.lstrip('@')
        if await is_user_valid(username=clean_username):
            user_id = await get_id_by_username(clean_username)
            if await get_user_status(username=clean_username) != 'Owner':
                if await is_admin(username=clean_username):
                    await replace_status('User', username=clean_username)
                    await bot.send_message(msg.chat.id, success_remove_admin(msg.text))
                    await bot.send_message(
                        user_id,
                        user_removed_admin
                    )
                    await remove_admin_notify(bot, msg.chat.id, user_id)
                else:
                    await bot.send_message(msg.chat.id, user_not_admin)
            else:
                await bot.send_message(user_id,
                                 attempt_demote_owner(msg.chat.id,
                                                      msg.from_user.username)
                                 )
                await bot.send_message(msg.chat.id, owner_demotion_error)
        else:
            await bot.send_message(msg.chat.id, user_nf)
    else:
        await bot.send_message(msg.chat.id, incorrect_format)
    await bot.send_message(msg.chat.id, owner_stats(), reply_markup=owner_menu())
async def return_admin(call, bot):
    user_id = int(re.search(r'ID Нарушителя: (\d+)', call.message.text).group(1))
    if user_id in owners_copy:
        await bot.send_message(call.message.chat.id, owner_unban)
    elif await get_user_status(user_id=user_id) == "Admin":
        await bot.send_message(call.message.chat.id, already_return_adm_msg)
    else:
        await replace_status('Admin', user_id=user_id)
        await bot.send_message(user_id, user_return_admin_msg)
        await bot.send_message(call.message.chat.id, succ_return_adm)
        await return_admin_notify(bot, user_id, call.message.chat.id)
    await bot.delete_message(call.message.chat.id, call.message.message_id)