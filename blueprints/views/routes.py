"""
페이지 뷰 관련 라우트
"""
from flask import render_template, session, redirect, url_for
from . import views_bp


def login_required(f):
    """로그인 필요 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@views_bp.route('/evaluation_form')
@login_required
def evaluation_form():
    """평가 폼 페이지"""
    return render_template('evaluation_form.html')


@views_bp.route('/evaluation_table')
@login_required
def evaluation_table():
    """평가 테이블 페이지"""
    return render_template('evaluation_table.html')
