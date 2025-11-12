"""
교량 관련 API
"""
import json
import pandas as pd
from flask import jsonify, session
from utils.common import clean_dataframe_data, get_db_connection
from utils.decorators import login_required
from . import api_bp


@api_bp.route('/bridge_list')
@login_required
def get_bridge_list():
    """현재 사용자의 교량 목록 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 현재 사용자의 업로드된 파일 목록 가져오기
        cur.execute("""
            SELECT "id","user_id","filename","original_filename","upload_date","file_data",
                   "bridge_name","length","width","structure_type","span_count","expansion_joint_location"
            FROM uploaded_files
            WHERE user_id = %s
            ORDER BY bridge_name
        """, (session['user_id'],))

        results = cur.fetchall()
        columns = ["id","user_id","filename","original_filename","upload_date","file_data",
                   "bridge_name","length","width","structure_type","span_count","expansion_joint_location"]

        bridges = []
        for row in results:
            bridge = dict(zip(columns, row))
            bridges.append(bridge)

        cur.close()
        conn.close()

        print(f'추출된 교량 목록: {bridges}')  # 디버깅용 로그

        return jsonify({
            'success': True,
            'bridges': bridges
        })
    except Exception as e:
        print(f'Error getting bridge list: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/bridge_data/<filename>')
@login_required
@login_required
def get_bridge_data(filename):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 파일명으로 데이터 조회
        cur.execute("""
            SELECT bridge_name, length, width, structure_type, span_count,
                   expansion_joint_location, file_data
            FROM uploaded_files
            WHERE filename = %s AND user_id = %s
        """, (filename, session['user_id']))

        result = cur.fetchone()

        if not result:
            return jsonify({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }), 404

        # JSON 데이터를 DataFrame으로 변환하여 손상 데이터 처리
        file_data_json = result[6]
        damage_data = {}

        if file_data_json:
            if isinstance(file_data_json, str):
                file_data_json = json.loads(file_data_json)

            df = pd.DataFrame(file_data_json)

            # DataFrame 데이터 정리 및 trim 처리
            df = clean_dataframe_data(df)

            # 부재별로 손상 데이터 그룹화
            for component in df['부재명'].unique():
                component_df = df[df['부재명'] == component]

                # 부재별 집계데이터 생성 (경간별로 집계)
                component_summary = component_df.groupby(['부재위치', '손상내용', '단위'])[['손상물량', '개소']].sum().reset_index()

                damage_data[component] = []

                for _, row in component_summary.iterrows():
                    damage_item = {
                        'position': str(row['부재위치']),
                        'damage_type': str(row['손상내용']),
                        'unit': str(row['단위']),
                        'damage_quantity': float(row['손상물량']) if pd.notnull(row['손상물량']) else 0,
                        'count': int(row['개소']) if pd.notnull(row['개소']) else 0,
                        'inspection_area': float(row.get('점검면적', 100)) if pd.notnull(row.get('점검면적', 100)) else 100
                    }
                    damage_data[component].append(damage_item)

        bridge_data = {
            'bridge_name': result[0] or '',
            'length': float(result[1]) if result[1] else 0,
            'width': float(result[2]) if result[2] else 0,
            'structure_type': result[3] or '',
            'span_count': int(result[4]) if result[4] else 0,
            'expansion_joint_location': result[5] or '',
            'has_file_data': bool(result[6]),
            'damage_data': damage_data if file_data_json else {}
        }

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': bridge_data
        })

    except Exception as e:
        print(f"교량 데이터 조회 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@api_bp.route('/bridge/<bridge_name>/components')
@login_required
def get_bridge_components(bridge_name):
    """교량의 부재 목록 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 교량명으로 파일 데이터 조회
        cur.execute("""
            SELECT file_data
            FROM uploaded_files
            WHERE bridge_name = %s AND user_id = %s
            LIMIT 1
        """, (bridge_name, session['user_id']))

        result = cur.fetchone()

        if not result:
            return jsonify({
                'success': False,
                'error': '교량을 찾을 수 없습니다.'
            }), 404

        file_data = result[0]

        # JSON 데이터로 변환
        if isinstance(file_data, str):
            file_data = json.loads(file_data)

        # 부재명 목록 추출
        components = []
        if isinstance(file_data, list) and len(file_data) > 0:
            for record in file_data:
                component = record.get('부재명', '')
                if component and component not in components:
                    components.append(component)

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'components': components
        })

    except Exception as e:
        print(f'Error getting bridge components: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
