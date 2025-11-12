"""
Flask 애플리케이션 공통 데코레이터
"""
from functools import wraps
from flask import session, redirect, url_for, jsonify


def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # AJAX 요청인 경우 JSON 응답
            if hasattr(f, '__name__') and any(x in f.__name__ for x in ['api_', 'ajax_', 'get_', 'update_']):
                return jsonify({'error': 'Login required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
