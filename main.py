import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
from functools import wraps
import logging
from requests.exceptions import ReadTimeout, ConnectionError
from database import init_db, add_user, update_user_activity_smart, update_username, \
    count_users_trackers, water_stats, get_timezone, tickets_by_user, load_tickets_info, get_all_admin
from handlers.broadcast import broadcast_send, accept_broadcast
from handlers.owner_menu import add_admin, remove_admin, return_admin
from handlers.sports.admin_exercises import exercise_management, start_add_exercise, handle_exercise_name, \
    handle_exercise_description, handle_exercise_category, handle_exercise_difficulty, handle_exercise_video, \
    save_exercise, open_video, exercise_go_back, edit_exercise_start, edit_exercise_handle_category, \
    edit_exercise_show_list, open_exercise_for_edit, save_exercise_changes, handle_exercise_edit, \
    accept_delete_exercise, delete_exercise, cancel_delete_exercise, stats_exercise
from handlers.sports.user_exercises import sports_start, sports_check_all_start, sports_handle_category, \
    sports_show_list, sports_show_exercise, toggle_favorite
from utils.antispam import mark_group_warned, is_group_warned
from utils.scheduler import Scheduler
from handlers.support.support import create_ticket, opening_ticket, handle_delete_ticket, \
    handling_aggressive_content, ticket_exit, admin_look_tickets, tickets_exit, look_ticket_page, \
    send_message_to_ticket, opening_photo_in_ticket
from handlers.water import handle_add_water, add_custom_water
from keyboards import main_menu, admin_menu, owner_menu, cancel_br_start, own_cancel, settings_keyboard, \
    water_setup_keyboard, water_goal_keyboard, get_water_interval_keyboard, water_add_keyboard, \
    timezone_selection_keyboard, support_selection_keyboard, consultation_support_keyboard, \
    technical_support_keyboard, supp_ticket_cancel_keyboard, opening_ticket_keyboard, \
    admin_ticket_section_keyboard, water_goal_not_set_keyboard, admin_exercise_keyboard, \
    exercise_category_filter_keyboard
from messages import start_message, nf_cmd, adm_start_message, exit_home, example_broadcast, cancellation, \
    add_new_adm_msg, remove_adm_msg, \
    error_msg, settings_msg, water_tracker_setup_msg, water_goal_selection_msg, water_interval_setup_msg, \
    water_tracker_dashboard_msg, water_goal_not_set_msg, timezone_selection_msg, support_selection_msg, \
    support_tech_msg, support_consult_msg, create_ticket_msg, no_active_tickets_msg, opening_ticket_msg, \
    my_tickets_msg, admin_ticket_section_msg, send_media_group_error_msg, exercise_saved_msg, \
    exercise_cancel_msg, media_is_closed_msg, edit_exercise_category_msg
from handlers.settings import set_reminder_type_water, water_smart_type_install, \
    water_setting_interval, select_timezone, water_goal_settings, water_goal_custom_stg
from handlers.sleeps import sleeps_main
from handlers.stats import adm_stats, owner_stats
from config import token, is_admin, is_owner
from utils.fsm import user_states, get_state, set_state, clear_state, clear_state_keep_data

bot = AsyncTeleBot(token,parse_mode = "Markdown")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)


def error_handler(func):
    @wraps
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Ошибка в {func.__name__}: {e}")
            chat_id = None
            if len(args) > 0:
                if hasattr(args[0], 'chat'):
                    chat_id = args[0].chat.id
                elif hasattr(args[0], 'message') and hasattr(args[0].message, 'chat'):
                    chat_id = args[0].message.chat.id

            if chat_id:
                try:
                    await bot.send_message(chat_id, error_msg)
                except:
                    pass

    return wrapper


