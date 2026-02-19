from config import is_admin
from database import count_users_trackers, water_set_reminder_type, get_timezone, set_timezone, \
    update_water_goal
from keyboards import water_goal_keyboard, water_setup_keyboard, water_goal_custom_cancel, \
    get_water_reminder_type_keyboard, main_menu
from messages import  water_goal_limit_msg, water_goal_success_msg, water_goal_selection_msg, \
    water_tracker_setup_msg, water_goal_incorrect_format_msg, water_reminder_type_selection_msg, \
    water_setup_required_msg, water_reminder_type_smart_msg, water_interval_selected_short_msg, cancellation, \
    timezone_suc_msg, start_message, water_goal_custom_msg
from utils.fsm import clear_state, set_state, user_states


async def select_timezone(call, bot):
    timezone_offset = int(call.data.split('_')[1])
    old_timezone = await get_timezone(call.message.chat.id)
    await set_timezone(call.message.chat.id, timezone_offset)
    await bot.answer_callback_query(call.id, timezone_suc_msg, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if old_timezone is None:
        user_is_admin = await is_admin(call.message.chat.id)
        await bot.send_message(
            call.message.chat.id,
            start_message(call.from_user.first_name),
            reply_markup=main_menu(call.message.chat.id,user_is_admin)
        )


async def set_reminder_type_water(call, bot):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if await count_users_trackers('track_water', 'goal_ml', call.message.chat.id):
        await bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        await bot.send_message(call.message.chat.id,
                         water_setup_required_msg,
                         reply_markup=water_goal_keyboard())


async def water_smart_type_install(call, bot):
    await bot.answer_callback_query(call.id, water_reminder_type_smart_msg, show_alert=False)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await water_set_reminder_type(call.message.chat.id, 'Smart')
    await bot.send_message(
        call.message.chat.id,
        water_tracker_setup_msg(call.from_user.first_name),
        reply_markup=water_setup_keyboard()
    )


async def water_setting_interval(call, bot, step):
    if step == 'exit':
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_reminder_type_selection_msg(
                call.from_user.first_name)
            , reply_markup=get_water_reminder_type_keyboard()
        )
    else:
        interval = int(call.data[-2])
        await bot.answer_callback_query(call.id, water_interval_selected_short_msg(interval), show_alert=False)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
        await water_set_reminder_type(call.message.chat.id, 'Interval', interval)


async def water_goal_custom_stg(bot, message, call, send_msg):
    ml = message.text.strip()
    if ml.replace('.', '', 1).isdigit():
        if 500 <= float(ml) <= 8000:
            clear_state(call.message.chat.id)
            await update_water_goal(call.from_user.id, ml)
            await bot.send_message(call.message.chat.id, water_goal_success_msg(ml))
            await bot.delete_message(message.chat.id, send_msg.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )


        else:
            await bot.delete_message(message.chat.id, send_msg.message_id)
            send_msg = await bot.send_message(message.chat.id, water_goal_limit_msg,
                                        reply_markup=water_goal_custom_cancel())
            set_state(call.message.chat.id,'waiting_custom_water_goal',[call,send_msg])
    else:
        await bot.delete_message(message.chat.id, send_msg.message_id)
        send_msg = await bot.send_message(message.chat.id, water_goal_incorrect_format_msg,
                                    reply_markup=water_goal_custom_cancel())
        set_state(call.message.chat.id,'waiting_custom_water_goal',[call,send_msg])


async def water_goal_settings(call, bot, step):
    if step == 'set_goal':
        goal_ml = int(call.data.split('_')[-1])
        await update_water_goal(call.from_user.id, goal_ml)
        await bot.answer_callback_query(call.id, water_goal_success_msg(goal_ml))
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name),
            reply_markup=water_setup_keyboard()
        )
    elif step == 'set_goal_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        send_custom_selection_msg = await bot.send_message(
            call.message.chat.id,
            water_goal_custom_msg, reply_markup=water_goal_custom_cancel()
        )
        set_state(call.message.chat.id, 'waiting_custom_water_goal', [call, send_custom_selection_msg])
    elif step == 'exit':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        await bot.send_message(
            call.message.chat.id,
            water_tracker_setup_msg(call.from_user.first_name)
            , reply_markup=water_setup_keyboard()
        )
    elif step == 'cancel_custom':
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.answer_callback_query(call.id, cancellation, show_alert=False)
        clear_state(call.message.chat.id)
        await bot.send_message(call.message.chat.id,
                         water_goal_selection_msg(call.from_user.first_name),
                         reply_markup=water_goal_keyboard()
                         )
