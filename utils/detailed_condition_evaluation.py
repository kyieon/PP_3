"""
상세 교량 상태평가용 데이터 처리 모듈
각 부재별 상세 상태평가표 생성 및 자동 등급 계산
"""
import pandas as pd
import re
from collections import defaultdict
from utils.common import normalize_component, sort_components
import math


def extract_numerical_value(damage_desc, patterns):
    """손상내용에서 수치 추출"""
    for pattern in patterns:
        match = re.search(pattern, damage_desc)
        if match:
            return float(match.group(1))
    return None


def get_crack_grade(crack_width):
    """균열폭에 따른 등급 산정"""
    if crack_width is None or crack_width == 0:
        return 'a'
    elif crack_width >= 1.0:
        return 'e'
    elif crack_width >= 0.5:
        return 'd'
    elif crack_width >= 0.3:
        return 'c'
    elif crack_width >= 0.1:
        return 'b'
    else:
        return 'a'


def get_crack_ratio_grade(crack_ratio):
    """균열율에 따른 등급 산정"""
    if crack_ratio is None or crack_ratio == 0:
        return 'a'
    elif crack_ratio >= 20:
        return 'e'
    elif crack_ratio >= 15:
        return 'd'
    elif crack_ratio >= 10:
        return 'c'
    elif crack_ratio >= 5:
        return 'b'
    else:
        return 'a'


def get_surface_damage_grade(surface_ratio):
    """표면손상율에 따른 등급 산정"""
    if surface_ratio is None or surface_ratio == 0:
        return 'a'
    elif surface_ratio >= 20:
        return 'e'
    elif surface_ratio >= 10:
        return 'd'
    elif surface_ratio >= 5:
        return 'c'
    elif surface_ratio > 0:
        return 'b'
    else:
        return 'a'


def get_leakage_grade(leakage_ratio):
    """누수 및 백태율에 따른 등급 산정"""
    if leakage_ratio is None or leakage_ratio == 0:
        return 'a'
    elif leakage_ratio >= 20:
        return 'd'
    elif leakage_ratio >= 10:
        return 'c'
    elif leakage_ratio > 0:
        return 'b'
    else:
        return 'a'


def get_rebar_corrosion_grade(rebar_ratio):
    """철근부식율에 따른 등급 산정"""
    if rebar_ratio is None or rebar_ratio == 0:
        return 'a'
    elif rebar_ratio >= 3:
        return 'e'
    elif rebar_ratio >= 2:
        return 'd'
    elif rebar_ratio >= 1:
        return 'c'
    elif rebar_ratio > 0:
        return 'b'
    else:
        return 'a'


def calculate_final_grade(grades):
    """최종 등급 계산 (최고 등급 기준)"""
    grade_values = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
    grade_letters = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}

    max_grade = max([grade_values.get(g, 1) for g in grades if g])
    return grade_letters.get(max_grade, 'a')


def natural_sort_position(position):
    """부재위치를 자연 정렬 (s1, s2, s3... s10, s11... 순서로)"""
    import re
    parts = re.split(r'(\d+)', str(position))
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def merge_girder_data(component_df):
    """거더 내부/외부 데이터를 통합"""
    merged_data = {}

    for _, row in component_df.iterrows():
        position = row['부재위치']
        # s1i, s1o -> s1으로 통합
        base_position = re.sub(r'[io]$', '', str(position))

        if base_position not in merged_data:
            merged_data[base_position] = {
                '손상내용': [],
                '손상물량': 0,
                '점검면적': 0,
                '개소': 0
            }

        merged_data[base_position]['손상내용'].append(row['손상내용'])
        merged_data[base_position]['손상물량'] += row['손상물량']
        merged_data[base_position]['점검면적'] = max(merged_data[base_position]['점검면적'], row.get('점검면적', 300))
        merged_data[base_position]['개소'] += row.get('개소', 1)

    # DataFrame으로 변환
    merged_rows = []
    for position, data in merged_data.items():
        for damage_content in data['손상내용']:
            merged_rows.append({
                '부재위치': position,
                '손상내용': damage_content,
                '손상물량': data['손상물량'] / len(data['손상내용']),  # 평균 배분
                '점검면적': data['점검면적'],
                '개소': data['개소']
            })

    return pd.DataFrame(merged_rows) if merged_rows else pd.DataFrame()


