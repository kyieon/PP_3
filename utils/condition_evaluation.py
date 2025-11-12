"""
교량 상태평가용 데이터 처리 모듈 (개선된 1방향/2방향 균열 분류)
부재명, 부재위치, 손상내용, 균열폭, 손상물량 데이터를 상태평가용으로 피벗
"""
import pandas as pd
import re
from collections import defaultdict
from utils.common import normalize_component, sort_components
from utils.common import trim_dataframe_str_columns


def extract_crack_width_from_uploaded_data(df, component_name, position, damage_desc):
    """업로드한 파일의 균열폭 열에서 데이터를 추출 (개선된 버전)"""
    # 문자열 컬럼 trim 처리
    df = trim_dataframe_str_columns(df)
    # ...기존 코드...
    try:
        # 첫 번째: 균열폭 컬럼에서 데이터 검색 (우선순위 높음)
        # 해당 경간의 해당 손상에 대한 균열폭 데이터 검색
        mask = (df['부재명'] == component_name) & \
               (df['부재위치'] == position) & \
               (df['손상내용'] == damage_desc)

        matched_data = df[mask]

        if not matched_data.empty:
            # 여러 균열폭 컬럼 검사 ('균열폭', '균열폭\n(㎜)' 등)
            for col in ['균열폭', '균열폭\n(㎜)', 'Crack Width', '균열 폭']:
                if col in df.columns:
                    crack_widths = pd.to_numeric(matched_data[col], errors='coerce').dropna()
                    if not crack_widths.empty and crack_widths.max() > 0:
                        return float(crack_widths.max())

        # 두 번째: 손상내용에서 추출 시도 (백업 방식)
        desc_width = extract_crack_width_from_description(damage_desc)
        return desc_width  # None일 수 있음 (망상균열의 경우)

    except Exception as e:
        print(f"균열폭 추출 중 오류: {e}")
        return extract_crack_width_from_description(damage_desc)


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


