from database import count_users_trackers, water_set_reminder_type, get_timezone, set_timezone, \
    update_water_goal
from keyboards import water_goal_keyboard, water_setup_keyboard, water_goal_custom_cancel, \
    get_water_reminder_type_keyboard, main_menu
from messages import  water_goal_limit_msg, water_goal_success_msg, water_goal_selection_msg, \
    water_tracker_setup_msg, water_goal_incorrect_format_msg, water_reminder_type_selection_msg, \
    water_setup_required_msg, water_reminder_type_smart_msg, water_interval_selected_short_msg, cancellation, \
    timezone_suc_msg, start_message, water_goal_custom_msg


def select_timezone(call, bot):
    timezone_offset = int(call.data.split('_')[1])
    old_timezone = get_timezone(call.message.chat.id)
    set_timezone(call.message.chat.id, timezone_offset)
    bot.answer_callback_query(call.id, timezone_suc_msg, show_alert=False)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if old_timezone is None:
        bot.send_message(
            call.message.chat.id,
            start_message(call.from_user.first_name),
            reply_markup=main_menu(call.message.chat.id)
        )


def set_reminder_type_water(call, bot):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if count_users_trackers('track_water', 'goal_ml', call.message.chat.id):
        bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        bot.send_message(call.message.chat.id,
                         water_setup_required_msg,
                         reply_markup=water_goal_keyboard())


def water_smart_type_install(call, bot):
    bot.answer_callback_query(call.id, water_reminder_type_smart_msg, show_alert=False)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    water_set_reminder_type(call.message.chat.id, 'Smart')
    bot.send_message(
        call.message.chat.id,
        water_tracker_setup_msg(call.from_user.first_name),
        reply_markup=water_setup_keyboard()
    )


def water_setting_interval(call, bot, step):
    if step == 'exit':
        bot.answer_callback_query(call.id, cancellation, show_alert=False)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        interval = int(call.data[-2])
        bot.answer_callback_query(call.id, water_interval_selected_short_msg(interval), show_alert=False)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
        water_set_reminder_type(call.message.chat.id, 'Interval', interval)


def water_goal_custom_stg(bot, message, call, send_msg):
    ml = message.text.strip()
    if ml.replace('.', '', 1).isdigit():
        if 500 <= float(ml) <= 8000:
            update_water_goal(call.from_user.id, ml)
            bot.send_message(call.message.chat.id, water_goal_success_msg(ml))
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
        send_msg = bot.send_message(message.chat.id, water_goal_incorrect_format_msg,
                                    reply_markup=water_goal_custom_cancel())
        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            lambda msg: water_goal_custom_stg(bot, msg, call, send_msg)
        )


def water_goal_settings(call, bot, step):
    if step == 'set_goal':
        goal_ml = int(call.data.split('_')[-1])
        update_water_goal(call.from_user.id, goal_ml)
        bot.answer_callback_query(call.id, water_goal_success_msg(goal_ml))
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
    elif step == 'set_goal_custom':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_custom_selection_msg = bot.send_message(
            call.message.chat.id,
            water_goal_custom_msg, reply_markup=water_goal_custom_cancel()
        )
        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            lambda msg: water_goal_custom_stg(bot, msg, call, send_custom_selection_msg)
        )
    elif step == 'exit':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, cancellation, show_alert=False)
        bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name)
            , reply_markup=water_setup_keyboard()
        )
    elif step == 'cancel_custom':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, cancellation, show_alert=False)
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        bot.send_message(call.message.chat.id,
                         water_goal_selection_msg(call.from_user.first_name),
                         reply_markup=water_goal_keyboard()
                         )
