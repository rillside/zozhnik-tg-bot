from database import all_users, get_active_users_count, get_new_users_count, count_users_trackers
from messages import adm_stats_msg

def case_of_numerals(number):
    forms = (' пользователь', ' пользователя', ' пользователей')
    if number % 10 == 1 and number % 100 != 11:
        return str(number) + forms[0]  # 1, 21, 31, 101...
    elif 2 <= number % 10 <= 4 and not (12 <= number % 100 <= 14):
        return str(number) + forms[1]  # 2, 3, 4, 22, 23, 24...
    else:
        return str(number) + forms[2] # 5-20, 25-30, 35-40..
def adm_stats():
    cnt_users = len(all_users())
    active_cnt_users = get_active_users_count()
    active_cnt_users_percent = round(active_cnt_users / cnt_users * 100)
    active_cnt_users = case_of_numerals(active_cnt_users)
    cnt_users = case_of_numerals(cnt_users)
    new_user_to_week = get_new_users_count(7)
    new_user_to_day = get_new_users_count(1)
    water_track_cnt = case_of_numerals(count_users_trackers('track_water','goal_ml'))

    return adm_stats_msg(cnt_users, active_cnt_users,active_cnt_users_percent, new_user_to_week, new_user_to_day,water_track_cnt)


def owner_stats(admins):
    if not admins:
        return "👑 Список администрации:\n\n📭 Администраторы не найдены"

    admins_list = []
    for admin in admins:
        admins_list.append(f"🆔 ID: {admin[0]}\n"
                           f"👤 Username: {'@' + admin[1] if admin[1] else 'Не указан'}")

    return "👑 Список администрации\n\n" + "\n\n".join(admins_list)
