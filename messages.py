from config import owners
from database import get_username_by_id


def plural_days(count: int) -> str:
    """Возвращает правильное склонение слова "день" для числа count."""

    # Особые случаи для чисел 11-19
    if 11 <= count % 100 <= 19:
        return f"{count} дней"

    # Для остальных смотрим последнюю цифру
    last_digit = count % 10

    if last_digit == 1:
        return f"{count} день"
    elif 2 <= last_digit <= 4:
        return f"{count} дня"
    else:
        return f"{count} дней"

def timezone_selection_msg(first_name: str) -> str:
    """Сообщение выбора часового пояса при первом запуске."""
    return f"""📍 <b>Настройка часового пояса</b>

{first_name}, для корректной работы напоминаний выбери свой часовой пояс!

🇷🇺 Я поддерживаю все регионы России — просто найди свой город в списке:

⏰ <b>Часовые пояса России</b> (относительно Москвы):
• 🏰 Калининград — <b>МСК-1</b>
• ⭐ Москва — <b>МСК+0</b>
• 🌉 Самара — <b>МСК+1</b>
• 🏔️ Екатеринбург — <b>МСК+2</b>
• 🌾 Омск — <b>МСК+3</b>
• ⛰️ Красноярск — <b>МСК+4</b>
• 🏞️ Иркутск — <b>МСК+5</b>
• ❄️ Якутск — <b>МСК+6</b>
• 🌅 Владивосток — <b>МСК+7</b>
• 🏝️ Магадан — <b>МСК+8</b>
• 🌋 Камчатка — <b>МСК+9</b>

✨ <b>Зачем это нужно:</b>
• Напоминания будут приходить в твоё локальное время
• Статистика будет учитывать твой часовой пояс
• Всё автоматически синхронизируется!

💡 <b>Не нашел свой город?</b>
Выбери ближайший крупный город в твоём регионе — это даст максимально точное время!

🎯 Потрать 10 секунд сейчас — и получай напоминания вовремя всегда!"""


def start_message(first_name: str) -> str:
    """Приветственное сообщение для нового пользователя."""
    start_msg = f"""
        🥰 Привет, <b>{first_name}</b>! Приятно познакомиться!

Я — <b>ЗОЖник</b>, твой персональный источник заботы о себе в телеграме.

Моя задача — мягко напоминать о самом важном:
🔹 Вовремя пить воду
🔹 Делать перерывы на разминку
🔹 Следить за режимом сна
...и делать это всё с удовольствием!

Хочешь, я позабочусь о твоём самочувствии? 🌿

Просто нажми на кнопку «<b>Настройки</b>», и мы всё подготовим!
        """
    return start_msg


# Администрирование

def adm_stats_msg(cnt_users: int, active_cnt_users: int, active_cnt_users_percent: float,
                  new_user_to_week: int, new_user_to_day: int,
                  water_track_cnt: int, activity_track_cnt: int, sleep_track_cnt: int) -> str:
    """Сообщение с административной статистикой платформы."""
    return f"""📊 <b>Статистика платформы</b>

👥 <b>Аудитория:</b>
• Всего: <b>{cnt_users}</b>
• Активных: <b>{active_cnt_users}</b> ({active_cnt_users_percent}%)
• Новых за неделю: <b>{new_user_to_week}</b> | за сутки: <b>{new_user_to_day}</b>

📊 <b>Трекеры:</b>
• 💧 Вода: <b>{water_track_cnt}</b>
• 💪 Активность: <b>{activity_track_cnt}</b>
• 😴 Сон: <b>{sleep_track_cnt}</b>
"""


def adm_start_message(first_name: str, id: int) -> str:
    """Приветственное сообщение для входа админа/владельца в панель управления."""
    adm_start_msg = f"""
🛠️ Привет, <b>{first_name}!</b>

Рад приветствовать вас в панели управления ботом "ЗОЖник".

Ваш статус: <b>{'👑 Владелец' if id in owners else '⚡ Администратор'}</b>

<b>Доступные функции</b> мониторинга и управления:
🔹 Просмотр статистики пользователей
🔹 Рассылка
🔹 Управление контентом упражнений
🔹 Мониторинг работоспособности бота

Бот работает в штатном режиме ✅
"""
    return adm_start_msg


def success_new_admin(name: str) -> str:
    """Уведомление о успешном назначении администратора."""
    return f"✅ Пользователь {name.strip()} теперь администратор!"


def success_remove_admin(name: str) -> str:
    """Уведомление о успешном снятии прав администратора."""
    return f"✅ Пользователь {name.strip()} больше не администратор!"


def attempt_demote_owner(id: int, username: str | None) -> str:
    """Сообщение владельцу о попытке снять его права."""
    return f"⚠️ Вас попытался снять Владелец {'@' + username if username is not None else id}"


def broadcast_stats(succ: int, unsucc: int) -> str:
    """Отчёт о результатах массовой рассылки."""
    return f"""🎉 <b>Рассылка отправлена!</b>


✅ Успешно — <b>{succ}</b>
🚫 Ошибка отправки — <b>{unsucc}</b>"""


def censorship_violation_msg(sender_id: int, sender_username: str | None, text_br: str, content_type: str) -> str:
    """Сообщение админам о нарушении цензуры."""
    content_type_names = {
        'supp': 'тикете',
        'br': 'рассылке',
        'exercise': 'упражнении'
    }

    action_names = {
        'supp': 'ответа',
        'br': 'рассылки',
        'exercise': 'упражнения'
    }

    # Формируем сообщение
    return f"""🚨 <b>Обнаружены запрещённые слова</b> в {content_type_names[content_type]}

📝 Текст {action_names[content_type]}:
{text_br}

🆔 <b>ID Нарушителя:</b> {sender_id}
👤 <b>Username Нарушителя:</b> {'@' + sender_username if sender_username is not None else 'Не установлен'}
📨 {'Ответ не отправлен' if content_type == 'supp' else 'Рассылка не отправлена' if content_type == 'br' else 'Упражнение не сохранено'}
🔧 <b>Права сняты</b> до выяснения обстоятельств
    """


def broadcast_return_adm(owner_id: int, owner_username: str | None, user_username: str | None) -> str:
    """Сообщение о восстановлении админских прав."""
    return (f"🔓 Владелец "
            f"{'@' + owner_username if owner_username is not None else owner_id}"
            f" вернул права Администратору "
            f"{'@' + user_username if user_username is not None else owner_id}")


def adm_update_username_msg(user_id: int, old_username: str | None, new_username: str | None) -> str:
    """Уведомление админам о смене username администратора."""
    return f"""🔄 <b>Администратор сменил username</b>

🆔 <b>ID:</b> {user_id}

⬅️  Было: <b>{'@' + old_username if old_username is not None else 'Не установлен'}</b>

➡️ Стало: <b>{'@' + new_username if new_username is not None else 'Не установлен'}</b>"""


def broadcast_add_adm_msg(user_id: int, owner_id: int) -> str:
    """Сообщение-рассылка админам о назначении нового администратора."""
    owner_username = get_username_by_id(owner_id)
    user_username = get_username_by_id(user_id)
    return (f"👑 {'@' + owner_username if owner_username is not None else owner_id}"
            f" добавил админа"
            f" {'@' + user_username if user_username is not None else owner_id}"
            )


def broadcast_remove_adm_msg(user_id: int, owner_id: int) -> str:
    """Сообщение-рассылка админам о снятии администратора."""
    owner_username = get_username_by_id(owner_id)
    user_username = get_username_by_id(user_id)
    return (f"👑 {'@' + owner_username if owner_username is not None else owner_id}"
            f" снял админа"
            f" {'@' + user_username if user_username is not None else owner_id}"
            )


# Настройки

def settings_msg(first_name: str) -> str:
    """Главное сообщение раздела настроек."""
    return f"""🔧 <b>Настройки напоминаний</b>

{first_name}, выбери категорию для настройки:

• 🚰 <b>Вода</b> — Установи цель и интервал для питья.
• 🏃 <b>Активность</b> — Настрой частоту перерывов на разминку.
• 😴 <b>Сон</b> — Определи идеальное время отбоя и подъема.
• 📈 <b>Обзор</b> — Посмотреть мои текущие цели."""


# Водный трекер

def water_tracker_setup_msg(first_name: str) -> str:
    """Сообщение настройки водного трекера."""
    return f"""🚰 <b>Настройка водного трекера</b>

{first_name}, давай настроим твою цель по воде!

🎯 <b>Цель на день:</b>
• Сколько воды ты хочешь выпивать ежедневно?
• Рекомендуется 8 стаканов (<b>2 литра</b>)

⏰ <b>Напоминания:</b>
• В какое время тебе удобно получать напоминания?
• Можно установить несколько напоминаний в день

✨ Выбери, что хочешь настроить:"""


