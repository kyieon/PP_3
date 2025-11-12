"""
교량 상태평가용 데이터 처리 모듈
부재명, 부재위치, 손상내용, 균열폭, 손상물량 데이터를 상태평가용으로 피벗
"""
import pandas as pd
import re
from collections import defaultdict
from utils.common import normalize_component, sort_components


def extract_crack_width_from_uploaded_data(df, component_name, position, damage_desc):
    """업로드한 파일의 균열폭 열에서 데이터를 추출"""
    try:
        # 해당 경간의 해당 손상에 대한 균열폭 데이터 검색
        mask = (df['부재명'] == component_name) & \
               (df['부재위치'] == position) & \
               (df['손상내용'] == damage_desc)
        
        matched_data = df[mask]
        
        if not matched_data.empty and '균열폭' in df.columns:
            # 균열폭 열이 있으면 해당 값들 중 최대값 반환
            crack_widths = pd.to_numeric(matched_data['균열폭'], errors='coerce').dropna()
            if not crack_widths.empty:
                return float(crack_widths.max())
        
        # 균열폭 열이 없거나 데이터가 없으면 손상내용에서 추출 시도
        return extract_crack_width_from_description(damage_desc)
        
    except Exception as e:
        print(f"균열폭 추출 중 오류: {e}")
        return extract_crack_width_from_description(damage_desc)


def extract_crack_width_from_description(damage_desc):
    """손상내용에서 균열폭 추출 (기존 방식)"""
    if '균열' not in damage_desc:
        return None
    
    # 균열폭 패턴 매칭 (mm, ㎜)
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)',
        r'균열\((\d+(?:\.\d+)?)(?:mm|㎜)?\)',
        r'폭[=:]\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, damage_desc)
        if match:
            return float(match.group(1))
    
    return None


def calculate_crack_ratio_for_span(df, component_name, position, crack_direction):
    """해당 경간의 균열율 계산 (모든 균열의 합계)"""
    try:
        # 해당 경간의 해당 방향 균열 데이터 필터링
        if crack_direction == '1방향':
            # 1방향 균열: 균열, 균열부 백태, 균열이 들어간 손상들 (망상균열 제외)
            mask = (df['부재명'] == component_name) & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('균열', na=False)) & \
                   (~df['손상내용'].str.contains('망상균열', na=False))
        else:  # 2방향
            # 2방향 균열: 망상균열이 포함된 손상들
            mask = (df['부재명'] == component_name) & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('망상균열', na=False))
        
        matched_data = df[mask]
        
        if not matched_data.empty:
            # 손상물량의 합계 반환
            total_quantity = pd.to_numeric(matched_data['손상물량'], errors='coerce').sum()
            return float(total_quantity) if pd.notnull(total_quantity) else 0
        
        return 0
        
    except Exception as e:
        print(f"균열율 계산 중 오류: {e}")
        return 0


def get_max_crack_width_for_span(df, component_name, position, crack_direction):
    """해당 경간의 최대 균열폭 계산"""
    try:
        # 해당 경간의 해당 방향 균열 데이터 필터링
        if crack_direction == '1방향':
            # 1방향 균열: 균열, 균열부 백태, 균열이 들어간 손상들 (망상균열 제외)
            mask = (df['부재명'] == component_name) & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('균열', na=False)) & \
                   (~df['손상내용'].str.contains('망상균열', na=False))
        else:  # 2방향
            # 2방향 균열: 망상균열이 포함된 손상들
            mask = (df['부재명'] == component_name) & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('망상균열', na=False))
        
        matched_data = df[mask]
        
        if matched_data.empty:
            return 0 if crack_direction == '1방향' else 0.2  # 2방향 균열폭이 없으면 0.2 자동 설정
        
        max_width = 0
        for _, row in matched_data.iterrows():
            width = extract_crack_width_from_uploaded_data(df, component_name, position, row['손상내용'])
            if width is not None:
                max_width = max(max_width, width)
        
        # 2방향 균열에서 균열폭이 없으면 0.2 자동 설정
        if max_width == 0 and crack_direction == '2방향':
            return 0.2
            
        return max_width
        
    except Exception as e:
        print(f"최대 균열폭 계산 중 오류: {e}")
        return 0 if crack_direction == '1방향' else 0.2