@bot.message_handler(commands=['start'])
# @error_handler
async def start(message):
    clear_state(message.chat.id)
    user_is_admin = await is_admin(message.chat.id)
    logging.info(f"Пользователь {message.chat.id} запустил бота")
    if is_owner(message.chat.id):
        await add_user(message.chat.id, message.from_user.username,
                       'Owner')

    else:

        await add_user(message.chat.id, message.from_user.username,
                       f"{'Admin' if user_is_admin else 'User'}")
    if await get_timezone(message.chat.id) is not None:
        await bot.send_message(
            message.chat.id,
            start_message(message.from_user.first_name),
            reply_markup=main_menu(message.chat.id, user_is_admin)
        )
    else:
        await bot.send_message(message.chat.id,
                               timezone_selection_msg(
                                   message.from_user.first_name),
                               reply_markup=timezone_selection_keyboard()
                               )


@bot.message_handler(content_types=['text'],func=lambda msg: user_states.get(msg.chat.id) is not None)
async def state_handler(message):
    state, data = get_state(message.chat.id)
    match state:
        case 'waiting_broadcast_text':
            await accept_broadcast(message, bot)
        case 'waiting_admin_id':
            if data == 'add':
                await add_admin(message, bot)
            elif data == 'remove':
                await remove_admin(message, bot)
        case 'waiting_ticket_title':
            await create_ticket(message, bot, data)
        case 'waiting_send_msg_to_ticket':
            await send_message_to_ticket(message,bot,*data)
        case 'waiting_add_water':
            await add_custom_water(message, bot)
        case 'waiting_custom_water_goal':
            await water_goal_custom_stg(bot, message, *data)
        case 'adding_exercise':
            if data == {}:
                await handle_exercise_name(message,bot)
            elif 'name' in data and 'description' not in data:
                await handle_exercise_description(message,bot)
        case 'waiting_new_exercise_field':
            if 'action' in data and 'ex_id' in data:
                await save_exercise_changes(bot,message=message)


_locks = {}
@bot.message_handler(content_types=['photo'], func=lambda msg: user_states.get(msg.chat.id))
async def handle_photo_with_state(message):
    state, data = get_state(message.chat.id)
    async with _locks.setdefault(message.chat.id, asyncio.Lock()):
        if message.media_group_id:
            group_id = message.media_group_id
            if not is_group_warned(group_id):
                await bot.send_message(
                    message.chat.id,
                    send_media_group_error_msg,
                    reply_markup=cancel_br_start()
                )
                mark_group_warned(group_id)

            return
    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption if message.caption else None
    match state:
        case 'waiting_broadcast_text':
            await accept_broadcast(message, bot,'photo', file_id,caption)
        case 'waiting_send_msg_to_ticket':
            await send_message_to_ticket(message,bot,*data,type_msg='photo',file_id=file_id,caption=caption)

@bot.message_handler(content_types=['video', 'animation'], func=lambda msg: user_states.get(msg.chat.id))
async def handle_video_with_state(message):
    state, data = get_state(message.chat.id)
    match state:
        case 'adding_exercise':
            if 'difficulty' in data:
                await handle_exercise_video(message,bot)
        case 'waiting_new_exercise_field':
            if 'action' in data and 'ex_id' in data:
                await save_exercise_changes(bot,message=message)


