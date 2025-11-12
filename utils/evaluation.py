"""
상태평가표 생성을 위한 유틸리티 함수들
"""
import re
from typing import List, Dict, Any
import pandas as pd
from utils.common import remove_special_characters, normalize_damage


def evaluate_slab_condition(crack_width=None, crack_ratio=None, leak_ratio=None,
                          surface_damage_ratio=None, rebar_corrosion_ratio=None,
                          other_damage=False):
    """
    일반 콘크리트 바닥판 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열폭 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 1.0:
            return 'e'
        elif crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    # 균열률 기준
    if crack_ratio is not None:
        has_any_damage = True
        if crack_ratio >= 20:
            return 'e'
        elif crack_ratio >= 10:
            grade = max(grade, 'd')
        elif crack_ratio >= 2:
            grade = max(grade, 'c')
        elif crack_ratio > 0:
            grade = max(grade, 'b')

    # 누수 및 백태 기준
    if leak_ratio is not None:
        has_any_damage = True
        if leak_ratio >= 10:
            grade = max(grade, 'c')
        elif leak_ratio > 0:
            grade = max(grade, 'b')

    # 표면손상 기준
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근 부식 기준 (철근노출 포함)
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 손상이 전혀 없는 경우
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_slab_damage(damage_desc):
    """
    손상 내용에 따라 콘크리트 바닥판의 상태평가 등급을 자동으로 결정하는 함수
    """
    # 균열 관련 패턴
    crack_pattern = r'균열\((\d+(?:\.\d+)?)mm\)'
    crack_match = re.search(crack_pattern, damage_desc)
    crack_width = float(crack_match.group(1)) if crack_match else None

    # 균열률 관련 패턴
    crack_ratio_pattern = r'균열률\s*(\d+(?:\.\d+)?)%'
    crack_ratio_match = re.search(crack_ratio_pattern, damage_desc)
    crack_ratio = float(crack_ratio_match.group(1)) if crack_ratio_match else None

    # 누수 및 백태 관련 패턴
    leak_pattern = r'(?:누수|백태)\s*(\d+(?:\.\d+)?)%'
    leak_match = re.search(leak_pattern, damage_desc)
    leak_ratio = float(leak_match.group(1)) if leak_match else None

    # 표면손상 관련 패턴
    surface_pattern = r'표면손상\s*(\d+(?:\.\d+)?)%'
    surface_match = re.search(surface_pattern, damage_desc)
    surface_damage_ratio = float(surface_match.group(1)) if surface_match else None

    # 철근부식 관련 패턴
    rebar_pattern = r'철근부식\s*(\d+(?:\.\d+)?)%'
    rebar_match = re.search(rebar_pattern, damage_desc)
    if rebar_match and '잡철근노출' not in damage_desc:
        return float(rebar_match.group(1))

    # 기타 손상 여부 확인
    other_damage = any(x in damage_desc for x in ['박리', '들뜸', '파손', '침식', '세굴'])

    # 상태평가 등급 결정
    return evaluate_slab_condition(
        crack_width=crack_width,
        crack_ratio=crack_ratio,
        leak_ratio=leak_ratio,
        surface_damage_ratio=surface_damage_ratio,
        rebar_corrosion_ratio=rebar_corrosion_ratio,
        other_damage=other_damage
    )

def get_default_evaluation_data(name):
    """
    기본 평가 데이터 구조 생성
    """
    return {
        '번호': name,
        '구조형식': 'PF',  # 기본값으로 PF 설정
        '상부구조': {
            '바닥판': evaluate_slab_condition(),  # 기본값
            '거더': 'b',
            '가로보': 'b',
            '포장': 'b',
            '배수': 'a'
        },
        '2차부재': {
            '난간연석': 'b',
            '신축이음': 'b',
            '교량받침': 'b'
        },
        '하부구조': {
            '하부': 'b',
            '기초': 'Q'
        },
        '내구성요소': {
            '탄산화': {'상부': 'a', '하부': 'a'},
            '염화물': {'상부': '-', '하부': '-'}
        }
    }

def get_weights_by_structure_type(structure_type):
    """
    구조형식별 부재 가중치 반환
    """
    # 표 1.30 구조형식에 따른 일반교량의 부재별 가중치
    weights = {
        '일반거더교': {
            '바닥판': 18,
            '거더': 18,
            '2차부재': 5,
            '교대/교각': 13,
            '기초': 7,
            '교량받침': 9,
            '신축이음': 9,
            '교면포장': 7,
            '배수시설': 3,
            '난간/연석': 2,
            '탄산화': {'상부': 2, '하부': 2},
            '염화물': {'상부': 2, '하부': 1}
        },
        '2차부재없음': {
            '바닥판': 18,
            '거더': 25,
            '2차부재': 0,
            '교대/교각': 13,
            '기초': 7,
            '교량받침': 9,
            '신축이음': 9,
            '교면포장': 7,
            '배수시설': 3,
            '난간/연석': 2,
            '탄산화': {'상부': 2, '하부': 2},
            '염화물': {'상부': 2, '하부': 1}
        },
        '바닥판거더일체형': {
            '바닥판': 37,
            '거더': 0,
            '2차부재': 11,
            '교대/교각': 18,
            '기초': 7,
            '교량받침': 14,
            '신축이음': 0,
            '교면포장': 0,
            '배수시설': 0,
            '난간/연석': 6,
            '탄산화': {'상부': 4, '하부': 4},
            '염화물': {'상부': 3, '하부': 3}
        }
    }

    return weights.get(structure_type, weights['일반거더교'])

def calculate_defect_score(eval_result):
    """
    평가 결과로부터 결함도 점수를 계산하는 함수

    Args:
        eval_result (dict): 평가 결과 데이터

    Returns:
        float: 결함도 점수
    """
    structure_type = eval_result.get('구조형식', '일반거더교')
    weights = get_weights_by_structure_type(structure_type)

    # 상부구조 평가
    superstructure_score = 0
    superstructure_weight = 0
    for component, grade in eval_result['상부구조'].items():
        if component in weights:
            superstructure_score += grade_to_defect_score(grade) * weights[component]
            superstructure_weight += weights[component]

    # 2차부재 평가
    secondary_score = 0
    secondary_weight = 0
    for component, grade in eval_result['2차부재'].items():
        if component in weights:
            secondary_score += grade_to_defect_score(grade) * weights[component]
            secondary_weight += weights[component]

    # 하부구조 평가
    substructure_score = 0
    substructure_weight = 0
    for component, grade in eval_result['하부구조'].items():
        if component in weights:
            substructure_score += grade_to_defect_score(grade) * weights[component]
            substructure_weight += weights[component]

    # 내구성요소 평가
    durability_score = 0
    durability_weight = 0
    for component, grades in eval_result['내구성요소'].items():
        if component in weights:
            for part, grade in grades.items():
                if part in weights[component]:
                    durability_score += grade_to_defect_score(grade) * weights[component][part]
                    durability_weight += weights[component][part]

    # 전체 가중치 계산
    total_weight = superstructure_weight + secondary_weight + substructure_weight + durability_weight

    if total_weight == 0:
        return 0.0

    # 최종 결함도 점수 계산
    final_score = (superstructure_score + secondary_score + substructure_score + durability_score) / total_weight

    return final_score

def get_condition_grade(defect_score):
    """
    결함도 점수에 따른 상태등급을 반환하는 함수

    Args:
        defect_score (float): 결함도 점수

    Returns:
        str: 상태등급 (A~E)
    """
    if defect_score <= 0.2:
        return 'A'
    elif defect_score <= 0.4:
        return 'B'
    elif defect_score <= 0.6:
        return 'C'
    elif defect_score <= 0.8:
        return 'D'
    else:
        return 'E'

def grade_to_defect_score(grade):
    """
    상태등급을 결함도 점수로 변환하는 함수

    Args:
        grade (str): 상태등급 (a~e)

    Returns:
        float: 결함도 점수
    """
    grade = grade.lower()
    if grade == 'a':
        return 0.0
    elif grade == 'b':
        return 0.3
    elif grade == 'c':
        return 0.5
    elif grade == 'd':
        return 0.7
    elif grade == 'e':
        return 1.0
    else:
        return 0.0

def update_evaluation_data(row_data, damage_desc):
    """
    손상 내용에 따라 평가 데이터 업데이트
    """
    # 바닥판 상태평가
    if '균열' in damage_desc:
        match = re.search(r'(\d+(\.\d+)?)mm', damage_desc)
        if match:
            crack_width = float(match.group(1))
            row_data['상부구조']['바닥판'] = evaluate_slab_condition(crack_width=crack_width)

    # 포장 관련 손상
    if '포장' in damage_desc:
        if '파손' in damage_desc or '균열' in damage_desc:
            row_data['상부구조']['포장'] = 'c'

    # 배수 관련 손상
    if '배수' in damage_desc or '누수' in damage_desc:
        row_data['상부구조']['배수'] = 'b'

    # 난간 관련 손상
    if '난간' in damage_desc:
        row_data['2차부재']['난간연석'] = 'b'

    # 신축이음 관련 손상
    if '신축이음' in damage_desc:
        row_data['2차부재']['신축이음'] = 'b'

    # 교량받침 관련 손상
    if '받침' in damage_desc:
        row_data['2차부재']['교량받침'] = 'b'

    # 하부구조 관련 손상
    if any(x in damage_desc for x in ['교각', '교대', '기둥']):
        row_data['하부구조']['하부'] = 'b'

def generate_evaluation_html(evaluation_data, spans):
    """
    평가 결과를 HTML 테이블 형식으로 생성

    Args:
        evaluation_data (dict): 평가 결과 데이터
        spans (list): 교량 연장 리스트

    Returns:
        str: HTML 형식의 평가 결과 테이블
    """
    if not evaluation_data:
        return "<p>평가 데이터가 없습니다.</p>"

    bridges_data = []
    html = """
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        .final-evaluation { margin-top: 20px; font-weight: bold; }
    </style>
    <table>
        <tr>
            <th>교량 번호</th>
            <th>연장(m)</th>
            <th>환산 결함도 점수</th>
            <th>상태등급</th>
        </tr>
    """

    for bridge_num, (span, eval_result) in enumerate(zip(spans, evaluation_data.values()), 1):
        defect_score = calculate_defect_score(eval_result)
        condition_grade = get_condition_grade(defect_score)

        bridges_data.append({
            '연장': span,
            '환산 결함도 점수': defect_score,
            '상태등급': condition_grade
        })

        html += f"""
        <tr>
            <td>{bridge_num}</td>
            <td>{span}</td>
            <td>{defect_score:.2f}</td>
            <td>{condition_grade}</td>
        </tr>
        """

    html += "</table>"

    if bridges_data:
        final_score, final_grade = generate_final_evaluation(bridges_data)
        html += f"""
        <div class="final-evaluation">
            <p>최종 평가 결과:</p>
            <p>연장비를 고려한 최종 환산 결함도 점수: {final_score:.2f}</p>
            <p>최종 상태등급: {final_grade}</p>
        </div>
        """

    return html

def generate_evaluation_table(df):
    """
    상태평가표 생성 메인 함수
    """
    evaluation_data = {}
    spans = {}

    for name, group in df.groupby('부재명'):
        # 기본 데이터 구조 생성
        row_data = get_default_evaluation_data(name)

        # 구조형식 설정
        if '라멘' in name.lower():
            row_data['구조형식'] = '바닥판거더일체형'
        elif '거더' in name.lower():
            row_data['구조형식'] = '일반거더교'

        # 손상 내용에 따른 평가 등급 조정
        for _, damage in group.iterrows():
            update_evaluation_data(row_data, damage['손상내용'])

            # 연장 정보 저장
            if '연장' in damage:
                spans[name] = float(damage['연장'])

        evaluation_data[name] = row_data

    return generate_evaluation_html(evaluation_data, spans)

def generate_final_evaluation(bridges_data):
    """
    연장비를 고려한 최종 평가 결과 계산

    Args:
        bridges_data (list): 각 교량의 연장, 결함도 점수, 상태등급 정보를 담은 딕셔너리 리스트

    Returns:
        tuple: (최종 환산 결함도 점수, 최종 상태등급)
    """
    total_length = sum(bridge['연장'] for bridge in bridges_data)
    weighted_score = sum(bridge['환산 결함도 점수'] * (bridge['연장'] / total_length) for bridge in bridges_data)

    # 최종 상태등급 결정
    final_grade = get_condition_grade(weighted_score)

    return weighted_score, final_grade

def evaluate_psc_slab_condition(crack_width=None, crack_ratio=None, leak_ratio=None,
                              surface_damage_ratio=None, rebar_corrosion_ratio=None,
                              other_damage=False):
    """
    프리스트레스 콘크리트 바닥판 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열폭 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 0.5:
            return 'e'
        elif crack_width >= 0.3:
            grade = max(grade, 'd')
        elif crack_width >= 0.2:
            grade = max(grade, 'c')
        else:
            grade = max(grade, 'b')

    # 균열률 기준
    if crack_ratio is not None:
        has_any_damage = True
        if crack_ratio >= 20:
            return 'e'
        elif crack_ratio >= 10:
            grade = max(grade, 'd')
        elif crack_ratio >= 2:
            grade = max(grade, 'c')
        else:
            grade = max(grade, 'b')

    # 백태/누수 기준
    if leak_ratio is not None:
        has_any_damage = True
        if leak_ratio >= 10:
            grade = max(grade, 'c')
        elif leak_ratio > 0:
            grade = max(grade, 'b')

    # 표면 손상 기준
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근 부식 기준
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 손상이 전혀 없는 경우
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_rc_girder_condition(crack_width=None, surface_damage_ratio=None,
                               rebar_corrosion_ratio=None,
                               structural_issue=False, other_damage=False):
    """
    철근콘크리트 거더 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열폭 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 1.0:
            return 'e'
        elif crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    # 표면손상 기준
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근부식 기준
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 구조적 손상 여부
    if structural_issue:
        has_any_damage = True
        return 'e'

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 손상 전혀 없으면 a 유지
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_psc_girder_condition(crack_width=None, surface_damage_ratio=None,
                                rebar_corrosion_ratio=None, tendon_corrosion_level=None,
                                structural_issue=False, other_damage=False):
    """
    프리스트레스트 콘크리트 거더 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 0.5:
            return 'e'
        elif crack_width >= 0.3:
            grade = max(grade, 'd')
        elif crack_width >= 0.2:
            grade = max(grade, 'c')
        else:
            grade = max(grade, 'b')

    # 표면 손상
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근 부식
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 강연선 부식 상태
    if tendon_corrosion_level is not None:
        has_any_damage = True
        if tendon_corrosion_level == 'broken':
            return 'e'
        elif tendon_corrosion_level == 'section_loss':
            grade = max(grade, 'd')
        elif tendon_corrosion_level == 'surface':
            grade = max(grade, 'c')
        elif tendon_corrosion_level == 'none':
            grade = max(grade, 'b')

    # 구조적 손상
    if structural_issue:
        has_any_damage = True
        return 'e'

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_steel_component(main_rust_area=None, sub_rust_area=None,
                           section_loss_area=None, weld_defect_level=None,
                           bolt_damage=False, structural_issue=False,
                           other_damage=False):
    """
    강 바닥판 / 강 거더 / 강 교각(강 주탑) 상태평가 등급(a~e) 반환
    """
    grade = 'a'
    has_any_damage = False

    # 주부재 부식
    if main_rust_area is not None:
        has_any_damage = True
        if main_rust_area >= 10:
            return 'e'
        elif main_rust_area >= 2:
            grade = max(grade, 'd')
        elif main_rust_area > 0:
            grade = max(grade, 'c')

    # 보조부재 부식
    if sub_rust_area is not None:
        has_any_damage = True
        if sub_rust_area >= 10:
            grade = max(grade, 'd')
        elif sub_rust_area >= 2:
            grade = max(grade, 'c')
        elif sub_rust_area > 0:
            grade = max(grade, 'b')

    # 단면손실
    if section_loss_area is not None:
        has_any_damage = True
        if section_loss_area >= 10:
            return 'e'
        elif section_loss_area >= 2:
            grade = max(grade, 'd')

    # 용접결함
    if weld_defect_level is not None:
        has_any_damage = True
        if weld_defect_level == 'severe':
            grade = max(grade, 'd')
        elif weld_defect_level == 'minor':
            grade = max(grade, 'c')

    # 연결 볼트 손상
    if bolt_damage:
        has_any_damage = True
        grade = max(grade, 'd')

    # 구조적 손상
    if structural_issue:
        has_any_damage = True
        return 'e'

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_concrete_crossbeam(crack_width=None, surface_damage_ratio=None,
                              rebar_corrosion_ratio=None, other_damage=False):
    """
    콘크리트 가로보 상태평가 등급(a~d)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열폭 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    # 표면손상 기준
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근부식 기준
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 손상 없음
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_steel_crossbeam(main_rust_area=None, sub_rust_area=None,
                           section_loss_area=None, weld_defect_level=None,
                           structural_issue=False, other_damage=False):
    """
    강 가로보·세로보 상태평가 등급(a~d)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 주부재 부식
    if main_rust_area is not None:
        has_any_damage = True
        if main_rust_area >= 2:
            grade = max(grade, 'd')
        elif main_rust_area > 0:
            grade = max(grade, 'c')

    # 보조부재 부식
    if sub_rust_area is not None:
        has_any_damage = True
        if sub_rust_area >= 10:
            grade = max(grade, 'd')
        elif sub_rust_area >= 2:
            grade = max(grade, 'c')
        elif sub_rust_area > 0:
            grade = max(grade, 'b')

    # 단면손상
    if section_loss_area is not None:
        has_any_damage = True
        if section_loss_area >= 2:
            grade = max(grade, 'd')
        elif section_loss_area > 0:
            grade = max(grade, 'c')

    # 용접결함
    if weld_defect_level is not None:
        has_any_damage = True
        if weld_defect_level == 'severe':
            grade = max(grade, 'd')
        elif weld_defect_level == 'minor':
            grade = max(grade, 'c')

    # 구조적 손상
    if structural_issue:
        has_any_damage = True
        grade = max(grade, 'd')

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 손상 없음
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_cable_component(corrosion_length_ratio=None, wire_break_ratio=None,
                           sheath_damage_ratio=None, anchorage_damage=False,
                           structural_failure=False, other_damage=False):
    """
    케이블 부재 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 소선 단선율
    if wire_break_ratio is not None:
        has_any_damage = True
        if wire_break_ratio >= 10:
            return 'e'
        elif wire_break_ratio >= 2:
            grade = max(grade, 'd')
        elif wire_break_ratio > 0:
            grade = max(grade, 'c')

    # 점녹/부식 길이 비율
    if corrosion_length_ratio is not None:
        has_any_damage = True
        if corrosion_length_ratio >= 2:
            grade = max(grade, 'd')
        elif corrosion_length_ratio > 0.1:
            grade = max(grade, 'c')
        else:
            grade = max(grade, 'b')

    # 보호관 손상 길이 비율
    if sheath_damage_ratio is not None:
        has_any_damage = True
        if sheath_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif sheath_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif sheath_damage_ratio > 0:
            grade = max(grade, 'b')

    # 정착구, 행어밴드 등 손상
    if anchorage_damage:
        has_any_damage = True
        grade = max(grade, 'd')

    # 구조적 파손 또는 단선
    if structural_failure:
        return 'e'

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_abutment_condition(crack_width=None, surface_damage_ratio=None,
                              rebar_corrosion_ratio=None, structural_issue=False,
                              severe_structural_risk=False, other_damage=False):
    """
    교대 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 균열폭 기준
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 1.0:
            return 'e'
        elif crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    # 표면손상 기준
    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    # 철근부식 기준
    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    # 구조적 손상 (침하, 기울음, 배면토 유출 등)
    if structural_issue:
        has_any_damage = True
        grade = max(grade, 'd')

    # 심각한 구조적 위험 (전도 위험, 코핑 파손 등)
    if severe_structural_risk:
        return 'e'

    # 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_pier_condition(crack_width=None, surface_damage_ratio=None,
                          rebar_corrosion_ratio=None, structural_issue=False,
                          severe_structural_risk=False, other_damage=False):
    """
    콘크리트 교각 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 1.0:
            return 'e'
        elif crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    if surface_damage_ratio is not None:
        has_any_damage = True
        if surface_damage_ratio >= 10:
            grade = max(grade, 'd')
        elif surface_damage_ratio >= 2:
            grade = max(grade, 'c')
        elif surface_damage_ratio > 0:
            grade = max(grade, 'b')

    if rebar_corrosion_ratio is not None:
        has_any_damage = True
        if rebar_corrosion_ratio >= 2:
            grade = max(grade, 'd')
        elif rebar_corrosion_ratio > 0:
            grade = max(grade, 'c')

    if severe_structural_risk:
        return 'e'

    if structural_issue:
        has_any_damage = True
        grade = max(grade, 'd')

    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_foundation_condition(crack_width=None, section_loss=False,
                               rebar_exposed=False, settlement_or_scour=False,
                               severe_risk=False, other_damage=False):
    """
    기초 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width > 0:
            grade = max(grade, 'b')

    if section_loss:
        has_any_damage = True
        grade = max(grade, 'c')

    if rebar_exposed:
        has_any_damage = True
        grade = max(grade, 'd')

    if settlement_or_scour:
        has_any_damage = True
        grade = max(grade, 'd')

    if severe_risk:
        return 'e'

    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_bearing_condition(rubber_split=False, rubber_bulging=False,
                             shear_deformation='정상',
                             corrosion_area='없음',
                             crack_width=None,
                             structural_failure=False,
                             other_damage=False):
    """
    교량받침 상태평가 등급(a~e)을 반환하는 함수
    """
    grade = 'a'
    has_any_damage = False

    # 1. 구조적 위험
    if structural_failure:
        return 'e'

    # 2. 부식/부착불량
    if corrosion_area == '1/2 이상':
        return 'e'
    elif corrosion_area == '일부':
        has_any_damage = True
        grade = max(grade, 'd')

    # 3. 전단변형량
    if shear_deformation == '1.5T 이상':
        has_any_damage = True
        grade = max(grade, 'd')
    elif shear_deformation == '0.7T 이상':
        has_any_damage = True
        grade = max(grade, 'c')

    # 4. 고무재 손상
    if rubber_split:
        has_any_damage = True
        if rubber_bulging:
            grade = max(grade, 'd')
        else:
            grade = max(grade, 'c')

    # 5. 균열 평가 (모든 종류 포함)
    if crack_width is not None:
        has_any_damage = True
        if crack_width >= 1.0:
            return 'e'
        elif crack_width >= 0.5:
            grade = max(grade, 'd')
        elif crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width >= 0.1:
            grade = max(grade, 'b')

    # 6. 기타 손상
    if other_damage:
        has_any_damage = True
        grade = max(grade, 'b')

    # 7. 손상 없음
    if not has_any_damage:
        grade = 'a'

    return grade

