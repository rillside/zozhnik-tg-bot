from typing import Any

user_states: dict[int, dict] = {}


# Управление состояниями пользователей

def set_state(user_id: int, state: str | None, data: Any) -> None:
    """Устанавливает состояние и произвольные данные для пользователя."""
    global user_states
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['state'] = state
    user_states[user_id]['data'] = data


def clear_state(user_id: int) -> None:
    """Полностью удаляет состояние пользователя."""
    global user_states
    if user_id not in user_states:
        return
    del user_states[user_id]


def clear_state_keep_data(user_id: int) -> None:
    """Сбрасывает активное состояние, сохраняя сохранённые данные."""
    global user_states
    if user_id not in user_states:
        return
    # Сохраняем данные, удаляем состояние
    data = user_states[user_id].get('data')
    user_states[user_id] = {
        'state': None,
        'data': data
    }


def get_state(user_id: int) -> tuple[str | None, Any]:
    """Возвращает пару (состояние, данные) для пользователя, или (None, None) если состояния нет."""
    if user_id not in user_states:
        return None, None
    return user_states[user_id]['state'],user_states[user_id]['data']
