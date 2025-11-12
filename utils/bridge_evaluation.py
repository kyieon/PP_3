"""
부재별 집계표 데이터를 기반으로 상태평가표를 자동 생성하는 모듈
"""
import pandas as pd
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from utils.common import trim_dataframe_str_columns
from .evaluation import (
    evaluate_slab_condition, evaluate_psc_slab_condition,
    evaluate_rc_girder_condition, evaluate_psc_girder_condition,
    evaluate_steel_component, evaluate_concrete_crossbeam,
    evaluate_steel_crossbeam, evaluate_abutment_condition,
    evaluate_pier_condition, evaluate_bearing_condition,
    evaluate_expansion_joint, evaluate_pavement_condition,
    evaluate_drainage_facility, evaluate_railing_or_curb,
    get_condition_grade, grade_to_defect_score
)

def extract_damage_values(damage_desc: str, damage_quantity: float) -> Dict[str, float]:
    """
    손상 내용에서 균열폭, 면적율 등의 값을 추출합니다.

    Args:
        damage_desc: 손상 내용 설명
        damage_quantity: 손상 물량

    Returns:
        Dict[str, float]: 추출된 손상 값들
    """
    values = {
        'crack_width': 0,
        'crack_ratio': 0,
        'leak_ratio': 0,
        'surface_damage_ratio': 0,
        'rebar_corrosion_ratio': 0,
        'area_ratio': 0
    }

    # 균열폭 추출 (mm 단위)
    crack_patterns = [
        r'균열\s*\(\s*(\d+(?:\.\d+)?)\s*mm\s*이상\s*\)',
        r'균열\s*\(\s*(\d+(?:\.\d+)?)\s*mm\s*\)',
        r'균열\s*\(\s*(\d+(?:\.\d+)?)\s*㎜\s*\)',
        r'(\d+(?:\.\d+)?)\s*mm\s*균열',
        r'(\d+(?:\.\d+)?)\s*㎜\s*균열'
    ]

    for pattern in crack_patterns:
        match = re.search(pattern, damage_desc)
        if match:
            values['crack_width'] = float(match.group(1))
            break

    # 0.3mm 미만/이상 패턴 처리
    if '0.3mm미만' in damage_desc or '0.3㎜미만' in damage_desc:
        values['crack_width'] = 0.2  # 0.3mm 미만은 0.2mm로 처리
    elif '0.3mm이상' in damage_desc or '0.3㎜이상' in damage_desc:
        values['crack_width'] = 0.3
    elif '0.2mm' in damage_desc or '0.2㎜' in damage_desc:
        values['crack_width'] = 0.2
    elif '0.1mm' in damage_desc or '0.1㎜' in damage_desc:
        values['crack_width'] = 0.1
    # 망상균열에 대해서는 손상물량 체크 후 처리
    elif '망상균열' in damage_desc:
        # 망상균열의 경우 손상물량이 있을 때만 0.2 설정
        if damage_quantity > 0:
            values['crack_width'] = 0.2
        # 손상물량이 0이면 crack_width는 0 유지

    # 손상 종류별 처리
    if '균열' in damage_desc:
        # 균열의 경우 손상물량을 길이로 처리하고 면적비로 변환
        values['crack_ratio'] = damage_quantity * 0.1  # 가정: 균열 길이를 면적비로 변환

    elif '누수' in damage_desc or '백태' in damage_desc:
        values['leak_ratio'] = damage_quantity

    elif '박리' in damage_desc or '박락' in damage_desc or '표면손상' in damage_desc:
        values['surface_damage_ratio'] = damage_quantity

    elif any(keyword in damage_desc for keyword in ['철근노출', '철근부식', '철근 노출', '철근 부식', '부식', '녹']) and '잡철근노출' not in damage_desc:
        values['rebar_corrosion_ratio'] = damage_quantity

    # 녹물 관련 손상은 표면손상으로 분류
    elif any(keyword in damage_desc for keyword in ['녹물']):
        values['surface_damage_ratio'] = damage_quantity

    return values

def process_slab_evaluation_data(component_data: List[Dict], component_type: str = 'RC') -> List[Dict]:
    """
    바닥판 부재별 집계표 데이터를 상태평가표 형식으로 변환합니다.

    Args:
        component_data: 부재별 집계표 데이터
        component_type: 부재 타입 ('RC', 'PSC', 'STEEL')

    Returns:
        List[Dict]: 상태평가표 데이터
    """
    evaluation_data = []

    # 경간별로 데이터 그룹화
    spans_data = {}
    for item in component_data:
        span_id = item['spanId']
        if span_id not in spans_data:
            spans_data[span_id] = {
                'span_id': span_id,
                'area': item.get('inspectionArea', 100),
                'crack_1d_width': 0,
                'crack_1d_ratio': 0,
                'crack_2d_width': 0,
                'crack_2d_ratio': 0,
                'leak_ratio': 0,
                'surface_damage_ratio': 0,
                'rebar_corrosion_ratio': 0
            }

        damage_values = extract_damage_values(item['damageType'], item['damageQuantity'])
        span_data = spans_data[span_id]

        # 균열 방향 구분
        if '1방향' in item['damageType'] or '종방향' in item['damageType']:
            span_data['crack_1d_width'] = max(span_data['crack_1d_width'], damage_values['crack_width'])
            span_data['crack_1d_ratio'] += damage_values['crack_ratio']
        elif '2방향' in item['damageType'] or '횡방향' in item['damageType'] or '망상' in item['damageType']:
            # 2방향 균열: 손상물량이 있는 경우에만 균열폭 설정
            if damage_values['crack_ratio'] > 0 or item['damageQuantity'] > 0:
                # 명시적인 균열폭이 없는 경우에만 0.2로 설정
                if damage_values['crack_width'] == 0:
                    span_data['crack_2d_width'] = 0.2
                else:
                    span_data['crack_2d_width'] = max(span_data['crack_2d_width'], damage_values['crack_width'])
                span_data['crack_2d_ratio'] += damage_values['crack_ratio']
            # 손상물량이 없으면 crack_2d_width는 기본값(0) 유지 (후에 None으로 처리)
        else:
            # 방향이 명시되지 않은 균열은 1방향으로 처리
            if damage_values['crack_width'] > 0:
                span_data['crack_1d_width'] = max(span_data['crack_1d_width'], damage_values['crack_width'])
                span_data['crack_1d_ratio'] += damage_values['crack_ratio']

        # 기타 손상
        span_data['leak_ratio'] += damage_values['leak_ratio']
        span_data['surface_damage_ratio'] += damage_values['surface_damage_ratio']
        span_data['rebar_corrosion_ratio'] += damage_values['rebar_corrosion_ratio']

    # 상태평가 등급 계산
    for span_id, span_data in spans_data.items():
        max_crack_width = max(span_data['crack_1d_width'], span_data['crack_2d_width'])
        max_crack_ratio = max(span_data['crack_1d_ratio'], span_data['crack_2d_ratio'])

        # 2방향 균열폭이 0이고 2방향 균열율도 0이면 None으로 설정 (손상물량 없음)
        if span_data['crack_2d_width'] == 0 and span_data['crack_2d_ratio'] == 0:
            span_data['crack_2d_width'] = None

        if component_type == 'PSC':
            grade = evaluate_psc_slab_condition(
                crack_width=max_crack_width if max_crack_width > 0 else None,
                crack_ratio=max_crack_ratio if max_crack_ratio > 0 else None,
                leak_ratio=span_data['leak_ratio'] if span_data['leak_ratio'] > 0 else None,
                surface_damage_ratio=span_data['surface_damage_ratio'] if span_data['surface_damage_ratio'] > 0 else None,
                rebar_corrosion_ratio=span_data['rebar_corrosion_ratio'] if span_data['rebar_corrosion_ratio'] > 0 else None
            )
        else:  # RC 또는 기타
            grade = evaluate_slab_condition(
                crack_width=max_crack_width if max_crack_width > 0 else None,
                crack_ratio=max_crack_ratio if max_crack_ratio > 0 else None,
                leak_ratio=span_data['leak_ratio'] if span_data['leak_ratio'] > 0 else None,
                surface_damage_ratio=span_data['surface_damage_ratio'] if span_data['surface_damage_ratio'] > 0 else None,
                rebar_corrosion_ratio=span_data['rebar_corrosion_ratio'] if span_data['rebar_corrosion_ratio'] > 0 else None
            )

        span_data['grade'] = grade
        evaluation_data.append(span_data)

    return sorted(evaluation_data, key=lambda x: x['span_id'])

