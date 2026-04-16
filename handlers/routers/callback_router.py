import telebot
from telebot.async_telebot import AsyncTeleBot

from config import is_admin
from database import get_all_admin, load_tickets_info, tickets_by_user
from handlers.admin_users import (
    admin_ban_user,
    admin_unban_user,
    admin_xp_cancel,
    admin_xp_start,
)
from handlers.ai.analyzer import ai_analyze_profile
from handlers.broadcast import broadcast_send
from handlers.leaderboard import show_leaderboard, show_xp_profile
from handlers.owner_menu import return_admin
from handlers.settings import (
    activity_goal_settings,
    activity_interval_open,
    activity_reminder_open,
    activity_setting_interval,
    activity_settings_open,
    activity_smart_type_install,
    activity_stg_cancel,
    select_timezone,
    set_reminder_type_water,
    sleep_custom_time_cancel,
    sleep_request_custom_sleep_time,
    sleep_request_custom_wake_time,
    sleep_select_sleep_time,
    sleep_select_wake_time,
    sleep_settings_open,
    sleep_stg_cancel,
    sleep_stg_sleep_time_open,
    sleep_stg_wake_time_open,
    sleep_toggle_reminder,
    water_goal_settings,
    water_setting_interval,
    water_smart_type_install,
)
from handlers.sleeps import (
    handle_sleep_history,
    handle_sleep_log_end,
    handle_sleep_log_start,
    sleeps_main,
)
from handlers.sports.admin_exercises import (
    accept_delete_exercise,
    cancel_delete_exercise,
    delete_exercise,
    edit_exercise_handle_category,
    edit_exercise_show_list,
    edit_exercise_start,
    exercise_go_back,
    exercise_management,
    handle_exercise_category,
    handle_exercise_difficulty,
    handle_exercise_edit,
    open_exercise_for_edit,
    open_video,
    save_exercise,
    save_exercise_changes,
    skip_exercise_video,
    start_add_exercise,
    stats_exercise,
)
from handlers.sports.user_exercises import (
    sports_back_to_categories,
    sports_back_to_main,
    sports_cancel_done,
    sports_check_all_start,
    sports_check_favorites_start,
    sports_confirm_done,
    sports_handle_category,
    sports_mark_done,
    sports_show_exercise,
    sports_show_exercise_stats,
    sports_show_favorites_page,
    sports_show_list,
    sports_show_my_stats,
    sports_start,
    toggle_favorite,
)
from handlers.stats import owner_stats, user_stats
from handlers.support.support import (
    admin_look_tickets,
    handle_delete_ticket,
    handling_aggressive_content,
    look_ticket_page,
    opening_photo_in_ticket,
    opening_ticket,
    ticket_exit,
    tickets_exit,
)
from handlers.water import handle_add_water
from keyboards import (
    activity_goal_keyboard,
    activity_setup_keyboard,
    admin_exercise_keyboard,
    admin_menu,
    consultation_support_keyboard,
    get_water_interval_keyboard,
    main_menu,
    opening_ticket_keyboard,
    own_cancel,
    owner_menu,
    settings_keyboard,
    stats_keyboard,
    supp_ticket_cancel_keyboard,
    support_selection_keyboard,
    technical_support_keyboard,
    timezone_selection_keyboard,
    water_goal_keyboard,
    water_setup_keyboard,
)
from messages import (
    admin_access_denied_msg,
    activity_goal_selection_msg,
    activity_tracker_setup_msg,
    add_new_adm_msg,
    cancellation,
    create_ticket_msg,
    exercise_cancel_msg,
    exit_home,
    media_is_closed_msg,
    my_tickets_msg,
    no_active_tickets_msg,
    opening_ticket_msg,
    remove_adm_msg,
    settings_msg,
    support_consult_msg,
    support_selection_msg,
    support_tech_msg,
    timezone_selection_msg,
    water_goal_selection_msg,
    water_interval_setup_msg,
    water_tracker_setup_msg,
)
from utils.fsm import State


class FakeMessage:
    def __init__(self, message: telebot.types.Message, chat: telebot.types.Chat, from_user: telebot.types.User) -> None:
        self.message = message
        self.chat = chat
        self.from_user = from_user


