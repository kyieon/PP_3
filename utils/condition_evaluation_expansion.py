"""
신축이음 상태평가용 데이터 처리 모듈
"""
import pandas as pd
import re
from collections import defaultdict


def classify_expansion_joint_damage(damage_desc):
    """신축이음 손상 분류 - 본체 및 후타재 구분"""
    damage_desc = damage_desc.strip()
    
    # 균열 관련
    if '균열' in damage_desc:
        return {
            'type': '균열',
            'category': '본체' if '본체' in damage_desc or ('후타재' not in damage_desc and '커버' not in damage_desc) else '후타재',
            'severity': 'medium'
        }
    
    # 단면손상 관련 (파손, 탈락, 변형 등)
    if any(keyword in damage_desc for keyword in ['파손', '탈락', '변형', '손상', '부식', '마모']):
        return {
            'type': '단면손상',
            'category': '본체' if '본체' in damage_desc or ('후타재' not in damage_desc and '커버' not in damage_desc) else '후타재',
            'severity': 'medium'
        }
    
    # 기본적으로 본체 단면손상으로 분류
    return {
        'type': '단면손상',
        'category': '본체',
        'severity': 'medium'
    }


def process_expansion_joint_data(df):
    """신축이음 데이터를 상태평가 형식으로 처리"""
    # 신축이음 관련 부재 필터링
    expansion_df = df[
        df['부재명'].str.contains('신축이음', na=False) | 
        df['부재명'].str.contains('이음장치', na=False)
    ].copy()
    
    if expansion_df.empty:
        return {}
    
    # 부재위치별로 그룹화 (A1, P1, P2, A2 등)
    positions = sorted(expansion_df['부재위치'].unique())
    
    evaluation_data = {}
    
    for position in positions:
        pos_df = expansion_df[expansion_df['부재위치'] == position]
        
        position_data = {
            'body_crack': [],           # 본체 균열
            'body_section_damage': [],  # 본체 단면손상
            'footer_crack_1': [],       # 후타재 균열 1
            'footer_section_damage_1': [], # 후타재 단면손상 1
            'footer_crack_2': [],       # 후타재 균열 2
            'footer_section_damage_2': [], # 후타재 단면손상 2
            'grade': 'a'
        }
        
        # 각 손상에 대해 분류 처리
        for _, row in pos_df.iterrows():
            damage_info = classify_expansion_joint_damage(row['손상내용'])
            damage_info['quantity'] = row['손상물량']
            damage_info['original_desc'] = row['손상내용']
            
            # 본체 손상 분류
            if damage_info['category'] == '본체':
                if damage_info['type'] == '균열':
                    position_data['body_crack'].append(damage_info)
                else:
                    position_data['body_section_damage'].append(damage_info)
            # 후타재 손상 분류 (현재는 1번에만 배치, 필요시 2번으로 확장 가능)
            else:
                if damage_info['type'] == '균열':
                    position_data['footer_crack_1'].append(damage_info)
                else:
                    position_data['footer_section_damage_1'].append(damage_info)
        
        # 상태등급 계산 (단순화된 버전)
        total_damages = (len(position_data['body_crack']) + 
                        len(position_data['body_section_damage']) + 
                        len(position_data['footer_crack_1']) + 
                        len(position_data['footer_section_damage_1']))
        
        if total_damages == 0:
            position_data['grade'] = 'a'
        elif total_damages <= 2:
            position_data['grade'] = 'b'
        elif total_damages <= 4:
            position_data['grade'] = 'c'
        else:
            position_data['grade'] = 'd'
        
        evaluation_data[position.upper()] = position_data
    
    return evaluation_data


def get_expansion_joint_condition_text(damages):
    """손상 리스트를 기반으로 상태 텍스트 생성"""
    if not damages:
        return '-'
    
    # 손상내용명 중복 제거하여 수집
    damage_descriptions = []
    for damage in damages:
        desc = damage.get('original_desc', '')
        if desc and desc not in damage_descriptions:
            damage_descriptions.append(desc)
    
    # 쉼표로 구분하여 연결
    return ', '.join(damage_descriptions) if damage_descriptions else '-'