def process_girder_evaluation_data(component_data: List[Dict], component_type: str = 'RC') -> List[Dict]:
    """
    거더 부재별 집계표 데이터를 상태평가표 형식으로 변환합니다.
    """
    evaluation_data = []

    spans_data = {}
    for item in component_data:
        span_id = item['spanId']
        if span_id not in spans_data:
            spans_data[span_id] = {
                'span_id': span_id,
                'area': item.get('inspectionArea', 100),
                'crack_width': 0,
                'surface_damage_ratio': 0,
                'rebar_corrosion_ratio': 0,
                'tendon_corrosion': None,
                'main_rust_area': 0,
                'sub_rust_area': 0,
                'section_loss_area': 0
            }

        damage_values = extract_damage_values(item['damageType'], item['damageQuantity'])
        span_data = spans_data[span_id]

        span_data['crack_width'] = max(span_data['crack_width'], damage_values['crack_width'])
        span_data['surface_damage_ratio'] += damage_values['surface_damage_ratio']
        span_data['rebar_corrosion_ratio'] += damage_values['rebar_corrosion_ratio']

        # 강재 관련 손상
        if '부식' in item['damageType']:
            if '주부재' in item['damageType']:
                span_data['main_rust_area'] += damage_values['area_ratio']
            else:
                span_data['sub_rust_area'] += damage_values['area_ratio']

        if '단면손실' in item['damageType']:
            span_data['section_loss_area'] += damage_values['area_ratio']

    # 상태평가 등급 계산
    for span_id, span_data in spans_data.items():
        if component_type == 'PSC':
            grade = evaluate_psc_girder_condition(
                crack_width=span_data['crack_width'] if span_data['crack_width'] > 0 else None,
                surface_damage_ratio=span_data['surface_damage_ratio'] if span_data['surface_damage_ratio'] > 0 else None,
                rebar_corrosion_ratio=span_data['rebar_corrosion_ratio'] if span_data['rebar_corrosion_ratio'] > 0 else None,
                tendon_corrosion_level=span_data['tendon_corrosion']
            )
        elif component_type == 'STEEL':
            grade = evaluate_steel_component(
                main_rust_area=span_data['main_rust_area'] if span_data['main_rust_area'] > 0 else None,
                sub_rust_area=span_data['sub_rust_area'] if span_data['sub_rust_area'] > 0 else None,
                section_loss_area=span_data['section_loss_area'] if span_data['section_loss_area'] > 0 else None
            )
        else:  # RC
            grade = evaluate_rc_girder_condition(
                crack_width=span_data['crack_width'] if span_data['crack_width'] > 0 else None,
                surface_damage_ratio=span_data['surface_damage_ratio'] if span_data['surface_damage_ratio'] > 0 else None,
                rebar_corrosion_ratio=span_data['rebar_corrosion_ratio'] if span_data['rebar_corrosion_ratio'] > 0 else None
            )

        span_data['grade'] = grade
        evaluation_data.append(span_data)

    return sorted(evaluation_data, key=lambda x: x['span_id'])