def calculate_crack_ratio_for_span(df, component_name, position, crack_direction):
    """해당 경간의 균열율 계산 (모든 균열의 합계)"""
    try:
        # 거더, 가로보, 기초, 신축이음, 교면포장, 배수시설, 난간 관련 모든 부재를 포함하도록 마스크 생성
        if '거더' in component_name:
            # 거더 관련 모든 부재 포함 (거더, 거더 내부, 거더 외부, 주거더, 부거더 등)
            component_mask = df['부재명'].str.contains('거더', na=False)
        elif '가로보' in component_name:
            # 가로보 관련 모든 부재 포함 (가로보, 세로보, 격벽, 가로보 내부, 가로보 외부 등)
            component_mask = (df['부재명'].str.contains('가로보', na=False) |
                            df['부재명'].str.contains('세로보', na=False) |
                            df['부재명'].str.contains('격벽', na=False))
        elif '기초' in component_name:
            # 기초 관련 모든 부재 포함 (기초, 엄지기초, 직접기초, 말뛅기초, 케이슨기초 등)
            component_mask = df['부재명'].str.contains('기초', na=False)
        elif '신축이음' in component_name:
            # 신축이음 관련 모든 부재 포함 (신축이음, 신축이음장치, 이음장치 등)
            component_mask = (df['부재명'].str.contains('신축이음', na=False) |
                            df['부재명'].str.contains('이음장치', na=False))
        elif '교면포장' in component_name or '포장' in component_name:
            # 교면포장 관련 모든 부재 포함 (교면포장, 포장 등)
            component_mask = (df['부재명'].str.contains('교면포장', na=False) |
                            df['부재명'].str.contains('포장', na=False))
        elif '배수시설' in component_name or '배수구' in component_name:
            # 배수시설 관련 모든 부재 포함 (배수시설, 배수구, 배수관 등)
            component_mask = (df['부재명'].str.contains('배수시설', na=False) |
                            df['부재명'].str.contains('배수구', na=False) |
                            df['부재명'].str.contains('배수관', na=False))
        elif '난간' in component_name or '연석' in component_name:
            # 난간 관련 모든 부재 포함 (추가 부재명 포함)
            component_mask = (df['부재명'].str.contains('난간', na=False) |
                            df['부재명'].str.contains('연석', na=False) |
                            df['부재명'].str.contains('방호울타리', na=False) |
                            df['부재명'].str.contains('방호벽', na=False) |
                            df['부재명'].str.contains('방음벽', na=False) |
                            df['부재명'].str.contains('방음판', na=False) |
                            df['부재명'].str.contains('방음', na=False) |
                            df['부재명'].str.contains('방호', na=False) |
                            df['부재명'].str.contains('중분대', na=False) |
                            df['부재명'].str.contains('중앙분리대', na=False) |
                            df['부재명'].str.contains('가드레일', na=False) |
                            df['부재명'].str.contains('낙석', na=False) |
                            df['부재명'].str.contains('차광', na=False) |
                            df['부재명'].str.contains('경계석', na=False) |
                            df['부재명'].str.contains('투석방지망', na=False))
        else:
            # 기존 로직 유지
            component_mask = (df['부재명'] == component_name)

        # 해당 경간의 해당 방향 균열 데이터 필터링
        if crack_direction == '1방향':
            # 1방향 균열: 균열, 균열부 백태, 균열이 들어간 손상들 (망상균열 제외)
            mask = component_mask & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('균열', na=False)) & \
                   (~df['손상내용'].str.contains('망상균열', na=False))
        else:  # 2방향
            # 2방향 균열: 망상균열이 포함된 손상들
            mask = component_mask & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('망상균열', na=False))

        matched_data = df[mask]

        if not matched_data.empty:
            # 손상물량의 합계 반환
            total_quantity = pd.to_numeric(matched_data['손상물량'], errors='coerce').sum()

            # 교면포장의 1방향 균열에 대해서만 0.25 곱하기 적용
            if ('교면포장' in component_name or '포장' in component_name) and crack_direction == '1방향':
                # 교면포장 1방향 균열의 경우, 단위가 'm'이고 망상균열이 아닌 경우에만 0.25 곱하기
                adjusted_quantity = total_quantity
                for _, row in matched_data.iterrows():
                    damage_desc = row['손상내용']
                    unit = row.get('단위', '').lower() if '단위' in row else ''

                    # 단위가 'm'이고 망상균열이 아닌 경우에만 0.25 곱하기
                    if ('균열' in damage_desc and
                        unit == 'm' and
                        '망상균열' not in damage_desc):
                        # 해당 행의 손상물량에 0.25 곱하기
                        row_quantity = pd.to_numeric(row['손상물량'], errors='coerce')
                        if pd.notnull(row_quantity) and row_quantity > 0:
                            # 전체 합계에서 해당 행의 원래 값을 빼고 0.25 곱한 값을 더함
                            adjusted_quantity = adjusted_quantity - row_quantity + (row_quantity * 0.25)
                            print(f"교면포장 1방향 균열 0.25 적용: {damage_desc}, 단위: {unit}, 원래값: {row_quantity}, 조정값: {row_quantity * 0.25}")

                total_quantity = adjusted_quantity

            if '거더' in component_name:
                print(f"거더 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '가로보' in component_name:
                print(f"가로보 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '기초' in component_name:
                print(f"기초 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '신축이음' in component_name:
                print(f"신축이음 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '교면포장' in component_name or '포장' in component_name:
                print(f"교면포장 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '배수시설' in component_name or '배수구' in component_name:
                print(f"배수시설 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            elif '난간' in component_name or '연석' in component_name or '방호울타리' in component_name:
                print(f"난간연석 균열율 계산 - 위치: {position}, 방향: {crack_direction}, 물량합계: {total_quantity}, 포함된 부재: {matched_data['부재명'].unique()}")
            return float(total_quantity) if pd.notnull(total_quantity) else 0

        return 0

    except Exception as e:
        print(f"균열율 계산 중 오류: {e}")
        return 0


def get_max_crack_width_for_span(df, component_name, position, crack_direction):
    """해당 경간의 최대 균열폭 계산"""
    # 문자열 컬럼 trim 처리
    #df = trim_dataframe_str_columns(df)
    # ...기존 코드...
    try:
        # 거더, 가로보, 기초, 신축이음, 교면포장, 배수시설, 난간 관련 모든 부재를 포함하도록 마스크 생성
        if '거더' in component_name:
            # 거더 관련 모든 부재 포함 (거더, 거더 내부, 거더 외부, 주거더, 부거더 등)
            component_mask = df['부재명'].str.contains('거더', na=False)
        elif '가로보' in component_name:
            # 가로보 관련 모든 부재 포함 (가로보, 세로보, 격벽, 가로보 내부, 가로보 외부 등)
            component_mask = (df['부재명'].str.contains('가로보', na=False) |
                            df['부재명'].str.contains('세로보', na=False) |
                            df['부재명'].str.contains('격벽', na=False))
        elif '기초' in component_name:
            # 기초 관련 모든 부재 포함 (기초, 엄지기초, 직접기초, 말뛅기초, 케이슨기초 등)
            component_mask = df['부재명'].str.contains('기초', na=False)
        elif '신축이음' in component_name:
            # 신축이음 관련 모든 부재 포함 (신축이음, 신축이음장치, 이음장치 등)
            component_mask = (df['부재명'].str.contains('신축이음', na=False) |
                            df['부재명'].str.contains('이음장치', na=False))
        elif '교면포장' in component_name or '포장' in component_name:
            # 교면포장 관련 모든 부재 포함 (교면포장, 포장 등)
            component_mask = (df['부재명'].str.contains('교면포장', na=False) |
                            df['부재명'].str.contains('포장', na=False))
        elif '배수시설' in component_name or '배수구' in component_name:
            # 배수시설 관련 모든 부재 포함 (배수시설, 배수구, 배수관 등)
            component_mask = (df['부재명'].str.contains('배수시설', na=False) |
                            df['부재명'].str.contains('배수구', na=False) |
                            df['부재명'].str.contains('배수관', na=False))
        elif '난간' in component_name or '연석' in component_name or '방호울타리' in component_name:
            # 난간 관련 모든 부재 포함 (추가 부재명 포함)
            component_mask = (df['부재명'].str.contains('난간', na=False) |
                            df['부재명'].str.contains('연석', na=False) |
                            df['부재명'].str.contains('방호울타리', na=False) |
                            df['부재명'].str.contains('방호벽', na=False) |
                            df['부재명'].str.contains('방음벽', na=False) |
                            df['부재명'].str.contains('방음판', na=False) |
                            df['부재명'].str.contains('방음', na=False) |
                            df['부재명'].str.contains('방호', na=False) |
                            df['부재명'].str.contains('중분대', na=False) |
                            df['부재명'].str.contains('중앙분리대', na=False) |
                            df['부재명'].str.contains('가드레일', na=False) |
                            df['부재명'].str.contains('낙석', na=False) |
                            df['부재명'].str.contains('차광', na=False) |
                            df['부재명'].str.contains('경계석', na=False) |
                            df['부재명'].str.contains('투석방지망', na=False))
        else:
            # 기존 로직 유지
            component_mask = (df['부재명'] == component_name)

        # 해당 경간의 해당 방향 균열 데이터 필터링
        if crack_direction == '1방향':
            # 1방향 균열: 균열, 균열부 백태, 균열이 들어간 손상들 (망상균열 제외)
            mask = component_mask & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('균열', na=False)) & \
                   (~df['손상내용'].str.contains('망상균열', na=False))
        else:  # 2방향
            # 2방향 균열: 망상균열이 포함된 손상들
            mask = component_mask & \
                   (df['부재위치'] == position) & \
                   (df['손상내용'].str.contains('망상균열', na=False))

        matched_data = df[mask]

        if matched_data.empty:
            return 0  # 데이터가 없으면 0 반환

        # 2방향 균열의 경우 손상물량(균열율) 먼저 확인
        if crack_direction == '2방향':
            # 손상물량의 합계 계산
            total_quantity = pd.to_numeric(matched_data['손상물량'], errors='coerce').sum()
            if pd.isna(total_quantity) or total_quantity == 0:
                return None  # 손상물량이 없으면 None 반환 (HTML에서 '-' 처리)

        max_width = 0
        has_explicit_crack_width = False  # 업로드 파일에 명시적인 균열폭이 있는지 확인

        for _, row in matched_data.iterrows():
            # 먼저 업로드 파일의 균열폭 컬럼 체크
            if '거더' in component_name:
                # 거더의 경우 모든 거더 관련 부재에서 검색
                mask_row = df['부재명'].str.contains('거더', na=False) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            elif '가로보' in component_name:
                # 가로보의 경우 모든 가로보 관련 부재에서 검색 (가로보, 세로보, 격벽 등)
                mask_row = (df['부재명'].str.contains('가로보', na=False) |
                           df['부재명'].str.contains('세로보', na=False) |
                           df['부재명'].str.contains('격벽', na=False)) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            elif '신축이음' in component_name:
                # 신축이음의 경우 모든 신축이음 관련 부재에서 검색
                mask_row = (df['부재명'].str.contains('신축이음', na=False) |
                           df['부재명'].str.contains('이음장치', na=False)) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            elif '교면포장' in component_name or '포장' in component_name:
                # 교면포장의 경우 모든 교면포장 관련 부재에서 검색
                mask_row = (df['부재명'].str.contains('교면포장', na=False) |
                           df['부재명'].str.contains('포장', na=False)) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            elif '배수시설' in component_name or '배수구' in component_name:
                # 배수시설의 경우 모든 배수시설 관련 부재에서 검색
                mask_row = (df['부재명'].str.contains('배수시설', na=False) |
                           df['부재명'].str.contains('배수구', na=False) |
                           df['부재명'].str.contains('배수관', na=False)) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            elif '난간' in component_name or '연석' in component_name:
                # 난간연석의 경우 모든 난간연석 관련 부재에서 검색 (추가 부재명 포함)
                mask_row = (df['부재명'].str.contains('난간', na=False) |
                           df['부재명'].str.contains('연석', na=False) |
                           df['부재명'].str.contains('방호울타리', na=False) |
                           df['부재명'].str.contains('방호벽', na=False) |
                           df['부재명'].str.contains('방음벽', na=False) |
                           df['부재명'].str.contains('방음판', na=False) |
                           df['부재명'].str.contains('방음', na=False) |
                           df['부재명'].str.contains('방호', na=False) |
                           df['부재명'].str.contains('중분대', na=False) |
                           df['부재명'].str.contains('중앙분리대', na=False) |
                           df['부재명'].str.contains('가드레일', na=False) |
                           df['부재명'].str.contains('낙석', na=False) |
                           df['부재명'].str.contains('차광', na=False) |
                           df['부재명'].str.contains('경계석', na=False) |
                           df['부재명'].str.contains('투석방지망', na=False)) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            else:
                # 기존 로직 유지
                mask_row = (df['부재명'] == component_name) & \
                          (df['부재위치'] == position) & \
                          (df['손상내용'] == row['손상내용'])
            matched_row_data = df[mask_row]

            # 업로드 파일에 균열폭 데이터가 있는지 확인
            found_in_column = False
            if not matched_row_data.empty:
                for col in ['균열폭', '균열폭\n(㎜)', 'Crack Width', '균열 폭']:
                    if col in df.columns:
                        crack_widths = pd.to_numeric(matched_row_data[col], errors='coerce').dropna()
                        if not crack_widths.empty and crack_widths.max() > 0:
                            width = float(crack_widths.max())
                            max_width = max(max_width, width)
                            has_explicit_crack_width = True  # 업로드 파일에 명시적 균열폭 존재
                            found_in_column = True
                            break

            # 업로드 파일에 없으면 손상내용에서 추출
            if not found_in_column:
                width = extract_crack_width_from_description(row['손상내용'])
                if width is not None and width > 0:
                    max_width = max(max_width, width)

        # 2방향 균열에서 손상물량이 있지만 균열폭이 명시되지 않은 경우에만 0.2 자동 설정
        if crack_direction == '2방향':
            # 손상물량 재확인
            total_quantity = pd.to_numeric(matched_data['손상물량'], errors='coerce').sum()
            if pd.notna(total_quantity) and total_quantity > 0:
                # 업로드 파일에 균열폭이 명시되지 않은 경우에만 0.2로 설정
                if not has_explicit_crack_width and max_width == 0:
                    return 0.2
                else:
                    return max_width if max_width > 0 else None
            else:
                return None  # 손상물량이 없으면 None 반환

        return max_width

    except Exception as e:
        print(f"최대 균열폭 계산 중 오류: {e}")
        return 0


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
    if component_name and any(comp in component_name for comp in ['난간', '연석', '방호', '방음', '가드레일', '낙석', '차광', '중분대', '중앙분리대', '투석방지망']):
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
    """손상 데이터를 기반으로 상태등급 계산 (개선된 1방향/2방향 균열 지원)"""
    # 최대 균열폭 기준
    max_crack_width = 0
    total_crack_ratio = 0
    has_surface_damage = False
    has_rebar_corrosion = False
    has_leakage = False

    for damage in damage_data:
        if damage['type'] == '균열':
            # 기존 crack_width 필드 또는 새로운 구조 모두 지원
            crack_width = damage.get('crack_width', 0)
            crack_ratio = damage.get('crack_ratio', 0)

            if crack_width:
                max_crack_width = max(max_crack_width, crack_width)
            if crack_ratio:
                total_crack_ratio += crack_ratio

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
    """부재 유형별로 데이터 필터링 (손상내용명에 '받침' 또는 '전단키' 포함 시 교량받침으로 분류)"""
    # 먼저 손상내용명에 "받침" 또는 "전단키"가 포함된 데이터를 교량받침으로 분류
    bearing_damage_mask = (df['손상내용'].str.contains('받침', na=False) |
                          df['손상내용'].str.contains('전단키', na=False))

    if component_filter == '바닥판':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        return df[df['부재명'].str.contains('바닥판', na=False) & ~bearing_damage_mask]
    elif component_filter == '거더':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        return df[df['부재명'].str.contains('거더', na=False) & ~bearing_damage_mask]
    elif component_filter == '가로보':
        # 가로보, 세로보, 격벽 등 모든 관련 부재 포함 (손상내용에 "받침", "전단키" 포함 시 제외)
        basic_mask = (df['부재명'].str.contains('가로보', na=False) |
                     df['부재명'].str.contains('세로보', na=False) |
                     df['부재명'].str.contains('격벽', na=False))
        return df[basic_mask & ~bearing_damage_mask]
    elif component_filter == '교대':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        return df[df['부재명'].str.contains('교대', na=False) & ~bearing_damage_mask]
    elif component_filter == '교각':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        return df[df['부재명'].str.contains('교각', na=False) & ~bearing_damage_mask]
    elif component_filter == '교량받침':
        # 기존 교량받침 부재 + 손상내용에 "받침" 또는 "전단키"가 포함된 모든 부재
        basic_bearing_mask = (df['부재명'].str.contains('받침', na=False) |
                             df['부재명'].str.contains('교량받침', na=False) |
                             df['부재명'].str.contains('받침장치', na=False) |
                             df['부재명'].str.contains('탄성받침', na=False) |
                             df['부재명'].str.contains('고무받침', na=False) |
                             df['부재명'].str.contains('강재받침', na=False) |
                             df['부재명'].str.contains('베어링', na=False))
        print(df[basic_bearing_mask | bearing_damage_mask])
        #df.loc[bearing_damage_mask, '부재명'] = '받침장치'
        return df[basic_bearing_mask | bearing_damage_mask]
    elif component_filter == '기초':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        return df[df['부재명'].str.contains('기초', na=False) & ~bearing_damage_mask]
    elif component_filter == '신축이음':
        # 손상내용에 "받침", "전단키"가 포함된 경우 제외
        basic_mask = (df['부재명'].str.contains('신축이음', na=False) |
                     df['부재명'].str.contains('이음장치', na=False))
        return df[basic_mask & ~bearing_damage_mask]
    elif component_filter == '교면포장':
        # 교면포장, 포장 등 모든 관련 부재 포함 (손상내용에 "받침", "전단키" 포함 시 제외)
        basic_mask = (df['부재명'].str.contains('교면포장', na=False) |
                     df['부재명'].str.contains('포장', na=False))
        return df[basic_mask & ~bearing_damage_mask]
    elif component_filter == '배수시설':
        # 배수시설, 배수구 등 모든 관련 부재 포함 (손상내용에 "받침", "전단키" 포함 시 제외)
        basic_mask = (df['부재명'].str.contains('배수시설', na=False) |
                     df['부재명'].str.contains('배수구', na=False) |
                     df['부재명'].str.contains('배수관', na=False))
        return df[basic_mask & ~bearing_damage_mask]
    elif component_filter == '난간':
        # 난간, 연석, 난간연석, 방호울타리 등 모든 관련 부재 포함 (추가 부재명 포함)
        basic_mask = (df['부재명'].str.contains('난간', na=False) |
                     df['부재명'].str.contains('연석', na=False) |
                     df['부재명'].str.contains('방호울타리', na=False) |
                     df['부재명'].str.contains('방호벽', na=False) |
                     df['부재명'].str.contains('방음벽', na=False) |
                     df['부재명'].str.contains('방음판', na=False) |
                     df['부재명'].str.contains('방음', na=False) |
                     df['부재명'].str.contains('방호', na=False) |
                     df['부재명'].str.contains('중분대', na=False) |
                     df['부재명'].str.contains('중앙분리대', na=False) |
                     df['부재명'].str.contains('가드레일', na=False) |
                     df['부재명'].str.contains('낙석', na=False) |
                     df['부재명'].str.contains('차광', na=False) |
                     df['부재명'].str.contains('경계석', na=False) |
                     df['부재명'].str.contains('투석방지망', na=False))
        return df[basic_mask & ~bearing_damage_mask]
    else:
        return df  # 전체 데이터 반환


def filter_positions_by_component(df, component_name):
    """부재명에 따라 적절한 부재위치만 필터링"""
    # 바닥판, 거더, 가로보(세로보, 격벽 포함), 교면포장, 배수시설, 난간 및 연석은 s 경간만
    span_components = ['바닥판', '거더', '가로보', '세로보', '격벽', '교면포장', '포장', '배수시설', '배수구', '배수관', '난간', '연석', '방호울타리', '방호벽', '방음벽', '방음판', '중분대', '중앙분리대', '가드레일', '낙석', '차광', '경계석', '투석방지망']

    # 기초는 a와 p 경간 모두 어디에나 존재할 수 있음
    if '기초' in component_name:
        return df[df['부재위치'].str.match(r'^[ap]\d*', case=False, na=False)]

    # 교량받침은 a와 p 경간에 위치 (디예: a1, p1, p2, a2)
    if '받침' in component_name or '교량받침' in component_name or '받침장치' in component_name or '탄성받침' in component_name or '고무받침' in component_name or '강재받침' in component_name or '베어링' in component_name:
        return df[df['부재위치'].str.match(r'^[ap]\d*', case=False, na=False)]

    # 신축이음은 a, p, s 경간 모두에 위치할 수 있음
    if '신축이음' in component_name or '이음장치' in component_name:
        return df[df['부재위치'].str.match(r'^[aps]\d*', case=False, na=False)]

    # 해당 부재가 span_components에 포함되는지 확인
    is_span_component = any(comp in component_name for comp in span_components)

    if is_span_component:
        # s로 시작하는 부재위치만 필터링 (s1, s2, s3 등)
        return df[df['부재위치'].str.match(r'^s\d+', case=False, na=False)]
    else:
        # a, p로 시작하는 부재위치만 필터링 (a1, p1, p2, a2 등)
        return df[df['부재위치'].str.match(r'^[ap]\d*', case=False, na=False)]


def generate_condition_evaluation_pivot(df, component_filter=None):
    """상태평가용 피벗 테이블 생성 (개선된 1방향/2방향 균열 분류 적용)"""
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
                'max_crack_width_1d': 0,
                'max_crack_width_2d': None,  # 2방향 균열폭은 None으로 초기화
                'crack_ratio_1d': 0,
                'crack_ratio_2d': 0,
                'total_damage_count': 0,
                'condition_grade': 'A'
            }
        }

        all_damages = []

        for position in positions:
            # 새로운 개선된 방식: 1방향/2방향 균열 분류

            # 거더, 가로보, 신축이음, 교면포장, 배수시설, 난간의 경우 모든 관련 부재에서 데이터 추출
            if '거더' in component:
                # 거더 관련 모든 부재의 해당 위치 데이터
                all_girder_mask = df['부재명'].str.contains('거더', na=False) & (df['부재위치'] == position)
                pos_df = df[all_girder_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            elif '가로보' in component:
                # 가로보 관련 모든 부재의 해당 위치 데이터 (가로보, 세로보, 격벽 등)
                all_crossbeam_mask = (df['부재명'].str.contains('가로보', na=False) |
                                    df['부재명'].str.contains('세로보', na=False) |
                                    df['부재명'].str.contains('격벽', na=False)) & (df['부재위치'] == position)
                pos_df = df[all_crossbeam_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            elif '신축이음' in component:
                # 신축이음 관련 모든 부재의 해당 위치 데이터
                all_expansion_mask = (df['부재명'].str.contains('신축이음', na=False) |
                                    df['부재명'].str.contains('이음장치', na=False)) & (df['부재위치'] == position)
                pos_df = df[all_expansion_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            elif '교면포장' in component or '포장' in component:
                # 교면포장 관련 모든 부재의 해당 위치 데이터
                all_pavement_mask = (df['부재명'].str.contains('교면포장', na=False) |
                                   df['부재명'].str.contains('포장', na=False)) & (df['부재위치'] == position)
                pos_df = df[all_pavement_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            elif '배수시설' in component or '배수구' in component:
                # 배수시설 관련 모든 부재의 해당 위치 데이터
                all_drainage_mask = (df['부재명'].str.contains('배수시설', na=False) |
                                   df['부재명'].str.contains('배수구', na=False) |
                                   df['부재명'].str.contains('배수관', na=False)) & (df['부재위치'] == position)
                pos_df = df[all_drainage_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            elif any(keyword in component for keyword in ['난간', '연석', '방호울타리', '방호벽', '방음벽', '방음판', '방음', '방호', '중분대', '중앙분리대', '가드레일', '낙석', '차광', '경계석', '투석방지망']):

                # 난간연석 관련 모든 부재의 해당 위치 데이터 (추가 부재명 포함)
                all_railing_mask = (df['부재명'].str.contains('난간', na=False) |
                                  df['부재명'].str.contains('연석', na=False) |
                                  df['부재명'].str.contains('방호울타리', na=False) |
                                  df['부재명'].str.contains('방호벽', na=False) |
                                  df['부재명'].str.contains('방음벽', na=False) |
                                  df['부재명'].str.contains('방음판', na=False) |
                                  df['부재명'].str.contains('방음', na=False) |
                                  df['부재명'].str.contains('방호', na=False) |
                                  df['부재명'].str.contains('중분대', na=False) |
                                  df['부재명'].str.contains('중앙분리대', na=False) |
                                  df['부재명'].str.contains('가드레일', na=False) |
                                  df['부재명'].str.contains('낙석', na=False) |
                                  df['부재명'].str.contains('차광', na=False) |
                                  df['부재명'].str.contains('경계석', na=False) |
                                  df['부재명'].str.contains('투석방지망', na=False)) & (df['부재위치'] == position)
                pos_df = df[all_railing_mask]
                # 처리할 전체 데이터는 df를 사용
                full_df = df
            else:
                # 기존 로직: 해당 부재만
                pos_df = component_df[component_df['부재위치'] == position]
                # 처리할 전체 데이터는 component_df를 사용
                full_df = component_df

            # 1방향 균열 데이터 처리
            crack_width_1d = get_max_crack_width_for_span(full_df, component, position, '1방향')
            crack_ratio_1d = calculate_crack_ratio_for_span(full_df, component, position, '1방향')

            # 2방향 균열 데이터 처리
            crack_width_2d = get_max_crack_width_for_span(full_df, component, position, '2방향')
            crack_ratio_2d = calculate_crack_ratio_for_span(full_df, component, position, '2방향')

            position_data = {
                'damages': [],
                'crack_width_1d': crack_width_1d,
                'crack_width_2d': crack_width_2d,
                'crack_ratio_1d': crack_ratio_1d,
                'crack_ratio_2d': crack_ratio_2d,
                'damage_quantities': {},
                'condition_grade': 'A'
            }

            # 기존 손상 데이터 처리 (비균열 손상들)
            for _, row in pos_df.iterrows():
                damage_info = classify_damage_for_evaluation(row['손상내용'], component)  # 부재명 전달
                damage_info['quantity'] = row['손상물량']
                damage_info['original_desc'] = row['손상내용']

                # 균열이 아닌 손상만 추가 (균열은 별도 처리)
                if damage_info['type'] != '균열':
                    position_data['damages'].append(damage_info)
                    all_damages.append(damage_info)

                    # 손상 유형별 물량 합계
                    damage_type = damage_info['type']
                    if damage_type not in position_data['damage_quantities']:
                        position_data['damage_quantities'][damage_type] = 0
                    position_data['damage_quantities'][damage_type] += damage_info['quantity']

            # 균열 데이터를 손상 리스트에 추가 (상태평가용)
            if crack_width_1d > 0 or crack_ratio_1d > 0:
                crack_info_1d = {
                    'type': '균열',
                    'crack_width': crack_width_1d,
                    'crack_ratio': crack_ratio_1d,
                    'direction': '1방향',
                    'quantity': crack_ratio_1d,
                    'original_desc': f'1방향 균열 (최대폭: {crack_width_1d}mm, 균열율: {crack_ratio_1d:.2f})'
                }
                position_data['damages'].append(crack_info_1d)
                all_damages.append(crack_info_1d)

            if (crack_width_2d is not None and crack_width_2d > 0) or crack_ratio_2d > 0:
                crack_width_display = crack_width_2d if crack_width_2d is not None else 0
                crack_info_2d = {
                    'type': '균열',
                    'crack_width': crack_width_2d,  # None일 수 있음
                    'crack_ratio': crack_ratio_2d,
                    'direction': '2방향',
                    'quantity': crack_ratio_2d,
                    'original_desc': f'2방향 균열 (최대폭: {crack_width_display}mm, 균열율: {crack_ratio_2d:.2f})' if crack_width_2d is not None else f'2방향 균열 (균열율: {crack_ratio_2d:.2f})'
                }
                position_data['damages'].append(crack_info_2d)
                all_damages.append(crack_info_2d)

            # 위치별 상태등급 계산
            position_data['condition_grade'] = calculate_condition_grade(position_data['damages'])
            evaluation_data[component]['positions'][position] = position_data

            # 부재 전체 요약 업데이트
            evaluation_data[component]['summary']['max_crack_width_1d'] = max(
                evaluation_data[component]['summary']['max_crack_width_1d'],
                crack_width_1d
            )
            # 2방향 균열폭은 None일 수 있으므로 별도 처리
            if crack_width_2d is not None:
                current_2d = evaluation_data[component]['summary']['max_crack_width_2d']
                if current_2d is None:
                    evaluation_data[component]['summary']['max_crack_width_2d'] = crack_width_2d
                else:
                    evaluation_data[component]['summary']['max_crack_width_2d'] = max(current_2d, crack_width_2d)
            # crack_width_2d가 None이면 기존 값 유지 (None 또는 이전 값)
            evaluation_data[component]['summary']['crack_ratio_1d'] = max(
                evaluation_data[component]['summary']['crack_ratio_1d'],
                crack_ratio_1d
            )
            evaluation_data[component]['summary']['crack_ratio_2d'] = max(
                evaluation_data[component]['summary']['crack_ratio_2d'],
                crack_ratio_2d
            )

        # 부재 전체 요약 정보 계산
        evaluation_data[component]['summary']['condition_grade'] = calculate_condition_grade(all_damages)
        evaluation_data[component]['summary']['total_damage_count'] = len(all_damages)

    return evaluation_data


def generate_condition_evaluation_html(evaluation_data, component_filter=None):
    """상태평가 결과를 HTML 테이블로 생성 (개선된 1방향/2방향 균열 표시)"""
    html = '<div class="condition-evaluation-container">'

    # 부재별 필터 제목 추가
    if component_filter:
        html += f'<h3>{component_filter} 상태평가 결과</h3>'
    else:
        html += '<h3>전체 상태평가 결과</h3>'

    # 요약 테이블 (1방향/2방향 균열 분리 표시)
    html += '<h4>부재별 상태평가 요약</h4>'
    html += '<div class="table-container">'
    html += '<table class="table table-striped">'
    html += '<thead><tr>'
    html += '<th>부재명</th><th>1방향 최대균열폭(mm)</th><th>1방향 균열율</th><th>2방향 최대균열폭(mm)</th><th>2방향 균열율</th><th>손상 개소</th><th>상태등급</th>'
    html += '</tr></thead><tbody>'

    for component, data in evaluation_data.items():
        summary = data['summary']

        # None 값 처리
        max_crack_width_1d = summary.get("max_crack_width_1d", 0)
        if max_crack_width_1d is None:
            max_crack_width_1d = 0
        max_crack_width_1d_str = '-' if max_crack_width_1d == 0 else f'{max_crack_width_1d:.1f}'

        max_crack_width_2d = summary.get("max_crack_width_2d", 0)
        # 2방향 균열: None이면 '-', 0이면 '-', 값이 있으면 표시
        if max_crack_width_2d is None or max_crack_width_2d == 0:
            max_crack_width_2d_str = '-'
        else:
            max_crack_width_2d_str = f'{max_crack_width_2d:.1f}'

        crack_ratio_1d = summary.get("crack_ratio_1d", 0)
        if crack_ratio_1d is None:
            crack_ratio_1d = 0
        crack_ratio_1d_str = '-' if crack_ratio_1d == 0 else f'{crack_ratio_1d:.2f}'

        crack_ratio_2d = summary.get("crack_ratio_2d", 0)
        if crack_ratio_2d is None:
            crack_ratio_2d = 0
        crack_ratio_2d_str = '-' if crack_ratio_2d == 0 else f'{crack_ratio_2d:.2f}'

        total_damage_count = summary.get("total_damage_count", 0)
        if total_damage_count is None:
            total_damage_count = 0
        total_damage_count_str = '-' if total_damage_count == 0 else str(total_damage_count)

        condition_grade = summary.get("condition_grade", "A")
        if condition_grade is None:
            condition_grade = "A"

        html += f'<tr>'
        html += f'<td><strong>{component}</strong></td>'
        html += f'<td>{max_crack_width_1d_str}</td>'
        html += f'<td>{crack_ratio_1d_str}</td>'
        html += f'<td>{max_crack_width_2d_str}</td>'
        html += f'<td>{crack_ratio_2d_str}</td>'
        html += f'<td>{total_damage_count_str}</td>'
        html += f'<td>{condition_grade.lower()}</td>'
        html += f'</tr>'

    html += '</tbody></table></div>'

    # 상세 테이블 (부재별)
    for component, data in evaluation_data.items():
        html += f'<h5 class="mt-4">{component} 상세 평가</h5>'
        html += '<div class="table-container">'
        html += '<table class="table table-sm">'
        html += '<thead><tr>'
        html += '<th>부재위치</th><th>손상내용</th><th>균열폭(mm)</th><th>균열율/손상물량</th><th>상태등급</th>'
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
                # None 또는 0인 경우 '-' 처리
                if crack_width is None or crack_width == 0:
                    crack_width_str = '-'
                else:
                    crack_width_str = f"{crack_width:.1f}"

                # 손상내용과 손상물량 None 값 처리
                original_desc = damage.get("original_desc", "")
                if original_desc is None:
                    original_desc = ""

                # 균열인 경우 균열율 표시, 아닌 경우 손상물량 표시
                if damage['type'] == '균열':
                    crack_ratio = damage.get('crack_ratio', 0)
                    quantity_str = f'{crack_ratio:.2f}' if crack_ratio > 0 else '-'
                else:
                    quantity = damage.get("quantity", 0)
                    if quantity is None:
                        quantity = 0
                    quantity_str = '-' if quantity == 0 else f'{quantity:.2f}'

                html += f'<td>{original_desc}</td>'
                html += f'<td>{crack_width_str}</td>'
                html += f'<td>{quantity_str}</td>'

                if i == 0:  # 첫 번째 행에만 등급 표시
                    condition_grade = pos_data.get('condition_grade', 'A')
                    if condition_grade is None:
                        condition_grade = 'A'
                    html += f'<td rowspan="{rowspan}">{condition_grade.lower()}</td>'

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
    # 문자열 컬럼 trim 처리
    df = trim_dataframe_str_columns(df)
    # ...기존 코드...

    # 부재별 평가 데이터 생성
    evaluation_data = generate_condition_evaluation_pivot(df, component_type)

    # HTML 생성
    html = generate_condition_evaluation_html(evaluation_data, component_type)

    return html


def generate_all_component_evaluations(df):
    # 문자열 컬럼 trim 처리
    df = trim_dataframe_str_columns(df)
    # ...기존 코드...
    """모든 부재에 대한 상태평가표 HTML 생성"""
    component_types = ['바닥판', '거더', '가로보', '교대', '교각', '교량받침', '기초', '신축이음', '교면포장', '배수시설', '난간']

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