def evaluate_expansion_joint(aging_or_dirt=False,
                           function_degradation=False,
                           impact_or_noise=False,
                           structural_damage=False,
                           other_damage=False):
    """
    신축이음 상태평가 등급(a~d)을 반환하는 함수
    """
    grade = 'a'

    if structural_damage:
        return 'd'

    if impact_or_noise:
        grade = max(grade, 'd')

    if function_degradation:
        grade = max(grade, 'c')

    if aging_or_dirt:
        grade = max(grade, 'b')

    if other_damage:
        grade = max(grade, 'b')

    return grade

def evaluate_pavement_condition(damage_ratio=None,
                              puddle_present=False,
                              pavement_type='아스팔트'):
    """
    교면포장 상태평가 등급(a~d)을 반환하는 함수
    """
    grade = 'a'

    if pavement_type not in ['아스팔트', '콘크리트']:
        raise ValueError("pavement_type must be either '아스팔트' or '콘크리트'")

    if damage_ratio is not None:
        if pavement_type == '아스팔트':
            if damage_ratio >= 10:
                grade = 'd'
            elif damage_ratio >= 5:
                grade = 'c'
            elif damage_ratio > 0:
                grade = 'b'
        elif pavement_type == '콘크리트':
            if damage_ratio >= 30:
                grade = 'd'
            elif damage_ratio >= 10:
                grade = 'c'
            elif damage_ratio > 0:
                grade = 'b'

    if puddle_present:
        grade = max(grade, 'b')

    return grade

