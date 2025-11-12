"""
상태평가표 데이터 생성 API (신축이음 수정 버전)
"""
from flask import request, jsonify, session
import pandas as pd
import json
import re
from . import api_bp
from utils.common import get_db_connection, clean_dataframe_data
from utils.condition_evaluation import generate_condition_evaluation_pivot

@api_bp.route('/generate_evaluation_data_fixed', methods=['POST'])
def generate_evaluation_data_fixed():
    """
    신축이음 데이터 처리 로직을 수정한 상태평가표 데이터 생성
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
            
        data = request.get_json()
        filename = data.get('filename')
        
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
        evaluation_data = convert_to_api_format_fixed(df)
        
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


def convert_to_api_format_fixed(df):
    """개선된 condition_evaluation 모듈의 결과를 API 형식으로 변환 (신축이음 수정)"""
    print("API 변환 시작...")
    
    # 부재별 상태평가 데이터 생성
    component_filters = ['바닥판', '거더', '가로보', '교대', '교각', '교량받침', '기초', '신축이음', '교면포장', '배수시설', '난간']
    
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
    
    # 각 부재별로 상태평가 데이터 생성
    for filter_name in component_filters:
        try:
            print(f"Processing {filter_name}...")
            evaluation_result = generate_condition_evaluation_pivot(df, filter_name)
            
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
                        
                        # 기본 span_data 구조
                        span_data = {
                            'span_id': position.upper(),
                            'crack_width_1d': pos_data.get('crack_width_1d', 0),
                            'crack_ratio_1d': pos_data.get('crack_ratio_1d', 0),
                            'crack_width_2d': pos_data.get('crack_width_2d'),
                            'crack_ratio_2d': pos_data.get('crack_ratio_2d', 0),
                            'grade': pos_data.get('condition_grade', 'a').lower(),
                            'original_damage_quantities': damage_quantities
                        }
                        
                        # 신축이음 특별 처리
                        if api_key == 'expansionJoint':
                            print(f"        Processing expansion joint damages for {position}:")
                            
                            # 실제 데이터에서 손상 분류
                            body_conditions = []
                            footer_crack_width = 0
                            footer_section_damages = []
                            
                            for damage in pos_data.get('damages', []):
                                damage_type = damage.get('type', '')
                                original_desc = damage.get('original_desc', '')
                                quantity = damage.get('quantity', 0)
                                crack_width = damage.get('crack_width', 0)
                                
                                print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {quantity}")
                                
                                # 본체 손상 처리 (본체, 볼트, 고무재, 유간, 이물질, 토사퇴적)
                                if damage_type == '본체_손상' and quantity > 0:
                                    if '부식' in original_desc:
                                        body_conditions.append('본체 부식')
                                    elif '파손' in original_desc or '탈락' in original_desc:
                                        body_conditions.append('본체 파손')
                                    elif '유간' in original_desc:
                                        body_conditions.append('유간 이상')
                                    elif '이물질' in original_desc:
                                        body_conditions.append('이물질 끼임')
                                    elif '토사퇴적' in original_desc:
                                        body_conditions.append('토사퇴적')
                                    elif '고무재' in original_desc:
                                        body_conditions.append('고무재 손상')
                                    elif '볼트' in original_desc:
                                        body_conditions.append('볼트 손상')
                                    else:
                                        body_conditions.append('본체 손상')
                                
                                # 후타재 균열 처리 (균열폭 추출)
                                elif damage_type == '후타재_균열' and quantity > 0:
                                    if crack_width > 0:
                                        footer_crack_width = max(footer_crack_width, crack_width)
                                    else:
                                        # 균열폭이 없으면 상태평가 데이터에서 가져오기
                                        crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                        crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                        footer_crack_width = max(footer_crack_width, crack_width_1d, crack_width_2d)
                                
                                # 후타재 단면손상 처리 (균열 제외한 모든 후타재 손상)
                                elif damage_type == '후타재_단면손상' and quantity > 0:
                                    footer_section_damages.append(original_desc)
                                
                                # 일반 균열도 후타재로 처리
                                elif damage_type == '균열' and quantity > 0:
                                    if crack_width > 0:
                                        footer_crack_width = max(footer_crack_width, crack_width)
                                    else:
                                        crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                        crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                        footer_crack_width = max(footer_crack_width, crack_width_1d, crack_width_2d)
                            
                            # 결과 결정
                            body_condition = ', '.join(list(set(body_conditions))[:2]) if body_conditions else '-'
                            footer_crack = '균열' if footer_crack_width > 0 else '-'
                            section_damage = '단면손상' if footer_section_damages else '-'
                            
                            print(f"        Expansion joint result - Body: {body_condition}, Crack: {footer_crack}, Section damage: {section_damage}, Crack width: {footer_crack_width}")
                            
                            span_data.update({
                                'body_condition': body_condition,
                                'footer_crack': footer_crack,
                                'section_damage': section_damage,
                                'footer_crack_width': footer_crack_width,
                                'body_conditions': body_conditions,
                                'footer_section_damages': footer_section_damages
                            })
                        
                        # 다른 부재들은 기존 로직 유지
                        elif api_key in ['slab', 'girder']:
                            leak_quantity = damage_quantities.get('누수', 0)
                            surface_damage_quantity = damage_quantities.get('표면손상', 0)
                            rebar_corrosion_quantity = damage_quantities.get('철근부식', 0)
                            
                            inspection_area = 100
                            span_data.update({
                                'inspection_area': inspection_area,
                                'leak_ratio': (leak_quantity / inspection_area) * 100 if leak_quantity > 0 else 0,
                                'surface_damage_ratio': (surface_damage_quantity / inspection_area) * 100 if surface_damage_quantity > 0 else 0,
                                'rebar_corrosion_ratio': (rebar_corrosion_quantity / inspection_area) * 100 if rebar_corrosion_quantity > 0 else 0,
                                'original_leak_quantity': leak_quantity,
                                'original_surface_damage_quantity': surface_damage_quantity,
                                'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                            })
                        
                        elif api_key == 'bearing':
                            # 교량받침 처리 로직
                            body_condition_damages = []
                            concrete_crack_width = 0
                            concrete_section_damages = []
                            
                            for damage in pos_data.get('damages', []):
                                original_desc = damage.get('original_desc', '')
                                damage_type = damage.get('type', '')
                                
                                if any(keyword in original_desc.lower() for keyword in ['부식', '편기', '도장', '볼트', '앵커', '너트', '전단키']):
                                    if original_desc not in body_condition_damages:
                                        body_condition_damages.append(original_desc)
                                elif '균열' in damage_type.lower():
                                    crack_width_1d = pos_data.get('crack_width_1d', 0) or 0
                                    crack_width_2d = pos_data.get('crack_width_2d', 0) or 0
                                    crack_width = max(crack_width_1d, crack_width_2d)
                                    concrete_crack_width = max(concrete_crack_width, crack_width)
                                elif any(keyword in original_desc.lower() for keyword in ['콘크리트', '몰탈']):
                                    if original_desc not in concrete_section_damages:
                                        concrete_section_damages.append(original_desc)
                            
                            body_condition = ', '.join(body_condition_damages[:2]) if body_condition_damages else '-'
                            concrete_damage_text = ', '.join(concrete_section_damages) if concrete_section_damages else '-'
                            
                            span_data.update({
                                'body_condition': body_condition,
                                'crack_width': concrete_crack_width if concrete_crack_width > 0 else 0,
                                'section_damage': concrete_damage_text
                            })
                        
                        api_data[api_key].append(span_data)
                        print(f"        Added span data: {span_data}")
                        
        except Exception as e:
            print(f"Component {filter_name} processing error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 기본 데이터가 비어있는 부재들에 대해 기본값 설정 (신축이음 제외)
    default_spans = ['S1', 'S2', 'S3']
    
    for component_key in api_data.keys():
        if not api_data[component_key] and component_key != 'expansionJoint':
            print(f"Setting default data for {component_key}")
            
            for span in default_spans:
                base_data = {
                    'span_id': span,
                    'crack_width_1d': 0,
                    'crack_ratio_1d': 0,
                    'crack_width_2d': None,
                    'crack_ratio_2d': 0,
                    'grade': 'a'
                }
                
                if component_key in ['slab', 'girder']:
                    base_data.update({
                        'inspection_area': 100,
                        'leak_ratio': 0,
                        'surface_damage_ratio': 0,
                        'rebar_corrosion_ratio': 0
                    })
                elif component_key == 'bearing':
                    base_data.update({
                        'body_condition': '-',
                        'crack_width': 0,
                        'section_damage': '-'
                    })
                
                api_data[component_key].append(base_data)
    
    print("API 변환 완료")
    return api_data


def convert_component_name_to_key(component_name):
    """부재명을 API 키로 변환"""
    mapping = {
        '바닥판': 'slab',
        '거더': 'girder',
        '가로보': 'crossbeam',
        '세로보': 'crossbeam',
        '격벽': 'crossbeam',
        '교대': 'abutment',
        '교각': 'pier',
        '기초': 'foundation',
        '받침': 'bearing',
        '교량받침': 'bearing',
        '받침장치': 'bearing',
        '탄성받침': 'bearing',
        '고무받침': 'bearing',
        '강재받침': 'bearing',
        '베어링': 'bearing',
        '신축이음': 'expansionJoint',
        '이음장치': 'expansionJoint',
        '신축이음장치': 'expansionJoint',
        '이음부': 'expansionJoint',
        '교면포장': 'pavement',
        '포장': 'pavement',
        '배수시설': 'drainage',
        '배수구': 'drainage',
        '난간': 'railing',
        '연석': 'railing',
        '난간연석': 'railing',
        '방호울타리': 'railing',
        '방호벽': 'railing',
        '방음벽': 'railing',
        '방음판': 'railing',
        '차광망': 'railing',
        '낙석방지망': 'railing',
        '낙석방지책': 'railing',
        '중분대': 'railing',
        '중앙분리대': 'railing',
        '경계석': 'railing'
    }
    
    # 정확한 매칭 먼저 시도
    if component_name in mapping:
        return mapping[component_name]
    
    # 부분 매칭 시도
    for key, value in mapping.items():
        if key in component_name:
            return value
    
    print(f"Unknown component name: {component_name}")
    return None