def generate_component_evaluation_table(component_name: str, evaluation_data: List[Dict], component_type: str = 'RC') -> str:
    """
    부재별 상태평가표 HTML을 생성합니다.
    """
    component_names = {
        'slab': '바닥판',
        'girder': '거더',
        'crossbeam': '가로보',
        'abutment': '교대',
        'pier': '교각',
        'bearing': '교량받침',
        'expansionJoint': '신축이음',
        'pavement': '교면포장',
        'drainage': '배수시설',
        'railing': '난간 및 연석'
    }

    korean_name = component_names.get(component_name, component_name)

    html = f'''
    <div class="evaluation-table-container mb-4">
        <h4 class="text-center mb-3">{korean_name} 상태평가표</h4>
        <div class="table-responsive">
            <table class="table table-bordered table-striped">
    '''

    # 바닥판 헤더
    if component_name == 'slab':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="4">1방향 균열</th>
                        <th colspan="4">2방향 균열</th>
                        <th colspan="6">열화 및 손상</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">누수 및 백태<br>면적율(%)</th>
                        <th colspan="2">표면손상<br>면적율(%)</th>
                        <th colspan="2">철근부식<br>손상면적율(%)</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            # 2방향 균열폭 및 균열율 처리
            crack_2d_width_display = '-' if data["crack_2d_width"] is None or data["crack_2d_width"] == 0 else f'{data["crack_2d_width"]:.2f}'
            crack_2d_ratio_display = '-' if data["crack_2d_ratio"] == 0 else f'{data["crack_2d_ratio"]:.2f}'
            crack_2d_width_grade = 'a' if data["crack_2d_width"] is None or data["crack_2d_width"] == 0 else evaluate_grade(data["crack_2d_width"])
            crack_2d_ratio_grade = 'a' if data["crack_2d_ratio"] == 0 else evaluate_grade(data["crack_2d_ratio"])

            # 1방향 균열율도 0인 경우 처리
            crack_1d_ratio_display = '-' if data["crack_1d_ratio"] == 0 else f'{data["crack_1d_ratio"]:.2f}'
            crack_1d_width_display = '-' if data["crack_1d_width"] == 0 else f'{data["crack_1d_width"]:.2f}'

            # 기타 면적율 0인 경우 처리
            leak_ratio_display = '-' if data["leak_ratio"] == 0 else f'{data["leak_ratio"]:.2f}'
            surface_damage_display = '-' if data["surface_damage_ratio"] == 0 else f'{data["surface_damage_ratio"]:.2f}'
            rebar_corrosion_display = '-' if data["rebar_corrosion_ratio"] == 0 else f'{data["rebar_corrosion_ratio"]:.2f}'

            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data["area"]:.1f}</td>
                        <td>{crack_1d_width_display}</td><td>{evaluate_grade(data["crack_1d_width"])}</td>
                        <td>{crack_1d_ratio_display}</td><td>{evaluate_grade(data["crack_1d_ratio"])}</td>
                        <td>{crack_2d_width_display}</td><td>{crack_2d_width_grade}</td>
                        <td>{crack_2d_ratio_display}</td><td>{crack_2d_ratio_grade}</td>
                        <td>{leak_ratio_display}</td><td>{evaluate_grade(data["leak_ratio"])}</td>
                        <td>{surface_damage_display}</td><td>{evaluate_grade(data["surface_damage_ratio"])}</td>
                        <td>{rebar_corrosion_display}</td><td>{evaluate_grade(data["rebar_corrosion_ratio"])}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 가로보 헤더 - 바닥판과 동일한 구조
    elif component_name == 'crossbeam':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="4">1방향 균열</th>
                        <th colspan="4">2방향 균열</th>
                        <th colspan="6">열화 및 손상</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">누수 및 백태<br>면적율(%)</th>
                        <th colspan="2">표면손상<br>면적율(%)</th>
                        <th colspan="2">철근부식<br>손상면적율(%)</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            # 2방향 균열폭 및 균열율 처리
            crack_2d_width_display = '-' if data["crack_2d_width"] is None or data["crack_2d_width"] == 0 else f'{data["crack_2d_width"]:.2f}'
            crack_2d_ratio_display = '-' if data["crack_2d_ratio"] == 0 else f'{data["crack_2d_ratio"]:.2f}'
            crack_2d_width_grade = 'a' if data["crack_2d_width"] is None or data["crack_2d_width"] == 0 else evaluate_grade(data["crack_2d_width"])
            crack_2d_ratio_grade = 'a' if data["crack_2d_ratio"] == 0 else evaluate_grade(data["crack_2d_ratio"])

            # 1방향 균열율도 0인 경우 처리
            crack_1d_ratio_display = '-' if data["crack_1d_ratio"] == 0 else f'{data["crack_1d_ratio"]:.2f}'
            crack_1d_width_display = '-' if data["crack_1d_width"] == 0 else f'{data["crack_1d_width"]:.2f}'

            # 기타 면적율 0인 경우 처리
            leak_ratio_display = '-' if data["leak_ratio"] == 0 else f'{data["leak_ratio"]:.2f}'
            surface_damage_display = '-' if data["surface_damage_ratio"] == 0 else f'{data["surface_damage_ratio"]:.2f}'
            rebar_corrosion_display = '-' if data["rebar_corrosion_ratio"] == 0 else f'{data["rebar_corrosion_ratio"]:.2f}'

            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data["area"]:.1f}</td>
                        <td>{crack_1d_width_display}</td><td>{evaluate_grade(data["crack_1d_width"])}</td>
                        <td>{crack_1d_ratio_display}</td><td>{evaluate_grade(data["crack_1d_ratio"])}</td>
                        <td>{crack_2d_width_display}</td><td>{crack_2d_width_grade}</td>
                        <td>{crack_2d_ratio_display}</td><td>{crack_2d_ratio_grade}</td>
                        <td>{leak_ratio_display}</td><td>{evaluate_grade(data["leak_ratio"])}</td>
                        <td>{surface_damage_display}</td><td>{evaluate_grade(data["surface_damage_ratio"])}</td>
                        <td>{rebar_corrosion_display}</td><td>{evaluate_grade(data["rebar_corrosion_ratio"])}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 거더 헤더
    elif component_name == 'girder':
        if component_type == 'STEEL':
            html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="8">모재 및 연결부 손상</th>
                        <th colspan="2">표면열화<br>면적율(%)</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">부재 균열</th>
                        <th colspan="2">변형, 파단</th>
                        <th colspan="2">연결 볼트<br>이완, 탈락</th>
                        <th colspan="2">용접연결부<br>결함</th>
                        <th colspan="2"></th>
                    </tr>
                </thead>
            '''
        else:
            html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">점검<br>면적<br>(m²)</th>
                        <th colspan="4">1방향 균열</th>
                        <th colspan="4">2방향 균열</th>
                        <th colspan="6">열화 및 손상</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">최대폭(mm)</th><th colspan="2">균열율(%)</th>
                        <th colspan="2">누수 및 백태<br>면적율(%)</th>
                        <th colspan="2">표면손상<br>면적율(%)</th>
                        <th colspan="2">철근부식<br>손상면적율(%)</th>
                    </tr>
                </thead>
            '''

        html += '<tbody>'
        for data in evaluation_data:
            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data["area"]:.1f}</td>
                        <td>{data["crack_width"]:.2f}</td><td>{evaluate_grade(data["crack_width"])}</td>
                        <td>-</td><td>a</td>
                        <td>-</td><td>a</td>
                        <td>-</td><td>a</td>
                        <td>{data["surface_damage_ratio"]:.2f}</td><td>{evaluate_grade(data["surface_damage_ratio"])}</td>
                        <td>{data["rebar_corrosion_ratio"]:.2f}</td><td>{evaluate_grade(data["rebar_corrosion_ratio"])}</td>
                        <td>-</td><td>a</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 교량받침 헤더
    elif component_name == 'bearing':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th colspan="2">받침본체(탄성받침, 강재받침)</th>
                        <th colspan="4">받침 콘크리트 등</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th>손상현황</th>
                        <th>등급</th>
                        <th>균열 최대폭(mm)</th>
                        <th>등급</th>
                        <th>단면손상</th>
                        <th>등급</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data.get("body_condition", "-")}</td>
                        <td>{"b" if data.get("body_condition", "-") != "-" else "a"}</td>
                        <td>{data.get("crack_width", "-")}</td>
                        <td>{evaluate_grade(data.get("crack_width", 0))}</td>
                        <td>{data.get("section_damage", "-")}</td>
                        <td>{"b" if data.get("section_damage", "-") != "-" else "a"}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 신축이음 헤더
    elif component_name == 'expansionJoint':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">개소<br>(개)</th>
                        <th colspan="6">신축이음의 기능 및 상태</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">구조적 손상</th>
                        <th colspan="2">기능 저하</th>
                        <th colspan="2">기타</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data.get("count", 1)}</td>
                        <td>{"○" if "파손" in data["condition"] or "균열" in data["condition"] else "-"}</td>
                        <td>{evaluate_expansion_grade("파손" in data["condition"] or "균열" in data["condition"])}</td>
                        <td>{"○" if "탈락" in data["condition"] or "변위" in data["condition"] else "-"}</td>
                        <td>{evaluate_expansion_grade("탈락" in data["condition"] or "변위" in data["condition"])}</td>
                        <td>{"○" if any(word in data["condition"] for word in ["이완", "변형", "기타"]) else "-"}</td>
                        <td>{evaluate_expansion_grade(any(word in data["condition"] for word in ["이완", "변형", "기타"]))}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 교면포장 헤더
    elif component_name == 'pavement':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">포장면적<br>(m²)</th>
                        <th colspan="4">포장손상</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">손상면적(m²)</th>
                        <th colspan="2">손상율(%)</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            damage_area = data.get('damage_area', data['damage_ratio'] * data.get('area', 100) / 100)
            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data.get("area", 100):.1f}</td>
                        <td>{damage_area:.2f}</td>
                        <td>{evaluate_grade(damage_area)}</td>
                        <td>{data["damage_ratio"]:.2f}</td>
                        <td>{evaluate_grade(data["damage_ratio"])}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 배수시설 헤더
    elif component_name == 'drainage':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">개소<br>(개)</th>
                        <th colspan="4">배수시설 상태</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">파손/노화</th>
                        <th colspan="2">누수</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data.get("count", 1)}</td>
                        <td>{"○" if "파손" in data["condition"] or "노화" in data["condition"] else "-"}</td>
                        <td>{evaluate_drainage_grade("파손" in data["condition"] or "노화" in data["condition"])}</td>
                        <td>{"○" if "누수" in data["condition"] else "-"}</td>
                        <td>{evaluate_drainage_grade("누수" in data["condition"])}</td>
                        <td class="fw-bold text-center">{data["grade"]}</td>
                    </tr>
            '''

    # 난간 및 연석 헤더
    elif component_name == 'railing':
        html += '''
                <thead class="table-dark">
                    <tr>
                        <th rowspan="2">구 분</th>
                        <th rowspan="2">길이<br>(m)</th>
                        <th colspan="6">강재</th>
                        <th colspan="4">콘크리트</th>
                        <th rowspan="2">상태<br>평가<br>결과</th>
                    </tr>
                    <tr>
                        <th colspan="2">도장손상(%)</th>
                        <th colspan="2">부식발생(%)</th>
                        <th colspan="2">연결재 및 단면손상(%)</th>
                        <th colspan="2">균열 최대폭(mm)</th>
                        <th colspan="2">표면손상, 철근부식 면적율(%)</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for data in evaluation_data:
                        # 데이터 안전성 검증
            paint_damage = data.get("paint_damage_ratio", 0) or 0
            corrosion_ratio = data.get("corrosion_ratio", 0) or 0
            connection_damage = data.get("connection_damage_ratio", 0) or 0
            crack_width = data.get("crack_width", 0) or 0
            surface_damage = data.get("surface_damage_ratio", 0) or 0

            html += f'''
                    <tr>
                        <td>{data["span_id"]}</td>
                        <td>{data.get("length", 100):.1f}</td>
                        <td>{paint_damage:.2f if paint_damage > 0 else "-"}</td><td>{evaluate_grade(paint_damage)}</td>
                        <td>{corrosion_ratio:.2f if corrosion_ratio > 0 else "-"}</td><td>{evaluate_grade(corrosion_ratio)}</td>
                        <td>{connection_damage:.2f if connection_damage > 0 else "-"}</td><td>{evaluate_grade(connection_damage)}</td>
                        <td>{crack_width:.2f if crack_width > 0 else "-"}</td><td>{evaluate_grade(crack_width)}</td>
                        <td>{surface_damage:.2f if surface_damage > 0 else "-"}</td><td>{evaluate_grade(surface_damage)}</td>
                        <td class="fw-bold text-center">{data.get("grade", "a")}</td>
                    </tr>
            '''

    html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''

    return html

