"""
상태평가 관련 라우트
"""
from flask import request, render_template, jsonify, session
from utils.condition_evaluation import generate_condition_evaluation_pivot, generate_condition_evaluation_html
from utils.bridge_evaluation import generate_all_component_evaluations, generate_component_evaluation_data
from utils.detailed_condition_evaluation import generate_detailed_condition_evaluation, generate_detailed_condition_html
from . import evaluation_bp


def login_required(f):
    """로그인 필요 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@evaluation_bp.route('/condition_evaluation', methods=['POST'])
@login_required
def condition_evaluation():
    """상태평가 처리"""
    # TODO: 기존 condition_evaluation 로직을 이곳으로 이동
    return jsonify({'message': 'condition_evaluation endpoint'})


@evaluation_bp.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    """평가 처리"""
    # TODO: 기존 evaluate 로직을 이곳으로 이동
    return jsonify({'message': 'evaluate endpoint'})


@evaluation_bp.route('/evaluation_form')
@login_required
def evaluation_form():
    """평가 폼 페이지"""
    return render_template('evaluation_form.html')


@evaluation_bp.route('/evaluation_table')
@login_required
def evaluation_table():
    """평가 테이블 페이지"""
    return render_template('evaluation_table.html')
