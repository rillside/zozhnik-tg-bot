import asyncio

# Защита от медиагрупп

# Хранилище предупреждённых медиагрупп
_warned_groups: set[str] = set()


async def _clear_group_warning(group_id: str, delay: int = 10) -> None:
    """Удаляет группу из хранилища через delay секунд."""
    await asyncio.sleep(delay)
    _warned_groups.discard(group_id)


def is_group_warned(group_id: str) -> bool:
    """Проверяет, было ли уже предупреждение для этой группы."""
    return group_id in _warned_groups


def mark_group_warned(group_id: str, cooldown: int = 10) -> None:
    """Отмечает группу как предупреждённую и запускает таймер очистки."""
    _warned_groups.add(group_id)
    asyncio.create_task(_clear_group_warning(group_id, cooldown))