def evaluate_grade(value: float) -> str:
    """손상 값에 따른 등급을 계산합니다."""
    if value == 0 or value is None:
        return 'a'
    elif value < 0.1:
        return 'b'
    elif value < 0.3:
        return 'c'
    elif value < 0.5:
        return 'd'
    else:
        return 'e'

def generate_total_evaluation_table(component_evaluations: Dict[str, List[Dict]], structure_type: str) -> str:
    """
    통합 상태평가 결과표를 생성합니다.
    """
    # 각 부재별 최종 등급 계산
    component_grades = {}

    for component, evaluations in component_evaluations.items():
        if evaluations:
            # 모든 경간의 등급 중 가장 낮은 등급(최악)을 선택
            grades = [data['grade'] for data in evaluations]
            worst_grade = max(grades, key=lambda x: ord(x))
            component_grades[component] = worst_grade
            print(f"{component} 부재 등급: {grades} -> 최종 {worst_grade}")
        else:
            component_grades[component] = 'a'

    # 구조형식별 가중치
    weights = {
        'PSC 박스거더교': {
            'slab': 0.20, 'girder': 0.20, 'crossbeam': 0.10,
            'pavement': 0.15, 'drainage': 0.05, 'railing': 0.05,
            'expansionJoint': 0.10, 'bearing': 0.10, 'abutment': 0.05
        },
        'PSC 빔교': {
            'slab': 0.18, 'girder': 0.18, 'crossbeam': 0.12,
            'pavement': 0.15, 'drainage': 0.05, 'railing': 0.05,
            'expansionJoint': 0.12, 'bearing': 0.10, 'abutment': 0.05
        }
    }

    weight_set = weights.get(structure_type, weights['PSC 박스거더교'])

    # 환산 결함도 점수 계산
    total_score = 0
    total_weight = 0

    for component, grade in component_grades.items():
        if component in weight_set:
            weight = weight_set[component]
            score = grade_to_defect_score(grade)
            total_score += score * weight
            total_weight += weight

    defect_score = total_score / total_weight if total_weight > 0 else 0
    final_grade = get_condition_grade(defect_score)

    html = f'''
    <div class="evaluation-summary mt-4">
        <h4 class="text-center mb-3">상태평가 통합 산정 결과표</h4>
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead class="table-dark">
                    <tr>
                        <th>부재의 분류</th>
                        <th>구조형식</th>
                        <th>바닥판</th>
                        <th>거더</th>
                        <th>가로보</th>
                        <th>포장</th>
                        <th>배수</th>
                        <th>난간연석</th>
                        <th>신축이음</th>
                        <th>교량받침</th>
                        <th>하부</th>
                        <th>상태평가 결과</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>등급</td>
                        <td>{structure_type}</td>
                        <td>{component_grades.get("slab", "a")}</td>
                        <td>{component_grades.get("girder", "a")}</td>
                        <td>{component_grades.get("crossbeam", "a")}</td>
                        <td>{component_grades.get("pavement", "a")}</td>
                        <td>{component_grades.get("drainage", "a")}</td>
                        <td>{component_grades.get("railing", "a")}</td>
                        <td>{component_grades.get("expansionJoint", "a")}</td>
                        <td>{component_grades.get("bearing", "a")}</td>
                        <td>{component_grades.get("abutment", "a")}</td>
                        <td class="fw-bold">{final_grade}</td>
                    </tr>
                    <tr>
                        <td>가중치</td>
                        <td>-</td>
                        <td>{weight_set.get("slab", 0):.3f}</td>
                        <td>{weight_set.get("girder", 0):.3f}</td>
                        <td>{weight_set.get("crossbeam", 0):.3f}</td>
                        <td>{weight_set.get("pavement", 0):.3f}</td>
                        <td>{weight_set.get("drainage", 0):.3f}</td>
                        <td>{weight_set.get("railing", 0):.3f}</td>
                        <td>{weight_set.get("expansionJoint", 0):.3f}</td>
                        <td>{weight_set.get("bearing", 0):.3f}</td>
                        <td>{weight_set.get("abutment", 0):.3f}</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="mt-3">
            <p><strong>환산 결함도 점수:</strong> {defect_score:.3f}</p>
            <p><strong>최종 상태평가 결과:</strong> <span class="badge bg-primary fs-6">{final_grade}</span></p>
        </div>
    </div>
    '''

    return html

