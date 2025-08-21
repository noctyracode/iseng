bots = []

def add_bot(token, name):
    bots.append({"token": token, "name": name})

def remove_bot(token):
    global bots
    bots = [b for b in bots if b["token"] != token]

def get_bots():
    return bots

states = {}

def save_state(user_id, state):
    states[user_id] = state

def get_state(user_id):
    return states.get(user_id)

def clear_state(user_id):
    if user_id in states:
        del states[user_id]