def process_slab_evaluation(component_df, area):
    """바닥판 상태평가 처리"""
    evaluation = {
        'inspection_area': area,
        '1d_crack_width': 0,
        '1d_crack_grade': 'a',
        '1d_crack_ratio': 0,
        '1d_crack_ratio_grade': 'a',
        '2d_crack_width': 0,
        '2d_crack_grade': 'a',
        '2d_crack_ratio': 0,
        '2d_crack_ratio_grade': 'a',
        'leakage_ratio': 0,
        'leakage_grade': 'a',
        'surface_damage_ratio': 0,
        'surface_damage_grade': 'a',
        'rebar_corrosion_ratio': 0,
        'rebar_corrosion_grade': 'a',
        'final_grade': 'a'
    }

    total_crack_length_1d = 0
    total_crack_length_2d = 0
    total_leakage_area = 0
    total_surface_damage_area = 0
    total_rebar_corrosion_area = 0

    for _, row in component_df.iterrows():
        damage_desc = row['손상내용']
        quantity = row['손상물량']

        # 균열 처리
        if '균열' in damage_desc:
            # 균열폭 추출
            crack_width = extract_numerical_value(damage_desc, [
                r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)',
                r'균열\((\d+(?:\.\d+)?)(?:mm|㎜)?\)',
                r'폭[=:]\s*(\d+(?:\.\d+)?)'
            ])

            if crack_width:
                # 1방향 균열 판단 (키워드 기반)
                if any(keyword in damage_desc for keyword in ['1방향', '종방향', '길이방향']):
                    evaluation['1d_crack_width'] = max(evaluation['1d_crack_width'], crack_width)
                    total_crack_length_1d += quantity
                # 2방향 균열 판단 (망상균열 등)
                elif any(keyword in damage_desc for keyword in ['2방향', '횡방향', '망상', '격자']):
                    evaluation['2d_crack_width'] = max(evaluation['2d_crack_width'], crack_width)
                    total_crack_length_2d += quantity
                else:
                    # 기본적으로 1방향으로 분류
                    evaluation['1d_crack_width'] = max(evaluation['1d_crack_width'], crack_width)
                    total_crack_length_1d += quantity

        # 누수 및 백태
        if any(keyword in damage_desc for keyword in ['누수', '백태', '침출', '석회화']):
            total_leakage_area += quantity

        # 표면손상
        if any(keyword in damage_desc for keyword in ['박리', '박락', '파손', '재료분리', '층분리', '스케일링']):
            total_surface_damage_area += quantity

        # 철근부식 (잡철근노출 제외)
        if any(keyword in damage_desc for keyword in ['철근부식', '철근노출']) and '잡철근노출' not in damage_desc:
            total_rebar_corrosion_area += quantity

    # 비율 계산 (면적 대비)
    if area > 0:
        evaluation['1d_crack_ratio'] = (total_crack_length_1d * 0.25 / area) * 100  # 가정: 균열 폭 0.25m
        evaluation['2d_crack_ratio'] = (total_crack_length_2d * 0.25 / area) * 100
        evaluation['leakage_ratio'] = (total_leakage_area / area) * 100
        evaluation['surface_damage_ratio'] = (total_surface_damage_area / area) * 100
        evaluation['rebar_corrosion_ratio'] = (total_rebar_corrosion_area / area) * 100

    # 등급 계산
    evaluation['1d_crack_grade'] = get_crack_grade(evaluation['1d_crack_width'])
    evaluation['1d_crack_ratio_grade'] = get_crack_ratio_grade(evaluation['1d_crack_ratio'])
    evaluation['2d_crack_grade'] = get_crack_grade(evaluation['2d_crack_width'])
    evaluation['2d_crack_ratio_grade'] = get_crack_ratio_grade(evaluation['2d_crack_ratio'])
    evaluation['leakage_grade'] = get_leakage_grade(evaluation['leakage_ratio'])
    evaluation['surface_damage_grade'] = get_surface_damage_grade(evaluation['surface_damage_ratio'])
    evaluation['rebar_corrosion_grade'] = get_rebar_corrosion_grade(evaluation['rebar_corrosion_ratio'])

    # 최종 등급
    grades = [
        evaluation['1d_crack_grade'], evaluation['1d_crack_ratio_grade'],
        evaluation['2d_crack_grade'], evaluation['2d_crack_ratio_grade'],
        evaluation['leakage_grade'], evaluation['surface_damage_grade'],
        evaluation['rebar_corrosion_grade']
    ]
    evaluation['final_grade'] = calculate_final_grade(grades)

    return evaluation


