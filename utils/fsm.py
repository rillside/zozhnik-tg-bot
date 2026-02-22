user_states = {}
def set_state(user_id,state,data):
    global user_states
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['state'] = state
    user_states[user_id]['data'] = data
def clear_state(user_id):
    global user_states
    if user_id not in user_states:
        return
    del user_states[user_id]
def clear_state_keep_data(user_id):
    global user_states
    if user_id not in user_states:
        return
    # Сохраняем данные, удаляем состояние
    data = user_states[user_id].get('data')
    user_states[user_id] = {
        'state': None,
        'data': data
    }

def get_state(user_id):
    if user_id not in user_states:
        return None,None
    return user_states[user_id]['state'],user_states[user_id]['data']
