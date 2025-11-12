# 기존 damage_ai_generator.py는 rag_damage_system.py로 대체됨
# 하위 호환성을 위해 get_damage_solution 함수만 유지

from utils.rag_damage_system import get_damage_solution_enhanced

def get_damage_solution(damage_type: str, component_name: str, repair_method: str) -> str:
    """
    손상 유형에 따른 대책방안을 반환하는 통합 함수 (하위 호환성 유지)
    
    Args:
        damage_type: 정규화된 손상 유형
        component_name: 부재명
        repair_method: 보수방안
        
    Returns:
        포맷팅된 손상 대책방안 문장
    """
    return get_damage_solution_enhanced(damage_type, component_name, repair_method)
