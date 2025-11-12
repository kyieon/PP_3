from flask import request, jsonify, session
from utils.common import get_db_connection
from . import api_bp

@api_bp.route('/save_span_damage', methods=['POST'])
def save_span_damage():
    try:
        data = request.get_json()
        filename = data.get('filename')
        user_id = session.get('user_id')
        email = session.get('email')
        username = session.get('username')
        damage_list = data.get('damage_list', [])

        if not filename or not user_id or not damage_list:
            return jsonify({'success': False, 'error': '필수 데이터가 누락되었습니다.'}), 400

        # 기존 데이터 삭제 (filename, user_id, damage_type별)
        conn = get_db_connection()
        cur = conn.cursor()
        for item in damage_list:
            cur.execute(
                '''
                DELETE FROM span_damage
                WHERE filename = %s AND user_id = '%s' AND type = %s
                ''',
                (filename, user_id, item.get('type'))
            )

        # 새 데이터 저장
        for item in damage_list:
            cur.execute('''
                INSERT INTO span_damage (
                    filename, user_id, username, email, span_id, type, damage_type,
                    damage_quantity, count, unit, inspection_area, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (
                filename,
                user_id,
                username,
                email,
                item.get('spanId'),
                item.get('type'),
                item.get('damageType'),
                item.get('damageQuantity'),
                item.get('count'),
                item.get('unit'),
                item.get('inspectionArea')
            ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': '손상 데이터가 저장되었습니다.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# span_damage 데이터 조회 API
@api_bp.route('/get_span_damage', methods=['GET'])
def get_span_damage():
    filename = request.args.get('filename')
    user_id = session.get('user_id')
    if not filename or not user_id:
        return jsonify({'success': False, 'error': '필수 파라미터가 누락되었습니다.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT span_id, type, damage_type, damage_quantity, count, unit, inspection_area, updated_at
        FROM span_damage
        WHERE filename = %s AND user_id = '%s'
        ORDER BY updated_at DESC
    ''', (filename, user_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # 컬럼명과 매핑
    columns = ['spanId', 'type', 'damageType', 'damageQuantity', 'count', 'unit', 'inspectionArea', 'updatedAt']
    data = [dict(zip(columns, row)) for row in rows]

    return jsonify({'success': True, 'data': data}), 200