def water_goal_selection_msg(first_name: str) -> str:
    """Сообщение выбора дневной цели по воде."""
    return f"""💧 <b>Выбор дневной цели по воде</b>

{first_name}, давай определим твою цель на день!

🎯 <b>Рекомендуемые варианты:</b>
• <b>1.5 л</b> — Минимальная норма
• <b>2.0 л</b> — Стандартная норма
• <b>2.5 л</b> — Активный образ жизни
• <b>3.0 л</b> — Интенсивные тренировки

✨ Или можешь установить свою цель!

💡 Совет: Начни с <b>2 литров</b> и корректируй по ощущениям!"""


def water_reminder_type_selection_msg(first_name: str) -> str:
    """Сообщение выбора типа напоминаний о воде."""
    return f"""💧 <b>Выбор типа напоминаний</b>

{first_name}, как ты хочешь получать напоминания о воде?

⏰ <b>По интервалу:</b>
• Напоминает пить воду через заданные промежутки времени
• Пример: каждые 2 часа
• Подходит для регулярного питья

🤖 <b>Умный режим:</b>
• Отслеживает, когда ты последний раз пил воду
• Напоминает, если прошло более <b>3 часов</b>
• Более гибкий и персонализированный

✨ Выбери подходящий вариант:"""


def water_interval_setup_msg(first_name: str) -> str:
    """Сообщение настройки интервальных напоминаний о воде."""
    return f"""⏰ <b>Настройка интервальных напоминаний</b>

{first_name}, установи интервал между напоминаниями о воде:

📅 <b>Рекомендуемые интервалы:</b>
• <b>1 час</b> — для активного дня
• <b>2 часа</b> — стандартный режим
• <b>3 часа</b> — спокойный темп


⏱️ Или укажи свой интервал в часах

💡 Совет: Начни с <b>2 часов</b> и корректируй по ощущениям!

✨ Выбери из списка или введи своё значение:"""


def water_goal_success_msg(volume: int) -> str:
    """Уведомление об успешном установлении цели по воде."""
    return f"💧 Цель: {volume} мл. установлена!"


def water_interval_selected_short_msg(interval_hours: int) -> str:
    """Короткое подтверждение выбранного интервала напоминаний о воде."""
    intervals_text = {
        1: "каждый час",
        2: "каждые 2 часа",
        3: "каждые 3 часа",
        4: "каждые 4 часа",
        5: "каждые 5 часов"
    }
    return f"✅ Установлен интервал: {intervals_text[interval_hours]}"


def water_tracker_dashboard_msg(first_name: str, current_goal: int, water_drunk: int) -> str:
    """Дашборд водного трекера с прогресс-баром."""
    progress_percent = round(water_drunk / current_goal * 100)
    water_left = current_goal - water_drunk if water_drunk < current_goal else 0
    filled_blocks = int(progress_percent / 10)
    empty_blocks = 10 - filled_blocks
    progress_bar = "█" * filled_blocks + "░" * empty_blocks
    if progress_percent >= 100:
        status_emoji = "🎉"
        status_text = "Цель достигнута! Отличная работа!"
    elif progress_percent >= 75:
        status_emoji = "😊"
        status_text = "Почти у цели! Продолжай в том же духе!"
    elif progress_percent >= 50:
        status_emoji = "🙂"
        status_text = "Хороший прогресс! Ты на верном пути!"
    elif progress_percent >= 25:
        status_emoji = "💪"
        status_text = "Неплохо! Помни о своей цели!"
    else:
        status_emoji = "🚰"
        status_text = "В начале пути! Каждая капля важна!"

    return f"""💧 <b>Трекер воды</b>

{first_name}, вот твой прогресс на сегодня:

🎯 Дневная цель: <b>{current_goal} мл.</b>
✅ Выпито: <b>{water_drunk} мл.</b>
⏳ Осталось: <b>{water_left} мл.</b>

📊 Прогресс: <b>{progress_percent}%</b>
{progress_bar}

{status_emoji} {status_text}

💫 Добавь выпитую воду:
• Стандартные порции
• Или введи своё значение

✨ Каждый глоток приближает к цели!"""


def owner_stats_msg(admins: list) -> str:
    """Список администраторов для владельца."""
    if not admins:
        return "👑 Список администрации:\n\n📭 Администраторы не найдены"

    admins_list = []
    for admin in admins:
        admins_list.append(f"🆔 ID: {admin[0]}\n"
                           f"👤 Username: {'@' + admin[1] if admin[1] else 'Не указан'}")

    return "👑 Список администрации\n\n" + "\n\n".join(admins_list)


def water_quick_reminder_msg(current_goal: int, water_drunk: int) -> str:
    """Короткое напоминание от планировщика выпить воды."""
    water_left = max(0, current_goal - water_drunk)

    return f"""💧 <b>Напоминание от ЗОЖника</b>

💦 Не забывайте пить воду! 💦

Вот твой прогресс на сегодня:

🎯 Дневная цель: <b>{current_goal} мл.</b>
✅ Выпито: <b>{water_drunk} мл.</b>
⏳ Осталось: <b>{water_left} мл.</b>

💡 Выпей сейчас и обнови статистику! ⬇️✨"""


def water_add_time_limit_msg(wait_time: int) -> str:
    """Сообщение о необходимости подождать перед следующей записью."""
    return f"⏳ Подождите {wait_time} мин. перед следующей записью"


def water_add_hard_limit_msg(daily_hard_limit: int) -> str:
    """Сообщение о превышении суточного лимита воды."""
    return f"""❌ <b>Превышен безопасный суточный лимит</b>

Вы попытались добавить больше <b>{daily_hard_limit // 1000} литров</b> воды за день.
Это превышает максимальную безопасную норму для организма.

💡 <b>Что делать:</b>
1. Не пытайтесь выпить слишком много воды за короткое время
2. Распределяйте потребление равномерно в течение дня
3. Индивидуальную норму можно рассчитать на консультации со специалистом

🎯 <b>Как получить консультацию:</b>
1. Нажмите «👨‍⚕️ Персональный специалист» в главном меню
2. Выберите «Индивидуальная консультация»
3. Опишите ваш запрос — и наш специалист свяжется с вами!


✨ Забота о здоровье — это <b>баланс и умеренность!</b>"""


def water_add_reasonable_limit_msg(over_amount: int) -> str:
    """Сообщение о превышении рекомендованной нормы воды."""
    return f"""⚠️ <b>Внимание: превышение рекомендуемой нормы</b>

Вы превысили рекомендуемую суточную норму на <b>{over_amount} мл.</b>

💧 <b>Для справки:</b>
Средняя норма потребления воды составляет <b>30-40 мл</b> на каждый килограмм вашего веса.

👨‍⚕️ <b>Персональный подход:</b>
Каждый организм уникален! Для точного расчёта вашей индивидуальной нормы рекомендуем обратиться к специалисту.

🎯 <b>Как получить консультацию:</b>
1. Нажмите «👨‍⚕️ Персональный специалист» в главном меню
2. Выберите «Индивидуальная консультация»
3. Опишите ваш запрос — и наш специалист свяжется с вами!

✨ Помните: правильная гидратация — <b>ключ к хорошему самочувствию!</b>"""


# Поддержка

def support_selection_msg(first_name: str) -> str:
    """Главное сообщение выбора типа обращения."""
    return f"""🛠️ <b>Направь свой запрос</b>

{first_name}, выбери категорию обращения:

🔧 Техподдержка бота:
• Ошибки в работе функций
• Проблемы с настройками
• Технические вопросы

👨‍⚕️ Персональная консультация:
• Индивидуальные нормы воды
• Подбор режима активности
• Рекомендации по здоровью

✨ Мы ценим твоё время:
• Ответим максимально быстро
• Найдём оптимальное решение
• Позаботимся о комфорте

🎯 Просто выбери подходящий вариант!"""


def create_ticket_msg(type_supp: str) -> str:
    """Сообщение с просьбой ввести заголовок тикета."""
    return f"""📝 Заголовок обращения

Напишите краткое название вашего запроса.

🎯 Лимит: 50 символов
💡 Пример: {"«Не работает водный трекер»" if type_supp == 'tech' else
    "«Подбор индивидуальной нормы воды»"}"""


def ticket_limit_error_msg(max_length: int = 50, content: str = 'заголовок') -> str:
    """Ошибка превышения лимита символов в тикете."""
    return f"❌ Лимит: {max_length} символов. Сократите {content}."


