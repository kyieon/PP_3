"""
교량 상태평가표 API 엔드포인트
"""
from flask import request, jsonify, session
import pandas as pd
import json
from . import api_bp
from utils.common import get_db_connection, clean_dataframe_data
from utils.bridge_evaluation import generate_all_component_evaluations

@api_bp.route('/bridge_evaluation/<filename>', methods=['GET'])
def get_bridge_evaluation(filename):
    """
    파일명을 기반으로 교량 상태평가표를 생성합니다.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
            
        # 데이터베이스에서 파일 데이터 가져오기
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT file_data, bridge_name, structure_type FROM uploaded_files WHERE filename = %s AND user_id = %s",
            (filename, session['user_id'])
        )
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
            
        # JSON 데이터를 DataFrame으로 변환
        file_data = result[0]
        bridge_name = result[1] or '교량명 없음'
        structure_type = result[2] or 'PSC 박스거더교'
        
        if isinstance(file_data, str):
            file_data = json.loads(file_data)
        df = pd.DataFrame(file_data)
        
        # DataFrame 데이터 정리 및 trim 처리
        df = clean_dataframe_data(df)
        
        cur.close()
        conn.close()
        
        # 상태평가표 HTML 생성
        evaluation_html = generate_all_component_evaluations(df)
        
        return jsonify({
            'success': True,
            'bridge_name': bridge_name,
            'structure_type': structure_type,
            'evaluation_html': evaluation_html
        })
        
    except Exception as e:
        print(f"상태평가표 생성 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'상태평가표 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@api_bp.route('/component_evaluation', methods=['POST'])
def get_component_evaluation():
    """
    특정 부재의 상태평가를 수행합니다.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
            
        data = request.get_json()
        component_type = data.get('component_type')
        filename = data.get('filename')
        
        if not component_type or not filename:
            return jsonify({'error': '부재 타입과 파일명이 필요합니다.'}), 400
            
        # 데이터베이스에서 파일 데이터 가져오기
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT file_data FROM uploaded_files WHERE filename = %s AND user_id = %s",
            (filename, session['user_id'])
        )
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
            
        # JSON 데이터를 DataFrame으로 변환
        file_data = result[0]
        if isinstance(file_data, str):
            file_data = json.loads(file_data)
        df = pd.DataFrame(file_data)
        
        # DataFrame 데이터 정리 및 trim 처리
        df = clean_dataframe_data(df)
        
        cur.close()
        conn.close()
        
        # 해당 부재의 데이터만 필터링
        component_df = df[df['부재명'].str.contains(component_type, na=False)]
        
        if component_df.empty:
            return jsonify({
                'success': True,
                'evaluation_html': f'<p>{component_type} 부재의 데이터가 없습니다.</p>'
            })
        
        # 상태평가 수행
        evaluation_html = generate_all_component_evaluations(component_df)
        
        return jsonify({
            'success': True,
            'evaluation_html': evaluation_html
        })
        
    except Exception as e:
        print(f"부재별 상태평가 중 오류: {str(e)}")
        return jsonify({'error': f'부재별 상태평가 중 오류가 발생했습니다: {str(e)}'}), 500

@api_bp.route('/save_evaluation_result', methods=['POST'])
def save_evaluation_result():
    """
    상태평가 결과를 저장합니다.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
            
        data = request.get_json()
        filename = data.get('filename')
        evaluation_data = data.get('evaluation_data')
        
        if not filename or not evaluation_data:
            return jsonify({'error': '파일명과 평가 데이터가 필요합니다.'}), 400
            
        # 평가 결과를 데이터베이스에 저장
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 기존 평가 결과가 있으면 업데이트, 없으면 삽입
        cur.execute('''
            INSERT INTO evaluation_results (user_id, filename, evaluation_data, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id, filename)
            DO UPDATE SET 
                evaluation_data = EXCLUDED.evaluation_data,
                updated_at = NOW()
        ''', (session['user_id'], filename, json.dumps(evaluation_data)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '상태평가 결과가 저장되었습니다.'
        })
        
    except Exception as e:
        print(f"상태평가 결과 저장 중 오류: {str(e)}")
        return jsonify({'error': f'상태평가 결과 저장 중 오류가 발생했습니다: {str(e)}'}), 500

@api_bp.route('/evaluation_history/<filename>', methods=['GET'])
def get_evaluation_history(filename):
    """
    저장된 상태평가 결과를 조회합니다.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT evaluation_data, created_at, updated_at
            FROM evaluation_results
            WHERE user_id = %s AND filename = %s
        ''', (session['user_id'], filename))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({
                'success': False,
                'message': '저장된 평가 결과가 없습니다.'
            })
            
        evaluation_data = result[0]
        if isinstance(evaluation_data, str):
            evaluation_data = json.loads(evaluation_data)
            
        return jsonify({
            'success': True,
            'evaluation_data': evaluation_data,
            'created_at': result[1].isoformat() if result[1] else None,
            'updated_at': result[2].isoformat() if result[2] else None
        })
        
    except Exception as e:
        print(f"상태평가 이력 조회 중 오류: {str(e)}")
        return jsonify({'error': f'상태평가 이력 조회 중 오류가 발생했습니다: {str(e)}'}), 500
