
def success(message, data):
    return {'status': 'success', 'message': message, 'data': data}


def error(message):
    return {'status': 'error', 'message': str(message)}