def process_girder_evaluation(component_df, area):
    """거더 상태평가 처리"""
    evaluation = {
        'inspection_area': area,
        'crack_width': 0,
        'crack_grade': 'a',
        'surface_damage_ratio': 0,
        'surface_damage_grade': 'a',
        'rebar_corrosion_ratio': 0,
        'rebar_corrosion_grade': 'a',
        'wire_exposure': False,
        'wire_exposure_grade': 'a',
        'grout_damage': False,
        'grout_damage_grade': 'a',
        'protection_damage': False,
        'protection_damage_grade': 'a',
        'final_grade': 'a'
    }

    total_surface_damage_area = 0
    total_rebar_corrosion_area = 0

    for _, row in component_df.iterrows():
        damage_desc = row['손상내용']
        quantity = row['손상물량']

        # 균열 처리
        if '균열' in damage_desc:
            crack_width = extract_numerical_value(damage_desc, [
                r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)',
                r'균열\((\d+(?:\.\d+)?)(?:mm|㎜)?\)'
            ])
            if crack_width:
                evaluation['crack_width'] = max(evaluation['crack_width'], crack_width)

        # 표면손상
        if any(keyword in damage_desc for keyword in ['박리', '박락', '파손', '재료분리']):
            total_surface_damage_area += quantity

        # 철근부식
        if any(keyword in damage_desc for keyword in ['철근노출', '철근부식', '부식']):
            total_rebar_corrosion_area += quantity

        # 녹물 관련 손상은 표면손상으로 분류
        if any(keyword in damage_desc for keyword in ['녹물']):
            total_surface_damage_area += quantity

        # 강연선 노출
        if any(keyword in damage_desc for keyword in ['강연선', '텐던', '노출']):
            evaluation['wire_exposure'] = True

        # 그라우트 손상
        if any(keyword in damage_desc for keyword in ['그라우트', '충전재']):
            evaluation['grout_damage'] = True

        # 보호관 손상
        if any(keyword in damage_desc for keyword in ['보호관', '덕트']):
            evaluation['protection_damage'] = True

    # 비율 계산
    if area > 0:
        evaluation['surface_damage_ratio'] = (total_surface_damage_area / area) * 100
        evaluation['rebar_corrosion_ratio'] = (total_rebar_corrosion_area / area) * 100

    # 등급 계산
    evaluation['crack_grade'] = get_crack_grade(evaluation['crack_width'])
    evaluation['surface_damage_grade'] = get_surface_damage_grade(evaluation['surface_damage_ratio'])
    evaluation['rebar_corrosion_grade'] = get_rebar_corrosion_grade(evaluation['rebar_corrosion_ratio'])
    evaluation['wire_exposure_grade'] = 'c' if evaluation['wire_exposure'] else 'a'
    evaluation['grout_damage_grade'] = 'b' if evaluation['grout_damage'] else 'a'
    evaluation['protection_damage_grade'] = 'b' if evaluation['protection_damage'] else 'a'

    # 최종 등급
    grades = [
        evaluation['crack_grade'], evaluation['surface_damage_grade'],
        evaluation['rebar_corrosion_grade'], evaluation['wire_exposure_grade'],
        evaluation['grout_damage_grade'], evaluation['protection_damage_grade']
    ]
    evaluation['final_grade'] = calculate_final_grade(grades)

    return evaluation