def evaluate_drainage_facility(deposit_amount='none',
                             leakage=False,
                             corrosion_due_to_leakage=False,
                             outlet_risk=False,
                             damaged_or_aged=False):
    """
    배수시설 상태평가 등급(a~d)을 반환하는 함수
    """
    if damaged_or_aged:
        return 'd'

    if leakage or corrosion_due_to_leakage or outlet_risk:
        return 'c'

    if deposit_amount == 'many':
        return 'c'
    elif deposit_amount == 'some':
        return 'b'
    else:
        return 'a'

def evaluate_railing_or_curb(paint_damage_ratio=0,
                           local_looseness=False,
                           crack_width=None,
                           section_loss_ratio=0,
                           spalling_or_exposed_rebar_ratio=0,
                           rebar_corrosion_length_ratio=0,
                           overturning_risk=False):
    """
    난간 및 연석 상태평가 등급(a~d)을 반환하는 함수
    """
    grade = 'a'

    if overturning_risk:
        return 'd'

    if section_loss_ratio >= 10 or spalling_or_exposed_rebar_ratio >= 10 or rebar_corrosion_length_ratio >= 2:
        return 'd'

    if section_loss_ratio > 0 or spalling_or_exposed_rebar_ratio > 0 or rebar_corrosion_length_ratio > 0:
        grade = max(grade, 'c')

    if crack_width is not None:
        if crack_width >= 0.3:
            grade = max(grade, 'c')
        elif crack_width > 0:
            grade = max(grade, 'b')

    if paint_damage_ratio >= 10:
        grade = max(grade, 'c')
    elif paint_damage_ratio > 0:
        grade = max(grade, 'b')

    if local_looseness:
        grade = max(grade, 'b')

    return grade

