from typing import Any


class State:
    """Конечный автомат для пользовательских состояний."""

    user_states: dict[int, dict[str, Any]] = {}

    @classmethod
    def set_state(cls, user_id: int, state: str | None, data: Any) -> None:
        """Устанавливает состояние и произвольные данные для пользователя."""
        if user_id not in cls.user_states:
            cls.user_states[user_id] = {}
        cls.user_states[user_id]["state"] = state
        cls.user_states[user_id]["data"] = data

        
    @staticmethod
    def get_data_only(user_id: int) -> Any:
        """Возвращает только данные для пользователя или None."""
        if user_id not in State.user_states:
            return None
        return State.user_states[user_id].get("data")


    @staticmethod
    def set_data(user_id: int, data: Any) -> None:
        """Обновляет только данные для пользователя, не изменяя состояние."""
        if user_id not in State.user_states:
            State.user_states[user_id] = {"state": None, "data": data}
        else:
            State.user_states[user_id]["data"] = data

    @classmethod
    def clear_state(cls, user_id: int) -> None:
        """Полностью удаляет состояние пользователя."""
        if user_id in cls.user_states:
            del cls.user_states[user_id]

    @classmethod
    def clear_state_keep_data(cls, user_id: int) -> None:
        """Сбрасывает состояние, оставляя сохраненные данные."""
        if user_id not in cls.user_states:
            return
        data = cls.user_states[user_id].get("data")
        cls.user_states[user_id] = {"state": None, "data": data}

    @classmethod
    def get_state(cls, user_id: int) -> tuple[str | None, Any]:
        """Возвращает `(состояние, данные)` для пользователя или `(None, None)`."""
        if user_id not in cls.user_states:
            return None, None
        state_data = cls.user_states[user_id]
        return state_data.get("state"), state_data.get("data")