def classify_damage_for_evaluation(damage_desc):
    """상태평가용 손상 분류"""
    damage_desc = damage_desc.strip()
    
    # 균열 관련
    if '균열' in damage_desc:
        crack_width = extract_crack_width(damage_desc)
        if crack_width is not None:
            return {
                'type': '균열',
                'crack_width': crack_width,
                'severity': get_crack_severity(crack_width)
            }
        return {'type': '균열', 'crack_width': None, 'severity': 'unknown'}
    
    # 누수 관련
    if any(keyword in damage_desc for keyword in ['누수', '백태', '침출']):
        return {'type': '누수', 'severity': 'moderate'}
    
    # 표면손상 관련
    if any(keyword in damage_desc for keyword in ['박리', '박락', '파손', '재료분리', '층분리']):
        return {'type': '표면손상', 'severity': 'severe'}
    
    # 철근부식 관련
    if any(keyword in damage_desc for keyword in ['철근노출', '철근부식', '부식']):
        return {'type': '철근부식', 'severity': 'severe'}
    
    # 기타
    return {'type': '기타', 'severity': 'minor'}


def get_crack_severity(crack_width):
    """균열폭에 따른 심각도 분류"""
    if crack_width is None:
        return 'unknown'
    elif crack_width >= 1.0:
        return 'very_severe'
    elif crack_width >= 0.5:
        return 'severe'
    elif crack_width >= 0.3:
        return 'moderate'
    elif crack_width >= 0.1:
        return 'minor'
    else:
        return 'very_minor'


def calculate_condition_grade(damage_data):
    """손상 데이터를 기반으로 상태등급 계산"""
    # 최대 균열폭 기준
    max_crack_width = 0
    total_crack_ratio = 0
    has_surface_damage = False
    has_rebar_corrosion = False
    has_leakage = False
    
    for damage in damage_data:
        if damage['type'] == '균열' and damage['crack_width']:
            max_crack_width = max(max_crack_width, damage['crack_width'])
            total_crack_ratio += damage.get('ratio', 0)
        elif damage['type'] == '표면손상':
            has_surface_damage = True
        elif damage['type'] == '철근부식':
            has_rebar_corrosion = True
        elif damage['type'] == '누수':
            has_leakage = True
    
    # 등급 산정 로직
    grade = 'A'  # 우수
    
    # 균열폭 기준
    if max_crack_width >= 1.0:
        grade = 'E'
    elif max_crack_width >= 0.5:
        grade = max(grade, 'D')
    elif max_crack_width >= 0.3:
        grade = max(grade, 'C')
    elif max_crack_width >= 0.1:
        grade = max(grade, 'B')
    
    # 철근부식이 있으면 최소 D등급
    if has_rebar_corrosion:
        grade = max(grade, 'D')
    
    # 표면손상이 있으면 최소 C등급
    if has_surface_damage:
        grade = max(grade, 'C')
    
    # 누수가 있으면 최소 B등급
    if has_leakage:
        grade = max(grade, 'B')
    
    return grade


def filter_data_by_component_type(df, component_filter):
    """부재 유형별로 데이터 필터링"""
    if component_filter == '바닥판':
        return df[df['부재명'].str.contains('바닥판', na=False)]
    elif component_filter == '거더':
        return df[df['부재명'].str.contains('거더', na=False)]
    elif component_filter == '교대':
        return df[df['부재명'].str.contains('교대', na=False)]
    elif component_filter == '교각':
        return df[df['부재명'].str.contains('교각', na=False)]
    else:
        return df  # 전체 데이터 반환


def filter_positions_by_component(df, component_name):
    """부재명에 따라 적절한 부재위치만 필터링"""
    # 바닥판, 거더, 교면포장, 배수시설, 난간 및 연석은 s 경간만
    span_components = ['바닥판', '거더', '교면포장', '배수시설', '난간', '연석']
    
    # 해당 부재가 span_components에 포함되는지 확인
    is_span_component = any(comp in component_name for comp in span_components)
    
    if is_span_component:
        # s로 시작하는 부재위치만 필터링 (s1, s2, s3 등)
        return df[df['부재위치'].str.match(r'^s\d+', case=False, na=False)]
    else:
        # a, p로 시작하는 부재위치만 필터링 (a1, p1, p2, a2 등)
        return df[df['부재위치'].str.match(r'^[ap]\d*', case=False, na=False)]