async def _route_base(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> bool:
    """Обрабатывает базовые колбеки, не относящиеся к конкретным разделам настроек, поддержки или спорта."""
    match call.data:
        case data if data.startswith("timezone_") and "settings" not in data:
            await select_timezone(call, bot)
        case data if data.startswith("br_accept_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            type_broadcast = data.split("_")[2]
            if type_broadcast == "msg":
                await broadcast_send(call, bot)
            elif type_broadcast == "photo":
                file_id, caption = State.get_state(call.message.chat.id)[1]
                await broadcast_send(call, bot, "photo", file_id, caption)
            elif type_broadcast == "media_group":
                pass
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case "br_cancel":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.send_message(call.message.chat.id, cancellation)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
        case "add_adm":
            sent = await bot.send_message(call.message.chat.id, add_new_adm_msg, reply_markup=own_cancel())
            State.set_state(
                call.message.chat.id,
                "waiting_admin_id",
                {"mode": "add", "prompt_msg_id": sent.message_id},
            )
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case "remove_adm":
            sent = await bot.send_message(call.message.chat.id, remove_adm_msg, reply_markup=own_cancel())
            State.set_state(
                call.message.chat.id,
                "waiting_admin_id",
                {"mode": "remove", "prompt_msg_id": sent.message_id},
            )
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case "own_cancel":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(
                call.message.chat.id,
                await owner_stats(),
                reply_markup=owner_menu(await get_all_admin()),
            )
        case "br_start_cancel":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            State.clear_state(call.message.chat.id)
            await bot.send_message(call.message.chat.id, cancellation)
        case "return_adm":
            await return_admin(call, bot)
        case _:
            return False
    return True


async def _route_settings(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> bool:
    """Обрабатывает колбеки, связанные с настройками (воды, активности, сна, часового пояса и т.д.)."""
    data = call.data
    match data:
        case "water_settings":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard(),
            )
        case "activity_settings":
            await activity_settings_open(call, bot)
        case "dream_settings":
            await sleep_settings_open(call, bot)
        case "review_settings":
            pass
        case "timezone_settings":
            await bot.answer_callback_query(call.id, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                timezone_selection_msg(call.from_user.first_name),
                reply_markup=timezone_selection_keyboard(),
            )
        case "water_reminder":
            await set_reminder_type_water(call, bot)
        case "type_smart":
            await water_smart_type_install(call, bot)
        case "type_interval":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_interval_setup_msg(call.from_user.first_name),
                reply_markup=get_water_interval_keyboard(),
            )
        case data if data.startswith("water_interval_"):
            step = "exit" if data.split("_")[-1] == "exit" else "install"
            await water_setting_interval(call, bot, step)
        case "water_goal":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                water_goal_selection_msg(call.from_user.first_name),
                reply_markup=water_goal_keyboard(),
            )
        case data if data.startswith("water_goal_") or data == "water_reminder_exit":
            action = data.split("_")[-1]
            match action:
                case "1500" | "2000" | "2500" | "3000":
                    step = "set_goal"
                case "custom":
                    step = "set_goal_custom"
                case "exit":
                    step = "exit"
                case "cancel":
                    step = "cancel_custom"
            await water_goal_settings(call, bot, step)
        case "water_stg_cancel":
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                settings_msg(call.message.from_user.first_name),
                reply_markup=settings_keyboard(),
            )
        case "activity_goal":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                activity_goal_selection_msg(call.from_user.first_name),
                reply_markup=activity_goal_keyboard(),
            )
        case "activity_reminder":
            await activity_reminder_open(call, bot)
        case "activity_type_smart":
            await activity_smart_type_install(call, bot)
        case "activity_type_interval":
            await activity_interval_open(call, bot)
        case data if data.startswith("activity_interval_"):
            last = data.split("_")[-1]
            step = "exit" if last == "exit" else "install"
            await activity_setting_interval(call, bot, step)
        case "activity_reminder_exit":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(
                call.message.chat.id,
                activity_tracker_setup_msg(call.from_user.first_name),
                reply_markup=activity_setup_keyboard(),
            )
        case data if data.startswith("activity_goal_"):
            last = data.split("_")[-1]
            if last == "custom":
                step = "set_goal_custom"
            elif last == "exit":
                step = "exit"
            elif last == "cancel":
                step = "cancel_custom"
            else:
                step = "set_goal"
            await activity_goal_settings(call, bot, step)
        case "activity_stg_cancel":
            await activity_stg_cancel(call, bot)
        case "sleep_stg_sleep_time":
            await sleep_stg_sleep_time_open(call, bot)
        case "sleep_stg_wake_time":
            await sleep_stg_wake_time_open(call, bot)
        case data if data.startswith("select_sleep_time_"):
            await sleep_select_sleep_time(call, bot)
        case data if data.startswith("select_wake_time_"):
            await sleep_select_wake_time(call, bot)
        case "sleep_time_custom":
            await sleep_request_custom_sleep_time(call, bot)
        case "wake_time_custom":
            await sleep_request_custom_wake_time(call, bot)
        case "sleep_time_exit":
            await sleep_settings_open(call, bot)
        case "wake_time_exit":
            await sleep_settings_open(call, bot)
        case "sleep_stg_toggle_reminder":
            await sleep_toggle_reminder(call, bot)
        case "sleep_stg_cancel":
            await sleep_stg_cancel(call, bot)
        case "sleep_custom_time_cancel":
            await sleep_custom_time_cancel(call, bot)
        case "sleep_log_start":
            await handle_sleep_log_start(call, bot)
        case "sleep_log_end":
            await handle_sleep_log_end(call, bot)
        case "sleep_history":
            await handle_sleep_history(call, bot)
        case "cancel_settings" | "water_add_exit":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id, user_is_admin),
            )
        case data if (
            (data == "water_add_custom" or data == "water_add_custom_cancel")
            or (data.startswith("water_add") and len(data.split("_")) == 3 and data.split("_")[-1].isdigit())
        ):
            match data.split("_")[-1]:
                case "custom":
                    step = "request_value"
                case "cancel":
                    step = "custom_cancel"
                case _:
                    step = "addition"
            await handle_add_water(call, bot, step)
        case _:
            return False
    return True


