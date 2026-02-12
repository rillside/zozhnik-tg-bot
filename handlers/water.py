from database import validate_water_addition, update_last_add_water_ml, add_water_ml, water_stats
from keyboards import accept_custom_add_water_keyboard, cancel_custom_add_water_keyboard, water_add_keyboard
from messages import water_custom_input_accept_msg, water_custom_input_limit_msg, water_custom_input_format_error_msg, \
    add_water_msg, water_tracker_dashboard_msg, water_add_custom_input_msg, cancellation


def handle_add_water(call, bot, step):
    if step == 'addition':
        water_add = call.data.split('_')[2]
        accept, msg = validate_water_addition(call.message.chat.id, water_add)

        if accept:
            update_last_add_water_ml(call.message.chat.id)
            add_water_ml(call.message.chat.id, water_add)
            bot.answer_callback_query(call.id, add_water_msg)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            current_goal, water_drunk = water_stats(call.message.chat.id)
            bot.send_message(call.message.chat.id,
                             water_tracker_dashboard_msg(
                                 call.from_user.first_name,
                                 current_goal, water_drunk),
                             reply_markup=water_add_keyboard()
                             )
        if msg:
            bot.send_message(call.message.chat.id, msg)
    elif step == 'request_value':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id,
                         water_add_custom_input_msg(
                             call.message.from_user.first_name),
                         reply_markup=cancel_custom_add_water_keyboard()
                         )
        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            lambda msg: add_custom_water(msg, bot)
        )
    elif step == 'custom_cancel':
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        bot.answer_callback_query(call.id, cancellation, show_alert=False)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        current_goal, water_drunk = water_stats(call.message.chat.id)
        bot.send_message(call.message.chat.id,
                         water_tracker_dashboard_msg(
                             call.message.from_user.first_name,
                             current_goal, water_drunk),
                         reply_markup=water_add_keyboard()
                         )


def add_custom_water(message, bot):
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
            bot.send_message(message.chat.id, water_custom_input_limit_msg(ml),
                             reply_markup=cancel_custom_add_water_keyboard()
                             )
    else:
        bot.send_message(message.chat.id, water_custom_input_format_error_msg,
                         reply_markup=cancel_custom_add_water_keyboard()
                         )
    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda msg: add_custom_water(msg, bot))