def generate_condition_evaluation_pivot(df, component_filter=None):
    """상태평가용 피벗 테이블 생성"""
    # 데이터 전처리
    df = df.copy()
    df['부재위치'] = df['부재위치'].astype(str)
    df['손상물량'] = pd.to_numeric(df['손상물량'], errors='coerce').fillna(0)
    
    # 부재 유형별 필터링 적용
    if component_filter:
        df = filter_data_by_component_type(df, component_filter)
    
    # 부재명별로 그룹화
    components = sort_components(df['부재명'].unique())
    
    evaluation_data = {}
    
    for component in components:
        component_df = df[df['부재명'] == component]
        
        # 부재명에 따라 적절한 부재위치만 필터링
        component_df = filter_positions_by_component(component_df, component)
        
        positions = sorted(component_df['부재위치'].unique())
        
        evaluation_data[component] = {
            'positions': {},
            'summary': {
                'max_crack_width': 0,
                'total_damage_count': 0,
                'condition_grade': 'A'
            }
        }
        
        all_damages = []
        
        for position in positions:
            # 기존 방식 (모든 부재들)
            pos_df = component_df[component_df['부재위치'] == position]
            
            position_data = {
                'damages': [],
                'crack_width_max': 0,
                'damage_quantities': {},
                'condition_grade': 'A'
            }
            
            for _, row in pos_df.iterrows():
                damage_info = classify_damage_for_evaluation(row['손상내용'])
                damage_info['quantity'] = row['손상물량']
                damage_info['original_desc'] = row['손상내용']
                
                position_data['damages'].append(damage_info)
                all_damages.append(damage_info)
                
                # 최대 균열폭 업데이트
                if damage_info['type'] == '균열' and damage_info.get('crack_width'):
                    position_data['crack_width_max'] = max(
                        position_data['crack_width_max'], 
                        damage_info['crack_width']
                    )
                
                # 손상 유형별 물량 합계
                damage_type = damage_info['type']
                if damage_type not in position_data['damage_quantities']:
                    position_data['damage_quantities'][damage_type] = 0
                position_data['damage_quantities'][damage_type] += damage_info['quantity']
            
            # 위치별 상태등급 계산
            position_data['condition_grade'] = calculate_condition_grade(position_data['damages'])
            evaluation_data[component]['positions'][position] = position_data
        
        # 부재 전체 요약 정보 계산
        evaluation_data[component]['summary']['condition_grade'] = calculate_condition_grade(all_damages)
        evaluation_data[component]['summary']['max_crack_width'] = max(
            [pos_data['crack_width_max'] for pos_data in evaluation_data[component]['positions'].values()],
            default=0
        )
        evaluation_data[component]['summary']['total_damage_count'] = len(all_damages)
    
    return evaluation_data


