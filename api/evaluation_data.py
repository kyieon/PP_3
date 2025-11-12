"""
상태평가표 데이터 생성 API (개선된 condition_evaluation 모듈 사용)
"""
from flask import request, jsonify, session
import pandas as pd
import json
import re

from utils.file_validation import normalize_component_source
from . import api_bp
from utils.common import get_db_connection, clean_dataframe_data, get_keyword_by_meta_id_and_source
from utils.common import get_meta_keywords_by_meta_id, get_meta
from utils.common import convert_component_name_to_key,get_source_by_meta_id_and_keyword



from utils.condition_evaluation import generate_condition_evaluation_pivot



# evaluation_result가 이미 생성되어 있다고 가정
# 교량받침(=bearing)만 추출하여 테이블 형태로 출력 및 md 파일 저장


def print_bearing_positions_table(component_data):
    rows = []
    # '교량받침' 키가 있는지 확인
    bearing_group = component_data.get('교량받침', {})
    for sub_name, sub_data in bearing_group.items():
        positions = sub_data.get('positions', {})
        for pos_name, pos_data in positions.items():
            row = {
                'sub_name': sub_name,  # '교량받침' or '받침장치'
                'position': pos_name,
                'crack_width_1d': pos_data.get('crack_width_1d'),
                'crack_width_2d': pos_data.get('crack_width_2d'),
                'crack_ratio_1d': pos_data.get('crack_ratio_1d'),
                'crack_ratio_2d': pos_data.get('crack_ratio_2d'),
                'damage_quantities': pos_data.get('damage_quantities'),
                'condition_grade': pos_data.get('condition_grade'),
            }
            rows.append(row)
    if not rows:
        print("교량받침 positions 데이터가 없습니다.")
        return
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))  # 콘솔 표 출력

    # 마크다운 테이블로 저장
    md_table = df.to_markdown(index=False)
    with open("bearing_positions_table.md", "w", encoding="utf-8") as f:
        f.write(md_table)
    print("bearing_positions_table.md 파일로 저장되었습니다.")



def print_bearing_table(component_data):
    # positions 딕셔너리 추출
    positions = component_data.get('positions', {})
    rows = []
    for pos_name, pos_data in positions.items():
        # pos_data의 주요 필드만 추출 (필요시 원하는 필드만 선택)
        row = {
            'position': pos_name,
            'crack_width_1d': pos_data.get('crack_width_1d'),
            'crack_width_2d': pos_data.get('crack_width_2d'),
            'crack_ratio_1d': pos_data.get('crack_ratio_1d'),
            'crack_ratio_2d': pos_data.get('crack_ratio_2d'),
            'damage_quantities': pos_data.get('damage_quantities'),
            'condition_grade': pos_data.get('condition_grade'),
        }
        rows.append(row)
    if not rows:
        print("positions 데이터가 없습니다.")
        return
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))  # 콘솔 표 출력

    # 마크다운 테이블로 저장
    md_table = df.to_markdown(index=False)
    with open("bearing_positions_table.md", "w", encoding="utf-8") as f:
        f.write(md_table)
    print("bearing_positions_table.md 파일로 저장되었습니다.")

# 사용 예시
# print_bearing_positions_table(component_data)