def aggressive_content_warning_msg(content_type: str) -> str:
    """Предупреждение пользователю о слишком резком содержании."""
    return f"""💬 Небольшое напоминание

Мы заметили, что в {content_type} есть формулировки, которые могут звучать слишком резко.

📝 На что стоит обратить внимание:
• Резкие или эмоциональные выражения
• Формулировки, которые могут быть восприняты как давление

🤍 Мы здесь, чтобы помочь:
Попробуйте переформулировать запрос в спокойном и нейтральном тоне — так мы сможем быстрее разобраться в ситуации.

⏳ Небольшой совет:
Пара мягких слов часто ускоряет решение вопроса и делает общение комфортнее для всех.

✨ Готовы продолжить?"""


def open_ticket_msg(ticket_id: int, title: str, type_ticket: str, created_date: str,
                    update_date: str, messages_history: list) -> str:
    """Содержимое открытого тикета со стороны пользователя."""
    cnt_photo = 0
    # Эмодзи для типа
    type_emoji = "🔧" if type_ticket == 'tech' else "👨‍⚕️"

    msg = f"""📨 Обращение #{ticket_id} {type_emoji}

{title}
📅 Создано: {created_date}
🔄 Обновлено: {update_date}


📬 История сообщений:
"""
    if messages_history:

        for msg_data in messages_history:
            is_from_user = msg_data['is_from_user']
            text = msg_data['text']
            type_msg = msg_data['type_msg']
            sender = "👤 Вы:" if is_from_user else "🛠️ Админ:"
            if type_msg == 'photo':
                cnt_photo += 1
                msg += f"\n{sender}{'\n' + text if text else ''}\n📷 Фото №{cnt_photo}\n"
            else:
                msg += f"\n{sender}\n{text}\n"
    else:
        msg += "\n💬 Переписка пока пуста..."

    msg += "\n\n\n💡 Для ответа просто напишите сообщение в этот чат."

    return msg


def admin_open_ticket_msg(ticket_id: int, title: str, user_id: int, username: str | None,
                          first_name: str, status: str, type_ticket: str, created_date: str,
                          update_date: str, messages_history: list) -> str:
    """Содержимое открытого тикета со стороны администратора."""
    cnt_photo = 0
    # Эмодзи для типа
    type_emoji = "🔧" if type_ticket == 'tech' else "👨‍⚕️"
    type_text = "Техподдержка" if type_ticket == 'tech' else "Консультация"

    # Статус с эмодзи
    status_emoji = "🆕" if status == 'new' else "✅"
    status_text = "Новые сообщения" if status == 'new' else "Прочитано"

    # Форматируем информацию о пользователе
    user_info = f"{first_name} (ID: {user_id})"
    if username:
        user_info += f" | @{username}"

    # Формируем заголовок
    msg = f"""📨 Обращение #{ticket_id} {type_emoji}

Заголовок: {title}
Тип: {type_text}
Статус: {status_emoji} {status_text}

👤 Пользователь: {user_info}
📅 Создано: {created_date}
🔄 Обновлено: {update_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📬 История переписки:
"""

    # История сообщений
    if messages_history:
        for i, msg_data in enumerate(messages_history, 1):
            is_from_user = msg_data['is_from_user']
            text = msg_data['text']
            type_msg = msg_data['type_msg']
            prefix = "👤 Пользователь:" if is_from_user else "🛠️ Администратор:"
            if type_msg == 'photo':
                cnt_photo += 1
                msg += f"\n{i}. {prefix}{'\n' + text if text else ''}\n📷 Фото №{cnt_photo}\n"
            else:
                msg += f"\n{i}. {prefix}\n{text}\n"
    else:
        msg += "\n💬 Переписка еще не начата."

    # Разделитель и подсказка
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━"
    msg += "\n💡 Для ответа просто напишите сообщение в этот чат."

    if status == 'new':
        msg += "\n\n🆕 Есть непрочитанные сообщения!"

    return msg


def notify_new_message_in_ticket(ticket_id: int) -> str:
    """Уведомление пользователю о новом ответе в его тикете."""
    return f"👤 Поступил ответ в обращении #{ticket_id}."


def admin_notify_new_ticket(ticket_id: int, type_ticket: str) -> str:
    """Уведомление админам о новом тикете."""
    type_text = "Техподдержка" if type_ticket == 'tech' else "Консультация"

    return f"👤 Открыт новый тикет #{ticket_id}. Тип: {type_text}"


def admin_notify_new_message_in_ticket(ticket_id: int, type_ticket: str) -> str:
    """Уведомление админам о новом сообщении в тикете."""
    type_text = "Техподдержка" if type_ticket == 'tech' else "Консультация"

    return f"👤 Новое сообщение в тикете #{ticket_id}. Тип: {type_text}"


def ticket_closed_msg(ticket_id: int | None = None) -> str:
    """Сообщение о закрытии диалога."""
    return f"""📭 Обращение {'#' + ticket_id if ticket_id else ''} закрыто

Диалог завершён. Если потребуется помощь — создайте новое обращение."""


def confirm_delete_ticket_msg(ticket_id: int) -> str:
    """Сообщение подтверждения удаления тикета."""
    return f"""🗑️ Подтверждение удаления

Вы собираетесь удалить обращение #{ticket_id}.

❓ Уверены, что хотите удалить обращение и всю историю переписки?

❗ Действие необратимо — восстановить данные будет невозможно.
"""


def admin_ticket_section_msg(first_name: str) -> str:
    """Общеознакомительное сообщение админа перед выбором типа обращений."""
    return f"""📨 Раздел обращений

{first_name}, здесь собраны все запросы пользователей.

Выберите, с какими обращениями хотите поработать:

🔧 Техподдержка
• Ошибки в работе бота
• Проблемы с настройками
• Технические вопросы

👨‍⚕️ Консультации
• Подбор индивидуальных норм
• Рекомендации по здоровым привычкам
• Персональные запросы пользователей

📋 В каждом разделе вы увидите список активных обращений.
Откройте нужное — и сразу сможете ответить пользователю.

✨ Быстро, удобно и всё под рукой!"""


def admin_tickets_msg(ticket_type: str) -> str:
    """Заголовок списка обращений для админа."""
    return f"""📋 Обращения от пользователей
Тип: {'🔧 Техподдержка' if ticket_type == 'tech' else '👨‍⚕️ Консультации'}

Выберите обращение:"""


def exit_home(menu_type: str = 'Главное') -> str:
    """Сообщение возврата в меню."""
    return f"🔙 Возврат в {menu_type} меню"


def remove_adm_censor_msg(content_type: str) -> str:
    """Сообщение админу об ограничении его прав из-за цензуры."""
    return f"""🚫 Ваши админ-права ограничены

Ваше сообщение содержит запрещённые слова и было отклонено системой.

📋 Дальнейшие действия:
• {'Сообщение не было отправлено' if content_type == 'supp' else 'Рассылка не была отправлена'}
• Ваши права админа временно приостановлены
• Ожидайте проверки владельцем

По всем вопросам обращайтесь к владельцу бота"""


def water_custom_input_limit_msg(amount_ml: int, min_limit: int = 50, max_limit: int = 1500) -> str:
    """Сообщение об ошибке при вводе недопустимого объёма воды."""
    return f"""❌ Некорректное значение

Количество {amount_ml} мл выходит за допустимые пределы.

📏 Допустимый диапазон: {min_limit}-{max_limit} мл

💡 Примеры корректного ввода:
• 250
• 500
• 1000

✨ Пожалуйста, введи значение в указанном диапазоне.

🎯 Каждая разумная порция приближает к цели!"""


def water_custom_input_accept_msg(amount_ml: int) -> str:
    """Сообщение подтверждения пользовательского ввода объёма воды."""
    return f"""💧 Подтверждение

Добавить {amount_ml} мл воды к твоему дневному балансу?

✅ Всё верно — подтверждай
🔄 Нет — введи другое значение

✨ Каждая порция учитывается в прогрессе!"""


def water_add_custom_input_msg(first_name: str) -> str:
    """Приглашение ввести произвольный объём выпитой воды."""
    return f"""💧 Введи своё значение

{first_name}, отправь количество воды в миллилитрах, которое ты выпил:

📏 Примеры формата:
• 250
• 330
• 500

✨ Можно указать любое число от 50 до 1500 мл

💡 Советы:
• Не старайся выпить слишком много за раз
• Равномерное распределение в течение дня эффективнее
• Слушай своё тело и его потребности!

🎯 Каждая порция учитывается и приближает тебя к цели!"""


# Упражнения

def admin_exercise_menu_msg(first_name: str) -> str:
    """Главное сообщение панели управления упражнениями."""
    return f"""🏋️ Управление упражнениями

{first_name}, выберите действие:

📝 Добавить — создать новое упражнение
✏️ Редактировать — изменить существующее
📊 Статистика — просмотр данных по упражнениям

⚡ Все изменения сразу доступны пользователям!"""


