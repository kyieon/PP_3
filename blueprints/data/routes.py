"""
데이터 처리 관련 라우트
"""
import pandas as pd
from flask import request, jsonify, session
from utils.common import get_db_connection
from utils.pivot_detail_view import *
from . import data_bp


def login_required(f):
    """로그인 필요 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@data_bp.route('/getData', methods=['GET', 'POST'])
@login_required
def get_data():
    """데이터 가져오기"""
    # TODO: 기존 getData 로직을 이곳으로 이동
    return jsonify({'message': 'getData endpoint'})


@data_bp.route('/update_repair', methods=['POST'])
@login_required
def update_repair():
    """보수 데이터 업데이트"""
    try:
        repair_data = request.get_json()
        # 기존: filtered_data = [item for item in repair_data if item['repairMethod'] != '주의관찰']
        # 전체 데이터로부터 보수물량표 생성 (주의관찰 포함)
        # 부재명별로 그룹화 (cost table용, 주의관찰 제외)
        filtered_data = [item for item in repair_data if item['repairMethod'] != '주의관찰']
        component_groups = {}
        for item in filtered_data:
            component = item['component']
            if component not in component_groups:
                component_groups[component] = []
            component_groups[component].append(item)

        # cost_table_html(개략공사비표) 생성 (주의관찰 제외)
        cost_table_html = '<table class="table table-bordered">'
        cost_table_html += '<thead><tr><th>부재명</th><th>보수방안</th><th>우선순위</th><th>단가</th><th>물량</th><th>공사비</th></tr></thead>'
        cost_table_html += '<tbody>'
        total_cost = 0
        for component, items in component_groups.items():
            grouped_items = {}
            for item in items:
                key = (item['repairMethod'], item['priority'])
                if key not in grouped_items:
                    grouped_items[key] = {
                        'component': item['component'],
                        'repairMethod': item['repairMethod'],
                        'priority': item['priority'],
                        'unitPrice': item['unitPrice'],
                        'quantity': 0
                    }
                grouped_items[key]['quantity'] += item['quantity']
            for key, item in grouped_items.items():
                cost = float(item['unitPrice']) * float(item['quantity'])
                total_cost += cost
                cost_table_html += f'<tr><td>{item["component"]}</td><td>{item["repairMethod"]}</td><td>{item["priority"]}</td><td>{item["unitPrice"]}</td><td>{item["quantity"]}</td><td>{cost:,.0f}</td></tr>'
        cost_table_html += '</tbody></table>'
        # 우선순위별 합계 HTML 생성 (생략)
        # 보수물량표(수량표)는 generate_repair_tables에서 이미 전체 데이터로 생성됨(주의관찰 포함)
        # 필요시 repair_html도 반환하도록 추가 가능
        return jsonify({
            'cost_table': cost_table_html
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/pivot_detail', methods=['POST'])
@login_required
def pivot_detail():
    try:
        data = request.get_json()

        filename=session['current_filename']

        detail_html = pivot_detail_view(filename,data['pivot'], data['detail']);
        return jsonify({
            'detail_html': detail_html,

        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/crack_subdivision', methods=['POST'])
@login_required
def crack_subdivision():
    """균열 세분화"""
    try:
        data = request.get_json()

        filename = session.get('current_filename')
        if not filename:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        from utils.pivot_detail_view import pivot_detail_view
        detail_html, detail_html_header_link = pivot_detail_view(filename, data.get('pivot'), data.get('detail'))

        return jsonify({
            'detail_html': detail_html,
            'detail_html_header_link': detail_html_header_link
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
