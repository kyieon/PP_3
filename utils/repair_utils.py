"""
보수 데이터 처리를 위한 유틸리티 함수들
"""
from typing import List, Dict, Any
import pandas as pd
from utils.common import clean_dataframe_data

def generate_repair_tables(damage_data: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    """
    손상 데이터로부터 보수 테이블을 생성합니다.
    
    Args:
        damage_data (List[Dict[str, Any]]): 손상 데이터 리스트
        
    Returns:
        Dict[str, pd.DataFrame]: 보수 테이블들을 담은 딕셔너리
    """
    # 손상 데이터를 DataFrame으로 변환
    df = pd.DataFrame(damage_data)
    
    # DataFrame 데이터 정리 및 trim 처리
    df = clean_dataframe_data(df)
    
    # 보수 방법별 그룹화
    repair_groups = df.groupby('repair_method')
    
    # 결과를 저장할 딕셔너리
    repair_tables = {}
    
    # 각 보수 방법별로 테이블 생성
    for method, group in repair_groups:
        # 필요한 컬럼만 선택
        table = group[['location', 'damage_type', 'severity', 'repair_method', 'estimated_cost']]
        
        # 정렬
        table = table.sort_values(['location', 'damage_type'])
        
        # 딕셔너리에 저장
        repair_tables[method] = table
    
    return repair_tables

def calculate_repair_costs(repair_tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    보수 테이블로부터 각 보수 방법별 예상 비용을 계산합니다.
    
    Args:
        repair_tables (Dict[str, pd.DataFrame]): 보수 테이블들
        
    Returns:
        Dict[str, float]: 보수 방법별 총 예상 비용
    """
    costs = {}
    
    for method, table in repair_tables.items():
        total_cost = table['estimated_cost'].sum()
        costs[method] = total_cost
    
    return costs

def generate_repair_schedule(repair_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    보수 일정을 생성합니다.
    
    Args:
        repair_tables (Dict[str, pd.DataFrame]): 보수 테이블들
        
    Returns:
        pd.DataFrame: 보수 일정 테이블
    """
    schedule_data = []
    
    for method, table in repair_tables.items():
        # 각 보수 작업의 우선순위 결정
        priority = 1
        for _, row in table.iterrows():
            schedule_data.append({
                'location': row['location'],
                'damage_type': row['damage_type'],
                'repair_method': method,
                'priority': priority,
                'estimated_duration': calculate_duration(row['damage_type'], method),
                'estimated_cost': row['estimated_cost']
            })
            priority += 1
    
    return pd.DataFrame(schedule_data)

def calculate_duration(damage_type: str, repair_method: str) -> int:
    """
    손상 유형과 보수 방법에 따른 예상 소요 시간을 계산합니다.
    
    Args:
        damage_type (str): 손상 유형
        repair_method (str): 보수 방법
        
    Returns:
        int: 예상 소요 시간(일)
    """
    # 기본 소요 시간 설정
    base_durations = {
        '주입공법': 2,
        '표면처리공법': 1,
        '방수공법': 3,
        '단면보수': 4,
        '단면복구': 5,
        '방청처리': 2,
        '교체': 7,
        '재설치': 3,
        '기초보강': 10,
        '표면보수': 1
    }
    
    # 손상 유형에 따른 추가 시간
    additional_durations = {
        '균열': 1,
        '누수': 2,
        '백태': 1,
        '박리': 2,
        '철근노출': 3,
        '파손': 4,
        '부식': 2,
        '단차': 1,
        '침하': 5,
        '들뜸': 2,
        '마모': 1,
        '탈락': 2
    }
    
    # 총 소요 시간 계산
    total_duration = base_durations.get(repair_method, 3) + additional_durations.get(damage_type, 1)
    
    return total_duration 