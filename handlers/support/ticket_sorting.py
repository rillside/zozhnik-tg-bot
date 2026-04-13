from datetime import datetime
from typing import Any


def sort_ticket(ticket: dict[str, Any]) -> tuple:
    """Сортирует тикеты по статусу (новые выше) и дате обновления (свежие выше)."""
    status = ticket.get('status_for_user') or ticket.get('status_for_admin')
    date_str = ticket.get('updated_at')

    status_key = 0 if status == 'new' else 1
    dt = datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
    date_key = -dt.timestamp()

    return status_key, date_key