def process_crossbeam_evaluation(component_df, area):
    """가로보/세로보 상태평가 처리"""
    evaluation = {
        'inspection_area': area,
        'crack_width': 0,
        'crack_grade': 'a',
        'surface_damage_ratio': 0,
        'surface_damage_grade': 'a',
        'connection_damage': False,
        'connection_damage_grade': 'a',
        'final_grade': 'a'
    }

    total_surface_damage_area = 0

    for _, row in component_df.iterrows():
        damage_desc = row['손상내용']
        quantity = row['손상물량']

        # 균열 처리
        if '균열' in damage_desc:
            crack_width = extract_numerical_value(damage_desc, [
                r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)',
                r'균열\((\d+(?:\.\d+)?)(?:mm|㎜)?\)'
            ])
            if crack_width:
                evaluation['crack_width'] = max(evaluation['crack_width'], crack_width)

        # 표면손상
        if any(keyword in damage_desc for keyword in ['박리', '박락', '파손', '재료분리']):
            total_surface_damage_area += quantity

        # 연결부 손상
        if any(keyword in damage_desc for keyword in ['연결부', '접합부', '볼트', '용접부']):
            evaluation['connection_damage'] = True

    # 비율 계산
    if area > 0:
        evaluation['surface_damage_ratio'] = (total_surface_damage_area / area) * 100

    # 등급 계산
    evaluation['crack_grade'] = get_crack_grade(evaluation['crack_width'])
    evaluation['surface_damage_grade'] = get_surface_damage_grade(evaluation['surface_damage_ratio'])
    evaluation['connection_damage_grade'] = 'c' if evaluation['connection_damage'] else 'a'

    # 최종 등급
    grades = [
        evaluation['crack_grade'], evaluation['surface_damage_grade'],
        evaluation['connection_damage_grade']
    ]
    evaluation['final_grade'] = calculate_final_grade(grades)

    return evaluation


def generate_detailed_condition_evaluation(df):
    """상세 상태평가표 생성"""
    # 데이터 전처리
    df = df.copy()
    df['부재위치'] = df['부재위치'].astype(str)
    df['손상물량'] = pd.to_numeric(df['손상물량'], errors='coerce').fillna(0)

    # 점검면적이 있으면 사용, 없으면 기본값 계산
    if '점검면적' in df.columns:
        df['점검면적'] = pd.to_numeric(df['점검면적'], errors='coerce').fillna(300)
    else:
        df['점검면적'] = 300  # 기본값

    # 부재명별로 그룹화
    components = sort_components(df['부재명'].unique())

    evaluation_results = {}

    for component in components:
        component_df = df[df['부재명'] == component]

        # 거더인 경우 내부/외부 데이터 통합
        normalized_component = normalize_component(component)
        if normalized_component == '거더':
            component_df = merge_girder_data(component_df)
            if component_df.empty:
                continue

        # 부재위치를 자연 정렬로 정렬 (s1, s2, s3... s10, s11... 순서)
        positions = sorted(component_df['부재위치'].unique(), key=natural_sort_position)

        evaluation_results[component] = {}

        for position in positions:
            pos_df = component_df[component_df['부재위치'] == position]
            area = pos_df['점검면적'].iloc[0] if len(pos_df) > 0 else 300

            # 부재 유형에 따른 평가 처리
            if normalized_component == '바닥판':
                evaluation = process_slab_evaluation(pos_df, area)
            elif normalized_component == '거더':
                evaluation = process_girder_evaluation(pos_df, area)
            elif normalized_component == '가로보':
                evaluation = process_crossbeam_evaluation(pos_df, area)
            else:
                # 기본 평가 (단순화된 평가)
                evaluation = process_basic_evaluation(pos_df, area)

            evaluation_results[component][position] = evaluation

    return evaluation_results