@bot.message_handler(content_types=['text'])
# @error_handler
async def msg(message):
    await update_username(message.chat.id, message.from_user.username, bot)
    await update_user_activity_smart(message.chat.id)
    match message.text:
        case "💧 Водный баланс":
            if await count_users_trackers('track_water', 'goal_ml', message.chat.id):
                current_goal, water_drunk = await water_stats(message.chat.id)
                await bot.send_message(message.chat.id,
                                       water_tracker_dashboard_msg(
                                           message.from_user.first_name,
                                           current_goal, water_drunk),
                                       reply_markup=water_add_keyboard()
                                       )
            else:
                await bot.send_message(message.chat.id,
                                       water_goal_not_set_msg,
                                       reply_markup=water_goal_not_set_keyboard())
        case "💪 Физ-активность":
            await sports_start(message,bot)

        case "😴 Сон":
            await bot.send_message(message.chat.id, sleeps_main())

        case "📊 Статистика":
            await bot.send_message(message.chat.id, "тут будет статистика")

        case "⚙️ Настройки":
            await bot.send_message(
                message.chat.id,
                settings_msg(message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case "👨‍⚕️ Персональный специалист":
            await bot.send_message(message.chat.id, support_selection_msg(
                message.from_user.first_name),
                                   reply_markup=support_selection_keyboard()
                                   )

        case '🛠️ Админ панель' if await is_admin(message.chat.id):
            await bot.send_message(
                message.chat.id,
                adm_start_message(message.from_user.first_name,
                                  message.chat.id),
                reply_markup=admin_menu(message.chat.id)
            )

        case "📊 Статистика пользователей" if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id, await adm_stats())
        case '📢 Рассылка' if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                                   example_broadcast, reply_markup=cancel_br_start())
            set_state(message.chat.id, 'waiting_broadcast_text', None)
        case '💪 Управление упражнениями' if await is_admin(message.chat.id):
            await exercise_management(message,bot)
        case '👨‍⚕️ Обращения' if await is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                                   admin_ticket_section_msg(
                                       message.from_user.first_name),
                                   reply_markup=admin_ticket_section_keyboard()
                                   )
        case "👑 Управление администрацией" if is_owner(message.chat.id):
            await bot.send_message(message.chat.id, await owner_stats(), reply_markup=owner_menu(await get_all_admin()))
        case "↩️ На главную":
            user_is_admin = await is_admin(message.chat.id)
            await bot.send_message(
                message.chat.id, exit_home(),
                reply_markup=main_menu(message.chat.id, user_is_admin)
            )
        case _:
            await bot.send_message(message.chat.id, nf_cmd)


