from config import is_admin
from database import is_user_valid, get_all_admin, get_user_status, \
    get_id_by_username, replace_status
from handlers.admin_notifications import add_admin_notify, remove_admin_notify
from handlers.stats import owner_stats
from keyboards import owner_menu
from messages import incorrect_format, user_nf, user_already_admin, success_new_admin, owner_demotion_error, \
    attempt_demote_owner, user_not_admin, success_remove_admin, user_removed_admin, user_now_admin


def add_admin(msg, bot):
    if msg.text.strip().isdigit():
        clean_user_id = msg.text.strip()
        if is_user_valid(user_id=clean_user_id):
            if not is_admin(user_id=clean_user_id):
                replace_status('Admin', user_id=clean_user_id)
                bot.send_message(msg.chat.id, success_new_admin(msg.text))
                bot.send_message(clean_user_id, user_now_admin)
                add_admin_notify(bot, msg.chat.id, clean_user_id)
            else:
                bot.send_message(msg.chat.id, user_already_admin)
        else:
            bot.send_message(msg.chat.id, user_nf)
    elif '@' in msg.text:
        clean_username = msg.text.lstrip('@')
        if is_user_valid(username=clean_username):
            user_id = get_id_by_username(clean_username)
            if not is_admin(username=clean_username):
                replace_status('Admin', username=clean_username)
                bot.send_message(msg.chat.id, success_new_admin(msg.text))
                bot.send_message(
                    user_id,
                    user_now_admin
                )
                add_admin_notify(bot, msg.chat.id, user_id)
            else:
                bot.send_message(msg.chat.id, user_already_admin)
        else:
            bot.send_message(msg.chat.id, user_nf)
    else:
        bot.send_message(msg.chat.id, incorrect_format)
    bot.send_message(msg.chat.id, owner_stats(get_all_admin()), reply_markup=owner_menu())


def remove_admin(msg, bot):
    if msg.text.strip().isdigit():
        clean_user_id = msg.text.strip()
        if is_user_valid(user_id=clean_user_id):
            if get_user_status(user_id=clean_user_id) != 'Owner':
                if is_admin(user_id=clean_user_id):
                    replace_status('User', user_id=clean_user_id)
                    bot.send_message(msg.chat.id, success_remove_admin(msg.text))
                    bot.send_message(clean_user_id, user_removed_admin)
                    remove_admin_notify(bot, msg.chat.id, clean_user_id)
                else:
                    bot.send_message(msg.chat.id, user_not_admin)
            else:
                bot.send_message(clean_user_id, attempt_demote_owner(msg.chat.id,msg.from_user.username))
                bot.send_message(msg.chat.id, owner_demotion_error)
        else:
            bot.send_message(msg.chat.id, user_nf)
    elif '@' in msg.text:
        clean_username = msg.text.lstrip('@')
        if is_user_valid(username=clean_username):
            user_id = get_id_by_username(clean_username)
            if get_user_status(username=clean_username) != 'Owner':
                if is_admin(username=clean_username):
                    replace_status('User', username=clean_username)
                    bot.send_message(msg.chat.id, success_remove_admin(msg.text))
                    bot.send_message(
                        user_id,
                        user_removed_admin
                    )
                    remove_admin_notify(bot, msg.chat.id, user_id)
                else:
                    bot.send_message(msg.chat.id, user_not_admin)
            else:
                bot.send_message(user_id,
                                 attempt_demote_owner(msg.chat.id,
                                                      msg.from_user.username)
                                 )
                bot.send_message(msg.chat.id, owner_demotion_error)
        else:
            bot.send_message(msg.chat.id, user_nf)
    else:
        bot.send_message(msg.chat.id, incorrect_format)
    bot.send_message(msg.chat.id, owner_stats(get_all_admin()), reply_markup=owner_menu())
