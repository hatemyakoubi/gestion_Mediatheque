# auth.py
from functools import wraps
from flask import request, jsonify
from flask_bcrypt import Bcrypt
import jwt
from datetime import datetime, timedelta

bcrypt = Bcrypt()
SECRET_KEY = 'your-secret-key'  # In production, use environment variable

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

'''def create_token(user_id):
    return jwt.encode(
        {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(days=1)
        },
        SECRET_KEY,
        algorithm='HS256'
    )'''

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            raise AuthError({'code': 'authorization_header_missing',
                           'description': 'Authorization header is required'}, 401)

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            raise AuthError({'code': 'token_expired',
                           'description': 'Token has expired'}, 401)
        except Exception:
            raise AuthError({'code': 'invalid_token',
                           'description': 'Invalid token'}, 401)
    return decorated

# error_handlers.py
from marshmallow import ValidationError
from flask import jsonify
from bson.errors import InvalidId

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({'error': 'Validation error', 'messages': error.messages}), 400

    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        return jsonify(error.error), error.status_code

    @app.errorhandler(InvalidId)
    def handle_invalid_object_id(error):
        return jsonify({'error': 'Invalid ID format'}), 400

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        return jsonify({'error': 'An unexpected error occurred'}), 500