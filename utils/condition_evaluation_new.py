"""
교량 상태평가용 데이터 처리 모듈 (개선된 1방향/2방향 균열 분류)
부재명, 부재위치, 손상내용, 균열폭, 손상물량 데이터를 상태평가용으로 피벗
"""
import pandas as pd
import re
from collections import defaultdict
from utils.common import normalize_component, sort_components


def classify_damage_for_evaluation(damage_desc, component_name=None):
    """상태평가용 손상 분류 (교대, 교각의 경우 누수를 표면손상에 포함, 기초의 경우 균열 외 단면손상으로 분류, 신축이음의 경우 본체/후타재 분류, 교량받침의 경우 본체/콘크리트 분류, 배수시설의 경우 모든 손상 포함)"""
    damage_desc = damage_desc.strip()

    # 균열 관련 - 기존 방식 유지하되 개선된 함수들과 연동
    if '균열' in damage_desc:
        crack_width = extract_crack_width_from_description(damage_desc)
        if crack_width is not None:
            return {
                'type': '균열',
                'crack_width': crack_width,
                'severity': get_crack_severity(crack_width)
            }
        return {'type': '균열', 'crack_width': None, 'severity': 'unknown'}

    # 철근부식 관련 - 철근노출이 포함된 모든 경우 포함
    if any(keyword in damage_desc for keyword in ['철근부식', '철근노출']) and '잡철근노출' not in damage_desc:
        return {'type': '철근부식', 'severity': 'high'}

    # 배수시설 부재의 경우: 모든 손상을 배수 손상으로 분류 (제한 없이 모든 손상내용 포함)
    if component_name and ('배수시설' in component_name or '배수구' in component_name or '배수관' in component_name):
        # 배수시설 관련 키워드들
        drainage_keywords = ['막힘', '토사퇴적', '퇴적', '탈락', '파손', '균열', '부식', '누수', '이물질', '청소불량', '적치', '길이부족', '설치불량', '망실', '미설치']

        # 특정 손상 유형별 세분화
        if any(keyword in damage_desc for keyword in ['막힘', '토사퇴적', '퇴적', '적치']):
            return {'type': '배수구막힘', 'severity': 'medium'}
        elif any(keyword in damage_desc for keyword in ['탈락', '파손', '망실', '미설치']):
            return {'type': '배수구파손', 'severity': 'high'}
        elif any(keyword in damage_desc for keyword in ['누수', '새어나옴']):
            return {'type': '배수구누수', 'severity': 'medium'}
        elif any(keyword in damage_desc for keyword in ['길이부족', '설치불량']):
            return {'type': '배수관설치불량', 'severity': 'medium'}
        else:
            # 기타 모든 배수시설 손상
            return {'type': '배수시설기타손상', 'severity': 'medium'}

    # 교량받침 부재의 경우: 본체와 콘크리트로 분류
    if component_name and ('받침' in component_name or '교량받침' in component_name or '받침장치' in component_name or '탄성받침' in component_name or '고무받침' in component_name or '강재받침' in component_name or '베어링' in component_name):
        # 본체 관련 키워드 확인
        body_keywords = ['부식', '도장박리', '도장탈락', '도장', '본체', '편기', '고무재', '볼트', '앵커', '너트']
        if any(keyword in damage_desc for keyword in body_keywords):
            if '균열' in damage_desc:
                return {'type': '본체_균열', 'severity': 'medium'}
            else:
                return {'type': '본체_단면손상', 'severity': 'medium'}

        # 콘크리트 관련 (콘크리트, 모르타르 등)
        concrete_keywords = ['콘크리트', '모르타르', '모르타', '받침콘크리트', '받침모르타르']
        if any(keyword in damage_desc for keyword in concrete_keywords):
            if '균열' in damage_desc:
                return {'type': '콘크리트_균열', 'severity': 'medium'}
            else:
                return {'type': '콘크리트_단면손상', 'severity': 'medium'}

        # 기타 받침 관련 손상은 본체로 분류
        if '균열' in damage_desc:
            return {'type': '본체_균열', 'severity': 'medium'}
        else:
            return {'type': '본체_단면손상', 'severity': 'medium'}

    # 신축이음 부재의 경우: 본체와 후타재로 분류
    if component_name and ('신축이음' in component_name or '이음장치' in component_name):
        # 본체 관련 키워드 확인 (본체, 볼트, 고무재, 유간, 이물질, 토사퇴적)
        body_keywords = ['본체', '볼트', '고무재', '유간', '이물질', '토사퇴적', '부식', '신축이음', '이음장치', '탈락', '파손', '노화']
        if any(keyword in damage_desc for keyword in body_keywords):
            return {'type': '본체_손상', 'severity': 'medium'}

        # 후타재 관련 키워드 확인 (후타재 또는 콘크리트/모르타르 관련)
        elif any(keyword in damage_desc for keyword in ['후타', '앵커', '볼트', '고정', '콘크리트', '모르타르']):
            if '균열' in damage_desc:
                return {'type': '후타재_균열', 'severity': 'medium'}
            else:
                return {'type': '후타재_단면손상', 'severity': 'medium'}

        # 일반 균열은 후타재 균열로 분류
        elif '균열' in damage_desc:
            return {'type': '후타재_균열', 'severity': 'medium'}

        # 기타 신축이음 관련 손상은 본체로 분류
        else:
            return {'type': '본체_손상', 'severity': 'medium'}

    # 기초 부재의 경우: 균열이 아닌 모든 손상을 단면손상으로 분류
    if component_name and '기초' in component_name:
        return {'type': '단면손상', 'severity': 'medium'}

    # 교대, 교각의 경우 누수, 백태, 녹물을 표면손상에 포함
    if component_name and ('교대' in component_name or '교각' in component_name):
        # 누수, 백태, 녹물도 표면손상으로 분류
        if any(keyword in damage_desc for keyword in ['누수', '백태', '침출', '녹물']):
            return {'type': '표면손상', 'severity': 'medium'}
    else:
        # 교대, 교각이 아닌 경우 기존 방식 유지 (누수는 별도 분류)
        if any(keyword in damage_desc for keyword in ['누수', '백태', '침출']):
            return {'type': '누수', 'severity': 'medium'}

    # 난간 및 연석 부재의 경우 특별한 손상 분류 적용
    if component_name and any(comp in component_name for comp in ['난간', '연석', '방호', '방음', '가드레일', '낙석', '차광', '중분대', '중앙분리대']):
        # 강재 - 도장손상 헤더열: 도장, 방음, 난간, 낙석 관련 손상
        if any(keyword in damage_desc for keyword in ['도장', '방음', '난간', '낙석']):
            return {'type': '도장손상', 'severity': 'medium'}

        # 강재 - 부식발생 헤더열: '부식' 글자가 들어간 손상 (철근부식 제외)
        if '부식' in damage_desc and '철근' not in damage_desc:
            return {'type': '부식', 'severity': 'medium'}

        # 강재 - 연결재 및 단면손상 헤더열: 볼트, 앵커, 너트, 지주 관련 손상
        if any(keyword in damage_desc for keyword in ['볼트', '앵커', '너트', '지주']):
            return {'type': '연결재손상', 'severity': 'medium'}

        # 구조손상이 아닌 손상은 모두 표면손상으로 분류 (균열, 철근노출 제외)
        if not any(keyword in damage_desc for keyword in ['균열', '철근노출', '철근부식']):
            return {'type': '표면손상', 'severity': 'medium'}

    # 기타 부재의 강재 관련 손상 (기존 로직 유지)
    if any(keyword in damage_desc for keyword in ['도장', '페인트', '페이트']):
        return {'type': '도장손상', 'severity': 'medium'}

    if any(keyword in damage_desc for keyword in ['부식', '녹']) and '철근' not in damage_desc:
        return {'type': '부식', 'severity': 'medium'}

    # 녹물 관련 손상은 표면손상으로 분류
    if any(keyword in damage_desc for keyword in ['녹물']):
        return {'type': '표면손상', 'severity': 'medium'}

    # 표면손상 관련 - 균열, 철근부식이 아닌 모든 손상
    return {'type': '표면손상', 'severity': 'medium'}