def evaluate_carbonation(remaining_depth=None, rebar_corrosion_confirmed=False):
    """
    탄산화 상태평가 등급(a~e)을 반환하는 함수
    """
    if remaining_depth is None:
        return 'a'

    if remaining_depth < 0:
        return 'e' if rebar_corrosion_confirmed else 'd'
    elif remaining_depth < 10:
        return 'c'
    elif remaining_depth < 30:
        return 'b'
    else:
        return 'a'

def evaluate_chloride(total_chloride=None, rebar_corrosion_confirmed=False):
    """
    염화물 상태평가 등급(a~e)을 반환하는 함수
    """
    if total_chloride is None:
        return 'a'

    if total_chloride >= 2.5:
        return 'e' if rebar_corrosion_confirmed else 'd'
    elif total_chloride >= 1.2:
        return 'c'
    elif total_chloride > 0.3:
        return 'b'
    else:
        return 'a'

# 구조형식별 가중치 사전 정의
STRUCTURE_WEIGHTS = {
    'PSC 박스거더교': {
        '바닥판': 20,
        '교량받침': 9,
        '난간/연석': 2,
        '염화물_상부': 2,
        '거더': 23,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 2,
        '탄산화_하부': 2,
        '염화물_하부': 1,
    },
    '강상형교': {
        '바닥판': 20,
        '교량받침': 9,
        '난간/연석': 2,
        '염화물_상부': 2,
        '강거더': 25,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 1,
        '탄산화_하부': 1,
        '염화물_하부': 2,
    },
    '라멘교': {
        '바닥판': 25,
        '신축이음': 10,
        '교각': 20,
        '교면포장': 8,
        '기초': 10,
        '난간/연석': 7,
    },
    '강박스거더교': {
        '바닥판': 20,
        '교량받침': 9,
        '난간/연석': 2,
        '염화물_상부': 2,
        '강거더': 25,
        '교대/교각': 13,
        '기초': 7,
        '신축이음': 9,
        '교면포장': 7,
        '배수시설': 3,
        '탄산화_상부': 1,
        '탄산화_하부': 1,
        '염화물_하부': 2,
    },
    'RC슬래브교': {
        '슬래브': 28,
        '신축이음': 10,
        '난간/연석': 5,
        '염화물_상부': 2,
        '교대/교각': 15,
        '교면포장': 10,
        '탄산화_상부': 3,
        '염화물_하부': 2,
        '기초': 7,
        '배수시설': 5,
        '탄산화_하부': 3,
    },
    '현수교': {
        '상판': 20,
        '신축이음': 5,
        '탄산화_상부': 2,
        '주탑': 20,
        '케이블': 20,
        '보강형': 15,
        '교면포장': 5,
        '난간/연석': 5,
        '탄산화_하부': 2,
        '염화물_상부': 1,
        '기초': 5,
    },
    '사장교': {
        '상판': 22,
        '신축이음': 5,
        '탄산화_상부': 2,
        '주탑': 20,
        '케이블': 18,
        '보강형': 15,
        '교면포장': 5,
        '난간/연석': 5,
        '탄산화_하부': 2,
        '염화물_상부': 1,
        '기초': 5,
    },
    '아치교': {
        '상부구조': 30,
        '신축이음': 10,
        '탄산화_상부': 3,
        '활하중지지부': 25,
        '교면포장': 10,
        '탄산화_하부': 3,
        '기초': 10,
        '난간/연석': 5,
        '염화물_상부': 2,
    },
}

