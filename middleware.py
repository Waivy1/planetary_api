from functools import wraps
from flask  import request, Response, g


def use_middleware(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        print(request.authorization)
        username = request.authorization['username']
        password = request.authorization['password']
        g.token = 'token'
        if username == 'test' and password == 'test':
            return func(*args, **kwargs)

        return Response('failed', mimetype='text/plain', status=401)

    return decorated_func