def process_damage_data_for_evaluation(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    # 문자열 컬럼 trim 처리
    df = trim_dataframe_str_columns(df)
    # ...기존 코드...

    """
    부재별 집계표 DataFrame을 상태평가용 데이터로 변환합니다.
    (손상내용명에 '받침' 또는 '전단키' 포함 시 교량받침으로 분류)
    """
    # 부재명 정규화 매핑
    component_mapping = {
        '바닥판': 'slab',
        '거더': 'girder',
        '가로보': 'crossbeam',
        '교대': 'abutment',
        '교각': 'pier',
        '교량받침': 'bearing',
        '받침': 'bearing',
        '신축이음': 'expansionJoint',
        '이음장치': 'expansionJoint',
        '교면포장': 'pavement',
        '포장': 'pavement',
        '배수시설': 'drainage',
        '배수구': 'drainage',
        '난간': 'railing',
        '연석': 'railing'
    }

    damage_data = {}

    # 부재별로 데이터 그룹화
    for component_name in df['부재명'].unique():
        component_df = df[df['부재명'] == component_name]

        # 경간별로 데이터 처리
        for _, row in component_df.iterrows():
            # 손상내용명에 "받침" 또는 "전단키"가 포함된 경우 교량받침으로 분류
            damage_content = str(row['손상내용'])
            if '받침' in damage_content or '전단키' in damage_content:
                normalized_component = 'bearing'
            else:
                # 부재명 정규화
                normalized_component = None
                for key, value in component_mapping.items():
                    if key in component_name:
                        normalized_component = value
                        break

                if not normalized_component:
                    continue

            if normalized_component not in damage_data:
                damage_data[normalized_component] = []

            damage_item = {
                'spanId': str(row['부재위치']),
                'damageType': damage_content,
                'damageQuantity': float(row['손상물량']) if pd.notnull(row['손상물량']) else 0,
                'count': int(row['개소']) if pd.notnull(row['개소']) else 0,
                'unit': str(row['단위']) if pd.notnull(row['단위']) else '',
                'inspectionArea': float(row.get('점검면적', 100)) if pd.notnull(row.get('점검면적', 100)) else 100
            }
            damage_data[normalized_component].append(damage_item)

    return damage_data

def generate_all_component_evaluations(df: pd.DataFrame) -> str:
    """
    모든 부재의 상태평가표를 생성합니다.
    """
    # DataFrame을 상태평가용 데이터로 변환
    damage_data = process_damage_data_for_evaluation(df)

    # 각 부재별 상태평가표 생성
    component_evaluations = {}
    html_output = ""

    # 바닥판 상태평가
    if 'slab' in damage_data:
        slab_evaluations = process_slab_evaluation_data(damage_data['slab'])
        component_evaluations['slab'] = slab_evaluations
        html_output += generate_component_evaluation_table('slab', slab_evaluations)

    # 거더 상태평가
    if 'girder' in damage_data:
        girder_evaluations = process_girder_evaluation_data(damage_data['girder'])
        component_evaluations['girder'] = girder_evaluations
        html_output += generate_component_evaluation_table('girder', girder_evaluations)

    # 가로보 상태평가
    if 'crossbeam' in damage_data:
        crossbeam_evaluations = process_slab_evaluation_data(damage_data['crossbeam'])  # 가로보를 바닥판과 동일하게 처리
        component_evaluations['crossbeam'] = crossbeam_evaluations
        html_output += generate_component_evaluation_table('crossbeam', crossbeam_evaluations)

    # 교대 상태평가
    if 'abutment' in damage_data:
        abutment_evaluations = process_girder_evaluation_data(damage_data['abutment'])  # 교대도 콘크리트 부재로 처리
        component_evaluations['abutment'] = abutment_evaluations
        html_output += generate_component_evaluation_table('abutment', abutment_evaluations)

    # 교각 상태평가
    if 'pier' in damage_data:
        pier_evaluations = process_girder_evaluation_data(damage_data['pier'])  # 교각도 콘크리트 부재로 처리
        component_evaluations['pier'] = pier_evaluations
        html_output += generate_component_evaluation_table('pier', pier_evaluations)

    # 교량받침 상태평가
    if 'bearing' in damage_data:
        bearing_evaluations = []
        for item in damage_data['bearing']:
            bearing_data = {
                'span_id': item['spanId'],
                'body_condition': item['damageType'],  # 본체 상태
                'crack_width': 0,  # 콘크리트 균열 최대폭
                'section_damage': '-',  # 콘크리트 단면손상
                'grade': evaluate_bearing_condition(
                    rubber_split='균열' in item['damageType'] or '분리' in item['damageType'],
                    corrosion_area='부식' in item['damageType']
                )
            }
            bearing_evaluations.append(bearing_data)
        component_evaluations['bearing'] = bearing_evaluations
        html_output += generate_component_evaluation_table('bearing', bearing_evaluations)

    # 신축이음 상태평가
    if 'expansionJoint' in damage_data:
        expansion_evaluations = []
        for item in damage_data['expansionJoint']:
            expansion_data = {
                'span_id': item['spanId'],
                'condition': item['damageType'],
                'count': item.get('count', 1),
                'grade': evaluate_expansion_joint(
                    structural_damage='파손' in item['damageType'] or '균열' in item['damageType'],
                    function_degradation='탈락' in item['damageType'] or '변위' in item['damageType']
                )
            }
            expansion_evaluations.append(expansion_data)
        component_evaluations['expansionJoint'] = expansion_evaluations
        html_output += generate_component_evaluation_table('expansionJoint', expansion_evaluations)

    # 교면포장 상태평가
    if 'pavement' in damage_data:
        pavement_evaluations = []
        for item in damage_data['pavement']:
            # 균열 단위가 m인 경우 손상물량에 0.25를 곱함
            adjusted_damage_quantity = item['damageQuantity']
            if '균열' in item['damageType'] and item.get('unit', '').lower() == 'm':
                adjusted_damage_quantity = item['damageQuantity'] * 0.25

            damage_ratio = (adjusted_damage_quantity / item['inspectionArea']) * 100 if item['inspectionArea'] > 0 else 0
            pavement_data = {
                'span_id': item['spanId'],
                'damage_ratio': damage_ratio,
                'grade': evaluate_pavement_condition(damage_ratio=damage_ratio)
            }
            pavement_evaluations.append(pavement_data)
        component_evaluations['pavement'] = pavement_evaluations
        html_output += generate_component_evaluation_table('pavement', pavement_evaluations)

    # 배수시설 상태평가
    if 'drainage' in damage_data:
        drainage_evaluations = []
        # 배수구 막힘 경간 수집
        blocked_spans = set()
        for item in damage_data['drainage']:
            if '배수구' in item['damageType'] and '막힘' in item['damageType']:
                blocked_spans.add(item['spanId'])

        for item in damage_data['drainage']:
            # 내용 수정: 토사퇴적, 퇴적, 적치, 이물질 등을 배수불량으로 처리
            condition = item['damageType']
            if item['spanId'] in blocked_spans and any(keyword in condition for keyword in ['토사퇴적', '퇴적', '적치', '이물질']):
                condition = '배수불량'

            drainage_data = {
                'span_id': item['spanId'],
                'condition': condition,
                'count': item.get('count', 1),
                'grade': evaluate_drainage_facility(
                    damaged_or_aged='파손' in condition or '노화' in condition,
                    leakage='누수' in condition or '배수불량' in condition
                )
            }
            drainage_evaluations.append(drainage_data)
        component_evaluations['drainage'] = drainage_evaluations
        html_output += generate_component_evaluation_table('drainage', drainage_evaluations)

    # 난간 및 연석 상태평가
    if 'railing' in damage_data:
        railing_evaluations = []
        for item in damage_data['railing']:
            damage_values = extract_damage_values(item['damageType'], item['damageQuantity'])
            railing_data = {
                'span_id': item['spanId'],
                'length': item.get('inspectionArea', 100),  # 길이
                'crack_width': damage_values['crack_width'],
                'surface_damage_ratio': damage_values['surface_damage_ratio'],
                'rebar_corrosion_ratio': damage_values['rebar_corrosion_ratio'],
                'paint_damage': 0,  # 강재 도장손상
                'corrosion_ratio': 0,  # 강재 부식발생
                'condition': item['damageType'],
                'grade': evaluate_railing_or_curb(
                    crack_width=damage_values['crack_width'] if damage_values['crack_width'] > 0 else None,
                    local_looseness='이완' in item['damageType']
                )
            }
            railing_evaluations.append(railing_data)
        component_evaluations['railing'] = railing_evaluations
        html_output += generate_component_evaluation_table('railing', railing_evaluations)

    # 통합 상태평가 결과표 생성
    html_output += generate_total_evaluation_table(component_evaluations, 'PSC 박스거더교')

    return html_output

def evaluate_bearing_grade(has_damage: bool) -> str:
    """교량받침 손상에 따른 등급을 계산합니다."""
    return 'd' if has_damage else 'a'

def evaluate_expansion_grade(has_damage: bool) -> str:
    """신축이음 손상에 따른 등급을 계산합니다."""
    return 'd' if has_damage else 'a'

def evaluate_drainage_grade(has_damage: bool) -> str:
    """배수시설 손상에 따른 등급을 계산합니다."""
    return 'd' if has_damage else 'a'

def generate_component_evaluation_data(df: pd.DataFrame, component_type: str) -> List[Dict]:
    """
    부재별 상태평가 데이터를 생성합니다.

    Args:
        df: 부재별 집계표 DataFrame
        component_type: 부재 유형 ('slab', 'girder', 'crossbeam', 등)

    Returns:
        List[Dict]: 상태평가 데이터 리스트
    """
    try:
        # 부재 필터링 용 매핑
        component_filters = {
            'slab': ['바닥판'],
            'girder': ['거더'],
            'crossbeam': ['가로보', '세로보', '격벽'],
            'abutment': ['교대'],
            'pier': ['교각'],
            'foundation': ['기초'],
            'bearing': ['받침', '교량받침', '받침장치', '탄성받침', '고무받침', '강재받침', '베어링'],
            'expansionJoint': ['신축이음', '이음장치'],
            'pavement': ['교면포장', '포장'],
            'drainage': ['배수시설', '배수구', '배수관'],
            'railing': ['난간', '연석', '방호울타리', '방호벽', '방음벽', '방음판', '방음', '방호', '중분대', '중앙분리대', '가드레일', '낙석', '차광', '경계석', '투석방지망']
        }

        # 해당 부재 데이터 필터링 (손상내용에 '받침' 또는 '전단키' 포함 시 교량받침으로 분류)
        component_keywords = component_filters.get(component_type, [])
        if not component_keywords:
            return []

        # 교량받침의 경우 손상내용에 '받침' 또는 '전단키' 포함된 모든 데이터 포함
        if component_type == 'bearing':
            # 기존 교량받침 부재 + 손상내용에 '받침' 또는 '전단키' 포함된 데이터
            basic_bearing_mask = df['부재명'].str.contains('|'.join(component_keywords), na=False)
            bearing_damage_mask = (df['손상내용'].str.contains('받침', na=False) |
                                  df['손상내용'].str.contains('전단키', na=False))
            filtered_df = df[basic_bearing_mask | bearing_damage_mask]
            print(f"교량받침 필터링 결과: 기본 {basic_bearing_mask.sum()}개, 손상내용 기반 {bearing_damage_mask.sum()}개, 총 {len(filtered_df)}개")
        else:
            # 다른 부재의 경우 손상내용에 '받침' 또는 '전단키' 포함된 데이터 제외
            basic_mask = df['부재명'].str.contains('|'.join(component_keywords), na=False)
            bearing_damage_mask = (df['손상내용'].str.contains('받침', na=False) |
                                  df['손상내용'].str.contains('전단키', na=False))
            filtered_df = df[basic_mask & ~bearing_damage_mask]
            if bearing_damage_mask.sum() > 0:
                print(f"{component_type} 부재에서 제외된 받침/전단키 관련 데이터: {bearing_damage_mask.sum()}개")

        if filtered_df.empty:
            return []

        # 부재별 데이터 처리
        from .condition_evaluation import (
            filter_positions_by_component,
            get_max_crack_width_for_span,
            calculate_crack_ratio_for_span,
            classify_damage_for_evaluation,
            calculate_condition_grade
        )

        evaluation_data = []

        # 경간별로 데이터 처리
        positions = sorted(filtered_df['부재위치'].unique())

        for position in positions:
            pos_data = filtered_df[filtered_df['부재위치'] == position]

            # 기본 상태평가 데이터 구조
            span_data = {
                'span_id': str(position),
                'inspection_area': 100,  # 기본 점검면적
                'grade': 'a'
            }

            # 부재 유형별 상세 데이터 처리
            if component_type in ['slab', 'girder', 'crossbeam']:
                # 콘크리트 부재: 1방향/2방향 균열 처리
                component_name = pos_data['부재명'].iloc[0] if not pos_data.empty else component_keywords[0]

                crack_width_1d = get_max_crack_width_for_span(df, component_name, position, '1방향')
                crack_ratio_1d = calculate_crack_ratio_for_span(df, component_name, position, '1방향')
                crack_width_2d = get_max_crack_width_for_span(df, component_name, position, '2방향')
                crack_ratio_2d = calculate_crack_ratio_for_span(df, component_name, position, '2방향')

                span_data.update({
                    'crack_width_1d': crack_width_1d,
                    'crack_ratio_1d': crack_ratio_1d,
                    'crack_width_2d': crack_width_2d,
                    'crack_ratio_2d': crack_ratio_2d,
                    'original_crack_length_1d': crack_ratio_1d / 0.25 if crack_ratio_1d > 0 else 0,
                    'original_crack_length_2d': crack_ratio_2d / 0.25 if crack_ratio_2d > 0 else 0
                })

                # 기타 손상 데이터 처리
                leak_quantity = 0
                surface_damage_quantity = 0
                rebar_corrosion_quantity = 0

                for _, row in pos_data.iterrows():
                    damage_info = classify_damage_for_evaluation(row['손상내용'], component_name)
                    damage_quantity = float(row['손상물량']) if pd.notnull(row['손상물량']) else 0

                    if damage_info['type'] == '누수':
                        leak_quantity += damage_quantity
                    elif damage_info['type'] == '표면손상':
                        surface_damage_quantity += damage_quantity
                    elif damage_info['type'] == '철근부식':
                        rebar_corrosion_quantity += damage_quantity

                span_data.update({
                    'leak_ratio': (leak_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'surface_damage_ratio': (surface_damage_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'original_leak_quantity': leak_quantity,
                    'original_surface_damage_quantity': surface_damage_quantity,
                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                })

            elif component_type in ['abutment', 'pier']:
                # 교대/교각: 균열폭, 변위, 표면손상, 철근부식
                max_crack_width = 0
                surface_damage_quantity = 0
                rebar_corrosion_quantity = 0

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']
                    damage_quantity = float(row['손상물량']) if pd.notnull(row['손상물량']) else 0

                    # 균열폭 추출
                    if '균열' in damage_desc:
                        from .condition_evaluation import extract_crack_width_from_description
                        crack_width = extract_crack_width_from_description(damage_desc)
                        if crack_width:
                            max_crack_width = max(max_crack_width, crack_width)

                    damage_info = classify_damage_for_evaluation(damage_desc, pos_data['부재명'].iloc[0])

                    if damage_info['type'] == '표면손상':
                        surface_damage_quantity += damage_quantity
                    elif damage_info['type'] == '철근부식':
                        rebar_corrosion_quantity += damage_quantity

                span_data.update({
                    'crack_width': max_crack_width,
                    'deformation': '-',  # 변위는 별도 처리 필요
                    'surface_damage_ratio': (surface_damage_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'original_surface_damage_quantity': surface_damage_quantity,
                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                })

            elif component_type == 'foundation':
                # 기초: 균열폭, 단면손상, 세굴, 침하
                max_crack_width = 0
                damage_condition = '-'
                erosion = '-'
                settlement = '-'

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']

                    if '균열' in damage_desc:
                        from .condition_evaluation import extract_crack_width_from_description
                        crack_width = extract_crack_width_from_description(damage_desc)
                        if crack_width:
                            max_crack_width = max(max_crack_width, crack_width)

                    if any(keyword in damage_desc for keyword in ['단면손상', '박리', '박락']):
                        damage_condition = '단면손상'

                    if '세굴' in damage_desc:
                        erosion = '세굴'

                    if '침하' in damage_desc:
                        settlement = '침하'

                span_data.update({
                    'crack_width': max_crack_width,
                    'damage_condition': damage_condition,
                    'erosion': erosion,
                    'settlement': settlement
                })

            elif component_type == 'bearing':
                # 교량받침: 본체 상태, 균열폭, 단면손상
                body_condition = '-'
                max_crack_width = 0
                section_damage = '-'

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']

                    if any(keyword in damage_desc for keyword in ['부식', '도장', '편기']):
                        body_condition = damage_desc[:10]  # 첫 10글자만 표시

                    if '균열' in damage_desc:
                        from .condition_evaluation import extract_crack_width_from_description
                        crack_width = extract_crack_width_from_description(damage_desc)
                        if crack_width:
                            max_crack_width = max(max_crack_width, crack_width)

                    if any(keyword in damage_desc for keyword in ['단면손상', '박리', '박락']):
                        section_damage = '단면손상'

                span_data.update({
                    'body_condition': body_condition,
                    'crack_width': max_crack_width,
                    'section_damage': section_damage
                })

            elif component_type == 'expansionJoint':
                # 신축이음: 본체 상태, 후타재 균열, 단면손상
                body_condition = '-'
                footer_crack = '-'
                section_damage = '-'

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']

                    if any(keyword in damage_desc for keyword in ['본체', '탈락', '파손']):
                        body_condition = damage_desc[:10]

                    if '균열' in damage_desc and any(keyword in damage_desc for keyword in ['후타', '콘크리트']):
                        footer_crack = '균열'

                    if any(keyword in damage_desc for keyword in ['단면손상', '박리', '박락']) and '후타' in damage_desc:
                        section_damage = '단면손상'

                span_data.update({
                    'body_condition': body_condition,
                    'footer_crack': footer_crack,
                    'section_damage': section_damage
                })

            elif component_type == 'pavement':
                # 교면포장: 포장불량 면적률, 주행성, 배수
                damage_quantity = 0
                traffic_condition = '양호'
                drainage_condition = '양호'

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']
                    quantity = float(row['손상물량']) if pd.notnull(row['손상물량']) else 0
                    unit = str(row['단위']) if pd.notnull(row['단위']) else ''

                    # 균열 단위가 m인 경우 0.25 곱하기
                    if '균열' in damage_desc and unit.lower() == 'm':
                        quantity *= 0.25

                    damage_quantity += quantity

                    if any(keyword in damage_desc for keyword in ['파손', '패임', '들뜨']):
                        traffic_condition = '소요'

                    if '배수' in damage_desc and '불량' in damage_desc:
                        drainage_condition = '배수불량'

                span_data.update({
                    'damage_ratio': (damage_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'traffic_condition': traffic_condition,
                    'drainage_condition': drainage_condition,
                    'original_damage_quantity': damage_quantity
                })

            elif component_type == 'drainage':
                # 배수시설: 배수구/배수관 손상현황
                outlet_condition = '-'
                pipe_condition = '-'

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']

                    if '배수구' in damage_desc:
                        if any(keyword in damage_desc for keyword in ['막힘', '퇴적', '파손']):
                            outlet_condition = damage_desc[:15]

                    if '배수관' in damage_desc:
                        if any(keyword in damage_desc for keyword in ['탈락', '길이부족', '설치불량']):
                            pipe_condition = damage_desc[:15]

                span_data.update({
                    'outlet_condition': outlet_condition,
                    'pipe_condition': pipe_condition
                })

            elif component_type == 'railing':
                # 난간 및 연석: 도장손상, 부식, 연결재손상, 균열, 표면손상, 철근부식
                max_crack_width = 0
                paint_damage = 0
                corrosion_ratio = 0
                connection_damage = 0  # 연결재 및 단면손상 추가
                surface_damage_quantity = 0
                rebar_corrosion_quantity = 0

                for _, row in pos_data.iterrows():
                    damage_desc = row['손상내용']
                    damage_quantity = float(row['손상물량']) if pd.notnull(row['손상물량']) else 0

                    if '균열' in damage_desc:
                        from .condition_evaluation import extract_crack_width_from_description
                        crack_width = extract_crack_width_from_description(damage_desc)
                        if crack_width:
                            max_crack_width = max(max_crack_width, crack_width)

                    # classify_damage_for_evaluation 결과에 따른 처리
                    damage_info = classify_damage_for_evaluation(damage_desc, pos_data['부재명'].iloc[0])

                    if damage_info['type'] == '도장손상':
                        paint_damage += damage_quantity
                    elif damage_info['type'] == '부식':
                        corrosion_ratio += damage_quantity
                    elif damage_info['type'] == '연결재손상':  # 연결재손상 처리 추가
                        connection_damage += damage_quantity
                    elif damage_info['type'] == '표면손상':
                        surface_damage_quantity += damage_quantity
                    elif damage_info['type'] == '철근부식':
                        rebar_corrosion_quantity += damage_quantity

                span_data.update({
                    'crack_width': max_crack_width,
                    'paint_damage': (paint_damage / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'corrosion_ratio': (corrosion_ratio / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'connection_damage_ratio': (connection_damage / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,  # 연결재손상 비율 추가
                    'surface_damage_ratio': (surface_damage_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'rebar_corrosion_ratio': (rebar_corrosion_quantity / span_data['inspection_area']) * 100 if span_data['inspection_area'] > 0 else 0,
                    'original_paint_damage': paint_damage,
                    'original_corrosion_ratio': corrosion_ratio,
                    'original_connection_damage': connection_damage,  # 원본 연결재손상 물량 추가
                    'original_surface_damage_quantity': surface_damage_quantity,
                    'original_rebar_corrosion_quantity': rebar_corrosion_quantity
                })

            # 등급 계산
            damages = []

            # 균열 정보 추가
            if 'crack_width' in span_data and span_data['crack_width'] > 0:
                damages.append({
                    'type': '균열',
                    'crack_width': span_data['crack_width'],
                    'severity': 'medium'
                })

            # 기타 손상 정보 추가
            if 'surface_damage_ratio' in span_data and span_data['surface_damage_ratio'] > 0:
                damages.append({'type': '표면손상', 'severity': 'medium'})

            if 'rebar_corrosion_ratio' in span_data and span_data['rebar_corrosion_ratio'] > 0:
                damages.append({'type': '철근부식', 'severity': 'high'})

            # 등급 계산
            span_data['grade'] = calculate_condition_grade(damages)

            evaluation_data.append(span_data)

        return evaluation_data

    except Exception as e:
        print(f"부재별 상태평가 데이터 생성 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