# 구조형식별 환산결함도 계산
def calculate_structure_defect(component_grades, weight_table):
    total_weight = 0
    weighted_sum = 0
    for component, weight in weight_table.items():
        grade = component_grades.get(component, 'a')  # 입력 없으면 'a'
        score = grade_to_defect_score(grade)
        weighted_sum += score * weight
        total_weight += weight
    return round(weighted_sum / total_weight, 3) if total_weight else 0.0

# 구조형식 이름만 입력하면 자동으로 가중치 적용 + 전체 상태 평가까지 수행
def evaluate_bridge_total_condition(structure_data):
    result = {
        'structure_scores': [],
        'total_defect_score': 0.0,
        'total_grade': 'A'
    }
    total_length = sum(item['length'] for item in structure_data)
    weighted_score_sum = 0

    for item in structure_data:
        name = item['name']
        length = item['length']
        grades = item['component_grades']
        weight_table = STRUCTURE_WEIGHTS.get(name)

        if not weight_table:
            raise ValueError(f"지원하지 않는 구조형식: {name}")

        defect_score = calculate_structure_defect(grades, weight_table)
        length_ratio = length / total_length if total_length else 0
        weighted_score_sum += defect_score * length_ratio

        result['structure_scores'].append({
            'name': name,
            'length': length,
            'defect_score': round(defect_score, 3),
            'grade': get_condition_grade(defect_score),
            'length_ratio': round(length_ratio, 3)
        })

    result['total_defect_score'] = round(weighted_score_sum, 3)
    result['total_grade'] = get_condition_grade(weighted_score_sum)

    import pandas as pd
    import ace_tools as tools
    df = pd.DataFrame(result['structure_scores'])
    tools.display_dataframe_to_user(name="구조형식별 환산결함도 결과", dataframe=df)

    return result