def generate_condition_evaluation_html(evaluation_data, component_filter=None):
    """상태평가 결과를 HTML 테이블로 생성"""
    html = '<div class="condition-evaluation-container">'
    
    # 부재별 필터 제목 추가
    if component_filter:
        html += f'<h3>{component_filter} 상태평가 결과</h3>'
    else:
        html += '<h3>전체 상태평가 결과</h3>'
    
    # 요약 테이블
    html += '<h4>부재별 상태평가 요약</h4>'
    html += '<div class="table-container">'
    html += '<table class="table table-striped">'
    html += '<thead><tr>'
    html += '<th>부재명</th><th>최대 균열폭(mm)</th><th>손상 개소</th><th>상태등급</th>'
    html += '</tr></thead><tbody>'
    
    for component, data in evaluation_data.items():
        summary = data['summary']
        
        # None 값 처리
        max_crack_width = summary.get("max_crack_width", 0)
        if max_crack_width is None:
            max_crack_width = 0
        # 0인 경우 '-'로 표시
        max_crack_width_str = '-' if max_crack_width == 0 else f'{max_crack_width:.1f}'
            
        total_damage_count = summary.get("total_damage_count", 0)
        if total_damage_count is None:
            total_damage_count = 0
        # 0인 경우 '-'로 표시
        total_damage_count_str = '-' if total_damage_count == 0 else str(total_damage_count)
            
        condition_grade = summary.get("condition_grade", "A")
        if condition_grade is None:
            condition_grade = "A"
        
        html += f'<tr>'
        html += f'<td><strong>{component}</strong></td>'
        html += f'<td>{max_crack_width_str}</td>'
        html += f'<td>{total_damage_count_str}</td>'
        html += f'<td>{condition_grade.lower()}</td>'  # 색상 제거, 등급만 표시
        html += f'</tr>'
    
    html += '</tbody></table></div>'
    
    # 상세 테이블 (부재별)
    for component, data in evaluation_data.items():
        html += f'<h5 class="mt-4">{component} 상세 평가</h5>'
        html += '<div class="table-container">'
        html += '<table class="table table-sm">'
        html += '<thead><tr>'
        html += '<th>부재위치</th><th>손상내용</th><th>균열폭(mm)</th><th>손상물량</th><th>상태등급</th>'
        html += '</tr></thead><tbody>'
        
        for position, pos_data in data['positions'].items():
            for i, damage in enumerate(pos_data['damages']):
                if i == 0:  # 첫 번째 행에만 위치와 등급 표시
                    rowspan = len(pos_data['damages'])
                    html += f'<tr>'
                    html += f'<td rowspan="{rowspan}">{position}</td>'
                else:
                    html += f'<tr>'
                
                crack_width = damage.get('crack_width')
                if crack_width is not None and crack_width > 0:
                    crack_width_str = f"{crack_width:.1f}"
                else:
                    crack_width_str = '-'
                
                # 손상내용과 손상물량 None 값 처리
                original_desc = damage.get("original_desc", "")
                if original_desc is None:
                    original_desc = ""
                    
                quantity = damage.get("quantity", 0)
                if quantity is None:
                    quantity = 0
                # 0인 경우 '-'로 표시
                quantity_str = '-' if quantity == 0 else f'{quantity:.2f}'
                
                html += f'<td>{original_desc}</td>'
                html += f'<td>{crack_width_str}</td>'
                html += f'<td>{quantity_str}</td>'
                
                if i == 0:  # 첫 번째 행에만 등급 표시
                    condition_grade = pos_data.get('condition_grade', 'A')
                    if condition_grade is None:
                        condition_grade = 'A'
                    html += f'<td rowspan="{rowspan}">{condition_grade.lower()}</td>'  # 색상 제거, 등급만 표시
                
                html += f'</tr>'
        
        html += '</tbody></table></div>'
    
    html += '</div>'
    
    # CSS 스타일 추가
    html += '''
    <style>
        .condition-evaluation-container {
            margin: 20px 0;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            color: white;
        }
        .grade-a { background-color: #28a745; }
        .grade-b { background-color: #17a2b8; }
        .grade-c { background-color: #ffc107; color: #212529; }
        .grade-d { background-color: #fd7e14; }
        .grade-e { background-color: #dc3545; }
    </style>
    '''
    
    return html


def generate_component_specific_evaluation_html(df, component_type):
    """부재별 상태평가표 HTML 생성"""
    # 부재별 평가 데이터 생성
    evaluation_data = generate_condition_evaluation_pivot(df, component_type)
    
    # HTML 생성
    html = generate_condition_evaluation_html(evaluation_data, component_type)
    
    return html


def generate_all_component_evaluations(df):
    """모든 부재에 대한 상태평가표 HTML 생성"""
    component_types = ['바닥판', '거더', '교대', '교각']
    
    all_html = '<div class="all-component-evaluations">'
    
    for component_type in component_types:
        # 해당 부재 데이터가 있는지 확인
        filtered_df = filter_data_by_component_type(df, component_type)
        if not filtered_df.empty:
            all_html += f'<div class="component-evaluation-section">'
            all_html += generate_component_specific_evaluation_html(df, component_type)
            all_html += f'</div>'
            all_html += '<hr style="margin: 30px 0;">'
    
    all_html += '</div>'
    
    return all_html
