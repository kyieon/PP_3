"""
손상 데이터 처리를 위한 유틸리티 함수들
"""
import re

def natural_sort_key(s):
    """
    자연스러운 정렬을 위한 키 생성 함수
    예: ['1', '2', '10'] -> ['1', '2', '10'] (문자열 정렬 시 '10'이 '2' 앞에 오는 것 방지)
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]

def normalize_damage(damage_desc):
    """
    손상 내용 정규화
    
    Args:
        damage_desc (str): 원본 손상 내용
        
    Returns:
        str: 정규화된 손상 내용
    """
    # 공백 제거 및 소문자 변환
    damage = damage_desc.strip().lower()
    
    # 특수문자 제거 (단, 괄호와 숫자는 유지)
    damage = re.sub(r'[^\w\s()0-9.]', '', damage)
    
    # 연속된 공백을 하나로
    damage = re.sub(r'\s+', ' ', damage)
    
    return damage

def get_damage_explanations():
    """
    손상 유형별 설명 사전 반환
    
    Returns:
        dict: 손상 유형과 그에 대한 설명을 담은 사전
    """
    return {
        '균열': '콘크리트나 강재의 표면에 발생한 갈라짐',
        '누수': '구조물을 통해 물이 새어나오는 현상',
        '백태': '콘크리트 표면에 하얀 가루가 피어나는 현상',
        '박리': '콘크리트 표면이 떨어져 나가는 현상',
        '철근노출': '콘크리트가 탈락하여 내부 철근이 드러난 상태',
        '파손': '구조물의 일부가 깨지거나 부서진 상태',
        '부식': '금속 재료가 산화되어 녹이 발생한 상태',
        '단차': '연결부위의 높이가 서로 다른 상태',
        '침하': '구조물이 아래로 가라앉은 상태',
        '들뜸': '포장면이 하부와 분리되어 떠있는 상태',
        '마모': '표면이 닳아 없어진 상태',
        '탈락': '부재의 일부가 떨어져 나간 상태'
    }

def classify_repair(damage_desc):
    """
    손상 내용에 따른 보수 방법 분류
    
    Args:
        damage_desc (str): 손상 내용
        
    Returns:
        str: 추천되는 보수 방법
    """
    damage = normalize_damage(damage_desc)
    
    if '균열' in damage:
        if any(x in damage for x in ['0.3mm', '0.5mm']):
            return '주입공법'
        else:
            return '표면처리공법'
            
    elif '누수' in damage or '백태' in damage:
        return '방수공법'
        
    elif '박리' in damage or '들뜸' in damage:
        return '단면보수'
        
    elif '철근노출' in damage:
        return '단면복구'
        
    elif '부식' in damage:
        return '방청처리'
        
    elif '파손' in damage or '탈락' in damage:
        return '교체'
        
    elif '단차' in damage:
        return '재설치'
        
    elif '침하' in damage:
        return '기초보강'
        
    elif '마모' in damage:
        return '표면보수'
        
    else:
        return '상태점검 후 결정' 