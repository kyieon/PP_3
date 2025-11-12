"""
신축이음 상태평가 부분을 수정한 evaluation_data.py의 신축이음 처리 부분
"""

def process_expansion_joint_damage(pos_data):
    """신축이음 손상 데이터 처리 함수"""
    print(f"        Processing expansion joint damages:")
    
    # 모든 손상 데이터 확인
    body_damages = []
    footer_crack_damages = []
    footer_section_damages = []
    
    for damage in pos_data.get('damages', []):
        original_desc = damage.get('original_desc', '').lower()
        damage_type = damage.get('type', '')
        quantity = damage.get('quantity', 0)
        
        print(f"          Damage: {original_desc}, Type: {damage_type}, Quantity: {quantity}")
        
        # 본체 관련 손상 처리 (유간, 이물질, 본체, 부식, 고무재, 이음부, 볼트 등)
        if (any(keyword in original_desc for keyword in ['유간', '이물질', '본체', '부식', '고무재', '이음부', '볼트']) or
            '신축이음' in original_desc or 
            '이음장치' in original_desc) and quantity > 0:
            
            if '부식' in original_desc:
                body_damages.append('본체 부식')
            elif '탈락' in original_desc or '파손' in original_desc:
                body_damages.append('본체 파손') 
            elif '노화' in original_desc:
                body_damages.append('본체 노화')
            elif '유간' in original_desc:
                body_damages.append('유간 이상')
            elif '이물질' in original_desc:
                body_damages.append('이물질 끼임')
            elif '고무재' in original_desc:
                body_damages.append('고무재 손상')
            elif '볼트' in original_desc:
                body_damages.append('볼트 손상')
            else:
                body_damages.append('본체 손상')
        
        # 후타재 관련 손상 처리 - 균열을 제외하고 단면손상으로
        elif '후타재' in original_desc and quantity > 0:
            if '균열' in original_desc or '균열' in damage_type:
                footer_crack_damages.append(original_desc)
            else:
                footer_section_damages.append(original_desc)
        
        # 콘크리트 관련 손상을 후타재로 처리
        elif ('콘크리트' in original_desc or '몰탈' in original_desc) and quantity > 0:
            if '균열' in original_desc or '균열' in damage_type:
                footer_crack_damages.append('후타재 균열')
            else:
                footer_section_damages.append('후타재 단면손상')
        
        # 일반 균열을 후타재 균열로 처리
        elif '균열' in damage_type and quantity > 0:
            footer_crack_damages.append('후타재 균열')
        
        # 후타재가 없는 일반 손상들 중 균열을 제외한 단면손상을 후타재 단면손상으로 처리
        elif ('후타재' not in original_desc and 
              '균열' not in original_desc and 
              '균열' not in damage_type and 
              quantity > 0 and
              not any(keyword in original_desc for keyword in ['유간', '이물질', '본체', '부식', '고무재', '이음부', '볼트'])):
            footer_section_damages.append(original_desc)
    
    # 본체 상태 결정
    if body_damages:
        body_condition = ', '.join(list(set(body_damages))[:2])  # 중복 제거하고 최대 2개
    else:
        body_condition = '-'
    
    # 후타재 균열 상태 결정
    footer_crack = '균열' if footer_crack_damages else '-'
    
    # 후타재 단면손상 상태 결정  
    footer_damage = '단면손상' if footer_section_damages else '-'
    
    print(f"        Expansion joint result - Body: {body_condition}, Crack: {footer_crack}, Damage: {footer_damage}")
    
    return {
        'body_condition': body_condition,
        'footer_crack': footer_crack,
        'section_damage': footer_damage,
        # 손상 세부 정보 추가
        'body_damages': body_damages,
        'footer_crack_damages': footer_crack_damages,
        'footer_section_damages': footer_section_damages
    }
