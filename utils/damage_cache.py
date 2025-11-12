import json
import os
from typing import Dict, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

class DamageSolutionCache:
    """손상 대책방안 캐시 시스템"""
    
    def __init__(self, cache_file: str = "damage_solutions_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """캐시 파일에서 데이터 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"캐시 파일 로드 실패: {e}")
        return {}
    
    def save_cache(self):
        """캐시 데이터를 파일에 저장"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"캐시 파일 저장 실패: {e}")
    
    def get_cache_key(self, damage_type: str, component_name: str, repair_method: str) -> str:
        """캐시 키 생성"""
        key_string = f"{damage_type}|{component_name}|{repair_method}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, damage_type: str, component_name: str, repair_method: str) -> Optional[str]:
        """캐시에서 대책방안 조회"""
        cache_key = self.get_cache_key(damage_type, component_name, repair_method)
        return self.cache.get(cache_key)
    
    def set(self, damage_type: str, component_name: str, repair_method: str, solution: str):
        """캐시에 대책방안 저장"""
        cache_key = self.get_cache_key(damage_type, component_name, repair_method)
        self.cache[cache_key] = solution
        self.save_cache()
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache = {}
        self.save_cache()
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 정보"""
        return {
            "total_entries": len(self.cache),
            "cache_file": self.cache_file,
            "file_exists": os.path.exists(self.cache_file)
        }

# 전역 캐시 인스턴스
damage_cache = DamageSolutionCache()