def exercise_confirm_msg(name: str, description: str, category: str, difficulty: str, has_video: bool = False) -> str:
    """Сообщение подтверждения добавления нового упражнения."""
    """Сообщение с данными упражнения для подтверждения"""

    # Словарь для отображения категорий
    categories = {
        'strength': '💪 Силовые',
        'cardio': '🏃 Кардио',
        'stretching': '🧘 Растяжка',
        'walking': '🚶 Ходьба',
        'warmup': '🧍 Зарядка'
    }

    # Словарь для отображения сложности
    difficulties = {
        'beginner': '🌱 Новичок',
        'intermediate': '🌿 Средний',
        'advanced': '🌳 Продвинутый'
    }

    cat_display = categories.get(category, category)
    diff_display = difficulties.get(difficulty, difficulty)

    video_line = 'загружено' if has_video else '📹 Видео: не прикреплено'

    return f"""📋 <b>Проверьте данные упражнения</b>

🏋️ <b>Название:</b> {name}

📝 <b>Описание:</b>
{description}

🏷️ <b>Категория:</b> {cat_display}

📊 <b>Сложность:</b> {diff_display}

<b>Видео:</b> {video_line}

✅ Всё верно? Подтвердите сохранение или отмените."""


def aggressive_exercise_info_msg(name: str, description: str) -> str:
    """Предупреждение админу о подозрительном содержании в упражнении."""
    return f"""🏋️ <b>Название:</b> {name}

📝 <b>Описание:</b>
{description}"""


def exercise_saved_msg(name: str) -> str:
    """Упражнение успешно сохранено."""
    return f"""✅ Упражнение успешно добавлено!

🏋️ Название: {name}

Теперь оно доступно пользователям в разделе «💪 Физ-активность»

🔍 Вы можете:
• Добавить ещё одно
• Посмотреть список упражнений
• Вернуться в меню"""


def exercise_full_details_msg(ex_id: int, name: str, description: str, category: str, difficulty: str,
                              created_by: int, created_at: str, is_active: bool,
                              has_video: bool = False) -> str:
    """Подробное описание упражнения для панели администратора."""

    # Словари для отображения
    categories = {
        'strength': '💪 Силовые',
        'cardio': '🏃 Кардио',
        'stretching': '🧘 Растяжка',
        'walking': '🚶 Ходьба',
        'warmup': '🧍 Зарядка',
        'balance': '⚖️ Баланс'
    }

    difficulties = {
        'beginner': '🌱 Новичок',
        'intermediate': '🌿 Средний',
        'advanced': '🌳 Продвинутый'
    }

    # Форматируем значения
    category_display = categories.get(category)
    difficulty_display = difficulties.get(difficulty)
    status = "✅ Активно" if is_active else "❌ Неактивно"

    video_line = 'прикреплено отдельно' if has_video else 'не прикреплено'

    return f"""🏋️ <b>Упражнение #{ex_id}</b>

📝 <b>Название:</b> {name}

📋 <b>Описание:</b>
{description}

🏷️ <b>Категория:</b> {category_display}
📊 <b>Сложность:</b> {difficulty_display}

👤 <b>Автор:</b> <code>{created_by}</code>
📅 <b>Создано:</b> {created_at}
📌 <b>Статус:</b> {status}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📹 <b>Видео:</b> {video_line}

Выберите, что хотите изменить:"""


def confirm_delete_exercise_msg(ex_id: int) -> str:
    """Сообщение подтверждения удаления упражнения."""
    return f"""🗑️ <b>Подтверждение удаления</b>

Вы уверены, что хотите удалить упражнение №{ex_id}?

⚠️ <b>Это действие:</b>
• Удалит упражнение из списка
• Очистит статистику по нему
• Удалит привязанное видео

❌ Восстановить будет невозможно!

Выберите действие:"""


def exercise_stats_msg(stats: dict) -> str:
    """Сводная статистика всех упражнений для администратора."""
    text = f"""📊 <b>Статистика упражнений</b>

📌 <b>Всего упражнений:</b> {stats['total']}
👥 <b>Всего выполнений:</b> {stats['total_completions']}

🔥 <b>Топ-5 популярных:</b>\n"""

    # Добавляем популярные упражнения
    for name, count in stats['popular']:
        text += f"• {name}: <b>{count}</b> раз\n"

    text += f"\n📅 <b>За неделю:</b> {stats['weekly']} выполнений"
    return text


def sports_activity_progress_bar(goal: int, today_count: int) -> str:
    """Генерирует текстовый прогресс-бар активности."""
    pct = min(100, round(today_count / goal * 100)) if goal else 0
    filled = int(pct / 10)
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    return f"📊 <b>Прогресс:</b> {today_count}/{goal} {bar} {pct}%\n\n"


def sports_main_menu_msg(first_name: str, goal: int | None = None, today_count: int = 0) -> str:
    """Главное сообщение раздела Физ-активность."""
    progress = ""
    if goal is not None and goal > 0:
        progress = sports_activity_progress_bar(goal, today_count)
    return f"""💪 <b>Физ-активность</b>

{progress}{first_name}, здесь ты можешь:

🏋️ <b>Все упражнения</b> — посмотреть список всех доступных упражнений
❤️ <b>Избранное</b> — твои любимые упражнения
📊 <b>Мой прогресс</b> — статистика выполнения

Выбери раздел:"""


def sports_exercise_details_msg(name: str, description: str, category: str, difficulty: str,
                                is_favorite: bool = False, has_video: bool = False) -> str:
    """Карточка упражнения для пользователя с деталями и доступными действиями."""

    categories = {
        'strength': '💪 Силовые',
        'cardio': '🏃 Кардио',
        'stretching': '🧘 Растяжка',
        'walking': '🚶 Ходьба',
        'warmup': '🧍 Зарядка',
        'balance': '⚖️ Баланс'
    }

    difficulties = {
        'beginner': '🌱 Новичок',
        'intermediate': '🌿 Средний',
        'advanced': '🌳 Продвинутый'
    }

    fav_emoji = "❤️" if is_favorite else "🤍"

    video_line = "📹 <b>Видео:</b> прикреплено" if has_video else "📹 <b>Видео:</b> не прикреплено"

    return f"""🏋️ <b>{name}</b>

📋 <b>Описание:</b>
{description}

🏷️ <b>Категория:</b> {categories.get(category)}
📊 <b>Сложность:</b> {difficulties.get(difficulty)}

{fav_emoji} <b>В избранном:</b> {'да' if is_favorite else 'нет'}

{video_line}

<b>Доступные действия:</b>

✅ <b>Выполнил</b> — отметить выполнение упражнения
{('📹 <b>Видео</b> — посмотреть демонстрацию' if has_video else '')}
{fav_emoji} <b>В избранное/убрать</b> — добавить или удалить из избранного
📊 <b>Статистика</b> — твоя статистика по этому упражнению
🔙 <b>К списку</b> — вернуться к списку упражнений
"""


def sports_my_stats_msg(total: int, weekly: int, top_list: list) -> str:
    """Сообщение с личной статистикой выполнения упражнений."""
    return f"""📊 <b>Мой прогресс</b>

<b>Всего выполнений:</b> {total}
<b>За неделю:</b> {weekly}

<b>Топ-5 упражнений:</b>
{top_list}"""


sports_my_stats_empty_msg = """📊 <b>Мой прогресс</b>

У вас пока нет выполненных упражнений.

Отмечайте выполнение кнопкой ✅ Выполнил в карточке упражнения!"""

sports_exercise_done_msg = "✅ Отлично! Выполнение засчитано."


def sports_stats_top_item_msg(name: str, cnt: int) -> str:
    """Строка списка популярных упражнений."""
    return f"• {name}: <b>{cnt}</b> раз"


sports_confirm_done_msg = """✅ <b>Подтверждение</b>

Вы уверены, что выполнили это упражнение?

Нажмите <b>Подтвердить</b>, чтобы засчитать выполнение."""


def sports_done_too_soon_same_msg(mins: int) -> str:
    """Предупреждение: это же упражнение выполнено слишком недавно."""
    return f"⏱ Одно и то же упражнение можно отмечать не чаще раза в 15 минут. Подождите ещё {mins} мин."


def sports_done_too_soon_other_msg(mins: int) -> str:
    """Предупреждение: любое упражнение выполнено слишком недавно."""
    return f"⏱ Лимит между разными упражнениями — не менее 5 минут. Подождите ещё {mins} мин."


def sports_ex_stats_msg(total: int, weekly: int) -> str:
    """Короткая статистика выполнения конкретного упражнения."""
    return f"""📊 <b>Статистика по упражнению</b>

<b>Всего раз:</b> {total}
<b>За неделю:</b> {weekly}"""


