"""
Slab 데이터 처리 유틸리티
"""
import re
from utils.common import get_db_connection


def process_slab_damage_data(component_data, damage_mapping=None):
    """
    부재별 집계표 데이터를 기반으로 콘크리트 바닥판 상태평가표 데이터를 생성합니다.

    Args:
        component_data (list): 부재별 집계표 데이터 리스트
        damage_mapping (dict): 손상 유형별 매핑 설정

    Returns:
        dict: 상태평가표 데이터
    """
    # 기본 손상 매핑 설정
    default_mapping = {
        '균열': {
            '1방향': {
                'keywords': ['균열부백태', '균열'],
                'length_factor': 0.25
            },
            '2방향': {
                'keywords': ['망상균열', '균열'],
                'length_factor': 0.25
            }
        },
        '누수': {
            'keywords': ['누수', '백태']
        },
        '표면손상': {
            'keywords': ['박리', '박락', '파손']
        },
        '철근부식': {
            'keywords': ['철근노출']
        }
    }

    # 사용자 정의 매핑이 있으면 기본 매핑을 업데이트
    if damage_mapping:
        for damage_type, mapping in damage_mapping.items():
            if damage_type in default_mapping:
                if isinstance(mapping, dict) and 'keywords' in mapping:
                    default_mapping[damage_type]['keywords'] = mapping['keywords']
                elif isinstance(mapping, dict):
                    for sub_type, sub_mapping in mapping.items():
                        if sub_type in default_mapping[damage_type]:
                            if 'keywords' in sub_mapping:
                                default_mapping[damage_type][sub_type]['keywords'] = sub_mapping['keywords']
                            if 'length_factor' in sub_mapping:
                                default_mapping[damage_type][sub_type]['length_factor'] = sub_mapping['length_factor']

    slab_data = {
        '구분': '콘크리트 바닥판',
        '점검면적': 0,
        '1방향 균열 최대폭': 0,
        '1방향 균열 균열율': 0,
        '2방향 균열 최대폭': 0,
        '2방향 균열 균열율': 0,
        '누수 및 백태 면적율': 0,
        '표면손상 면적율': 0,
        '철근부식 손상면적율': 0,
        '상태평가결과': 'a'
    }

    # 해당 경간의 콘크리트 바닥판 데이터만 필터링 ('바닥판'이라는 단어가 포함된 경우 포함)
    slab_components = [comp for comp in component_data if '바닥판' in comp.get('부재구분', '')]

    if not slab_components:
        return slab_data

    # 점검면적 계산 (모든 바닥판의 면적 합계)
    total_area = sum(float(comp.get('면적', 0)) for comp in slab_components)
    slab_data['점검면적'] = total_area

    # 손상 데이터 초기화
    max_crack_width_1d = 0
    total_crack_length_1d = 0
    max_crack_width_2d = 0
    total_crack_length_2d = 0
    leak_area = 0
    surface_damage_area = 0
    rebar_corrosion_area = 0

    for comp in slab_components:
        damage_desc = comp.get('손상내용', '')
        area = float(comp.get('면적', 0))
        damage_quantity = float(comp.get('손상물량', 0))

        # 균열 처리
        if all(keyword in damage_desc for keyword in default_mapping['균열']['1방향']['keywords']):
            crack_pattern = r'(\d+(?:\.\d+)?)\s*(?:mm|㎜|m|M)'
            crack_match = re.search(crack_pattern, damage_desc)

            if crack_match:
                crack_width = float(crack_match.group(1))
                length_factor = default_mapping['균열']['1방향']['length_factor']
                crack_length = damage_quantity * length_factor
                max_crack_width_1d = max(max_crack_width_1d, crack_width)
                total_crack_length_1d += crack_length

        elif all(keyword in damage_desc for keyword in default_mapping['균열']['2방향']['keywords']):
            crack_pattern = r'(\d+(?:\.\d+)?)\s*(?:mm|㎜|m|M)'
            crack_match = re.search(crack_pattern, damage_desc)

            if crack_match:
                crack_width = float(crack_match.group(1))
                length_factor = default_mapping['균열']['2방향']['length_factor']
                crack_length = damage_quantity * length_factor
                max_crack_width_2d = max(max_crack_width_2d, crack_width)
                total_crack_length_2d += crack_length

        # 누수 및 백태 처리
        if any(keyword in damage_desc for keyword in default_mapping['누수']['keywords']):
            leak_area += damage_quantity
            surface_damage_area += damage_quantity

        # 표면손상 처리
        if any(keyword in damage_desc for keyword in default_mapping['표면손상']['keywords']):
            surface_damage_area += damage_quantity

        # 철근부식 처리
        if any(keyword in damage_desc for keyword in ['철근노출', '철근부식', '부식']) and '잡철근노출' not in damage_desc:
            rebar_corrosion_area += damage_quantity

        # 녹물 관련 손상은 표면손상으로 분류
        if any(keyword in damage_desc for keyword in ['녹물']):
            surface_damage_area += damage_quantity

    # 결과 계산
    slab_data['1방향 균열 최대폭'] = max_crack_width_1d
    slab_data['1방향 균열 균열율'] = (total_crack_length_1d / total_area) * 100 if total_area > 0 else 0
    slab_data['2방향 균열 최대폭'] = '-' if max_crack_width_2d == 0 else max_crack_width_2d
    slab_data['2방향 균열 균열율'] = (total_crack_length_2d / total_area) * 100 if total_area > 0 else 0
    slab_data['누수 및 백태 면적율'] = (leak_area / total_area) * 100 if total_area > 0 else 0
    slab_data['표면손상 면적율'] = (surface_damage_area / total_area) * 100 if total_area > 0 else 0
    slab_data['철근부식 손상면적율'] = (rebar_corrosion_area / total_area) * 100 if total_area > 0 else 0

    # 상태평가결과 계산
    max_crack_width = max(max_crack_width_1d, max_crack_width_2d if max_crack_width_2d != '-' else 0)
    max_crack_ratio = max(slab_data['1방향 균열 균열율'], slab_data['2방향 균열 균열율'])
    leak_ratio = slab_data['누수 및 백태 면적율']
    surface_damage_ratio = slab_data['표면손상 면적율']
    rebar_corrosion_ratio = slab_data['철근부식 손상면적율']

    # 등급 초기값
    grade = 'a'

    # 균열폭 기준
    if max_crack_width >= 1.0:
        grade = 'e'
    elif max_crack_width >= 0.5:
        grade = 'd'
    elif max_crack_width >= 0.3:
        grade = 'c'
    elif max_crack_width >= 0.1:
        grade = 'b'

    # 균열률 기준
    if max_crack_ratio >= 20:
        grade = max(grade, 'e') if grade < 'e' else grade
    elif max_crack_ratio >= 10:
        grade = max(grade, 'd') if grade < 'd' else grade
    elif max_crack_ratio >= 2:
        grade = max(grade, 'c') if grade < 'c' else grade
    elif max_crack_ratio > 0:
        grade = max(grade, 'b') if grade < 'b' else grade

    # 누수 및 백태 기준
    if leak_ratio >= 10:
        grade = max(grade, 'c') if grade < 'c' else grade
    elif leak_ratio > 0:
        grade = max(grade, 'b') if grade < 'b' else grade

    # 표면손상 기준
    if surface_damage_ratio >= 10:
        grade = max(grade, 'd') if grade < 'd' else grade
    elif surface_damage_ratio >= 2:
        grade = max(grade, 'c') if grade < 'c' else grade
    elif surface_damage_ratio > 0:
        grade = max(grade, 'b') if grade < 'b' else grade

    # 철근부식 기준
    if rebar_corrosion_ratio >= 2:
        grade = max(grade, 'd') if grade < 'd' else grade
    elif rebar_corrosion_ratio > 0:
        grade = max(grade, 'c') if grade < 'c' else grade

    slab_data['상태평가결과'] = grade

    return slab_data