@api_bp.route('/generate_evaluation_data', methods=['POST'])
def generate_evaluation_data():
    """
    부재별 집계표 데이터를 기반으로 상태평가표 데이터를 생성합니다.
    개선된 condition_evaluation 모듈을 사용하여 1방향/2방향 균열 분류를 적용합니다.
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401

        data = request.get_json()
        filename = data.get('filename')
        component_type = data.get('component_type')

        if not filename:
            return jsonify({'error': '파일명이 필요합니다.'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 파일 데이터 조회
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

        # 개선된 condition_evaluation 모듈 사용
        evaluation_data = convert_to_api_format(df, filename, session['user_id'])

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': evaluation_data
        })

    except Exception as e:
        print(f"상태평가 데이터 생성 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'상태평가 데이터 생성 중 오류가 발생했습니다: {str(e)}'}), 500


def get_damage_condition_text(quantity):
    """손상물량에 따른 상태 텍스트 반환"""
    if quantity == 0:
        return '-'
    elif quantity < 5:
        return '소요'
    elif quantity < 10:
        return '중요'
    else:
        return '심각'


def convert_to_api_format(df, filename, user_id):
    """개선된 condition_evaluation 모듈의 결과를 API 형식으로 변환"""
    print("API 변환 시작...")

    # span_damage 테이블에서 inspection_area 데이터 조회
    inspection_area_map = {}  # {span_id: {component_type: inspection_area}}
    bridge_info = {}  # 부재 타입 정보
    try:
        print(f"[DEBUG] Querying span_damage table for filename={filename}, user_id={user_id} (type: {type(user_id)})")
        conn = get_db_connection()
        cur = conn.cursor()
        # user_id를 문자열로 변환
        cur.execute('''
            SELECT span_id, type, inspection_area
            FROM span_damage
            WHERE filename = %s AND user_id = %s
        ''', (filename, str(user_id)))
        print("[DEBUG] Query executed, fetching results...")
        rows = cur.fetchall()
        print(f"[DEBUG] Fetched {len(rows)} rows from span_damage table")

        # 부재 선택 데이터 조회 (bridge_info 가져오기)
        cur.execute('''
            SELECT bridge_info
            FROM component_selection
            WHERE file_id = %s
        ''', (filename,))
        component_selection_row = cur.fetchone()
        if component_selection_row and component_selection_row[0]:
            bridge_info = json.loads(component_selection_row[0])
            print(f"[DEBUG] Loaded bridge_info: {bridge_info}")

        cur.close()
        conn.close()
        print("[DEBUG] Database connection closed")

        # inspection_area 매핑 생성
        for span_id, component_type, inspection_area in rows:
            if span_id not in inspection_area_map:
                inspection_area_map[span_id] = {}
            # 가장 큰 inspection_area 값을 사용 (여러 손상이 있을 경우)
            if component_type not in inspection_area_map[span_id] or inspection_area > inspection_area_map[span_id][component_type]:
                inspection_area_map[span_id][component_type] = inspection_area

        print(f"Loaded inspection_area data from span_damage table: {inspection_area_map}")
    except Exception as e:
        print(f"Warning: Failed to load inspection_area from span_damage table: {e}")
        inspection_area_map = {}

    # 부재별 상태평가 데이터 생성 (신축이음 추가)
    component_filters =  get_meta(1000001)  # 부재별 필터 목록

    api_data = {
        'slab': [],
        'girder': [],
        'crossbeam': [],
        'abutment': [],
        'pier': [],
        'foundation': [],
        'bearing': [],
        'expansionJoint': [],
        'pavement': [],
        'drainage': [],
        'railing': []
    }

    if '부재위치' in df.columns:
        df['정규화부재명'] = df.apply(lambda row: normalize_component_source(row['부재명'], row['부재위치']), axis=1)
    else:
        df['정규화부재명'] = df['부재명'].apply(normalize_component_source)

    conn = get_db_connection()
    cur = conn.cursor()

    # '정규화부재명' 컬럼이 존재하는 경우만 매핑 수행
    if '정규화부재명' in df.columns:
        cur.execute("SELECT TRIM(keyword), source FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s ORDER BY LENGTH(TRIM(keyword)) DESC", ('1000001',))
        rows = cur.fetchall()
        for row in rows:
            keyword = row[0]
            source = row[1]
            df.loc[df['정규화부재명'].str.contains(source, na=False), '부재명'] = keyword
    cur.close()
    conn.close()


    #df['부재명'] = df.apply(update_component_name, axis=1)

    # 전체 부재 데이터를 미리 생성하여 모든 부재에 접근 가능하도록 함
    all_evaluation_results = {}
    for filter_name in component_filters:
        try:
            print(f"Pre-processing {filter_name}...")
            evaluation_result = generate_condition_evaluation_pivot(df, filter_name)
            all_evaluation_results[filter_name] = evaluation_result
        except Exception as e:
            print(f"Component {filter_name} pre-processing error: {e}")
            import traceback
            traceback.print_exc()
            continue

    #print_bearing_positions_table(all_evaluation_results)
    # 각 부재별로 상태평가 데이터 생성
    for filter_name in component_filters:
        try:
            print(f"Processing {filter_name}...")
            evaluation_result = all_evaluation_results.get(filter_name, {})
            if filter_name== '교량받침':
                print(f"Processing bearing positions for {filter_name}...")

            for component_name, component_data in evaluation_result.items():
                print(f"  Component: {component_name}")

                # 부재명을 API 키로 변환
                api_key = convert_component_name_to_key(component_name)
                if api_key:
                    print(f"    API Key: {api_key}")

                    # 위치별 데이터를 API 형식으로 변환
                    for position, pos_data in component_data['positions'].items():
                        print(f"      Position: {position}")

                        # 원본 손상물량 데이터 추출
                        damage_quantities = pos_data.get('damage_quantities', {})
                        crack_length_1d = pos_data.get('crack_length_1d', 0)
                        crack_length_2d = pos_data.get('crack_length_2d', 0)

                        # 기본 span_data 구조
                        span_data = {
                            'span_id': position.upper(),  # s1 -> S1
                            'crack_width_1d': pos_data.get('crack_width_1d', 0),
                            'crack_ratio_1d': pos_data.get('crack_ratio_1d', 0),
                            'crack_width_2d': pos_data.get('crack_width_2d'),  # None일 수 있음 (손상물량 없음)
                            'crack_ratio_2d': pos_data.get('crack_ratio_2d', 0),
                            'grade': pos_data.get('condition_grade', 'a').lower(),
                            # 원본 손상물량 정보 추가
                            'original_crack_length_1d': crack_length_1d,
                            'original_crack_length_2d': crack_length_2d,
                            'original_damage_quantities': damage_quantities
                        }

                        # 부재에 따라 추가 데이터 처리
                        if api_key == 'slab':
                            # 부재 타입 결정: 1순위 bridge_info, 2순위 부재명 분석
                            slab_type = bridge_info.get('slabType', '').upper()

                            # bridge_info에 slabType이 있으면 그것을 최우선으로 사용
                            if slab_type == 'STEEL':
                                is_steel_slab = True
                            elif slab_type in ['RC', 'PSC']:
                                is_steel_slab = False
                            else:
                                # bridge_info가 없거나 값을 모르면 부재명으로 판단
                                has_concrete_indicators = any(keyword in component_name.upper() for keyword in ['콘크리트', 'RC', 'PSC', 'PS'])
                                has_steel_indicators = '강' in component_name or any('강' in damage.get('original_desc', '') for damage in pos_data.get('damages', []))
                                is_steel_slab = not has_concrete_indicators and has_steel_indicators

                            print(f"        Slab classification - Component: {component_name}")
                            print(f"          Bridge info slabType: {slab_type}, Is steel slab: {is_steel_slab}")

                            if is_steel_slab:
                                # 강 바닥판의 경우 - 강거더와 동일한 처리 로직 사용
                                print(f"        Processing steel slab damages for {position}:")

                                # 모재 및 연결부 손상 데이터 수집
                                component_crack_damages = []  # 부재 균열
                                deformation_fracture_damages = []  # 변형, 파단
                                bolt_loosening_damages = []  # 연결 볼트 이완, 탈락
                                weld_defect_damages = []  # 용접연결부 결함
                                surface_deterioration_area = 0  # 표면열화 면적

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                # 손상 데이터를 반복하여 강 바닥판 관련 손상 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {damage_quantity}")

                                    if damage_quantity > 0:
                                        # 표면열화 (도장, 부식 관련 - 우선순위 높음)
                                        if any(keyword in original_desc for keyword in ['도장', '부식', '녹', 'rust', 'corrosion']):
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration: {damage_quantity}")

                                        # 부재 균열 (균열 관련)
                                        elif '균열' in damage_type or '균열' in original_desc or 'crack' in original_desc:
                                            component_crack_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to component_crack: {original_desc}")

                                        # 변형, 파단 (변형, 파단, 굴곡, 좌굴 등)
                                        elif any(keyword in original_desc for keyword in ['변형', '파단', '굴곡', '좌굴', '처짐', 'deformation']):
                                            deformation_fracture_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to deformation_fracture: {original_desc}")

                                        # 연결 볼트 이완, 탈락 (볼트, 너트, 앵커 관련 - 부식 제외)
                                        elif any(keyword in original_desc for keyword in ['볼트', '너트', '앵커', 'bolt', 'nut', 'anchor']) and not any(corr_keyword in original_desc for corr_keyword in ['부식', '녹', '도장']):
                                            bolt_loosening_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to bolt_loosening: {original_desc}")

                                        # 용접연결부 결함 (용접 관련)
                                        elif any(keyword in original_desc for keyword in ['용접', '결함', 'weld']):
                                            weld_defect_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to weld_defect: {original_desc}")

                                        # 기타 손상들은 표면열화로 분류
                                        else:
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration (other): {damage_quantity}")

                                # 표면열화 면적율 계산

                                surface_deterioration_ratio = (surface_deterioration_area / inspection_area) * 100 if surface_deterioration_area > 0 else 0

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    # 모재 및 연결부 손상
                                    'component_crack': ', '.join(list(set(component_crack_damages))) if component_crack_damages else '-',
                                    'deformation_fracture': ', '.join(list(set(deformation_fracture_damages))) if deformation_fracture_damages else '-',
                                    'bolt_loosening': ', '.join(list(set(bolt_loosening_damages))) if bolt_loosening_damages else '-',
                                    'weld_defect': ', '.join(list(set(weld_defect_damages))) if weld_defect_damages else '-',
                                    # 표면열화
                                    'surface_deterioration_ratio': surface_deterioration_ratio,
                                    # 원본 손상물량 추가
                                    'original_surface_deterioration_area': surface_deterioration_area,
                                    'component_crack_damages': component_crack_damages,
                                    'deformation_fracture_damages': deformation_fracture_damages,
                                    'bolt_loosening_damages': bolt_loosening_damages,
                                    'weld_defect_damages': weld_defect_damages
                                })

                                print(f"        Steel slab result - Crack: {len(component_crack_damages)}, Deformation: {len(deformation_fracture_damages)}, Bolt: {len(bolt_loosening_damages)}, Weld: {len(weld_defect_damages)}, Surface: {surface_deterioration_ratio:.2f}%")

                            else:
                                # 콘크리트 바닥판의 경우 - 우선순위 기반 분류
                                print(f"        Concrete slab damage_quantities: {damage_quantities}")

                                # 손상 데이터를 우선순위에 따라 분류
                                rebar_corrosion_quantity = 0
                                leak_quantity = 0
                                surface_damage_quantity = 0

                                # 실제 손상 데이터에서 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    if damage_quantity > 0:
                                        # 균열 데이터는 표면손상에서 제외
                                        if '균열' in original_desc or '균열' in damage_type:
                                            print(f"            -> 균열 데이터는 표면손상에서 제외: {original_desc}")

                                        # 1순위: 철근부식 (철근이라는 글자가 들어간 데이터, 잡철근 제외)
                                        elif ('철근' in original_desc and '잡철근' not in original_desc) or '철근부식' in original_desc or '철근노출' in original_desc:
                                            rebar_corrosion_quantity += damage_quantity
                                            print(f"            -> 철근부식으로 분류: {original_desc} ({damage_quantity})")

                                        # 2순위: 누수/백태 (누수, 백태라는 글자가 들어간 데이터)
                                        elif '누수' in original_desc or '백태' in original_desc:
                                            leak_quantity += damage_quantity
                                            print(f"            -> 누수/백태로 분류: {original_desc} ({damage_quantity})")

                                        # 3순위: 표면손상 (누수흔적, 누수오염 등 흔적, 오염 포함)
                                        elif '흔적' in original_desc or '오염' in original_desc or '표면손상' in original_desc:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류: {original_desc} ({damage_quantity})")

                                        # 기타 모든 데이터는 표면손상으로 분류
                                        else:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류 (기타): {original_desc} ({damage_quantity})")

                                print(f"        분류 결과 - 철근부식: {rebar_corrosion_quantity}, 누수/백태: {leak_quantity}, 표면손상: {surface_damage_quantity}")

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                print(f"        Concrete slab processing - Position: {position}, Leak: {leak_quantity}, Surface: {surface_damage_quantity}, Rebar: {rebar_corrosion_quantity}")

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    'leak_ratio': (leak_quantity / inspection_area) * 100 if leak_quantity > 0 else 0,
                                    'surface_damage_ratio': (surface_damage_quantity / inspection_area) * 100 if surface_damage_quantity > 0 else 0,
                                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / inspection_area) * 100 if rebar_corrosion_quantity > 0 else 0,
                                    # 원본 손상물량 추가
                                    'original_leak_quantity': leak_quantity,
                                    'original_surface_damage_quantity': surface_damage_quantity,
                                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                                })

                        elif api_key == 'girder':
                            # 거더 타입 결정: 1순위 bridge_info, 2순위 부재명 분석
                            girder_type = bridge_info.get('girderType', '').upper()

                            # bridge_info에 girderType이 있으면 그것을 최우선으로 사용
                            if girder_type == 'STEEL':
                                is_steel_girder = True
                            elif girder_type in ['RC', 'PSC']:
                                is_steel_girder = False
                            else:
                                # bridge_info가 없거나 값을 모르면 부재명으로 판단
                                has_concrete_indicators = any(keyword in component_name.upper() for keyword in ['콘크리트', 'RC', 'PSC', 'PS'])
                                has_steel_indicators = '강' in component_name or any('강' in damage.get('original_desc', '') for damage in pos_data.get('damages', []))
                                is_steel_girder = not has_concrete_indicators and has_steel_indicators

                            print(f"        Girder classification - Component: {component_name}")
                            print(f"          Bridge info girderType: {girder_type}, Is steel girder: {is_steel_girder}")

                            if is_steel_girder:
                                # 강거더의 경우 - 표 1.12 강거더 상태평가기준에 따른 처리
                                print(f"        Processing steel girder damages for {position}:")

                                # 모재 및 연결부 손상 데이터 수집
                                component_crack_damages = []  # 부재 균열
                                deformation_fracture_damages = []  # 변형, 파단
                                bolt_loosening_damages = []  # 연결 볼트 이완, 탈락
                                weld_defect_damages = []  # 용접연결부 결함
                                surface_deterioration_area = 0  # 표면열화 면적

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                # 손상 데이터를 반복하여 강거더 관련 손상 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {damage_quantity}")

                                    if damage_quantity > 0:
                                        # 표면열화 (도장, 부식 관련 - 우선순위 높음) 백태 철근노출 추가
                                        if any(keyword in original_desc for keyword in ['도장', '부식', '백태', '철근노출', '녹', 'rust', 'corrosion']):
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration: {damage_quantity}")

                                        # 부재 균열 (균열 관련)
                                        elif '균열' in damage_type or '균열' in original_desc or 'crack' in original_desc:
                                            component_crack_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to component_crack: {original_desc}")

                                        # 변형, 파단 (변형, 파단, 굴곡, 좌굴 등)
                                        elif any(keyword in original_desc for keyword in ['변형', '파단', '굴곡', '좌굴', '처짐', 'deformation']):
                                            deformation_fracture_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to deformation_fracture: {original_desc}")

                                        # 연결 볼트 이완, 탈락 (볼트, 너트, 앵커 관련 - 부식 제외)
                                        elif any(keyword in original_desc for keyword in ['볼트', '너트', '앵커', 'bolt', 'nut', 'anchor']) and not any(corr_keyword in original_desc for corr_keyword in ['부식', '녹', '도장']):
                                            bolt_loosening_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to bolt_loosening: {original_desc}")

                                        # 용접연결부 결함 (용접 관련)
                                        elif any(keyword in original_desc for keyword in ['용접', '결함', 'weld']):
                                            weld_defect_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to weld_defect: {original_desc}")

                                        # 기타 손상들은 표면열화로 분류
                                        else:
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration (other): {damage_quantity}")

                                # 표면열화 면적율 계산
                                surface_deterioration_ratio = (surface_deterioration_area / inspection_area) * 100 if surface_deterioration_area > 0 else 0

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    # 모재 및 연결부 손상
                                    'component_crack': ', '.join(list(set(component_crack_damages))) if component_crack_damages else '-',
                                    'deformation_fracture': ', '.join(list(set(deformation_fracture_damages))) if deformation_fracture_damages else '-',
                                    'bolt_loosening': ', '.join(list(set(bolt_loosening_damages))) if bolt_loosening_damages else '-',
                                    'weld_defect': ', '.join(list(set(weld_defect_damages))) if weld_defect_damages else '-',
                                    # 표면열화
                                    'surface_deterioration_ratio': surface_deterioration_ratio,
                                    # 원본 손상물량 추가
                                    'original_surface_deterioration_area': surface_deterioration_area,
                                    'component_crack_damages': component_crack_damages,
                                    'deformation_fracture_damages': deformation_fracture_damages,
                                    'bolt_loosening_damages': bolt_loosening_damages,
                                    'weld_defect_damages': weld_defect_damages
                                })

                                print(f"        Steel girder result - Crack: {len(component_crack_damages)}, Deformation: {len(deformation_fracture_damages)}, Bolt: {len(bolt_loosening_damages)}, Weld: {len(weld_defect_damages)}, Surface: {surface_deterioration_ratio:.2f}%")

                            else:
                                # 콘크리트 거더의 경우 - 우선순위 기반 분류
                                print(f"        Concrete girder damage_quantities: {damage_quantities}")

                                # 손상 데이터를 우선순위에 따라 분류
                                rebar_corrosion_quantity = 0
                                leak_quantity = 0
                                surface_damage_quantity = 0

                                # 실제 손상 데이터에서 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    if damage_quantity > 0:
                                        # 균열 데이터는 표면손상에서 제외
                                        if '균열' in original_desc or '균열' in damage_type:
                                            print(f"            -> 균열 데이터는 표면손상에서 제외: {original_desc}")

                                        # 1순위: 철근부식 (철근이라는 글자가 들어간 데이터, 잡철근 제외)
                                        elif ('철근' in original_desc and '잡철근' not in original_desc) or '철근부식' in original_desc or '철근노출' in original_desc:
                                            rebar_corrosion_quantity += damage_quantity
                                            print(f"            -> 철근부식으로 분류: {original_desc} ({damage_quantity})")

                                        # 2순위: 누수/백태 (누수, 백태라는 글자가 들어간 데이터)
                                        elif '누수' in original_desc or '백태' in original_desc:
                                            leak_quantity += damage_quantity
                                            print(f"            -> 누수/백태로 분류: {original_desc} ({damage_quantity})")

                                        # 3순위: 표면손상 (누수흔적, 누수오염 등 흔적, 오염 포함)
                                        elif '흔적' in original_desc or '오염' in original_desc or '표면손상' in original_desc:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류: {original_desc} ({damage_quantity})")

                                        # 기타 모든 데이터는 표면손상으로 분류
                                        else:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류 (기타): {original_desc} ({damage_quantity})")

                                print(f"        분류 결과 - 철근부식: {rebar_corrosion_quantity}, 누수/백태: {leak_quantity}, 표면손상: {surface_damage_quantity}")

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                print(f"        Concrete girder processing - Position: {position}, Leak: {leak_quantity}, Surface: {surface_damage_quantity}, Rebar: {rebar_corrosion_quantity}")

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    'leak_ratio': (leak_quantity / inspection_area) * 100 if leak_quantity > 0 else 0,
                                    'surface_damage_ratio': (surface_damage_quantity / inspection_area) * 100 if surface_damage_quantity > 0 else 0,
                                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / inspection_area) * 100 if rebar_corrosion_quantity > 0 else 0,
                                    # 원본 손상물량 추가
                                    'original_leak_quantity': leak_quantity,
                                    'original_surface_damage_quantity': surface_damage_quantity,
                                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                                })

                        elif api_key == 'crossbeam':
                            # 가로보 타입 결정: 1순위 bridge_info, 2순위 부재명 분석
                            crossbeam_type = bridge_info.get('crossbeamType', '').upper()

                            # bridge_info에 crossbeamType이 있으면 그것을 최우선으로 사용
                            if crossbeam_type == 'STEEL':
                                is_steel_crossbeam = True
                            elif crossbeam_type in ['RC', 'PSC']:
                                is_steel_crossbeam = False
                            else:
                                # bridge_info가 없거나 값을 모르면 부재명으로 판단
                                has_concrete_indicators = any(keyword in component_name.upper() for keyword in ['콘크리트', 'RC', 'PSC', 'PS'])
                                has_steel_indicators = '강' in component_name or any('강' in damage.get('original_desc', '') for damage in pos_data.get('damages', []))
                                is_steel_crossbeam = not has_concrete_indicators and has_steel_indicators

                            print(f"        Crossbeam classification - Component: {component_name}")
                            print(f"          Bridge info crossbeamType: {crossbeam_type}, Is steel crossbeam: {is_steel_crossbeam}")

                            if is_steel_crossbeam:
                                # 강 가로보의 경우 - 표 1.17 강 가로보·세로보 상태평가기준에 따른 처리
                                print(f"        Processing steel crossbeam damages for {position}:")

                                # 모재 및 연결부 손상 데이터 수집
                                component_crack_damages = []  # 부재 균열
                                deformation_fracture_damages = []  # 변형, 파단
                                bolt_loosening_damages = []  # 연결 볼트 이완, 탈락
                                weld_defect_damages = []  # 용접연결부 결함
                                surface_deterioration_area = 0  # 표면열화 면적

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                # 손상 데이터를 반복하여 강 가로보 관련 손상 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {damage_quantity}")

                                    if damage_quantity > 0:
                                        # 표면열화 (도장, 부식 관련 - 우선순위 높음)
                                        if any(keyword in original_desc for keyword in ['도장', '부식', '녹', 'rust', 'corrosion']):
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration: {damage_quantity}")

                                        # 부재 균열 (균열 관련)
                                        elif '균열' in damage_type or '균열' in original_desc or 'crack' in original_desc:
                                            component_crack_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to component_crack: {original_desc}")

                                        # 변형, 파단 (변형, 파단, 굴곡, 좌굴 등)
                                        elif any(keyword in original_desc for keyword in ['변형', '파단', '굴곡', '좌굴', '처짐', 'deformation']):
                                            deformation_fracture_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to deformation_fracture: {original_desc}")

                                        # 연결 볼트 이완, 탈락 (볼트, 너트, 앵커 관련 - 부식 제외)
                                        elif any(keyword in original_desc for keyword in ['볼트', '너트', '앵커', 'bolt', 'nut', 'anchor']) and not any(corr_keyword in original_desc for corr_keyword in ['부식', '녹', '도장']):
                                            bolt_loosening_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to bolt_loosening: {original_desc}")

                                        # 용접연결부 결함 (용접 관련)
                                        elif any(keyword in original_desc for keyword in ['용접', '결함', 'weld']):
                                            weld_defect_damages.append(damage.get('original_desc', ''))
                                            print(f"            -> Added to weld_defect: {original_desc}")

                                        # 기타 손상들은 표면열화로 분류
                                        else:
                                            surface_deterioration_area += damage_quantity
                                            print(f"            -> Added to surface_deterioration (other): {damage_quantity}")

                                # 표면열화 면적율 계산
                                surface_deterioration_ratio = (surface_deterioration_area / inspection_area) * 100 if surface_deterioration_area > 0 else 0

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    # 모재 및 연결부 손상
                                    'component_crack': ', '.join(list(set(component_crack_damages))) if component_crack_damages else '-',
                                    'deformation_fracture': ', '.join(list(set(deformation_fracture_damages))) if deformation_fracture_damages else '-',
                                    'bolt_loosening': ', '.join(list(set(bolt_loosening_damages))) if bolt_loosening_damages else '-',
                                    'weld_defect': ', '.join(list(set(weld_defect_damages))) if weld_defect_damages else '-',
                                    # 표면열화
                                    'surface_deterioration_ratio': surface_deterioration_ratio,
                                    # 원본 손상물량 추가
                                    'original_surface_deterioration_area': surface_deterioration_area,
                                    'component_crack_damages': component_crack_damages,
                                    'deformation_fracture_damages': deformation_fracture_damages,
                                    'bolt_loosening_damages': bolt_loosening_damages,
                                    'weld_defect_damages': weld_defect_damages
                                })

                                print(f"        Steel crossbeam result - Crack: {len(component_crack_damages)}, Deformation: {len(deformation_fracture_damages)}, Bolt: {len(bolt_loosening_damages)}, Weld: {len(weld_defect_damages)}, Surface: {surface_deterioration_ratio:.2f}%")

                            else:
                                # 콘크리트 가로보의 경우 - 우선순위 기반 분류
                                print(f"        Concrete crossbeam damage_quantities: {damage_quantities}")

                                # 손상 데이터를 우선순위에 따라 분류
                                rebar_corrosion_quantity = 0
                                leak_quantity = 0
                                surface_damage_quantity = 0

                                # 실제 손상 데이터에서 분류
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    damage_quantity = damage.get('quantity', 0)

                                    if damage_quantity > 0:
                                        # 균열 데이터는 표면손상에서 제외
                                        if '균열' in original_desc or '균열' in damage_type:
                                            print(f"            -> 균열 데이터는 표면손상에서 제외: {original_desc}")

                                        # 1순위: 철근부식 (철근이라는 글자가 들어간 데이터, 잡철근 제외)
                                        elif ('철근' in original_desc and '잡철근' not in original_desc) or '철근부식' in original_desc or '철근노출' in original_desc:
                                            rebar_corrosion_quantity += damage_quantity
                                            print(f"            -> 철근부식으로 분류: {original_desc} ({damage_quantity})")

                                        # 2순위: 누수/백태 (누수, 백태라는 글자가 들어간 데이터)
                                        elif '누수' in original_desc or '백태' in original_desc:
                                            leak_quantity += damage_quantity
                                            print(f"            -> 누수/백태로 분류: {original_desc} ({damage_quantity})")

                                        # 3순위: 표면손상 (누수흔적, 누수오염 등 흔적, 오염 포함)
                                        elif '흔적' in original_desc or '오염' in original_desc or '표면손상' in original_desc:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류: {original_desc} ({damage_quantity})")

                                        # 기타 모든 데이터는 표면손상으로 분류
                                        else:
                                            surface_damage_quantity += damage_quantity
                                            print(f"            -> 표면손상으로 분류 (기타): {original_desc} ({damage_quantity})")

                                print(f"        분류 결과 - 철근부식: {rebar_corrosion_quantity}, 누수/백태: {leak_quantity}, 표면손상: {surface_damage_quantity}")

                                # span_damage 테이블에서 inspection_area 가져오기
                                inspection_area = 100  # 기본값
                                # span_id_key = position.upper()
                                # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                                #     inspection_area = inspection_area_map[span_id_key][api_key]
                                #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                                print(f"        Concrete crossbeam processing - Position: {position}, Leak: {leak_quantity}, Surface: {surface_damage_quantity}, Rebar: {rebar_corrosion_quantity}")

                                span_data.update({
                                    'inspection_area': inspection_area,
                                    'leak_ratio': (leak_quantity / inspection_area) * 100 if leak_quantity > 0 else 0,
                                    'surface_damage_ratio': (surface_damage_quantity / inspection_area) * 100 if surface_damage_quantity > 0 else 0,
                                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / inspection_area) * 100 if rebar_corrosion_quantity > 0 else 0,
                                    # 원본 손상물량 추가
                                    'original_leak_quantity': leak_quantity,
                                    'original_surface_damage_quantity': surface_damage_quantity,
                                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                                })

                        elif api_key in ['abutment', 'pier']:
                            # 교대, 교각의 경우 - 우선순위 기반 분류
                            print(f"        {api_key} damage_quantities: {damage_quantities}")

                            # 손상 데이터를 우선순위에 따라 분류
                            rebar_corrosion_quantity = 0
                            surface_damage_quantity = 0

                            # 실제 손상 데이터에서 분류
                            for damage in pos_data.get('damages', []):
                                original_desc = damage.get('original_desc', '').lower()
                                damage_type = damage.get('type', '')
                                damage_quantity = damage.get('quantity', 0)

                                if damage_quantity > 0:
                                    # 균열 데이터는 표면손상에서 제외
                                    if '균열' in original_desc or '균열' in damage_type:
                                        print(f"            -> 균열 데이터는 표면손상에서 제외: {original_desc}")

                                    # 1순위: 철근부식 (철근이라는 글자가 들어간 데이터, 잡철근 제외)
                                    elif ('철근' in original_desc and '잡철근' not in original_desc) or '철근부식' in original_desc or '철근노출' in original_desc:
                                        rebar_corrosion_quantity += damage_quantity
                                        print(f"            -> 철근부식으로 분류: {original_desc} ({damage_quantity})")

                                    # 교대/교각의 경우 누수/백태 등은 표면손상으로 분류
                                    else:
                                        surface_damage_quantity += damage_quantity
                                        print(f"            -> 표면손상으로 분류: {original_desc} ({damage_quantity})")

                            print(f"        분류 결과 - 철근부식: {rebar_corrosion_quantity}, 표면손상: {surface_damage_quantity}")

                            # 교대/교각의 경우 표면손상은 모든 데이터가 포함됨
                            total_surface_damage = surface_damage_quantity

                            # span_damage 테이블에서 inspection_area 가져오기
                            inspection_area = 100  # 기본값
                            # span_id_key = position.upper()
                            # if span_id_key in inspection_area_map and api_key in inspection_area_map[span_id_key]:
                            #     inspection_area = inspection_area_map[span_id_key][api_key]
                            #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                            span_data.update({
                                'inspection_area': inspection_area,
                                'crack_width': max(pos_data.get('crack_width_1d', 0), pos_data.get('crack_width_2d', 0)),
                                'deformation': '-',  # 변형 상태 (별도 로직 필요)
                                'surface_damage_ratio': (total_surface_damage / inspection_area) * 100,
                                'rebar_corrosion_ratio': (rebar_corrosion_quantity / inspection_area) * 100,
                                # 원본 손상물량 추가
                                'original_surface_damage_quantity': surface_damage_quantity,
                                'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                            })

                        elif api_key == 'bearing':
                            # 교량받침의 경우 - 본체와 콘크리트 상태 평가
                            # 본체 관련 손상 수집 (부식, 편기, 도장, 볼트, 앵커, 너트, 전단키 등)
                            body_condition_damages = []
                            concrete_crack_width = 0
                            concrete_section_damages = []

                            print(f"        Processing bearing damages for {position}:")

                            # 손상 데이터를 반복하여 본체와 콘크리트 손상 분류
                            for damage in pos_data.get('damages', []):
                                original_desc = damage.get('original_desc', '')
                                damage_type = damage.get('type', '')
                                damage_quantity = damage.get('quantity', 0)

                                print(f"Damage: {original_desc}, Type: {damage_type}, Quantity: {damage_quantity}")

                                # 본체 관련 손상 (부식, 편기, 도장, 볼트, 앵커, 너트, 전단키 등)

                                corrosion_keywords = get_meta_keywords_by_meta_id(1000006)

                                if any(keyword in original_desc.lower() for keyword in corrosion_keywords):
                                    if original_desc not in body_condition_damages:
                                        body_condition_damages.append(original_desc)
                                        print(f"            -> Added to body_condition: {original_desc}")

                                # 균열 손상 처리 (콘크리트/몰탈 관련 + 일반 균열)
                                elif ('균열' in damage_type.lower() or '균열' in original_desc.lower()):
                                    # 콘크리트/몰탈 관련 균열인지 확인
                                    if any(keyword in original_desc.lower() for keyword in ['콘크리트', '몰탈', '받침콘크리트', '받침몰탈']):
                                        # 콘크리트 균열의 최대 균열폭 계산
                                        crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                        crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                        crack_width = max(crack_width_1d, crack_width_2d)
                                        concrete_crack_width = max(concrete_crack_width, crack_width)
                                        print(f"            -> Concrete crack width: {crack_width} (1d: {crack_width_1d}, 2d: {crack_width_2d})")
                                    # 일반 균열도 콘크리트로 처리
                                    else:
                                        crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                        crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                        crack_width = max(crack_width_1d, crack_width_2d)
                                        concrete_crack_width = max(concrete_crack_width, crack_width)
                                        print(f"            -> General crack width: {crack_width} (1d: {crack_width_1d}, 2d: {crack_width_2d})")

                                # 콘크리트/몰탈 관련 비균열 손상 - 단면손상으로 처리 (철근부식 포함)
                                elif any(keyword in original_desc.lower() for keyword in ['콘크리트', '몰탈', '받침콘크리트', '받침몰탈']) or damage_type in ['단면손상', '철근부식']:
                                    if original_desc not in concrete_section_damages:
                                        if(original_desc not in  concrete_section_damages ):
                                            concrete_section_damages.append(original_desc)
                                        print(f"            -> Added to section_damage: {original_desc}")
                                else:
                                    if(original_desc not in  concrete_section_damages ):
                                        concrete_section_damages.append(original_desc)





                            # 본체 상태 평가
                            if body_condition_damages:
                                body_condition = ', '.join(body_condition_damages)  # 모든 손상내용 표시
                            else:
                                body_condition = '-'

                            # 콘크리트 단면손상 평가 (철근부식 포함)
                            if concrete_section_damages:
                                concrete_damage_text = ', '.join(concrete_section_damages)
                            else:
                                concrete_damage_text = '-'

                            print(f"        Bearing result - Body: {body_condition}, Crack width: {concrete_crack_width}, Section damage: {concrete_damage_text}")

                            span_data.update({
                                'body_condition': body_condition,
                                'crack_width': concrete_crack_width if concrete_crack_width > 0 else 0,
                                'section_damage': concrete_damage_text
                            })

                        elif api_key == 'foundation':
                            # 기초의 경우 - 기초 손상 및 지반 안정성 관련
                            # 비균열 손상 데이터 추출 (단면손상 + 철근부식)
                            damage_condition_quantity = damage_quantities.get('단면손상', 0) + damage_quantities.get('철근부식', 0)

                            # 단면손상 및 철근부식 손상내용명 수집 (중복 제거)
                            damage_condition_descriptions = []
                            for damage in pos_data['damages']:
                                if damage['type'] in ['단면손상', '철근부식']:
                                    desc = damage.get('original_desc', '')
                                    if desc and desc not in damage_condition_descriptions:
                                        damage_condition_descriptions.append(desc)

                            # 손상내용명을 쉼표로 구분하여 연결
                            damage_condition_text = ', '.join(damage_condition_descriptions) if damage_condition_descriptions else '-'

                            span_data.update({
                                'crack_width': max(pos_data.get('crack_width_1d', 0), pos_data.get('crack_width_2d', 0)),
                                'damage_condition': damage_condition_text,  # 실제 손상내용명 (단면손상 + 철근부식 포함)
                                'erosion': '-',  # 세굴 여부 (별도 로직 필요)
                                'settlement': '-',  # 침하 (별도 로직 필요)
                                # 원본 손상물량 추가
                                'original_damage_condition_quantity': damage_condition_quantity,
                                'damage_condition_descriptions': damage_condition_descriptions
                            })

                        elif api_key == 'railing':
                            # 난간 및 연석의 경우 - 강재와 콘크리트 헤더 구분 처리
                            print(f"        Processing railing damages for {position}:")
                            print(f"          Position data: {pos_data}")
                            print(f"          Component name: {component_name}")

                            # 강재 헤더: 도장손상, 부식발생, 연결재 및 단면손상
                            paint_damage_quantity = damage_quantities.get('도장손상', 0)
                            corrosion_quantity = damage_quantities.get('부식', 0)
                            connection_damage_quantity = damage_quantities.get('연결재손상', 0)

                            # 콘크리트 헤더: 균열 최대폭, 표면손상
                            # 1방향과 2방향 균열 모두 균열 최대폭에 들어감
                            crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                            crack_width_2d = pos_data.get('crack_width_2d', 0) or 0

                            # ===== 균열 폭 데이터 수정 시작 =====
                            # 실제 균열 손상이 길이(m) 단위로 저장되어 있을 경우, 균열폭으로 변환
                            crack_length = damage_quantities.get('균열', 0)  # 균열 길이 데이터

                            # 균열폭 추정: 균열이 있으면 기본 0.2mm, 많으면 더 큰 값 적용
                            estimated_crack_width = 0
                            if crack_length > 0:
                                if crack_length >= 10:  # 10m 이상이면 심각한 균열로 간주
                                    estimated_crack_width = 0.5  # 0.5mm
                                elif crack_length >= 5:  # 5m 이상
                                    estimated_crack_width = 0.3  # 0.3mm
                                elif crack_length >= 1:  # 1m 이상
                                    estimated_crack_width = 0.2  # 0.2mm
                                else:
                                    estimated_crack_width = 0.1  # 1m 미만은 0.1mm

                            # 기존 균열폭 데이터와 추정값 중 큰 값 사용
                            max_crack_width = max(crack_width_1d, crack_width_2d, estimated_crack_width)

                            print(f"          균열 길이: {crack_length}m, 추정 균열폭: {estimated_crack_width}mm, 최종 균열폭: {max_crack_width}mm")
                            # ===== 균열 폭 데이터 수정 종료 =====

                            # ===== railing 데이터 중복 처리 시작 =====
                            # 같은 경간의 기존 데이터가 있는지 확인
                            existing_data = None
                            for existing_item in api_data[api_key]:
                                if existing_item['span_id'] == position.upper():
                                    existing_data = existing_item
                                    break

                            # 기존 데이터가 있으면 더 좋은 데이터로 업데이트 또는 병합
                            if existing_data:
                                print(f"          기존 {position} 데이터 발견: 기존 균열폭={existing_data.get('crack_width', 0)}, 새 균열폭={max_crack_width}")

                                # 더 큰 균열폭 사용
                                if max_crack_width > existing_data.get('crack_width', 0):
                                    print(f"          -> 더 큰 균열폭 사용: {max_crack_width}mm")
                                    # 데이터 병합은 나중에 진행
                                    should_update = True
                                else:
                                    print(f"          -> 기존 균열폭 유지: {existing_data.get('crack_width', 0)}mm")
                                    should_update = False
                                    continue  # 다음 데이터로 스킨
                            else:
                                should_update = True
                            # ===== railing 데이터 중복 처리 종료 =====

                            # 표면손상 헤더에는 누수, 백태, 단면손상, 표면손상, 철근부식이 모두 포함
                            surface_damage_quantity = damage_quantities.get('표면손상', 0)
                            leak_quantity = damage_quantities.get('누수', 0)
                            rebar_corrosion_quantity = damage_quantities.get('철근부식', 0)
                            section_damage_quantity = damage_quantities.get('단면손상', 0)

                            # 모든 콘크리트 손상을 표면손상으로 합산
                            total_concrete_surface_damage = (surface_damage_quantity + leak_quantity +
                                                            rebar_corrosion_quantity + section_damage_quantity)

                            # 타입 검증
                            for val_name, val in [('paint_damage', paint_damage_quantity), ('corrosion', corrosion_quantity),
                                                 ('connection_damage', connection_damage_quantity), ('surface_damage', surface_damage_quantity),
                                                 ('leak', leak_quantity), ('rebar_corrosion', rebar_corrosion_quantity), ('section_damage', section_damage_quantity)]:
                                if not isinstance(val, (int, float)):
                                    print(f"Warning: {val_name} is not numeric: {val}, setting to 0")
                                    if val_name == 'paint_damage':
                                        paint_damage_quantity = 0
                                    elif val_name == 'corrosion':
                                        corrosion_quantity = 0
                                    elif val_name == 'connection_damage':
                                        connection_damage_quantity = 0
                                    elif val_name == 'surface_damage':
                                        surface_damage_quantity = 0
                                    elif val_name == 'leak':
                                        leak_quantity = 0
                                    elif val_name == 'rebar_corrosion':
                                        rebar_corrosion_quantity = 0
                                    elif val_name == 'section_damage':
                                        section_damage_quantity = 0

                            # 결과 출력 (디버깅용)
                            print(f"강재 - 도장손상: {paint_damage_quantity}, 부식발생: {corrosion_quantity}, 연결재손상: {connection_damage_quantity}")
                            print(f"콘크리트 - 균열최대폭: {max_crack_width}, 표면손상 합계: {total_concrete_surface_damage}")
                            print(f"  (표면손상: {surface_damage_quantity}, 누수: {leak_quantity}, 철근부식: {rebar_corrosion_quantity}, 단면손상: {section_damage_quantity})")

                            # 기본 길이
                            length = 100

                            span_data.update({
                                'length': length,
                                # 강재 헤더 데이터 (JavaScript 필드명에 맞춰 수정)
                                'paint_damage': (paint_damage_quantity / length) * 100 if paint_damage_quantity > 0 else 0,
                                'corrosion_ratio': (corrosion_quantity / length) * 100 if corrosion_quantity > 0 else 0,
                                'damage_ratio': (connection_damage_quantity / length) * 100 if connection_damage_quantity > 0 else 0,
                                # 콘크리트 헤더 데이터
                                'crack_width': max_crack_width,  # 1방향과 2방향 균열 최대폭
                                'surface_damage_ratio': (total_concrete_surface_damage / length) * 100 if total_concrete_surface_damage > 0 else 0,
                                'total_damage_quantity': total_concrete_surface_damage,  # JavaScript에서 기대하는 필드 추가
                                'rebar_corrosion_ratio': (rebar_corrosion_quantity / length) * 100 if rebar_corrosion_quantity > 0 else 0,  # 철근부식 비율 추가
                                # 원본 손상물량 추가 (JavaScript 필드명에 맞춰 수정)
                                'original_paint_damage': paint_damage_quantity,
                                'original_corrosion_ratio': corrosion_quantity,
                                'original_damage_ratio': connection_damage_quantity,
                                'original_surface_damage_quantity': surface_damage_quantity,
                                'original_leak_quantity': leak_quantity,
                                'original_rebar_corrosion_quantity': rebar_corrosion_quantity,
                                'original_section_damage_quantity': section_damage_quantity,
                                'original_total_concrete_surface_damage': total_concrete_surface_damage
                            })

                            print(f"        Railing result - 강재(도장:{paint_damage_quantity}, 부식:{corrosion_quantity}, 연결재:{connection_damage_quantity}), 콘크리트(균열폭:{max_crack_width}, 표면손상:{total_concrete_surface_damage})")

                            # ===== railing 데이터 업데이트 또는 추가 =====
                            if existing_data:
                                # 기존 데이터 업데이트
                                if should_update:
                                    print(f"          -> 기존 {position} 데이터 업데이트")
                                    # 더 좋은 데이터로 업데이트
                                    existing_data.update({
                                        'length': length,
                                        'paint_damage': max((paint_damage_quantity / length) * 100 if paint_damage_quantity > 0 else 0, existing_data.get('paint_damage', 0)),
                                        'corrosion_ratio': max((corrosion_quantity / length) * 100 if corrosion_quantity > 0 else 0, existing_data.get('corrosion_ratio', 0)),
                                        'damage_ratio': max((connection_damage_quantity / length) * 100 if connection_damage_quantity > 0 else 0, existing_data.get('damage_ratio', 0)),
                                        'crack_width': max_crack_width,  # 항상 더 큰 값 사용
                                        'surface_damage_ratio': max((total_concrete_surface_damage / length) * 100 if total_concrete_surface_damage > 0 else 0, existing_data.get('surface_damage_ratio', 0)),
                                        'total_damage_quantity': max(total_concrete_surface_damage, existing_data.get('total_damage_quantity', 0)),
                                        'rebar_corrosion_ratio': max((rebar_corrosion_quantity / length) * 100 if rebar_corrosion_quantity > 0 else 0, existing_data.get('rebar_corrosion_ratio', 0)),
                                        # 원본 손상물량도 더 큰 값으로 업데이트
                                        'original_paint_damage': max(paint_damage_quantity, existing_data.get('original_paint_damage', 0)),
                                        'original_corrosion_ratio': max(corrosion_quantity, existing_data.get('original_corrosion_ratio', 0)),
                                        'original_damage_ratio': max(connection_damage_quantity, existing_data.get('original_damage_ratio', 0))
                                    })
                                # 기존 데이터가 더 좋으면 스킨
                                continue
                            else:
                                # 새 데이터 추가
                                if should_update:
                                    span_data.update({
                                        'length': length,
                                        'paint_damage': (paint_damage_quantity / length) * 100 if paint_damage_quantity > 0 else 0,
                                        'corrosion_ratio': (corrosion_quantity / length) * 100 if corrosion_quantity > 0 else 0,
                                        'damage_ratio': (connection_damage_quantity / length) * 100 if connection_damage_quantity > 0 else 0,
                                        'crack_width': max_crack_width,
                                        'surface_damage_ratio': (total_concrete_surface_damage / length) * 100 if total_concrete_surface_damage > 0 else 0,
                                        'total_damage_quantity': total_concrete_surface_damage,
                                        'rebar_corrosion_ratio': (rebar_corrosion_quantity / length) * 100 if rebar_corrosion_quantity > 0 else 0,
                                        'original_paint_damage': paint_damage_quantity,
                                        'original_corrosion_ratio': corrosion_quantity,
                                        'original_damage_ratio': connection_damage_quantity,
                                        'original_surface_damage_quantity': surface_damage_quantity,
                                        'original_leak_quantity': leak_quantity,
                                        'original_rebar_corrosion_quantity': rebar_corrosion_quantity,
                                        'original_section_damage_quantity': section_damage_quantity,
                                        'original_total_concrete_surface_damage': total_concrete_surface_damage
                                    })

                                    print(f"          -> 새 {position} 데이터 추가: crack_width={max_crack_width}mm")
                            # ===== railing 데이터 업데이트/추가 완료 =====)

                        elif api_key == 'expansionJoint':
                            # 신축이음의 경우 - 본체와 후타재 데이터 처리
                            print(f"        Processing expansion joint damages for {position}:")
                            print(f"          Position data: {pos_data}")

                            # 모든 손상 데이터 확인
                            body_damages = []
                            footer_crack_width = 0
                            footer_section_damages = []

                            # 신축이음의 경우 실제 데이터가 없으면 빈 데이터로 처리
                            if not pos_data.get('damages'):
                                print(f"          No damage data for position {position}, leaving empty")
                                # 실제 데이터가 없으면 빈 데이터로 둘어 클라이언트에서 처리하도록 하기
                                pass
                            else:
                                for damage in pos_data.get('damages', []):
                                    original_desc = damage.get('original_desc', '').lower()
                                    damage_type = damage.get('type', '')
                                    quantity = damage.get('quantity', 0)

                                    print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {quantity}")

                                    # 본체 관련 손상 처리 (유간, 이물질, 본체, 부식, 고무재, 이음부, 볼트 등)
                                    if (any(keyword in original_desc for keyword in ['유간', '이물질', '본체', '부식', '고무재', '이음부', '볼트']) or
                                        '신축이음' in original_desc or
                                        '이음장치' in original_desc) and quantity > 0:

                                        # 차수판/차수 관련 손상은 후타재 단면손상으로 분류
                                        if '차수판' in original_desc or '차수' in original_desc:
                                            if original_desc not in footer_section_damages:
                                                footer_section_damages.append(original_desc)
                                                print(f"            -> Added to footer_section_damages (waterstop): {original_desc}")
                                        else:
                                            # 실제 손상내용명을 그대로 추가
                                            if original_desc not in body_damages:
                                                body_damages.append(original_desc)
                                                print(f"            -> Added to body_damages: {original_desc}")

                                    # 후타재 관련 손상 처리 - 균열과 단면손상 분리
                                    elif '후타재' in original_desc and quantity > 0:
                                        if '균열' in original_desc or '균열' in damage_type:
                                            # 후타재 균열의 최대 균열폭 계산
                                            crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                            crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                            crack_width = max(crack_width_1d, crack_width_2d)
                                            footer_crack_width = max(footer_crack_width, crack_width)
                                            print(f"            -> Footer crack width: {crack_width} (1d: {crack_width_1d}, 2d: {crack_width_2d})")
                                        else:
                                            footer_section_damages.append(original_desc)

                                    # 콘크리트 관련 손상을 후타재로 처리
                                    elif ('콘크리트' in original_desc or '몰탈' in original_desc) and quantity > 0:
                                        if '균열' in original_desc or '균열' in damage_type:
                                            # 콘크리트 균열의 최대 균열폭 계산
                                            crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                            crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                            crack_width = max(crack_width_1d, crack_width_2d)
                                            footer_crack_width = max(footer_crack_width, crack_width)
                                            print(f"            -> Concrete crack width: {crack_width} (1d: {crack_width_1d}, 2d: {crack_width_2d})")
                                        else:
                                            footer_section_damages.append('후타재 단면손상')

                                    # 일반 균열을 후타재 균열로 처리
                                    elif '균열' in damage_type and quantity > 0:
                                        # 일반 균열의 최대 균열폭 계산
                                        crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                        crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                        crack_width = max(crack_width_1d, crack_width_2d)
                                        footer_crack_width = max(footer_crack_width, crack_width)
                                        print(f"            -> General crack width: {crack_width} (1d: {crack_width_1d}, 2d: {crack_width_2d})")

                                    # 후타재가 없는 일반 손상들 중 균열을 제외한 단면손상을 후타재 단면손상으로 처리
                                    elif ('후타재' not in original_desc and
                                          '균열' not in original_desc and
                                          '균열' not in damage_type and
                                          quantity > 0 and
                                          not any(keyword in original_desc for keyword in ['유간', '이물질', '본체', '부식', '고무재', '이음부', '볼트'])):
                                        footer_section_damages.append(original_desc)

                            # 본체 상태 결정
                            if body_damages:
                                body_condition = ', '.join(list(set(body_damages)))  # 중복 제거하고 모든 손상내용 표시
                            else:
                                body_condition = '-'

                            # 후타재 균열 상태 결정 (실제 균열폭 표시)
                            footer_crack = footer_crack_width if footer_crack_width > 0 else '-'

                            # 후타재 단면손상 상태 결정 (실제 손상내용 표시, 중복 제거)
                            footer_damage = ', '.join(list(set(footer_section_damages))) if footer_section_damages else '-'

                            print(f"        Expansion joint result - Body: {body_condition}, Crack width: {footer_crack}, Section damage: {footer_damage}")

                            span_data.update({
                                'body_condition': body_condition,
                                'footer_crack': footer_crack,
                                'section_damage': footer_damage,
                                # 손상 세부 정보 추가
                                'body_damages': body_damages,
                                'footer_crack_damages': footer_section_damages,
                                'footer_section_damages': footer_section_damages
                            })

                            print(f"        Added span data: {span_data}")

                            # 신축이음 데이터를 api_data에 추가
                            api_data[api_key].append(span_data)

                        elif api_key == 'pavement':
                            # 교면포장의 경우 - 손상율, 교통상태, 배수상태 관련
                            damage_ratio_quantity = damage_quantities.get('표면손상', 0)
                            crack_ratio_quantity_1d = pos_data.get('crack_ratio_1d', 0)
                            crack_ratio_quantity_2d = pos_data.get('crack_ratio_2d', 0)

                            # condition_evaluation.py에서 이미 0.25 곱하기가 적용되었으므로 원래값 사용
                            adjusted_crack_ratio_1d = crack_ratio_quantity_1d
                            adjusted_crack_ratio_2d = crack_ratio_quantity_2d

                            total_damage_quantity = damage_ratio_quantity + adjusted_crack_ratio_1d + adjusted_crack_ratio_2d

                            # 배수상태 확인 - 배수시설 부재의 데이터를 참조
                            drainage_condition = '양호'
                            drainage_damages = []

                            # 배수시설 부재의 데이터에서 손상 확인
                            # 전체 부재 데이터에서 배수시설 데이터 검색
                            for filter_name, evaluation_result in all_evaluation_results.items():
                                if '배수' in filter_name:
                                    for component_name, component_data in evaluation_result.items():
                                        if '배수' in component_name or '배수구' in component_name:
                                            for pos, pos_data in component_data['positions'].items():
                                                if pos == position:  # 같은 경간의 배수시설 데이터
                                                    for damage in pos_data.get('damages', []):
                                                        original_desc = damage.get('original_desc', '')
                                                        damage_quantity = damage.get('quantity', 0)

                                                        # 배수 관련 손상 확인 (막힘, 퇴적, 이물질, 적치만 포함)
                                                        if damage_quantity > 0 and any(keyword in original_desc for keyword in ['막힘', '퇴적', '이물질', '적치']):
                                                            if original_desc not in drainage_damages:
                                                                drainage_damages.append(original_desc)
                                                                print(f"            -> Added to pavement drainage from drainage component: {original_desc}")

                            # 배수상태 결정
                            if drainage_damages:
                                drainage_condition = ', '.join(drainage_damages)
                            else:
                                drainage_condition = '양호'

                            # span_damage 테이블에서 inspection_area 가져오기
                            inspection_area = 100  # 기본값
                            # span_id_key = position.upper()
                            # if span_id_key in inspection_area_map and component_name in inspection_area_map[span_id_key]:
                            #     inspection_area = inspection_area_map[span_id_key][api_key]
                            #     print(f"            -> Using inspection_area from span_damage: {inspection_area}")

                            span_data.update({
                                'inspection_area': inspection_area,
                                'damage_ratio': (total_damage_quantity / inspection_area) * 100 if total_damage_quantity > 0 else 0,
                                'traffic_condition': '양호',  # 별도 로직 필요
                                'drainage_condition': drainage_condition,  # 배수시설 데이터 기반
                                # 원본 손상물량 추가
                                'original_damage_ratio_quantity': damage_ratio_quantity,
                                'original_crack_ratio_quantity_1d': crack_ratio_quantity_1d,
                                'original_crack_ratio_quantity_2d': crack_ratio_quantity_2d,
                                'adjusted_crack_ratio_1d': adjusted_crack_ratio_1d,
                                'adjusted_crack_ratio_2d': adjusted_crack_ratio_2d,
                                'drainage_damages': drainage_damages
                            })

                        elif api_key == 'drainage':
                            # 배수시설의 경우 - 배출구 상태, 관로 상태 관련
                            outlet_damages = []
                            pipe_damages = []

                            # 배수구 막힘 경간 확인
                            is_blocked_span = False
                            for damage in pos_data.get('damages', []):
                                original_desc = damage.get('original_desc', '')
                                if '배수구' in original_desc and '막힘' in original_desc:
                                    is_blocked_span = True
                                    break

                            print(f"        Processing drainage damages for {position}:")

                            for damage in pos_data.get('damages', []):
                                original_desc = damage.get('original_desc', '')
                                damage_quantity = damage.get('quantity', 0)

                                print(f"          Damage: {original_desc}, Quantity: {damage_quantity}")

                                if damage_quantity > 0:  # 손상물량이 있는 경우만 처리
                                    # 배수구 막힘 경간에서 토사퇴적, 퇴적, 적치, 이물질 등을 배수불량으로 처리
                                    if is_blocked_span and any(keyword in original_desc for keyword in ['토사퇴적', '퇴적', '적치', '이물질']):
                                        modified_desc = '배수불량'
                                        if modified_desc not in pipe_damages:
                                            pipe_damages.append(modified_desc)
                                            print(f"            -> Added to pipe_damages (modified): {modified_desc}")
                                    elif any(keyword in original_desc for keyword in ['배출구', '출구', '토출구']):
                                        if original_desc not in outlet_damages:
                                            outlet_damages.append(original_desc)
                                            print(f"            -> Added to outlet_damages: {original_desc}")
                                    elif any(keyword in original_desc for keyword in ['관로', '파이프', '관']):
                                        if original_desc not in pipe_damages:
                                            pipe_damages.append(original_desc)
                                            print(f"            -> Added to pipe_damages: {original_desc}")
                                    elif '누수' in original_desc:
                                        # 누수는 pipe_damages에 추가
                                        if original_desc not in pipe_damages:
                                            pipe_damages.append(original_desc)
                                            print(f"            -> Added to pipe_damages (leak): {original_desc}")
                                    else:
                                        # 기타 배수시설 손상은 관로로 분류
                                        if original_desc not in pipe_damages:
                                            pipe_damages.append(original_desc)
                                            print(f"            -> Added to pipe_damages (other): {original_desc}")

                            # 제한 없이 모든 손상내용 표시
                            outlet_condition = ', '.join(outlet_damages) if outlet_damages else '-'
                            pipe_condition = ', '.join(pipe_damages) if pipe_damages else '-'

                            # 모든 손상을 합쳐서 손상현황으로 표시
                            all_damages = outlet_damages + pipe_damages
                            damage_condition = ', '.join(all_damages) if all_damages else '-'

                            print(f"        Drainage result - Outlet: {outlet_condition}, Pipe: {pipe_condition}, All: {damage_condition}")

                            span_data.update({
                                'outlet_condition': outlet_condition,
                                'pipe_condition': pipe_condition,
                                'damage_condition': damage_condition,  # 전체 손상현황
                                # 손상 세부 정보 추가
                                'outlet_damages': outlet_damages,
                                'pipe_damages': pipe_damages,
                                'is_blocked_span': is_blocked_span
                            })

                        # 데이터 추가 (난간은 이미 위에서 처리됨)
                        if api_key != 'railing':
                            api_data[api_key].append(span_data)
                            print(f"        Added span data: {span_data}")
                        elif api_key == 'railing' and not existing_data and should_update:
                            # 난간의 경우 중복체크 후 추가
                            api_data[api_key].append(span_data)
                            print(f"        Added railing span data: {span_data['span_id']} with crack_width={span_data.get('crack_width', 0)}mm")

        except Exception as e:
            print(f"Component {filter_name} processing error: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 기본 데이터가 비어있는 부재들에 대해 기본값 설정 (신축이음 제외)
    default_spans = get_source_by_meta_id_and_keyword(200077, '기본부재')

    for component_key in api_data.keys():
        if not api_data[component_key] and component_key != 'expansionJoint':  # 비어있으면 기본값 설정 (신축이음 제외)
            print(f"Setting default data for {component_key}")

            for span in default_spans:
                base_data = {
                    'span_id': span,
                    'crack_width_1d': 0,
                    'crack_ratio_1d': 0,
                    'crack_width_2d': None,  # 2방향 균열폭은 손상물량 없으면 None
                    'crack_ratio_2d': 0,
                    'grade': 'a'
                }

                # 부재별 추가 필드
                if component_key == 'slab':
                    # 강 바닥판인지 확인하여 다른 필드 설정
                    # 기본적으로 콘크리트 바닥판 구조로 설정
                    base_data.update({
                        'inspection_area': 100,
                        'leak_ratio': 0,
                        'surface_damage_ratio': 0,
                        'rebar_corrosion_ratio': 0
                    })
                elif component_key == 'girder':
                    # 강거더의 경우 - 표 1.12 기준
                    base_data.update({
                        'inspection_area': 100,
                        'component_crack': '-',
                        'deformation_fracture': '-',
                        'bolt_loosening': '-',
                        'weld_defect': '-',
                        'surface_deterioration_ratio': 0
                    })
                elif component_key == 'crossbeam':
                    # 강 가로보의 경우 - 표 1.17 기준
                    base_data.update({
                        'inspection_area': 100,
                        'component_crack': '-',
                        'deformation_fracture': '-',
                        'bolt_loosening': '-',
                        'weld_defect': '-',
                        'surface_deterioration_ratio': 0
                    })
                elif component_key in ['abutment', 'pier']:
                    base_data.update({
                        'inspection_area': 100,
                        'crack_width': 0,
                        'deformation': '-',
                        'surface_damage_ratio': 0,
                        'rebar_corrosion_ratio': 0
                    })
                elif component_key == 'foundation':
                    base_data.update({
                        'crack_width': 0,
                        'damage_condition': '-',
                        'erosion': '-',
                        'settlement': '-'
                    })
                elif component_key == 'bearing':
                    base_data.update({
                        'body_condition': '-',
                        'crack_width': 0,
                        'section_damage': '-'
                    })
                # 신축이음은 기본 데이터를 생성하지 않음
                elif component_key == 'pavement':
                    base_data.update({
                        'inspection_area': 100,
                        'damage_ratio': 0,
                        'traffic_condition': '양호',
                        'drainage_condition': '양호'
                    })
                elif component_key == 'drainage':
                    base_data.update({
                        'outlet_condition': '-',
                        'pipe_condition': '-',
                        'damage_condition': '-',  # 전체 손상현황
                        'outlet_damages': [],
                        'pipe_damages': [],
                        'is_blocked_span': False
                    })
                elif component_key == 'railing':
                    base_data.update({
                        'length': 100,  # 길이
                        'surface_damage_ratio': 0,  # 표면손상
                        'rebar_corrosion_ratio': 0,  # 철근노출
                        # 원본 손상물량 추가
                        'original_surface_damage_quantity': 0,
                        'original_rebar_corrosion_quantity': 0
                    })

                api_data[component_key].append(base_data)

    print("API 변환 완료")
    return api_data




    # 정확한 매칭 먼저 시도
    if component_name in mapping:
        return mapping[component_name]

    # 부분 매칭 시도 (더 포괄적으로)
    for key, value in mapping.items():
        if key in component_name:
            return value

    # 난간 관련 키워드 추가 검색
    railing_keywords = ['난간', '연석', '방호', '방음', '차광', '낙석', '중분대', '경계석', '가드레일', '울타리', '보호', '안전']
    if any(keyword in component_name for keyword in railing_keywords):
        return 'railing'

    print(f"Unknown component name: {component_name}")
    return None
