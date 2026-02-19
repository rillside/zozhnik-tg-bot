import asyncio
# ЗАЩИТА ОТ МЕДИАГРУПП

# Хранилище предупрежденных медиагрупп
_warned_groups = set()

async def _clear_group_warning(group_id, delay=10):
    """Удаляет группу из хранилища через delay секунд"""
    await asyncio.sleep(delay)
    _warned_groups.discard(group_id)

def is_group_warned(group_id):
    """Проверяет, было ли уже предупреждение для этой группы"""
    return group_id in _warned_groups

def mark_group_warned(group_id, cooldown=10):
    """Отмечает группу как предупрежденную и запускает таймер очистки"""
    _warned_groups.add(group_id)
    asyncio.create_task(_clear_group_warning(group_id, cooldown))