import json


def success(message):
    return json.dumps({'status': 'success', 'message': message})


def error(message):
    return json.dumps({'status': 'error', 'message': message})
