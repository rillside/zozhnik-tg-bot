from database import update_goal
from keyboards import water_goal_keyboard, water_setup_keyboard, water_goal_custom_cancel
from messages import incorrect_format, water_goal_limit_msg, water_goal_success_msg, water_goal_selection_msg, \
    water_tracker_setup_msg, water_goal_incorrect_format_msg


def water_goal_custom_stg(bot,message,call,send_msg):
    ml = message.text.strip()
    if ml.replace('.','',1).isdigit():
        if 500 <= float(ml) <= 8000:
            update_goal(call.from_user.id, ml)
            bot.send_message(call.message.chat.id,water_goal_success_msg(ml))
            bot.delete_message(message.chat.id, send_msg.message_id)
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )


        else:
            bot.delete_message(message.chat.id, send_msg.message_id)
            send_msg = bot.send_message(message.chat.id, water_goal_limit_msg,
                             reply_markup=water_goal_custom_cancel())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: water_goal_custom_stg(bot, msg, call, send_msg)
            )
    else:
        bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = bot.send_message(message.chat.id, water_goal_incorrect_format_msg,reply_markup=water_goal_custom_cancel())
        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            lambda msg: water_goal_custom_stg(bot, msg, call, send_msg)
        )