# Физическая активность

def activity_tracker_setup_msg(first_name: str) -> str:
    """Сообщение настройки трекера активности."""
    return f"""💪 <b>Настройка трекера активности</b>

{first_name}, давай настроим твои цели по упражнениям!

🎯 <b>Ежедневная цель:</b>
• Сколько упражнений хочешь выполнять в день?
• Рекомендуется 3–5 для поддержания формы

⏰ <b>Напоминания:</b>
• Когда напоминать о разминке?
• Умный режим или по интервалу

✨ Выбери, что настроить:"""


def activity_goal_selection_msg(first_name: str) -> str:
    """Сообщение выбора дневной цели по упражнениям."""
    return f"""🎯 <b>Выбор ежедневной цели</b>

{first_name}, сколько упражнений планируешь выполнять в день?

Рекомендуемые варианты:
• 1 — минимум для тонуса
• 3 — поддержание формы
• 5 — активный день
• 10 — интенсивные тренировки

✨ Выбери или укажи своё число:"""


activity_setup_required_msg = """💪 <b>Настройка обязательна</b>

Перед использованием раздела «Физ-активность» нужно задать ежедневную цель и (по желанию) напоминания.

Нажми <b>Настроить</b>, чтобы перейти к настройкам."""


def activity_goal_success_msg(goal: int) -> str:
    """Уведомление об успешном установлении цели по активности."""
    return f"✅ Ежедневная цель: {goal} упражнений установлена!"


def activity_reminder_type_selection_msg(first_name: str) -> str:
    """Сообщение выбора типа напоминаний об активности."""
    return f"""⏰ <b>Напоминания о разминке</b>

{first_name}, как хочешь получать напоминания?

⏰ <b>По интервалу:</b>
• Напоминает через заданные часы
• Подходит для регулярных перерывов

🤖 <b>Умный режим:</b>
• Отслеживает последнее выполнение
• Напоминает, если давно не занимался (например, 3+ часов)

✨ Выбери вариант:"""


def activity_interval_setup_msg(first_name: str) -> str:
    """Сообщение настройки интервала напоминаний об активности."""
    return f"""⏰ <b>Интервал напоминаний</b>

{first_name}, как часто напоминать о разминке?

Выбери интервал в часах:"""


activity_reminder_type_smart_msg = "✅ Умный режим напоминаний включён!"

activity_goal_custom_msg = """✏️ <b>Своя цель</b>

Введите число упражнений от 1 до 30:"""

activity_goal_limit_msg = "❌ Укажите число от 1 до 30!"

activity_goal_incorrect_format_msg = "❌ Введите целое число от 1 до 30."


def activity_interval_selected_msg(hours: int) -> str:
    """Короткое подтверждение выбранного интервала напоминаний об активности."""
    return f"✅ Интервал: каждые {hours} ч."


def activity_quick_reminder_msg(today_count: int, goal: int) -> str:
    """Короткое напоминание от планировщика сделать упражнение."""
    return f"""💪 <b>Время размяться!</b>

Сегодня выполнено: <b>{today_count}/{goal}</b> упражнений.

Напоминаю выполнить ещё одно — это займёт пару минут!"""


# Трекер сна

def sleep_tracker_setup_msg(first_name: str, sleep_time: str | None = None,
                            wake_time: str | None = None, reminders_enabled: bool = True) -> str:
    """Сообщение настройки трекера сна."""
    current = ""
    if sleep_time and wake_time:
        current = f"\n\n✅ <b>Текущие настройки:</b>\n🌙 Отбой: {sleep_time} | ☀️ Подъём: {wake_time}"
    return f"""😴 <b>Настройка трекера сна</b>

{first_name}, давай настроим твой режим сна!{current}

🌙 <b>Время отбоя:</b>
• За 30 минут придёт мягкое напоминание

☀️ <b>Время подъёма:</b>
• Утреннее приветствие в твоё время

🔕 <b>Тихие часы:</b>
• В окне сна никакие уведомления не приходят

🔔 <b>Напоминания:</b> {'вкл ✅' if reminders_enabled else 'выкл ❌'}

✨ Выбери, что настроить:"""


sleep_not_set_msg = """😴 <b>Трекер сна не настроен</b>

Укажи время отбоя и подъёма, чтобы начать отслеживать сон и включить тихие часы.

Нажми <b>Настроить</b>, чтобы перейти к настройкам."""


def sleep_dashboard_msg(first_name: str, sleep_time: str, wake_time: str, last_sleep: tuple | None,
                         avg_duration: float | None, is_sleeping: bool, sleep_start: str | None = None) -> str:
    """Сообщение дашборда трекера сна с текущим состоянием и последней сессией."""
    schedule = f"🌙 Отбой: <b>{sleep_time}</b> | ☀️ Подъём: <b>{wake_time}</b>"

    if is_sleeping and sleep_start:
        state_section = f"😴 <b>Ты сейчас спишь</b>\n⏱ Начало: {sleep_start}"
    elif last_sleep:
        _, _, _, duration = last_sleep
        if duration:
            h, m = divmod(duration, 60)
            dur_str = f"{h}ч {m}мин" if h else f"{m}мин"
        else:
            dur_str = "—"
        state_section = f"💤 Последний сон: <b>{dur_str}</b>"
    else:
        state_section = "💤 Сон пока не отмечен"

    avg_str = ""
    if avg_duration:
        h, m = divmod(int(avg_duration), 60)
        avg_str = f"\n📈 Среднее за 7 дней: <b>{h}ч {m}мин</b>"

    action_hint = ("☀️ Нажми <b>«Проснулся!»</b> когда проснёшься"
                   if is_sleeping else
                   "😴 Нажми <b>«Ложусь спать»</b> перед сном")

    return f"""😴 <b>Трекер сна</b>

{first_name}, твой режим:
{schedule}

{state_section}{avg_str}

{action_hint}"""


def sleep_time_selection_msg(first_name: str) -> str:
    """Сообщение выбора времени отбоя."""
    return f"""🌙 <b>Время отбоя</b>

{first_name}, во сколько ты обычно ложишься спать?

За 30 минут до этого времени придёт напоминание."""


def wake_time_selection_msg(first_name: str) -> str:
    """Сообщение выбора времени подъёма."""
    return f"""☀️ <b>Время подъёма</b>

{first_name}, во сколько обычно просыпаешься?

В это время придёт доброе утро ☀️"""


def sleep_time_set_msg(time_str: str) -> str:
    """Уведомление об установке времени отбоя."""
    return f"🌙 Время отбоя установлено: <b>{time_str}</b>"


def wake_time_set_msg(time_str: str) -> str:
    """Уведомление об установке времени подъёма."""
    return f"☀️ Время подъёма установлено: <b>{time_str}</b>"


def sleep_log_start_msg(time_str: str) -> str:
    """Сообщение о начале отслеживания сна."""
    return f"😴 Сон начат в <b>{time_str}</b>.\n\nСпокойной ночи! 🌙"


def sleep_log_end_msg(duration_min: int) -> str:
    """Сообщение о завершении сессии сна с оценкой продолжительности."""
    h, m = divmod(duration_min, 60)
    dur = f"{h}ч {m}мин" if h else f"{m}мин"
    if duration_min >= 420:
        status = "🌟 Отличный сон! Так держать!"
    elif duration_min >= 360:
        status = "😊 Неплохо! Стремись к 7–9 часам."
    elif duration_min >= 120:
        status = "😐 Маловато. Постарайся ложиться раньше!"
    else:
        status = "😔 Совсем мало поспал. Береги себя!"
    return f"""☀️ <b>Доброе утро!</b>

Продолжительность сна: <b>{dur}</b>

{status}"""


def sleep_history_msg(records: list) -> str:
    """История сна за последние записи."""
    if not records:
        return "📋 <b>История сна</b>\n\nЗаписей пока нет. Начни отслеживание прямо сейчас!"
    lines = ["📋 <b>История сна (последние 7 сессий)</b>\n"]
    for sleep_start, wake_up, duration in records:
        try:
            from datetime import datetime
            ss = datetime.strptime(sleep_start[:16], '%Y-%m-%d %H:%M').strftime('%d.%m %H:%M')
            wu = datetime.strptime(wake_up[:16], '%Y-%m-%d %H:%M').strftime('%H:%M')
        except Exception:
            ss, wu = sleep_start[:16], wake_up[:16]
        if duration:
            h, m = divmod(duration, 60)
            dur = f"{h}ч {m}мин" if h else f"{m}мин"
        else:
            dur = "—"
        lines.append(f"• {ss} → {wu} | <b>{dur}</b>")
    return "\n".join(lines)