def calculate_automatic_areas(bridge_data: Dict[str, Any]) -> Dict[str, float]:
    """
    교량의 기본 정보를 바탕으로 자동 계산되는 면적들을 계산합니다.

    Args:
        bridge_data (Dict[str, Any]): 교량 기본 정보
            - length: 연장 (m)
            - width: 폭 (m)
            - span_count: 경간 수

    Returns:
        Dict[str, float]: 자동 계산된 면적들
    """
    length = bridge_data['length']
    width = bridge_data['width']
    span_count = bridge_data['span_count']

    # 경간당 길이 계산
    span_length = length / span_count

    # 자동 계산되는 면적들
    areas = {
        'slab': length * width,  # 바닥판 전체 면적
        'pavement': length * width,  # 교면포장 전체 면적
        'railing': length * 2,  # 연석 (좌우 2개)

        # 경간당 면적들
        'span_slab': span_length * width,  # 경간당 바닥판 면적
        'span_pavement': span_length * width,  # 경간당 교면포장 면적
        'span_railing': span_length * 2  # 경간당 연석 길이
    }

    return areas

def validate_bridge_input(bridge_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    교량 입력 데이터의 유효성을 검사하고 필요한 계산을 수행합니다.

    Args:
        bridge_data (Dict[str, Any]): 교량 입력 데이터
            - name: 교량명
            - length: 연장 (m)
            - width: 폭 (m)
            - structure_type: 구조형식
            - span_count: 경간 수
            - expansion_joint_locations: 신축이음 위치 리스트
            - component_areas: 부재별 면적
                - girder: 거더 면적
                - crossbeam: 가로보 면적
                - abutment: 교대 면적
                - pier: 교각 면적

    Returns:
        Dict[str, Any]: 검증 및 계산이 완료된 교량 데이터
    """
    # 필수 입력값 검증
    required_fields = ['name', 'length', 'width', 'structure_type', 'span_count']
    for field in required_fields:
        if field not in bridge_data:
            raise ValueError(f"필수 입력값이 누락되었습니다: {field}")

    # 숫자형 데이터 검증
    if not isinstance(bridge_data['length'], (int, float)) or bridge_data['length'] <= 0:
        raise ValueError("연장은 0보다 큰 숫자여야 합니다.")
    if not isinstance(bridge_data['width'], (int, float)) or bridge_data['width'] <= 0:
        raise ValueError("폭은 0보다 큰 숫자여야 합니다.")
    if not isinstance(bridge_data['span_count'], int) or bridge_data['span_count'] <= 0:
        raise ValueError("경간 수는 0보다 큰 정수여야 합니다.")

    # 자동 계산되는 면적들 추가
    auto_areas = calculate_automatic_areas(bridge_data)

    # 입력된 부재 면적과 자동 계산 면적을 병합
    if 'component_areas' not in bridge_data:
        bridge_data['component_areas'] = {}

    bridge_data['component_areas'].update(auto_areas)

    return bridge_data

def generate_bridge_evaluation_form(bridge_data: Dict[str, Any] = None) -> str:
    """상태평가 입력 폼의 HTML을 생성합니다.

    Args:
        bridge_data: 교량 데이터 (선택적)

    Returns:
        str: 생성된 HTML 폼
    """
    html = '''
    <div class="evaluation-form">
        <h3>교량 상태평가</h3>
        <form id="bridgeEvaluationForm">
            <div class="form-grid">
                <div class="form-section">
                    <h4>교량 기본 정보</h4>
                    <div class="form-group">
                        <label for="bridgeName">교량명</label>
                        <input type="text" id="bridgeName" name="bridgeName" required>
                    </div>
                    <div class="form-group">
                        <label for="length">연장(m)</label>
                        <input type="number" id="length" name="length" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="width">폭(m)</label>
                        <input type="number" id="width" name="width" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="structureType">구조형식</label>
                        <select id="structureType" name="structureType" required>
                            <option value="PSCI">PSCI</option>
                            <option value="STB">STB</option>
                            <option value="RCS">RCS</option>
                            <option value="RA">RA</option>
                            <option value="PSC BOX">PSC BOX</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="spanCount">경간 수</label>
                        <input type="number" id="spanCount" name="spanCount" min="1" required>
                    </div>
                    <div class="form-group">
                        <label for="expansionJoint">신축이음 위치</label>
                        <input type="text" id="expansionJoint" name="expansionJoint" placeholder="예: A1, P1, P2" required>
                    </div>
                </div>
                <div class="form-section">
                    <h4>부재별 면적(m²)</h4>
                    <div class="form-group">
                        <label for="girderArea">거더 면적</label>
                        <input type="number" id="girderArea" name="girderArea" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="crossbeamArea">가로보 면적</label>
                        <input type="number" id="crossbeamArea" name="crossbeamArea" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="abutmentArea">교대 면적</label>
                        <input type="number" id="abutmentArea" name="abutmentArea" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="pierArea">교각 면적</label>
                        <input type="number" id="pierArea" name="pierArea" step="0.01" required>
                    </div>
                </div>
            </div>
            <div class="form-buttons">
                <button type="button" id="evaluateBridge" class="btn btn-primary">평가하기</button>
                <button type="button" id="saveData" class="btn btn-secondary">저장</button>
            </div>
        </form>
        <div id="evaluationResult" class="mt-4">
            <!-- 평가 결과가 여기에 표시됩니다 -->
        </div>
    </div>
    '''

    if bridge_data:
        # 기존 데이터가 있는 경우 폼에 값을 채워넣는 JavaScript 코드 추가
        html += f'''
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                document.getElementById('bridgeName').value = '{bridge_data.get("bridgeName", "")}';
                document.getElementById('length').value = '{bridge_data.get("length", "")}';
                document.getElementById('width').value = '{bridge_data.get("width", "")}';
                document.getElementById('structureType').value = '{bridge_data.get("structureType", "PSCI")}';
                document.getElementById('spanCount').value = '{bridge_data.get("spanCount", "")}';
                document.getElementById('expansionJoint').value = '{bridge_data.get("expansionJoint", "")}';
                document.getElementById('girderArea').value = '{bridge_data.get("girderArea", "")}';
                document.getElementById('crossbeamArea').value = '{bridge_data.get("crossbeamArea", "")}';
                document.getElementById('abutmentArea').value = '{bridge_data.get("abutmentArea", "")}';
                document.getElementById('pierArea').value = '{bridge_data.get("pierArea", "")}';
            }});
        </script>
        '''

    return html

def generate_bridge_evaluation_form(bridge_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    교량 상태평가를 위한 입력 폼을 생성합니다.

    Args:
        bridge_data (Dict[str, Any]): 교량 기본 정보

    Returns:
        Dict[str, Any]: 상태평가 입력 폼
    """
    # 입력 데이터 검증 및 계산
    validated_data = validate_bridge_input(bridge_data)

    # 상태평가 입력 폼 생성
    evaluation_form = {
        'basic_info': {
            '교량명': validated_data['name'],
            '연장': validated_data['length'],
            '폭': validated_data['width'],
            '구조형식': validated_data['structure_type'],
            '경간수': validated_data['span_count'],
            '신축이음위치': validated_data.get('expansion_joint_locations', [])
        },
        'component_areas': validated_data['component_areas'],
        'evaluation_data': {
            '상부구조': {
                '바닥판': {
                    'area': validated_data['component_areas']['slab'],
                    'span_area': validated_data['component_areas']['span_slab'],
                    'grade': None,
                    'damage_data': []
                },
                '거더': {
                    'area': validated_data['component_areas'].get('girder', 0),
                    'grade': None,
                    'damage_data': []
                },
                '가로보': {
                    'area': validated_data['component_areas'].get('crossbeam', 0),
                    'grade': None,
                    'damage_data': []
                },
                '포장': {
                    'area': validated_data['component_areas']['pavement'],
                    'span_area': validated_data['component_areas']['span_pavement'],
                    'grade': None,
                    'damage_data': []
                }
            },
            '하부구조': {
                '교대': {
                    'area': validated_data['component_areas'].get('abutment', 0),
                    'grade': None,
                    'damage_data': []
                },
                '교각': {
                    'area': validated_data['component_areas'].get('pier', 0),
                    'grade': None,
                    'damage_data': []
                }
            },
            '2차부재': {
                '연석': {
                    'length': validated_data['component_areas']['railing'],
                    'span_length': validated_data['component_areas']['span_railing'],
                    'grade': None,
                    'damage_data': []
                }
            }
        }
    }

    return evaluation_form

def classify_repair(desc):
    """보수방안 분류 함수"""
    desc = remove_special_characters(desc)  # 특수문자 제거

    original_desc = desc
    is_pavement = any(keyword in desc for keyword in ["교면포장", "포장", "신축이음", "포장균열"])
    is_railing = any(keyword in desc for keyword in ["난간", "연석", "방호울타리", "방호벽", "방음벽", "방음판", "차광망", "낙석방지망", "낙석방지책", "중분대", "중앙분리대", "경계석", "가드레일", "안전난간", "보행자난간", "차량방호울타리", "중앙분리난간", "측면방호울타리", "원형난간", "사각난간", "방호시설", "안전시설", "교량난간", "보도난간", "차도난간", "콘크리트난간", "강재난간", "알루미늄난간", "스테인리스난간", "복합난간", "투명난간", "유리난간", "펜스", "울타리", "방벽"])

    desc = (desc.replace("보수부", "")
                .replace("받침콘크리트", "")
                .replace("받침몰탈", "")
                .replace("받침", "")
                .replace("전단키", "")
                .replace("연석", ""))

    # ✅ 명시된 문자열 먼저 우선 처리
    if re.search(r"균열\(0\.3mm\)|균열\(0\.3mm이상\)|균열\(0\.3㎜\)|균열\(0\.3㎜이상\)", desc):
        return "주입보수"
    if re.search(r"균열\(0\.3mm미만\)|균열\(0\.2mm이하\)|균열\(0\.2㎜이하\)|균열\(0\.3㎜미만\)", desc):
        return "표면처리"

    if '균열' in desc:
        match = re.search(r'(\d+(\.\d+)?)mm', desc)
        if match:
            crack_size = float(match.group(1))
            if crack_size >= 1.0:
                return "충진보수"
            elif crack_size >= 0.3:
                return "주입보수"
            else:
                return "표면처리"
        else:
            return "표면처리"

    if is_pavement:
        if re.search("균열|망상균열", original_desc):
            return "실링보수"
        elif re.search("파손|패임|들뜸", original_desc):
            return "부분재포장"
        else:
            return "주의관찰"

    if is_railing:
        if re.search("파손|탈락|변형", original_desc):
            return "재설치"
        elif re.search("부식|도장", original_desc):
            return "도장보수"
        else:
            return "주의관찰"

    if re.search("신축이음|이음장치", desc):
    # ✅ '후타재'가 포함되어 있으면 무조건 주의관찰
        if re.search("후타재", desc):
            return "주의관찰"
        # ✅ 그 외 파손/탈락은 신축이음 재설치
        if re.search("본체파손|본체탈락|탈락|파손", desc):
            return "주의관찰"

    if re.search("철근노출", desc): return "단면보수(방청)"
    if re.search("박리|들뜸|박락|재료분리|파손|침식|세굴|층분리", desc): return "단면보수"
    if re.search("백태|누수흔적|오염|망상균열|흔적|균열부백태|누수오염|녹물", desc): return "표면처리"
    if re.search("부식|도장박리|도장박락|도장|플레이트", desc): return "도장보수"
    if re.search("탈락|망실|미설치", desc): return "재설치"
    if re.search("막힘|퇴적|적치", desc): return "청소"
    if re.search("배수관탈락|길이부족", desc): return "배수관 재설치"

    return "주의관찰"


def match_priority(desc, repair_method=None):
    """우선순위 분류 함수"""
    desc = remove_special_characters(desc)  # 특수문자 제거

    # 보수방안이 "주의관찰"인 경우만 3순위로 확정
    if repair_method == "주의관찰":
        return "3"

    # 1순위: 긴급한 손상들
    if re.search(r"균열\(0\.3mm\)|균열\(0\.3mm이상\)|철근노출|세굴", desc):
        return "1"

    # 3순위: 포장균열 관련
    if re.search("포장균열|포장망상균열", desc):
        return "3"

    # 2순위: 신축이음 본체파손
    if re.search("신축이음|이음장치", desc):
        if re.search("본체파손|본체탈락|탈락|파손", desc):
            return "2"

    # 2순위: 교면포장 파손
    if re.search("교면포장|포장", desc):
        if re.search("파손|패임|들뜸", desc):
            return "2"

    # 난간/연석 관련 부재들의 우선순위 처리
    if re.search("난간|연석|방호울타리|방호벽|방음벽|방음판|차광망|낙석방지망|낙석방지책|중분대|중앙분리대|경계석|가드레일|안전난간|보행자난간|차량방호울타리|중앙분리난간|측면방호울타리|원형난간|사각난간|방호시설|안전시설|교량난간|보도난간|차도난간|콘크리트난간|강재난간|알루미늄난간|스테인리스난간|복합난간|투명난간|유리난간|펜스|울타리|방벽", desc):
        if re.search("파손|탈락|변형", desc):
            return "2"
        return "3"

    # 기본값: 2순위
    return "2"


def match_unit_price(desc):
    """단가 매핑 함수"""
    desc = remove_special_characters(desc)  # 특수문자 제거

    desc = normalize_damage(desc)
    check = (desc.replace("보수부", "")
                .replace("받침콘크리트", "")
                .replace("받침몰탈", "")
                .replace("받침", "")
                .replace("전단키", "")
                .replace("연석", ""))

    if re.search("교면포장|포장", desc):
        if re.search("균열", desc): return 20000
        if re.search("파손|패임", desc): return 40000
        if re.search("들뜸|탈락", desc): return 40000

    if re.search("신축이음|이음장치", desc):
        if re.search("본체파손|본체탈락|탈락|파손", desc): return 300000

    # 난간/연석 관련 부재들의 단가 처리
    if re.search("난간|연석|방호울타리|방호벽|방음벽|방음판|차광망|낙석방지망|낙석방지책|중분대|중앙분리대|경계석", desc):
        if re.search("파손|탈락|변형", desc): return 150000
        if re.search("부식|도장", desc): return 65000
        return 30000

    if re.search(r"균열\(0\.3mm이상\)", check): return 87000
    if re.search(r"균열\(0\.3mm\)", check): return 87000
    if re.search(r"균열\(0\.3mm미만\)", check): return 62000
    if re.search(r"균열\(0\.2mm\)", check): return 62000
    if re.search("백태", check): return 62000
    if re.search("균열", check): return 62000
    if re.search("철근노출", check): return 310000
    if re.search("박리|들뜸|박락|재료분리|파손|침식|세굴|층분리", check): return 300000
    if re.search("백태|누수흔적|오염|망상균열|흔적|균열부백태|누수오염", check): return 62000
    if re.search("부식|도장박리|도장박락|도장|플레이트", check): return 65000
    if re.search("탈락|망실|미설치", check): return 100000
    if re.search("막힘|퇴적|적치", check): return 11000
    if re.search("배수관탈락|길이부족", check): return 250000

    return 30000


def adjust(row, markup_rate ): #  markup_rate : 할증율
    """보수물량 계산 함수"""
    try:
        # 필수 키 존재 확인
        required_keys = ['단위', '손상내용', '손상물량']
        for key in required_keys:
            if key not in row:
                raise KeyError(f"필수 키 '{key}'가 row에 없습니다.")

        # 데이터 타입 검증 및 변환
        damage_quantity = float(row['손상물량']) if row['손상물량'] is not None else 0.0
        unit = str(row['단위']) if row['단위'] is not None else ''
        damage_content = str(row['손상내용']) if row['손상내용'] is not None else ''

        # 단위에 따른 적용할증율 계산
        persional_rate = 1.2
        if unit in ['ea', 'EA', '개소']:
            persional_rate = 1.0
        else:
            persional_rate = (1 + markup_rate/100 ) if markup_rate is not None else 1.2

        # 할증율 적용 계산
        if unit in ['개소', 'ea', 'EA']:
            return damage_quantity * row['개소']  # 개소 단위는 그대로
        elif ('균열' in damage_content or '균열부' in damage_content) and '누수' not in damage_content and '망상균열' not in damage_content and unit == 'm':
            # 0.3mm 이상의 숫자나 특정 표현이 포함되어 있는지 확인 (정규표현식 사용)
            import re
            # 0.3미만 관련 표현 확인 (정규표현식 사용)
            # 0.3과 미만이 모두 포함된 경우 0.25를 곱함
            if re.search(r'0\.3.*미만|미만.*0\.3', damage_content):
                return round(damage_quantity * persional_rate * 0.25, 3)

            # 0.3mm 이상의 숫자 패턴 찾기 (예: 0.3mm이상, 0.4, 0.5, 1.0, 10, 11.5 등)
            # 단, 0.1, 0.2, 0.15, 0.05 등 0.3보다 작은 숫자는 제외
            large_crack_pattern = r'([1-9]\d*\.?\d*|0\.[4-9]\d*|0\.3[㎜mm]이상)'
            if not re.search(large_crack_pattern, damage_content):
                return round(damage_quantity * persional_rate * 0.25, 3)  # 0.3mm 미만 균열 관련 손상
            else:
                return round(damage_quantity * persional_rate, 3)  # 0.3mm 이상 균열
        else:
            return round(damage_quantity * persional_rate , 3)  # 일반적인 경우

    except Exception as e:
        print(f"adjust 함수 오류: {e}")
        print(f"row 데이터: {row}")
        # 기본값 반환
        try:
            return float(row.get('손상물량', 0)) * 1.2 * 0.25
        except:
            return 0.0

def natural_sort_key(s):
    """자연 정렬을 위한 키 함수"""
    import re
    parts = re.split('([0-9]+)', str(s))
    return [int(part) if part.isdigit() else part for part in parts]
