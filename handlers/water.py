from keyboards import accept_custom_add_water_keyboard, cancel_custom_add_water_keyboard
from messages import water_custom_input_accept_msg, water_custom_input_limit_msg, water_custom_input_format_error_msg


def add_custom_water(message,bot):
    ml = message.text.strip()
    if ml.isdigit():
        if 50 <= int(ml) <= 1500:
            bot.send_message(message.chat.id,
                             water_custom_input_accept_msg(ml),
                             reply_markup=
                             accept_custom_add_water_keyboard(ml)
                             )
            return
        else:
            bot.send_message(message.chat.id,water_custom_input_limit_msg(ml),
                             reply_markup=cancel_custom_add_water_keyboard()
                             )
    else:
        bot.send_message(message.chat.id,water_custom_input_format_error_msg,
                             reply_markup=cancel_custom_add_water_keyboard()
                         )
    bot.register_next_step_handler_by_chat_id(message.chat.id,lambda msg: add_custom_water(msg,bot))