@bot.callback_query_handler(func=lambda call: True)
# @error_handler
async def callback_inline(call):
    match call.data:
        case data if data.startswith('timezone_'):
            await select_timezone(call, bot)
        case data if data.startswith('br_accept_'):
            type_broadcast = data.split('_')[2]
            if type_broadcast == 'msg':
                await broadcast_send(call, bot)
            elif type_broadcast == 'photo':
                file_id,caption = get_state(call.message.chat.id)[1]
                await broadcast_send(call, bot,'photo',file_id,caption)
            elif type_broadcast == 'media_group':
                pass
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'br_cancel':
            await bot.send_message(call.message.chat.id, cancellation)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            clear_state(call.message.chat.id)
        case 'add_adm':
            await bot.send_message(call.message.chat.id, add_new_adm_msg, reply_markup=own_cancel())
            set_state(call.message.chat.id, 'waiting_admin_id', 'add')
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'remove_adm':
            await bot.send_message(call.message.chat.id, remove_adm_msg, reply_markup=own_cancel())
            set_state(call.message.chat.id, 'waiting_admin_id', 'remove')
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'own_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            clear_state(call.message.chat.id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(call.message.chat.id, await owner_stats(), reply_markup=owner_menu(await get_all_admin()))
        case 'br_start_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            clear_state(call.message.chat.id)
            await bot.send_message(call.message.chat.id, cancellation)
        case 'return_adm':
            await return_admin(call, bot)

        case 'water_settings':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )
        case 'activity_settings':
            pass
        case 'dream_settings':
            pass

        case 'review_settings':
            pass
        case 'timezone_settings':
            await bot.send_message(call.message.chat.id,
                                   timezone_selection_msg(
                                       call.message.from_user.first_name),
                                   reply_markup=timezone_selection_keyboard()
                                   )

        case 'water_reminder':
            await set_reminder_type_water(call, bot)
        case 'type_smart':
            await water_smart_type_install(call, bot)
        case 'type_interval':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id, water_interval_setup_msg(call.from_user.first_name),
                reply_markup=get_water_interval_keyboard()
            )
        case data if data.startswith('water_interval_'):
            step = 'exit' if data.split('_')[-1] == 'exit' else 'install'
            await water_setting_interval(call, bot, step)
        case 'water_goal':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   water_goal_selection_msg(call.from_user.first_name),
                                   reply_markup=water_goal_keyboard()
                                   )
        case data if data.startswith('water_goal_') or data == 'water_reminder_exit':
            match int(call.data.split('_')[-1]):
                case 1500 | 2000 | 2500 | 3000:
                    step = 'set_goal'
                case 'custom':
                    step = 'set_goal_custom'
                case 'exit':
                    step = 'exit'
                case 'cancel':
                    step = 'cancel_custom'
            await water_goal_settings(call, bot, step)

        case 'water_stg_cancel':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                settings_msg(call.message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case 'cancel_settings' | 'water_add_exit':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id, user_is_admin)
            )
        case data if ((data == 'water_add_custom'
                       or data == 'water_add_custom_cancel')
                      or (data.startswith('water_add')
                          and len(data.split('_')) == 3
                          and data.split('_')[-1].isdigit())):
            match data.split('_')[-1]:
                case 'custom':
                    step = 'request_value'
                case 'cancel':
                    step = 'custom_cancel'
                case _:
                    step = 'addition'
            await handle_add_water(call, bot, step)
        case 'technical_support' | 'personal_consultation':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   support_tech_msg if call.data == 'technical_support'
                                   else support_consult_msg,
                                   reply_markup=technical_support_keyboard()
                                   if call.data == 'technical_support'
                                   else consultation_support_keyboard()
                                   )
        case 'tech_supp_open_ticket' | 'consult_supp_open_ticket':
            type_supp = call.data.split('_')[0]
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, create_ticket_msg(type_supp),
                                   reply_markup=supp_ticket_cancel_keyboard())
            set_state(call.message.chat.id,'waiting_ticket_title',type_supp)
        case 'back_to_main':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(call.message.chat.id, exit_home(),
                                   reply_markup=main_menu(call.message.chat.id, user_is_admin))
        case data if data.startswith('accept_ticket_'):
            id_ticket = data.split('_')[2]
            await bot.answer_callback_query(call.id, opening_ticket_msg)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await opening_ticket(call.message, bot, id_ticket, 'user')
        case data if data.startswith(('delete_ticket_',
                                      'confirm_delete_ticket_',
                                      'cancel_delete_ticket_')
                                     ):
            type_handle = data.split('_')[0]
            await handle_delete_ticket(call, bot, type_handle)

        case data if data.startswith(('aggressive_title_', 'aggressive_msg_to_ticket_')):
            content_type = 'msg' if data.split('_')[1] == 'msg' else 'title'
            await handling_aggressive_content(call, bot, content_type)
        case 'my_tickets':
            if await tickets_by_user(call.message.chat.id):
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.send_message(
                    call.message.chat.id,
                    my_tickets_msg,
                    reply_markup=opening_ticket_keyboard('user',
                                                         await load_tickets_info(call.message.chat.id))
                )
            else:
                await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
        case data if data.startswith('opening_photo_'):
            msg_id = data.split('_')[2]
            await opening_photo_in_ticket(call,bot, msg_id)
        case data if data.startswith('ticket_exit'):
            await ticket_exit(call, bot)
        case 'adm_tickets_tech' | 'adm_tickets_consult':
            await admin_look_tickets(call, bot)
        case data if data.startswith('tickets_exit'):
            await tickets_exit(call, bot)
        case 'adm_back_main':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   exit_home('Админ'),
                                   reply_markup=admin_menu(call.message.chat.id)
                                   )
        case data if data.startswith('tickets_page_'):
            await look_ticket_page(call, bot)
        case data if data.startswith('open_ticket_'):
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            ticket_id, role = data.split('_')[2], data.split('_')[3]
            await opening_ticket(call.message, bot, ticket_id, role)

        case 'supp_cancel_opening' | 'supp_ticket_exit':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, support_selection_msg(
                call.message.from_user.first_name),
                                   reply_markup=support_selection_keyboard()
                                   )
        case 'cancel_media':
            await bot.answer_callback_query(call.id, media_is_closed_msg, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'admin_exercise_add':
            await start_add_exercise(call, bot)
        case data if data.startswith('add_exercise_category_'):
            await handle_exercise_category(call, bot)
        case data if data.startswith('add_exercise_difficulty_'):
            await handle_exercise_difficulty(call,bot)
        case 'exercise_confirm_open_video':
            await open_video(call, bot)
        case 'exercise_confirm_save':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await save_exercise(call.message.chat.id,call.message.from_user.username,bot)
            clear_state(call.message.chat.id)
        case 'add_exercise_back':
            await exercise_go_back(call, bot)
        case 'add_exercise_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,exercise_cancel_msg,
                                   reply_markup=admin_exercise_keyboard())
            clear_state(call.message.chat.id)
        case 'admin_exercise_edit' | 'edit_exercise_back_to_categories' :
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await edit_exercise_start(call, bot)
        case data if data.startswith('filter_edit_exercise_category_'):
            await edit_exercise_handle_category(call,bot)
        case data if (data.startswith('filter_edit_exercise_difficulty_') #Первое открытие списка
                      or data.startswith('edit_exercises_page_') #Переход между страницами
                      or data.startswith('edit_exercise_back_to_list_')): #После закрытия др. Упражнения
            await edit_exercise_show_list(call,bot)
        case data if data.startswith('edit_exercise_select_'):
            await open_exercise_for_edit(call=call,bot=bot)
        case 'edit_exercise_cancel':
            clear_state(call.message.chat.id)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await exercise_management(call.message, bot,call.from_user.first_name)
        case data if data.startswith('ex_edit_open_video_'):
            await open_video(call,bot,is_moment_of_creation=False)
        case data if data.startswith('ex_edit_field_'):
            await handle_exercise_edit(call,bot)
        case data if data.startswith('edit_exercise_category') or data.startswith('edit_exercise_difficulty'):
            await save_exercise_changes(bot,call=call)
        case data if data.startswith('ex_edit_delete_'):
            await accept_delete_exercise(call,bot)
        case data if data.startswith('confirm_delete_ex_'):
            await delete_exercise(call,bot)
        case data if data.startswith('cancel_delete_ex_'):
            await cancel_delete_exercise(call,bot)
        case 'admin_exercise_stats':
            await stats_exercise(call,bot)
        case 'cancel_any':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'sports_check_all':
            await sports_check_all_start(call,bot)
        case 'sports_close':
            await sports_start(call.message,bot,
                               first_name=call.message.from_user.first_name
                               )
        case data if data.startswith('sports_category_'):
            await sports_handle_category(call,bot)
        case data if data.startswith('sports_difficulty_')\
            or data.startswith('sport_ex_all_page_')\
            or data.startswith('sports_back_to_list_'):
            await sports_show_list(call,bot)
        case data if data.startswith('sports_open_ex'):
            await sports_show_exercise(call,bot)
        case data if data.startswith('sports_fav_'):
            await toggle_favorite(call,bot)
















async def start_bot():
    await init_db()
    reminder_service = Scheduler(bot)
    await reminder_service.start()
    while True:
        try:
            logging.info("Бот запущен")
            await bot.polling(none_stop=True)
        except (ReadTimeout, ConnectionError, telebot.apihelper.ApiException) as e:

            logging.error(f"Произошла ошибка: {e}. Перезапуск через 15 секунд...")
            await asyncio.sleep(15)
        except KeyboardInterrupt:
            logging.info('Бот принудительно остановлен')
            await reminder_service.stop()
            break

    # except Exception as e:
    # logging.error(f"Непредвиденная ошибка: {e}. Перезапуск через 30 секунд...")

    # await asyncio.sleep(30)


if __name__ == '__main__':
    asyncio.run(start_bot())