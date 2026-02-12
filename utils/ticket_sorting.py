from datetime import datetime


def sort_ticket(ticket):
    status = ticket[2]
    date_str = ticket[3]

    # Статус: непрочитанные первыми
    status_key = 0 if status == 'new' else 1

    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    date_key = -dt.timestamp()  # отрицательный timestamp = новые первыми

    return status_key, date_key