def process_basic_evaluation(component_df, area):
    """교대, 교각 등 기본 부재의 상태평가 처리"""
    merged_data = {}

    for _, row in component_df.iterrows():
        position = row['부재위치']
        base_position = position

        if base_position not in merged_data:
            merged_data[base_position] = {
                'crack_width': 0,
                'crack_ratio': 0,
                'surface_damage': 0,
                'leakage': 0,
                'rebar_corrosion': 0,
                'damage_desc': []
            }

        # 균열 데이터 처리
        if '균열' in row['손상내용']:
            crack_width = extract_numerical_value(row['손상내용'], [r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)'])
            if crack_width:
                merged_data[base_position]['crack_width'] = max(merged_data[base_position]['crack_width'], crack_width)
            merged_data[base_position]['crack_ratio'] += row['손상물량']

        # 표면손상 데이터 처리 (누수, 백태 포함)
        if any(keyword in row['손상내용'] for keyword in ['박락', '박리', '파손', '누수', '백태']):
            merged_data[base_position]['surface_damage'] += row['손상물량']

        # 누수 데이터 처리
        if '누수' in row['손상내용'] or '백태' in row['손상내용']:
            merged_data[base_position]['leakage'] += row['손상물량']

        # 철근부식 데이터 처리
        if '철근부식' in row['손상내용'] or '철근노출' in row['손상내용']:
            merged_data[base_position]['rebar_corrosion'] += row['손상물량']

        merged_data[base_position]['damage_desc'].append(row['손상내용'])

    # 상태등급 계산
    for position, data in merged_data.items():
        crack_grade = get_crack_grade(data['crack_width'])
        crack_ratio_grade = get_crack_ratio_grade(data['crack_ratio'])
        surface_grade = get_surface_damage_grade(data['surface_damage'])
        leakage_grade = get_leakage_grade(data['leakage'])
        rebar_grade = get_rebar_corrosion_grade(data['rebar_corrosion'])

        final_grade = calculate_final_grade([
            crack_grade, crack_ratio_grade, surface_grade,
            leakage_grade, rebar_grade
        ])

        merged_data[position]['final_grade'] = final_grade

    return merged_data


def generate_detailed_condition_html(evaluation_results):
    """상세 상태평가표 HTML 생성"""
    html = '<div class="detailed-condition-evaluation">'

    for component, positions in evaluation_results.items():
        normalized_component = normalize_component(component)

        if normalized_component == '바닥판':
            html += generate_slab_evaluation_table(component, positions)
        elif normalized_component == '거더':
            html += generate_girder_evaluation_table(component, positions)
        elif normalized_component == '가로보':
            html += generate_crossbeam_evaluation_table(component, positions)
        else:
            html += generate_basic_evaluation_table(component, positions)

    html += '</div>'

    # CSS 스타일 추가
    html += '''
    <style>
        .detailed-condition-evaluation {
            margin: 20px 0;
        }
        .detailed-condition-evaluation h4 {
            color: #2c3e50;
            margin: 30px 0 15px 0;
            font-size: 1.3rem;
            font-weight: 600;
        }
        .detailed-condition-evaluation table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            font-size: 11px;
        }
        .detailed-condition-evaluation th,
        .detailed-condition-evaluation td {
            padding: 6px 4px;
            text-align: center;
            border: 1px solid #333;
            vertical-align: middle;
        }
        .detailed-condition-evaluation th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }
        .detailed-condition-evaluation .main-header {
            background-color: #d4edda;
            font-weight: bold;
        }
        .detailed-condition-evaluation .sub-header {
            background-color: #e9ecef;
        }
        .grade-a { color: #28a745; font-weight: bold; }
        .grade-b { color: #17a2b8; font-weight: bold; }
        .grade-c { color: #ffc107; font-weight: bold; }
        .grade-d { color: #fd7e14; font-weight: bold; }
        .grade-e { color: #dc3545; font-weight: bold; }
    </style>
    '''

    return html


def generate_slab_evaluation_table(component, positions):
    """바닥판 상태평가표 HTML 생성"""
    html = f'<h4>{component} 상태평가 결과</h4>'
    html += '<table>'
    html += '<thead>'
    html += '<tr>'
    html += '<th rowspan="3">구분</th>'
    html += '<th rowspan="3">점검면적<br>(m²)</th>'
    html += '<th colspan="4" class="main-header">1방향 균열</th>'
    html += '<th colspan="4" class="main-header">2방향 균열</th>'
    html += '<th colspan="6" class="main-header">열화 및 손상</th>'
    html += '<th rowspan="3" class="main-header">상태평가<br>결과</th>'
    html += '</tr>'
    html += '<tr>'
    html += '<th colspan="2" class="sub-header">최대폭</th>'
    html += '<th colspan="2" class="sub-header">균열율</th>'
    html += '<th colspan="2" class="sub-header">최대폭</th>'
    html += '<th colspan="2" class="sub-header">균열율</th>'
    html += '<th colspan="2" class="sub-header">누수 및<br>백태<br>면적율(%)</th>'
    html += '<th colspan="2" class="sub-header">표면손상<br>면적율(%)</th>'
    html += '<th colspan="2" class="sub-header">철근부식<br>손상면적율(%)</th>'
    html += '</tr>'
    html += '<tr>'
    html += '<th>(mm)</th><th>평가</th>'
    html += '<th>(%)</th><th>평가</th>'
    html += '<th>(mm)</th><th>평가</th>'
    html += '<th>(%)</th><th>평가</th>'
    html += '<th>값</th><th>평가</th>'
    html += '<th>값</th><th>평가</th>'
    html += '<th>값</th><th>평가</th>'
    html += '</tr>'
    html += '</thead>'
    html += '<tbody>'

    for position, eval_data in positions.items():
        html += '<tr>'
        # None 값 안전 처리
        inspection_area = eval_data.get("inspection_area", 0)
        if inspection_area is None:
            inspection_area = 0
        # 0인 경우 '-'로 표시
        inspection_area_str = '-' if inspection_area == 0 else f'{inspection_area:.1f}'

        # 1방향 균열 데이터 안전 처리
        crack_1d_width = eval_data.get("1d_crack_width", 0)
        if crack_1d_width is None:
            crack_1d_width = 0
        crack_1d_width_str = '-' if crack_1d_width == 0 else f'{crack_1d_width:.1f}'

        crack_1d_grade = eval_data.get("1d_crack_grade", "a")
        if crack_1d_grade is None:
            crack_1d_grade = "a"

        crack_1d_ratio = eval_data.get("1d_crack_ratio", 0)
        if crack_1d_ratio is None:
            crack_1d_ratio = 0
        crack_1d_ratio_str = '-' if crack_1d_ratio == 0 else f'{crack_1d_ratio:.2f}'

        crack_1d_ratio_grade = eval_data.get("1d_crack_ratio_grade", "a")
        if crack_1d_ratio_grade is None:
            crack_1d_ratio_grade = "a"

        # 2방향 균열 데이터 안전 처리
        crack_2d_width = eval_data.get("2d_crack_width", 0)
        if crack_2d_width is None:
            crack_2d_width = 0
        crack_2d_width_str = '-' if crack_2d_width == 0 else f'{crack_2d_width:.1f}'

        crack_2d_grade = eval_data.get("2d_crack_grade", "a")
        if crack_2d_grade is None:
            crack_2d_grade = "a"

        crack_2d_ratio = eval_data.get("2d_crack_ratio", 0)
        if crack_2d_ratio is None:
            crack_2d_ratio = 0
        crack_2d_ratio_str = '-' if crack_2d_ratio == 0 else f'{crack_2d_ratio:.2f}'

        crack_2d_ratio_grade = eval_data.get("2d_crack_ratio_grade", "a")
        if crack_2d_ratio_grade is None:
            crack_2d_ratio_grade = "a"

        # 열화 및 손상 데이터 안전 처리 (API와 일치하는 필드명 사용)
        # API에서 leak_ratio, surface_damage_ratio, rebar_corrosion_ratio 사용
        leakage_ratio = eval_data.get("leak_ratio", 0) or eval_data.get("leakage_ratio", 0)
        if leakage_ratio is None:
            leakage_ratio = 0
        leakage_ratio_str = '-' if leakage_ratio == 0 else f'{leakage_ratio:.2f}'

        leakage_grade = eval_data.get("leakage_grade", "a")
        if leakage_grade is None:
            leakage_grade = "a"

        surface_damage_ratio = eval_data.get("surface_damage_ratio", 0) or eval_data.get("surface_deterioration_ratio", 0)
        if surface_damage_ratio is None:
            surface_damage_ratio = 0
        surface_damage_ratio_str = '-' if surface_damage_ratio == 0 else f'{surface_damage_ratio:.3f}'

        surface_damage_grade = eval_data.get("surface_damage_grade", "a")
        if surface_damage_grade is None:
            surface_damage_grade = "a"

        rebar_corrosion_ratio = eval_data.get("rebar_corrosion_ratio", 0)
        if rebar_corrosion_ratio is None:
            rebar_corrosion_ratio = 0
        rebar_corrosion_ratio_str = '-' if rebar_corrosion_ratio == 0 else f'{rebar_corrosion_ratio:.2f}'

        rebar_corrosion_grade = eval_data.get("rebar_corrosion_grade", "a")
        if rebar_corrosion_grade is None:
            rebar_corrosion_grade = "a"

        # 최종 등급 안전 처리
        final_grade = eval_data.get("final_grade", "a")
        if final_grade is None:
            final_grade = "a"

        html += f'<td>{position}</td>'
        html += f'<td>{inspection_area_str}</td>'

        # 1방향 균열
        html += f'<td>{crack_1d_width_str}</td>'
        html += f'<td>{crack_1d_grade}</td>'
        html += f'<td>{crack_1d_ratio_str}</td>'
        html += f'<td>{crack_1d_ratio_grade}</td>'

        # 2방향 균열
        html += f'<td>{crack_2d_width_str}</td>'
        html += f'<td>{crack_2d_grade}</td>'
        html += f'<td>{crack_2d_ratio_str}</td>'
        html += f'<td>{crack_2d_ratio_grade}</td>'

        # 열화 및 손상
        html += f'<td>{leakage_ratio_str}</td>'
        html += f'<td>{leakage_grade}</td>'
        html += f'<td>{surface_damage_ratio_str}</td>'
        html += f'<td>{surface_damage_grade}</td>'
        html += f'<td>{rebar_corrosion_ratio_str}</td>'
        html += f'<td>{rebar_corrosion_grade}</td>'

        # 최종 등급
        html += f'<td>{final_grade}</td>'
        html += '</tr>'

    html += '</tbody></table>'
    return html


def generate_girder_evaluation_table(component, positions):
    """거더 상태평가표 HTML 생성"""
    html = f'<h4>{component} 상태평가 결과</h4>'
    html += '<table>'
    html += '<thead>'
    html += '<tr>'
    html += '<th rowspan="2">구분</th>'
    html += '<th rowspan="2">점검면적<br>(m²)</th>'
    html += '<th colspan="6" class="main-header">모재 및 연결부 손상</th>'
    html += '<th colspan="2" class="main-header">표면열화<br>면적율(%)</th>'
    html += '<th rowspan="2" class="main-header">상태평가<br>결과</th>'
    html += '</tr>'
    html += '<tr>'
    html += '<th>부재 균열</th><th>변형, 파단</th>'
    html += '<th>연결 볼트<br>이완, 탈락</th><th>용접연결부<br>결함</th>'
    html += '<th>표면열화<br>면적율(%)</th><th>상태평가<br>결과</th>'
    html += '</tr>'
    html += '</thead>'
    html += '<tbody>'

    for position, eval_data in positions.items():
        # None 값 안전 처리
        inspection_area = eval_data.get("inspection_area", 0)
        if inspection_area is None:
            inspection_area = 0
        inspection_area_str = '-' if inspection_area == 0 else f'{inspection_area:.1f}'

        crack_grade = eval_data.get("crack_grade", "a")
        if crack_grade is None:
            crack_grade = "a"

        surface_damage_ratio = eval_data.get("surface_damage_ratio", 0) or eval_data.get("surface_deterioration_ratio", 0)
        if surface_damage_ratio is None:
            surface_damage_ratio = 0
        surface_damage_ratio_str = '-' if surface_damage_ratio == 0 else f'{surface_damage_ratio:.2f}'

        surface_damage_grade = eval_data.get("surface_damage_grade", "a")
        if surface_damage_grade is None:
            surface_damage_grade = "a"

        final_grade = eval_data.get("final_grade", "a")
        if final_grade is None:
            final_grade = "a"

        html += '<tr>'
        html += f'<td>{position}</td>'
        html += f'<td>{inspection_area_str}</td>'

        # 모재 및 연결부 손상 (간략화)
        html += f'<td>{crack_grade}</td>'
        html += '<td>a</td>'  # 변형, 파단
        html += '<td>a</td>'  # 연결 볼트
        html += '<td>a</td>'  # 용접연결부

        # 표면열화
        html += f'<td>{surface_damage_ratio_str}</td>'
        html += f'<td>{surface_damage_grade}</td>'

        # 최종 등급
        html += f'<td>{final_grade}</td>'
        html += '</tr>'

    html += '</tbody></table>'
    return html


def generate_crossbeam_evaluation_table(component, positions):
    """가로보/세로보 상태평가표 HTML 생성"""
    html = f'<h4>{component} 상태평가 결과</h4>'
    html += '<table>'
    html += '<thead>'
    html += '<tr>'
    html += '<th rowspan="2">구분</th>'
    html += '<th rowspan="2">점검면적<br>(m²)</th>'
    html += '<th colspan="4" class="main-header">모재 및 연결부 손상</th>'
    html += '<th colspan="2" class="main-header">표면열화<br>면적율(%)</th>'
    html += '<th rowspan="2" class="main-header">상태평가<br>결과</th>'
    html += '</tr>'
    html += '<tr>'
    html += '<th>부재 균열</th><th>변형, 파단</th>'
    html += '<th>연결 볼트<br>이완, 탈락</th><th>용접연결부<br>결함</th>'
    html += '<th>표면열화<br>면적율(%)</th><th>상태평가<br>결과</th>'
    html += '</tr>'
    html += '</thead>'
    html += '<tbody>'

    for position, eval_data in positions.items():
        # None 값 안전 처리
        inspection_area = eval_data.get("inspection_area", 0)
        if inspection_area is None:
            inspection_area = 0
        inspection_area_str = '-' if inspection_area == 0 else f'{inspection_area:.1f}'

        crack_grade = eval_data.get("crack_grade", "a")
        if crack_grade is None:
            crack_grade = "a"

        surface_damage_ratio = eval_data.get("surface_damage_ratio", 0) or eval_data.get("surface_deterioration_ratio", 0)
        if surface_damage_ratio is None:
            surface_damage_ratio = 0
        surface_damage_ratio_str = '-' if surface_damage_ratio == 0 else f'{surface_damage_ratio:.2f}'

        surface_damage_grade = eval_data.get("surface_damage_grade", "a")
        if surface_damage_grade is None:
            surface_damage_grade = "a"

        final_grade = eval_data.get("final_grade", "a")
        if final_grade is None:
            final_grade = "a"

        html += '<tr>'
        html += f'<td>{position}</td>'
        html += f'<td>{inspection_area_str}</td>'

        # 모재 및 연결부 손상
        html += f'<td>{crack_grade}</td>'
        html += '<td>a</td>'  # 변형, 파단
        html += '<td>a</td>'  # 연결 볼트
        html += '<td>a</td>'  # 용접연결부

        # 표면열화
        html += f'<td>{surface_damage_ratio_str}</td>'
        html += f'<td>{surface_damage_grade}</td>'

        # 최종 등급
        html += f'<td>{final_grade}</td>'
        html += '</tr>'

    html += '</tbody></table>'
    return html


def generate_basic_evaluation_table(component, positions):
    """교대, 교각 등 기본 부재의 상태평가 테이블 생성"""
    html = f'<h4>{component} 상태평가</h4>'
    html += '<div class="table-container">'
    html += '<table class="table table-sm">'
    html += '<thead><tr>'
    html += '<th>부재위치</th>'
    html += '<th>최대균열폭(mm)</th>'
    html += '<th>균열율(%)</th>'
    html += '<th>표면손상 면적율(%)</th>'
    html += '<th>누수 면적율(%)</th>'
    html += '<th>철근부식 면적율(%)</th>'
    html += '<th>상태등급</th>'
    html += '</tr></thead><tbody>'

    for position in sorted(positions.keys(), key=natural_sort_position):
        data = positions[position]

        # 표시값 처리
        crack_width = data['crack_width']
        crack_width_str = '-' if crack_width == 0 else f'{crack_width:.1f}'

        crack_ratio = data['crack_ratio']
        crack_ratio_str = '-' if crack_ratio == 0 else f'{crack_ratio:.2f}'

        surface_damage = data['surface_damage']
        surface_damage_str = '-' if surface_damage == 0 else f'{surface_damage:.2f}'

        leakage = data['leakage']
        leakage_str = '-' if leakage == 0 else f'{leakage:.2f}'

        rebar_corrosion = data['rebar_corrosion']
        rebar_corrosion_str = '-' if rebar_corrosion == 0 else f'{rebar_corrosion:.2f}'

        final_grade = data['final_grade']

        html += f'<tr>'
        html += f'<td>{position}</td>'
        html += f'<td>{crack_width_str}</td>'
        html += f'<td>{crack_ratio_str}</td>'
        html += f'<td>{surface_damage_str}</td>'
        html += f'<td>{leakage_str}</td>'
        html += f'<td>{rebar_corrosion_str}</td>'
        html += f'<td>{final_grade}</td>'
        html += f'</tr>'

    html += '</tbody></table></div>'
    return html
