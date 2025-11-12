from flask import Blueprint, request, jsonify
import json
from datetime import datetime

from sqlalchemy import false
from utils.common import get_db_connection

component_selection_bp = Blueprint('component_selection', __name__)

# 부재별 선택 데이터 저장 API
@component_selection_bp.route('/save_component_selection', methods=['POST'])
def save_component_selection():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        selected_components = data.get('selected_components', {})
        bridge_info = data.get('bridge_info', {})
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
            
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 부재 선택 테이블 생성 (없으면)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component_selection (
                id SERIAL PRIMARY KEY,
                file_id TEXT NOT NULL UNIQUE,
                selected_components TEXT NOT NULL,
                bridge_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # JSON 문자열로 변환
        selected_components_json = json.dumps(selected_components)
        bridge_info_json = json.dumps(bridge_info)
        
        # 기존 데이터가 있으면 업데이트, 없으면 삽입 (PostgreSQL UPSERT)
        cursor.execute('''
            INSERT INTO component_selection 
            (file_id, selected_components, bridge_info, created_at, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (file_id) 
            DO UPDATE SET 
                selected_components = EXCLUDED.selected_components,
                bridge_info = EXCLUDED.bridge_info,
                updated_at = CURRENT_TIMESTAMP
        ''', (file_id, selected_components_json, bridge_info_json))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '부재 선택 데이터가 저장되었습니다.'
        })
        
    except Exception as e:
        print(f"부재 선택 데이터 저장 오류: {str(e)}")
        return jsonify({'error': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

# 부재별 선택 데이터 조회 API
@component_selection_bp.route('/get_component_selection', methods=['GET'])
def get_component_selection():
    try:
        file_id = request.args.get('file_id')
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
        
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 부재 선택 데이터 조회
        cursor.execute('''
            SELECT selected_components, bridge_info, created_at, updated_at
            FROM component_selection 
            WHERE file_id = %s
        ''', (file_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            # JSON 문자열을 파이썬 객체로 변환
            selected_components = json.loads(row[0]) if row[0] else {}
            bridge_info = json.loads(row[1]) if row[1] else {}
            
            return jsonify({
                'success': True,
                'selected_components': selected_components,
                'bridge_info': bridge_info,
                'created_at': row[2],
                'updated_at': row[3]
            })
        else:
            return jsonify({
                'success': True, 
                'selected_components':{"slab": True, "girder": True, "crossbeam": True, "abutment": True, "pier": True, "foundation": True, "bearing": True, "expansionJoint": True, "pavement": True, "drainage": True, "railing": True, "carbonationUpper": True, "carbonationLower": True},
                'bridge_info': True,
                'message': '저장된 데이터가 없습니다.'
            })
        
    except Exception as e:
        print(f"부재 선택 데이터 조회 오류: {str(e)}")
        return jsonify({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}), 500

# 교량 정보 저장 API
@component_selection_bp.route('/save_bridge_info', methods=['POST'])
def save_bridge_info():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        bridge_info = data.get('bridge_info', {})
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
            
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 교량 정보 테이블 생성 (없으면)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bridge_info (
                id SERIAL PRIMARY KEY,
                file_id TEXT NOT NULL UNIQUE,
                bridge_name TEXT,
                structure_type TEXT,
                span_count INTEGER,
                carbonation_upper_positions TEXT,
                carbonation_lower_positions TEXT,
                chloride_upper_positions TEXT,
                chloride_lower_positions TEXT,
                additional_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 교량 정보 저장
        bridge_name = bridge_info.get('bridgeName', '')
        structure_type = bridge_info.get('structureType', '')
        span_count = bridge_info.get('spanCount', 0)
        carbonation_upper_positions = bridge_info.get('carbonationUpperPositions', '')
        carbonation_lower_positions = bridge_info.get('carbonationLowerPositions', '')
        chloride_upper_positions = bridge_info.get('chlorideUpperPositions', '')
        chloride_lower_positions = bridge_info.get('chlorideLowerPositions', '')
        additional_info = json.dumps(bridge_info)
        
        # PostgreSQL UPSERT
        cursor.execute('''
            INSERT INTO bridge_info 
            (file_id, bridge_name, structure_type, span_count, 
             carbonation_upper_positions, carbonation_lower_positions,
             chloride_upper_positions, chloride_lower_positions,
             additional_info, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (file_id) 
            DO UPDATE SET 
                bridge_name = EXCLUDED.bridge_name,
                structure_type = EXCLUDED.structure_type,
                span_count = EXCLUDED.span_count,
                carbonation_upper_positions = EXCLUDED.carbonation_upper_positions,
                carbonation_lower_positions = EXCLUDED.carbonation_lower_positions,
                chloride_upper_positions = EXCLUDED.chloride_upper_positions,
                chloride_lower_positions = EXCLUDED.chloride_lower_positions,
                additional_info = EXCLUDED.additional_info,
                updated_at = CURRENT_TIMESTAMP
        ''', (file_id, bridge_name, structure_type, span_count,
              carbonation_upper_positions, carbonation_lower_positions,
              chloride_upper_positions, chloride_lower_positions,
              additional_info))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '교량 정보가 저장되었습니다.'
        })
        
    except Exception as e:
        print(f"교량 정보 저장 오류: {str(e)}")
        return jsonify({'error': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

# 교량 정보 조회 API
@component_selection_bp.route('/get_bridge_info', methods=['GET'])
def get_bridge_info():
    try:
        file_id = request.args.get('file_id')
        
        if not file_id:
            return jsonify({'error': '파일 ID가 필요합니다.'}), 400
        
        # 데이터베이스 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 교량 정보 조회
        cursor.execute('''
            SELECT bridge_name, structure_type, span_count,
                   carbonation_upper_positions, carbonation_lower_positions,
                   chloride_upper_positions, chloride_lower_positions,
                   additional_info, created_at, updated_at
            FROM bridge_info 
            WHERE file_id = %s
        ''', (file_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            additional_info = json.loads(row[7]) if row[7] else {}
            
            return jsonify({
                'success': True,
                'bridge_info': {
                    'bridgeName': row[0],
                    'structureType': row[1],
                    'spanCount': row[2],
                    'carbonationUpperPositions': row[3],
                    'carbonationLowerPositions': row[4],
                    'chlorideUpperPositions': row[5],
                    'chlorideLowerPositions': row[6],
                    **additional_info
                },
                'created_at': row[8],
                'updated_at': row[9]
            })
        else:
            return jsonify({
                'success': True,
                'bridge_info': {},
                'message': '저장된 교량 정보가 없습니다.'
            })
        
    except Exception as e:
        print(f"교량 정보 조회 오류: {str(e)}")
        return jsonify({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}), 500