async def _route_support(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> bool:
    data = call.data
    match data:
        case "technical_support" | "personal_consultation":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                support_tech_msg if data == "technical_support" else support_consult_msg,
                reply_markup=technical_support_keyboard() if data == "technical_support" else consultation_support_keyboard(),
            )
        case "tech_supp_open_ticket" | "consult_supp_open_ticket":
            type_supp = data.split("_")[0]
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = await bot.send_message(
                call.message.chat.id,
                create_ticket_msg(type_supp),
                reply_markup=supp_ticket_cancel_keyboard(),
            )
            State.set_state(call.message.chat.id, "waiting_ticket_title", (type_supp, msg.message_id))
        case "back_to_main":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            user_is_admin = await is_admin(call.message.chat.id)
            await bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id, user_is_admin),
            )
        case data if data.startswith("accept_ticket_"):
            ticket_id = data.split("_")[2]
            await bot.answer_callback_query(call.id, opening_ticket_msg, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await opening_ticket(call.message, bot, ticket_id, "user")
        case data if data.startswith(("delete_ticket_", "confirm_delete_ticket_", "cancel_delete_ticket_")):
            type_handle = data.split("_")[0]
            await handle_delete_ticket(call, bot, type_handle)
        case data if data.startswith(("aggressive_title_", "aggressive_msg_to_ticket_")):
            content_type = "msg" if data.split("_")[1] == "msg" else "title"
            await handling_aggressive_content(call, bot, content_type)
        case "my_tickets":
            if await tickets_by_user(call.message.chat.id):
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.send_message(
                    call.message.chat.id,
                    my_tickets_msg,
                    reply_markup=opening_ticket_keyboard("user", await load_tickets_info(call.message.chat.id)),
                )
            else:
                await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
        case data if data.startswith("opening_photo_"):
            msg_id = data.split("_")[2]
            await opening_photo_in_ticket(call, bot, msg_id)
        case data if data.startswith("ticket_exit"):
            await ticket_exit(call, bot)
        case "adm_tickets_tech" | "adm_tickets_consult":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_look_tickets(call, bot)
        case data if data.startswith("tickets_exit"):
            await tickets_exit(call, bot)
        case "adm_back_main":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                exit_home("Админ"),
                reply_markup=admin_menu(call.message.chat.id),
            )
        case data if data.startswith("tickets_page_"):
            parts = data.split("_")
            if len(parts) > 3 and parts[3] == "admin" and not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await look_ticket_page(call, bot)
        case data if data.startswith("open_ticket_"):
            parts = data.split("_")
            if len(parts) > 3 and parts[3] == "admin" and not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            ticket_id, role = data.split("_")[2], data.split("_")[3]
            await opening_ticket(call.message, bot, ticket_id, role, call=call)
        case "supp_cancel_opening" | "supp_ticket_exit":
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                support_selection_msg(call.message.from_user.first_name),
                reply_markup=support_selection_keyboard(),
            )
        case "cancel_media":
            await bot.answer_callback_query(call.id, media_is_closed_msg, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case _:
            return False
    return True


async def _route_admin_and_stats(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> bool:
    """Обрабатывает колбеки, связанные с админкой и статистикой."""
    data = call.data

    match data:
        case "admin_exercise_add":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await start_add_exercise(call, bot)
        case data if data.startswith("add_exercise_category_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await handle_exercise_category(call, bot)
        case data if data.startswith("add_exercise_difficulty_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await handle_exercise_difficulty(call, bot)
        case "exercise_confirm_open_video":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await open_video(call, bot)
        case "add_exercise_skip_video":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await skip_exercise_video(call, bot)
        case "exercise_confirm_save":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await save_exercise(call.message.chat.id, call.message.from_user.username, bot)
            State.clear_state(call.message.chat.id)
        case "add_exercise_back":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await exercise_go_back(call, bot)
        case "add_exercise_cancel":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                exercise_cancel_msg,
                reply_markup=admin_exercise_keyboard(),
            )
            State.clear_state(call.message.chat.id)
        case "admin_exercise_edit" | "edit_exercise_back_to_categories":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await edit_exercise_start(call, bot)
        case data if data.startswith("filter_edit_exercise_category_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await edit_exercise_handle_category(call, bot)
        case data if (
            data.startswith("filter_edit_exercise_difficulty_")
            or data.startswith("edit_exercises_page_")
            or data.startswith("edit_exercise_back_to_list_")
        ):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await edit_exercise_show_list(call, bot)
        case data if data.startswith("edit_exercise_select_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await open_exercise_for_edit(call=call, bot=bot)
        case "edit_exercise_cancel":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            State.clear_state(call.message.chat.id)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await exercise_management(call.message, bot, call.from_user.first_name)
        case data if data.startswith("ex_edit_open_video_"):
            await open_video(call, bot, is_moment_of_creation=False)
        case data if data.startswith("ex_edit_field_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await handle_exercise_edit(call, bot)
        case data if data.startswith("edit_exercise_category") or data.startswith("edit_exercise_difficulty"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await save_exercise_changes(bot, call=call)
        case data if data.startswith("ex_edit_delete_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await accept_delete_exercise(call, bot)
        case data if data.startswith("confirm_delete_ex_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await delete_exercise(call, bot)
        case data if data.startswith("cancel_delete_ex_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await cancel_delete_exercise(call, bot)
        case "admin_exercise_stats":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await stats_exercise(call, bot)
        case "ai_analyze":
            await ai_analyze_profile(call, bot)
        case data if data.startswith("adm_ban_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_ban_user(call, bot)
        case data if data.startswith("adm_unban_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_unban_user(call, bot)
        case data if data.startswith("adm_xp_add_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_xp_start(call, bot, "add")
        case data if data.startswith("adm_xp_sub_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_xp_start(call, bot, "sub")
        case data if data.startswith("adm_xp_cancel_"):
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            await admin_xp_cancel(call, bot)
        case "adm_search_cancel":
            if not await is_admin(call.message.chat.id):
                await bot.answer_callback_query(call.id, admin_access_denied_msg, show_alert=True)
                return True
            State.clear_state(call.message.chat.id)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case "cancel_any":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case "back_to_stats":
            stats_text = await user_stats(call.message.chat.id)
            if stats_text is None:
                stats_text = "Ошибка при загрузке статистики"
            try:
                await bot.edit_message_text(
                    stats_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=stats_keyboard(),
                )
            except Exception:
                await bot.send_message(call.message.chat.id, stats_text, reply_markup=stats_keyboard())
        case _:
            return False
    return True


async def _route_sports(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> bool:
    """Обрабатывает колбеки, связанные с разделом спорта."""
    data = call.data
    match data:
        case "leaderboard_open" | "leaderboard_refresh":
            await show_leaderboard(call, bot)
        case "xp_profile":
            await show_xp_profile(call, bot)
        case "sports_check_all":
            await sports_check_all_start(call, bot)
        case "sports_check_favorites":
            await sports_check_favorites_start(call, bot)
        case "sports_check_my_stats":
            await sports_show_my_stats(call, bot)
        case "sports_close":
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await sports_start(
                call.message,
                bot,
                first_name=call.message.from_user.first_name,
            )
        case "sports_back_to_main":
            await sports_back_to_main(call, bot)
        case "sports_back_to_categories":
            await sports_back_to_categories(call, bot)
        case data if data.startswith("sport_ex_fav_page_"):
            await sports_show_favorites_page(call, bot)
        case data if data.startswith("sports_category_"):
            await sports_handle_category(call, bot)
        case data if (
            data.startswith("sports_difficulty_")
            or data.startswith("sport_ex_all_page_")
            or data.startswith("sports_back_to_list_")
        ):
            await sports_show_list(call, bot)
        case data if data.startswith("sports_open_ex_"):
            await sports_show_exercise(call, bot)
        case data if data.startswith("sports_fav_"):
            await toggle_favorite(call, bot)
        case data if data.startswith("sports_do_"):
            await sports_mark_done(call, bot)
        case data if data.startswith("sports_confirm_do_"):
            await sports_confirm_done(call, bot)
        case data if data.startswith("sports_cancel_do_"):
            await sports_cancel_done(call, bot)
        case data if data.startswith("sports_my_stats_"):
            await sports_show_exercise_stats(call, bot)
        case data if data.startswith("cancel_sleep_history"):
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await sleeps_main(FakeMessage(call.message, call.message.chat, call.from_user), bot)
        case _:
            return False
    return True


async def route_callback(call: telebot.types.CallbackQuery, bot: AsyncTeleBot) -> None:
    """Маршрутизирует колбек-запросы к соответствующим обработчикам в зависимости от префикса данных колбека."""
    for router in (_route_base, _route_settings, _route_support, _route_admin_and_stats, _route_sports):
        if await router(call, bot):
            return
