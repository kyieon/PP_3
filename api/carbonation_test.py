from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from utils.common import get_db_connection

carbonation_test_bp = Blueprint('carbonation_test', __name__)

# 탄산화 시험 데이터 저장 API
@carbonation_test_bp.route('/save_carbonation_test', methods=['POST'])
def save_carbonation_test():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        carbonation_data = data.get('carbonation_data', [])
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
            
        if not carbonation_data:
            return jsonify({'error': '탄산화 데이터가 없습니다.'}), 400
        
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 탄산화 시험 테이블 생성 (없으면)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carbonation_test (
                id SERIAL PRIMARY KEY, 
                file_id TEXT NOT NULL,
                component TEXT NOT NULL,
                position TEXT NOT NULL,
                test_type TEXT NOT NULL,
                grade TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 기존 데이터 삭제 (같은 파일의 데이터 갱신)
        cursor.execute('DELETE FROM carbonation_test WHERE file_id = %s', (file_id,))
        
        # 새 데이터 삽입
        insert_count = 0
        for item in carbonation_data:
            component = item.get('component')
            position = item.get('position')
            test_type = item.get('test_type')  # 'upper' 또는 'lower'
            grade = item.get('grade')
            
            if component and position and test_type and grade:
                cursor.execute('''
                    INSERT INTO carbonation_test 
                    (file_id, component, position, test_type, grade, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (file_id, component, position, test_type, grade))
                insert_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{insert_count}개의 탄산화 시험 데이터가 저장되었습니다.',
            'saved_count': insert_count
        })
        
    except Exception as e:
        print(f"탄산화 시험 데이터 저장 오류: {str(e)}")
        return jsonify({'error': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

# 탄산화 시험 데이터 조회 API
@carbonation_test_bp.route('/get_carbonation_test', methods=['GET'])
def get_carbonation_test():
    try:
        file_id = request.args.get('file_id')
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
        
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 탄산화 시험 데이터 조회
        cursor.execute('''
            SELECT component, position, test_type, grade, created_at, updated_at
            FROM carbonation_test 
            WHERE file_id = %s
            ORDER BY position, test_type
        ''', (file_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 결과 데이터 구성
        carbonation_data = []
        for row in rows:
            carbonation_data.append({
                'component': row[0],
                'position': row[1],
                'test_type': row[2],
                'grade': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        return jsonify({
            'success': True,
            'carbonation_data': carbonation_data,
            'count': len(carbonation_data)
        })
        
    except Exception as e:
        print(f"탄산화 시험 데이터 조회 오류: {str(e)}")
        return jsonify({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}), 500