sleep_custom_time_input_msg = """✏️ <b>Введи время в формате ЧЧ:ММ</b>

Примеры: <code>23:00</code>, <code>07:30</code>, <code>00:15</code>"""

sleep_time_format_error_msg = "❌ Неверный формат. Введи время в формате ЧЧ:ММ (например, 23:00)"


def sleep_reminder_before_msg(sleep_time: str) -> str:
    """Напоминание о приближающемся времени отбоя."""
    return f"""🌙 <b>Скоро идти спать!</b>

Через 30 минут — запланированный отбой ({sleep_time}).

Заверши дела, подготовься ко сну и хорошо отдохни 🛏️"""


def sleep_reminder_wakeup_msg(wake_time: str) -> str:
    """Напоминание о приближающемся времени подъёма."""
    return f"""☀️ <b>Доброе утро!</b>

Настало время подъёма ({wake_time}).

Нажми кнопку ниже, чтобы отметить пробуждение! 😊"""


def sleep_capped_msg() -> str:
    """Уведомление о том, что было засчитано только 18 часов сна."""
    return """⚠️ <b>Длительный сон</b>

Твой сон длился более 18 часов — в трекере засчитано <b>18 часов</b> (максимум).

Если данные некорректны, проверь, не забыл ли ты отметить пробуждение раньше 🙂"""


def sleep_reminder_toggle_msg(enabled: bool) -> str:
    """Сообщение об изменении состояния напоминаний сна."""
    return "🔔 Напоминания о сне включены!" if enabled else "🔕 Напоминания о сне отключены"


sleep_no_open_session_msg = "😴 Нет активной сессии сна. Нажми «Ложусь спать»чтобы начать!"