def extract_crack_width_from_description(damage_desc):
    """손상내용에서 균열폭 추출 (개선된 방식)"""
    if '균열' not in damage_desc:
        return None

    # 대표적인 균열 패턴들을 기본값으로 처리
    if '0.3㎜미만' in damage_desc or '0.3mm미만' in damage_desc:
        return 0.2  # 0.3mm 미만은 0.2mm로 설정
    elif '0.3㎜이상' in damage_desc or '0.3mm이상' in damage_desc:
        return 0.3  # 0.3mm 이상은 0.3mm로 설정
    elif '0.5㎜이상' in damage_desc or '0.5mm이상' in damage_desc:
        return 0.5  # 0.5mm 이상은 0.5mm로 설정

    # 균열폭 패턴 매칭 (mm, ㎜)
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:mm|㎜)',  # 숫자 + mm 또는 ㎜
        r'균열\((\d+(?:\.\d+)?)(?:mm|㎜)?\)',  # 균열(숫자mm)
        r'폭[=:]\s*(\d+(?:\.\d+)?)',  # 폭=숫자
        r'(\d+(?:\.\d+)?)(?:mm|㎜)\s*이상',  # 숫자mm이상
        r'(\d+(?:\.\d+)?)(?:mm|㎜)\s*미만',  # 숫자mm미만 (미만이면 절반값)
    ]

    for pattern in patterns:
        match = re.search(pattern, damage_desc)
        if match:
            width = float(match.group(1))
            # 미만인 경우 절반값 사용
            if '미만' in damage_desc:
                return width / 2
            return width

    # 패턴이 없으면 - 망상균열은 None 반환 (상위 레벨에서 손상물량 체크 후 처리)
    if '망상균열' in damage_desc:
        return None  # 망상균열은 상위 레벨에서 손상물량 체크 후 처리

    return 0.1  # 기본 균열폭


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