def user_stats_msg(stats: dict) -> str:
    """Форматирует подробную статистику пользователя для отображения."""
    # Парсим дату регистрации
    from datetime import datetime
    try:
        created_dt = datetime.strptime(stats['created_date'], '%Y-%m-%d %H:%M:%S')
        created_formatted = created_dt.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        created_formatted = "N/A"

    # Количество дней на платформе
    try:
        reg_date = datetime.strptime(stats['created_date'], '%Y-%m-%d %H:%M:%S')
        days_on_platform = (datetime.now() - reg_date).days
    except (ValueError, TypeError):
        days_on_platform = 0

    # Вода
    water_stats = stats.get('water', {})
    water_goal = water_stats.get('goal')
    water_today = water_stats.get('today', 0)
    water_total = water_stats.get('total', 0)

    if water_goal:
        water_percent = round((water_today / water_goal * 100) if water_goal else 0)
        water_bar = "█" * (water_percent // 10) + "░" * (10 - water_percent // 10)
        water_section = f"""

💧 <b>Водный баланс</b>
• Цель: {water_goal} мл
• Сегодня: {water_today} мл ({water_percent}%)
• {water_bar}
• Всего этой неделей: {water_total} мл"""
    else:
        water_section = """

💧 <b>Водный баланс</b>
• Не настроен (в настройках)"""

    # Активность
    activity_stats = stats.get('activity', {})
    activity_goal = activity_stats.get('goal')
    activity_today = activity_stats.get('today', 0)
    activity_weekly = activity_stats.get('weekly', 0)
    if activity_goal:
        activity_percent = round(activity_today / activity_goal * 100) if activity_goal else 0
        activity_bar = "█" * (activity_percent // 10) + "░" * (10 - activity_percent // 10)
        activity_section = f"""

💪 <b>Физическая активность</b>
• Цель: {activity_goal} упражнений
• сегодня: {activity_today} упражнения ({activity_percent}%)
• {activity_bar}
• На этой неделе: {activity_weekly} упражнений"""
    else:
        activity_section = """

💪 <b>Физическая активность</b>
• Не настроена (в настройках)"""

    # Сон
    sleep_stats = stats.get('sleep', {})
    sleep_time_val = sleep_stats.get('sleep_time')
    wake_time_val = sleep_stats.get('wake_time')
    sleep_avg = sleep_stats.get('avg_duration')
    sleep_week_count = sleep_stats.get('week_count', 0)
    if sleep_time_val and wake_time_val:
        if sleep_avg:
            sh, sm = divmod(int(sleep_avg), 60)
            avg_str = f"{sh}ч {sm}мин"
        else:
            avg_str = "нет данных"
        sleep_section = f"""

😴 <b>Сон</b>
• Отбой: {sleep_time_val} | Подъём: {wake_time_val}
• Сессий за неделю: {sleep_week_count}
• Среднее время сна: {avg_str}"""
    else:
        sleep_section = """

😴 <b>Сон</b>
• Не настроен (в настройках)"""

    return f"""📊 <b>Статистика профиля</b>

👤 <b>Ник: @{stats['username'] or 'Не установлен'}</b>

📅 <b>На платформе: {plural_days(days_on_platform)}</b>

⏰ <b>Дата регистрации:</b> {created_formatted}{water_section}{activity_section}{sleep_section}

✨ Продолжай в том же духе!"""



exercise_cancel_msg = """❌ Добавление упражнения отменено.

Все введённые данные удалены.

Выберите действие в меню."""
exercise_add_error = """❌ Произошла ошибка при добавлении упражнения.

Возможно, бот был перезапущен. Попробуйте начать заново."""
exercise_edit_error_msg = """❌ Произошла ошибка при изменении упражнения.

Возможно, бот был перезапущен. Попробуйте начать заново."""
water_custom_input_format_error_msg = """❌ Неверный формат

Пожалуйста, введи только число — количество миллилитров.

📏 Примеры правильного ввода:
• 250 — Стакан воды
• 500 — Большая кружка
• 1000 — Литр воды
• 1500 — Полтора литра

🚫 Что не принимается:
• Буквы или текст («стакан», «мл»)
• Символы (+, -, =, мл, л)
• Десятичные дроби (0.5, 1.5)
• Несколько чисел через пробел

💡 Просто отправь одно целое число от 50 до 1500.

✨ Например: 250 или 500 или 1000

🎯 Мы добавим эту порцию к твоему прогрессу!"""
timezone_suc_msg = '✅ Часовой пояс установлен!'
example_broadcast = "📝 Введите текст рассылки:\n\n💡 Например: 'Привет! Напоминаю выпить воды 💧'"
cancellation = "✅ Действие отменено!"
nf_cmd = ("💫 Не распознал команду. Давайте сосредоточимся на здоровых "
          "привычках — выберите действие из меню ниже 👇")
incorrect_format = "❌ Не верный формат ввода."
incorrect_format_adm_msg = "❌ Не верный формат ввода.\n\n📝 Введите ID или Username, либо отмените действие"
add_new_adm_msg = "📝 Введите ID или Username пользователя"
remove_adm_msg = "📝 Введите ID или Username администратора"
user_nf = "⚠️ Пользователь не найден!\n\n📝 Введите ID или Username, либо отмените действие"
user_already_admin = "⚠️ Пользователь и так администратор!\n\n📝 Введите ID или Username, либо отмените действие"
owner_demotion_error = "❌ Нельзя снять владельца!\n\n📝 Введите ID или Username, либо отмените действие"
user_not_admin = "⚠️ Пользователь не является администратором!\n\n📝 Введите ID или Username, либо отмените действие"
user_now_admin = "🎉 Поздравляем! Вы были назначены администратором бота!"
user_removed_admin = "ℹ️ Ваши права администратора были сняты"
succ_return_adm = '✅ Права восстановлены!'
media_is_closed_msg = "✅ Медиа-файл закрыт!"
owner_unban = "🔒 Права владельца можно восстановить только через Config file"
user_return_admin_msg = "ℹ️ Ваши права Администратора восстановлены"
already_return_adm_msg = "🔄 Права уже были восстановлены"
error_msg = '❌ Произошла Ошибка!'
send_media_group_error_msg = "❌ Пожалуйста, отправляйте фото по одному, а не группой"
water_goal_custom_msg = """✏️ Установка индивидуальной цели

🎯 Отправьте желаемое количество воды в миллилитрах.

💡 Примеры ввода:
• 1500 - (1.5 литра)
• 2000 - (2.0 литра)
• 2500 - (2.5 литра)

📏 Можно указать любое значение от 500 до 8000 мл.

💫 Персонализация — ключ к эффективности!"""
water_goal_limit_msg = """❌ Можно указать любое значение от 500 до 8000 мл!

🎯 Отправьте желаемое количество воды в миллилитрах.

💡 Примеры ввода:
• 1500 - (1.5 литра)
• 2000 - (2.0 литра)
• 2500 - (2.5 литра)

📏 Можно указать любое значение от 500 до 8000 мл."""
water_goal_incorrect_format_msg = """❌ Не верный формат ввода.

🎯 Отправьте желаемое количество воды в миллилитрах.

💡 Примеры ввода:
• 1500 - (1.5 литра)
• 2000 - (2.0 литра)
• 2500 - (2.5 литра)

📏 Можно указать любое значение от 500 до 8000 мл.
"""
water_reminder_type_smart_msg = "✅ Установлен умный режим!"
water_setup_required_msg = """❌ Сначала установите дневную цель по воде!

🎯 Рекомендуемые варианты:
• 1.5 л — Минимальная норма
• 2.0 л — Стандартная норма
• 2.5 л — Активный образ жизни
• 3.0 л — Интенсивные тренировки

✨ Или можешь установить свою цель!

💡 Совет: Начни с 2 литров и корректируй по ощущениям!"""
water_goal_not_set_msg = """🎯 Цель по воде не установлена

Для использования водного трекера необходимо сначала установить дневную цель по воде.

✨ Как это сделать:
1. Нажмите кнопку «Настройки»
2. Выберите раздел «🚰 Вода»
3. Установите комфортную для вас цель

🎯 Цель — это не ограничение, а ваш ориентир на пути к здоровым привычкам!

🔧 Перейдите в настройки и установите цель прямо сейчас!"""
add_water_msg = "💧 Данные обновлены!"
support_tech_msg = """🔧 Техническая поддержка

Отлично! Сейчас подключим нашего техспециалиста.

✨ Чтобы помочь вам быстрее, подготовьте:
• Подробное описание проблемы/вопроса
• Скриншоты (если есть)
• Шаги, которые привели к ошибке

🕐 Время ответа:
Обычно отвечаем в течение часа в рабочее время.

⬇️ Готовы? Нажмите кнопку ниже, чтобы открыть обращение!

💡 Не забудьте: чем подробнее опишете проблему — тем быстрее получите решение!"""
support_consult_msg = """👨‍⚕️ Персональная консультация

Прекрасный выбор! Сейчас соединим вас с нашим специалистом по здоровым привычкам.

✨ Что поможет консультанту:
• Ваш текущий режим дня
• Цели по здоровью (что хотите улучшить)
• Особенности образа жизни/работы

🕐 Время ответа:
Мы свяжемся с вами в течении часа для глубокой проработки вашего запроса.

⬇️ Готовы начать? Нажмите кнопку ниже, чтобы открыть обращение!

💫 Каждая консультация — это шаг к более осознанному и здоровому образу жизни!"""
send_msg_to_ticket_msg = """📝 Подробное описание

💬 Опишите ваш запрос максимально подробно:

🚫 Передумали? Нажмите «Отмена» внизу."""
no_active_tickets_msg = "📭 Нет активных обращений"
succ_ticket_title_msg = """✅ Заголовок сохранён!

🔄 Обращение ожидает описания.

Вы можете:
• Перейти к диалогу со специалистом
• Удалить черновик и начать заново"""
opening_ticket_msg = "✅ Открываем диалог"
my_tickets_msg = """📋 Мои обращения

Выберите обращение:"""
succ_send_msg = "✅ Сообщение отправлено!"
error_ticket_opening_msg = "❌ Произошла ошибка. Видимо Обращение закрыто."
ticket_locked_by_other_admin_msg = "Ошибка: обращение уже открыто другим администратором."

# Шаг 1 - запрос названия
exercise_request_name_msg = """📝 Добавление упражнения - шаг 1/5

Отправьте название упражнения.

💡 Примеры:
• Отжимания
• Приседания
• Планка
• Бег

📏 Максимум: 50 символов
❌ Для отмены нажмите кнопку ниже"""

# Шаг 2 - запрос описания
exercise_request_description_msg = """📋 Добавление упражнения - шаг 2/5

Отправьте описание упражнения.

💡 Что указать:
• Техника выполнения
• Количество подходов и повторений
• Особенности и нюансы
• Противопоказания

📏 Минимум: 20 символов
📏 Максимум: 500 символов
❌ Для отмены нажмите кнопку ниже"""

# Шаг 3 - выбор категории
exercise_request_category_msg = """🏷️ Добавление упражнения - шаг 3/5

Выберите категорию упражнения:

💪 <b>Силовые</b> - упражнения с весом или сопротивлением
🏃 <b>Кардио</b> - бег, прыжки, активные движения
🧘 <b>Растяжка</b> - упражнения на гибкость
🚶 <b>Ходьба</b> - обычные прогулки, шаги
🧍 <b>Зарядка</b> - утренняя разминка, легкие упражнения
⚖️ <b>Баланс</b> - равновесие, координация

❌ Для отмены нажмите кнопку ниже"""

# Шаг 4 - выбор сложности
exercise_request_difficulty_msg = """📊 Добавление упражнения - шаг 4/5

Выберите уровень сложности:

🌱 Новичок - просто, доступно всем
🌿 Средний - требуется подготовка
🌳 Продвинутый - для опытных

❌ Для отмены нажмите кнопку ниже"""

# Шаг 5 - запрос видео
exercise_request_video_msg = """📹 Добавление упражнения - шаг 5/5

Загрузите видео или GIF с демонстрацией упражнения.

💡 Требования:
• Формат MP4 или GIF
• Размер до 20 МБ
• Чёткая демонстрация техники
• Можно отправить как видео или анимацию

❌ Для отмены нажмите кнопку ниже"""

exercise_name_exists = """⚠️ Упражнение с таким названием уже существует.

Придумайте другое название или отредактируйте существующее.

❌ Для отмены нажмите кнопку ниже"""
# Ошибки валидации
exercise_name_too_long_msg = """⚠️ Название слишком длинное

Максимум 50 символов. Отправьте более короткое название.

❌ Для отмены нажмите кнопку ниже"""

exercise_description_too_short_msg = """⚠️ Описание слишком короткое

Минимум 20 символов. Добавьте больше деталей.

❌ Для отмены нажмите кнопку ниже"""

exercise_description_too_long_msg = """⚠️ Описание слишком длинное

Максимум 500 символов. Сократите описание.

❌ Для отмены нажмите кнопку ниже"""

exercise_invalid_video_msg = """⚠️ Неверный формат

Отправьте видео (MP4) или GIF анимацию.

💡 Как отправить:
• Выберите файл в Telegram
• Нажмите "Отправить как видео"
• Дождитесь загрузки

❌ Для отмены нажмите кнопку ниже"""
step_back_msg = "⬅️ Шаг назад"
edit_exercise_category_msg = """🔍 <b>Редактирование упражнений - шаг 1/2</b>

Выберите категорию упражнений для редактирования:

💪 <b>Силовые</b> - упражнения с весом или сопротивлением
🏃 <b>Кардио</b> - бег, прыжки, активные движения
🧘 <b>Растяжка</b> - упражнения на гибкость
🚶 <b>Ходьба</b> - обычные прогулки, шаги
🧍 <b>Зарядка</b> - утренняя разминка, легкие упражнения
⚖️ <b>Баланс</b> - равновесие, координация

После выбора категории нужно будет указать уровень сложности.

❌ Для отмены нажмите кнопку ниже"""

edit_exercise_difficulty_msg = """📊 <b>Редактирование упражнений - шаг 2/2</b>

Выберите уровень сложности:

🌱 <b>Новичок</b> - простые упражнения, доступные всем
🌿 <b>Средний</b> - требуют определенной подготовки
🌳 <b>Продвинутый</b> - для опытных пользователей

После выбора будет показан список упражнений для редактирования.

❌ Для отмены нажмите кнопку ниже"""
exercises_list_header_msg = """📋 <b>Список упражнений</b>

Выберите упражнение для редактирования:"""
no_exercises_found_msg = """❌ <b>Упражнения не найдены</b>

По выбранным фильтрам ничего не найдено."""

# Запрос нового названия
edit_exercise_field_name_msg = """✏️ <b>Редактирование названия</b>


Введите новое название для упражнения.

📏 Максимум: 50 символов
❌ Для отмены нажмите кнопку ниже"""

# Запрос нового описания
edit_exercise_field_description_msg = """✏️ <b>Редактирование описания</b>

Введите новое описание для упражнения.

📏 Минимум: 20 символов
📏 Максимум: 500 символов
❌ Для отмены нажмите кнопку ниже"""

# Запрос новой категории
edit_exercise_field_category_msg = """✏️ <b>Редактирование категории</b>

Выберите новую категорию из списка ниже:

💪 <b>Силовые</b> - упражнения с весом или сопротивлением
🏃 <b>Кардио</b> - бег, прыжки, активные движения
🧘 <b>Растяжка</b> - упражнения на гибкость
🚶 <b>Ходьба</b> - обычные прогулки, шаги
🧍 <b>Зарядка</b> - утренняя разминка, легкие упражнения
⚖️ <b>Баланс</b> - равновесие, координация

❌ Для отмены нажмите кнопку ниже"""

# Запрос новой сложности
edit_exercise_field_difficulty_msg = """✏️ <b>Редактирование уровня сложности</b>

Выберите новый уровень сложности:

🌱 <b>Новичок</b> - просто, доступно всем
🌿 <b>Средний</b> - требуется подготовка
🌳 <b>Продвинутый</b> - для опытных

❌ Для отмены нажмите кнопку ниже"""

# Запрос нового видео
edit_exercise_field_video_msg = """✏️ <b>Замена видео</b>

Отправьте новое видео или GIF для замены.

💡 <b>Требования:</b>
• Формат MP4 или GIF
• Размер до 20 МБ
• Чёткая демонстрация техники

❌ Для отмены нажмите кнопку ниже"""
exercise_deleted_msg = "✅ Упражнение удалено"

activity_inactive_reminder_msg = """👋 <b>Мы скучаем!</b>

Ты давно не заходил в бота.

Напоминаем: здесь есть упражнения для разминки, трекер воды и многое другое. Загляни, когда будет минутка! 💪"""

sports_category_msg = """🏋️ <b>Выбор категории</b>

Выберите категорию упражнений:

💪 <b>Силовые</b> — упражнения с весом или сопротивлением
🏃 <b>Кардио</b> — бег, прыжки, активные движения
🧘 <b>Растяжка</b> — упражнения на гибкость
🚶 <b>Ходьба</b> — обычные прогулки, шаги
🧍 <b>Зарядка</b> — утренняя разминка, легкие упражнения
⚖️ <b>Баланс</b> — упражнения на равновесие и координацию

⬇️ Выберите категорию ниже:"""

sports_difficulty_msg = """📊 <b>Выбор уровня сложности</b>

Выберите подходящий уровень:

🌱 <b>Новичок</b> — простые упражнения, доступные всем
🌿 <b>Средний</b> — требуют определенной подготовки
🌳 <b>Продвинутый</b> — для опытных пользователей

⬇️ Выберите уровень ниже:"""
sports_ex_list_msg = """📋 <b>Список упражнений</b>

Выберите упражнение:"""
sports_not_found_ex_msg = "❌ Упражнение не найдено"

sports_favorites_empty_msg = """❤️ <b>Избранное</b>

У вас пока нет избранных упражнений.

Добавляйте упражнения в избранное, нажимая 🤍 В избранное в карточке упражнения."""

sports_favorites_header_msg = """❤️ <b>Избранное</b>

Ваши любимые упражнения:"""


# XP и уровни

def sleep_too_soon_msg(wait_mins: int) -> str:
    """Сообщение о слишком раннем завершении сессии сна."""
    return f"⏳ Рано просыпаться! Подождите ещё {wait_mins} мин. (минимум 30 минут сна)"

LEVEL_TITLES = {
    1: "🌱 Новичок",
    5: "💧 Гидратированный",
    10: "🏃 Активный",
    15: "💪 Спортсмен",
    20: "🌙 Соня",
    30: "⭐ Про",
    50: "🏆 Чемпион",
    75: "👑 Легенда",
    100: "🌟 Мастер",
}


def get_level_title(level: int) -> str:
    """Возвращает текстовый титул для заданного уровня пользователя."""
    title = "🌱 Новичок"
    for lvl, t in sorted(LEVEL_TITLES.items()):
        if level >= lvl:
            title = t
    return title


def xp_gained_msg(action_name: str, xp: int, total_xp: int, level: int) -> str:
    """Короткое уведомление о полученных XP за действие."""
    return f"✨ +{xp} XP за {action_name}! Уровень {level} · {total_xp} XP"


def level_up_msg(new_level: int, total_xp: int) -> str:
    """Поздравление с повышением уровня."""
    title = get_level_title(new_level)
    return f"""🎉 <b>ПОВЫШЕНИЕ УРОВНЯ!</b>

Ты достиг <b>{new_level} уровня</b>!
Новый титул: <b>{title}</b>

Всего XP: <b>{total_xp}</b>

Продолжай в том же духе! 💪"""


def profile_xp_msg(first_name: str, xp: int, level: int, rank: int | None) -> str:
    """Страница XP-профиля пользователя с прогресс-баром до следующего уровня."""
    from database import XP_PER_LEVEL, xp_for_next_level
    title = get_level_title(level)
    to_next = xp_for_next_level(xp)
    progress_pct = round((xp % XP_PER_LEVEL) / XP_PER_LEVEL * 100)
    filled = progress_pct // 10
    bar = "█" * filled + "░" * (10 - filled)
    rank_str = f"🏅 Место в топе: #{rank}" if rank else "🏅 Место в топе: не в рейтинге"
    return f"""🎮 <b>Мой профиль</b>

👤 {first_name}
🏷 Титул: <b>{title}</b>
⚡ Уровень: <b>{level}</b>
✨ Всего XP: <b>{xp}</b>

📊 До следующего уровня: <b>{to_next} XP</b>
{bar} {progress_pct}%

{rank_str}"""


banned_msg = "🚫 <b>Ваш аккаунт заблокирован.</b>\n\nВы не можете пользоваться этим ботом."


def user_profile_admin_msg(user_id: int, username: str | None, status: str, created_date: str,
                            last_activity: str, timezone: int | None,
                            xp: int, level: int, rank: int | None) -> str:
    """Сообщение с полным профилем пользователя для администратора."""
    from datetime import datetime
    try:
        reg_fmt = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        reg_fmt = str(created_date)
    try:
        act_fmt = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
    except (ValueError, TypeError):
        act_fmt = str(last_activity)
    uname_str = f"@{username}" if username else "не указан"
    tz_str = f"МСК+{timezone or 0}" if timezone else "МСК"
    status_emoji = {'User': '👤', 'Admin': '⚡', 'Owner': '👑', 'BANNED': '🚫'}.get(status, '👤')
    rank_str = f"#{rank}" if rank else "не в топе"
    return f"""👤 <b>Профиль пользователя</b>

🆔 ID: <code>{user_id}</code>
👤 Username: {uname_str}
{status_emoji} Статус: <b>{status}</b>
🌍 Часовой пояс: {tz_str}
📅 Регистрация: {reg_fmt}
🕐 Последняя активность: {act_fmt}

🎮 XP: <b>{xp}</b> | Уровень: <b>{level}</b>
🏆 Рейтинг: <b>{rank_str}</b>"""


def admin_xp_change_success_msg(user_id: int, delta: int, new_xp: int) -> str:
    """Сообщение об успешном изменении XP пользователя администратором."""
    sign = '+' if delta > 0 else ''
    return f"✅ XP пользователя <code>{user_id}</code> изменён: <b>{sign}{delta}</b>\nТекущий XP: <b>{new_xp}</b>"


def user_search_not_found_msg(query: str) -> str:
    """Сообщение об отсутствии пользователя при поиске."""
    return f"❌ Пользователь <code>{query}</code> не найден в базе данных."


def user_banned_notify_msg(admin_username: str | None) -> str:
    """Уведомление пользователю о блокировке его аккаунта."""
    adm = f"@{admin_username}" if admin_username else "Администратор"
    return f"🚫 Ваш аккаунт заблокирован администратором {adm}."


def user_unbanned_notify_msg(admin_username: str | None) -> str:
    """Уведомление пользователю о снятии блокировки его аккаунта."""
    adm = f"@{admin_username}" if admin_username else "Администратор"
    return f"✅ Ваш аккаунт разблокирован администратором {adm}."


def leaderboard_msg(rows: list, user_rank: int | None, user_xp: int, user_level: int) -> str:
    """Сообщение таблицы лидеров с позицией текущего пользователя."""
    if not rows:
        return "🏆 <b>Таблица лидеров</b>\n\nПока никто не набрал очков. Будь первым!"
    lines = ["🏆 <b>Таблица лидеров</b>\n"]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for rank, uid, username, xp, level in rows:
        medal = medals.get(rank, f"{rank}.")
        name = f"@{username}" if username else f"id{uid}"
        title = get_level_title(level)
        lines.append(f"{medal} {name} — ур. <b>{level}</b> ({title}) · <b>{xp} XP</b>")
    lines.append("")
    if user_rank:
        lines.append(f"📍 Твоя позиция: <b>#{user_rank}</b> · {user_xp} XP · ур. {user_level}")
    else:
        lines.append("📍 Тебя пока нет в топе — зарабатывай очки!")
    return "\n".join(lines)

ai_analyze_off_msg = "❌ ИИ-анализ временно отключен."

