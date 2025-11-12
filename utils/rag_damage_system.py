import os
import openai
import re
from typing import List, Dict, Tuple, Optional
import logging
from difflib import SequenceMatcher
from static.data.damage_solutions import damage_solutions
from utils.damage_cache import damage_cache

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGDamageSystem:
    """RAG 기반 손상 유형 분석 및 대책방안 생성 시스템"""
    
    def __init__(self):
        self.damage_solutions = damage_solutions
        self.similarity_threshold = 0.8  # 80% 이상 유사도
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도를 계산"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_similar_damages(self, target_damage: str, threshold: float = None) -> List[Tuple[str, float]]:
        """유사한 손상 유형을 찾아서 반환"""
        if threshold is None:
            threshold = self.similarity_threshold
            
        similar_damages = []
        
        # 키워드 기반 유사도 검색 개선
        target_keywords = self.extract_keywords(target_damage)
        
        for damage_type in self.damage_solutions.keys():
            # 1. 기본 문자열 유사도
            basic_similarity = self.calculate_similarity(target_damage, damage_type)
            
            # 2. 키워드 기반 유사도
            damage_keywords = self.extract_keywords(damage_type)
            keyword_similarity = self.calculate_keyword_similarity(target_keywords, damage_keywords)
            
            # 3. 부분 문자열 매칭
            partial_similarity = self.calculate_partial_similarity(target_damage, damage_type)
            
            # 최종 유사도는 가중 평균으로 계산
            final_similarity = max(basic_similarity, keyword_similarity * 1.2, partial_similarity * 1.1)
            
            if final_similarity >= threshold:
                similar_damages.append((damage_type, final_similarity))
        
        # 유사도 순으로 정렬
        similar_damages.sort(key=lambda x: x[1], reverse=True)
        return similar_damages
    
    def extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 손상 관련 주요 키워드들
        keywords = []
        text_lower = text.lower()
        
        # 주요 손상 키워드들
        damage_keywords = ['균열', '파손', '박리', '박락', '부식', '백태', '누수', '들뜸', '층분리', '재료분리']
        for keyword in damage_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # 부재 관련 키워드들
        component_keywords = ['콘크리트', '몰탈', '받침', '보수부', '도장']
        for keyword in component_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """키워드 기반 유사도 계산"""
        if not keywords1 or not keywords2:
            return 0.0
        
        # 교집합과 합집합 계산
        intersection = set(keywords1) & set(keywords2)
        union = set(keywords1) | set(keywords2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def calculate_partial_similarity(self, text1: str, text2: str) -> float:
        """부분 문자열 매칭 기반 유사도 계산"""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # 한쪽이 다른 쪽에 포함되는 경우
        if text1_lower in text2_lower or text2_lower in text1_lower:
            return 0.9
        
        # 공통 부분 문자열의 길이 기반 유사도
        common_length = 0
        for i in range(min(len(text1), len(text2))):
            if text1_lower[i] == text2_lower[i]:
                common_length += 1
            else:
                break
        
        if common_length > 0:
            return common_length / max(len(text1), len(text2))
        
        return 0.0
    
    def extract_reference_sentences(self, similar_damages: List[Tuple[str, float]], max_sentences: int = 5) -> List[str]:
        """유사한 손상 유형의 참고 문장들을 추출"""
        reference_sentences = []
        
        for damage_type, similarity in similar_damages:
            if damage_type in self.damage_solutions:
                sentences = self.damage_solutions[damage_type]
                # 각 손상 유형에서 최대 2개 문장씩 가져오기
                reference_sentences.extend(sentences[:2])
                
                if len(reference_sentences) >= max_sentences:
                    break
        
        return reference_sentences[:max_sentences]
    
    def generate_with_rag(self, damage_type: str, component_name: str, repair_method: str) -> str:
        """RAG를 활용한 손상 대책방안 생성"""
        try:
            # 1. 유사한 손상 유형 찾기
            similar_damages = self.find_similar_damages(damage_type)
            
            if not similar_damages:
                logger.info(f"'{damage_type}'에 대한 유사한 손상 유형을 찾을 수 없습니다.")
                return self.generate_with_gpt(damage_type, component_name, repair_method, [])
            
            # 2. 참고 문장들 추출
            reference_sentences = self.extract_reference_sentences(similar_damages)
            
            logger.info(f"'{damage_type}'에 대해 {len(similar_damages)}개의 유사한 손상 유형을 찾았습니다.")
            logger.info(f"참고 문장 {len(reference_sentences)}개를 추출했습니다.")
            
            # 3. GPT로 생성 (참고 문장 포함)
            generated_text = self.generate_with_gpt(damage_type, component_name, repair_method, reference_sentences)
            # 한국어 조사 처리
            repair_method_with_particle = self._add_korean_particle(repair_method)
            return generated_text.replace('{name}', component_name).replace('{보수방안}', repair_method_with_particle)
            
        except Exception as e:
            logger.error(f"RAG 기반 생성 중 오류 발생: {str(e)}")
            return self.generate_with_gpt(damage_type, component_name, repair_method, [])
    
    def generate_with_gpt(self, damage_type: str, component_name: str, repair_method: str, reference_sentences: List[str] = None) -> str:
        """GPT를 활용한 손상 대책방안 생성"""
        try:
            # OpenAI API 키 설정
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OpenAI API 키가 설정되지 않았습니다.")
                return self.get_fallback_solution(damage_type, component_name, repair_method)
            
            # OpenAI 클라이언트 생성
            client = openai.OpenAI(api_key=api_key)
            
            # 참고 문장이 있는 경우와 없는 경우를 구분하여 프롬프트 생성
            if reference_sentences:
                # RAG 기반 프롬프트 (유사한 손상 유형의 문장들을 참고)
                reference_text = "\n".join(reference_sentences[:3])  # 최대 3개 문장만 사용
                
                prompt = f"""당신은 교량 외관조사 전문가입니다. 아래 조건에 맞춰 손상별 원인 및 대책방안을 작성해주세요.

**조건:**
1. 다음 유사한 손상 유형의 기존 문장들을 참고하여 비슷한 패턴과 전문용어를 활용하세요:
{reference_text}

2. 작성할 내용:
   - 손상 유형: {damage_type}
   - 부재명: {component_name}
   - 보수방안: {repair_method}

3. 문장 구조 규칙:
   - "■ {{name}}에 발생한/조사된/확인된 [손상유형]"으로 시작
   - 원인 분석 (장기공용 노후화, 우수유입, 외부충격, 시공미흡 등)
   - "~으로 판단되며" 또는 "~으로 추정되며"로 원인 설명 마무리
   - 보수방안이 "주의관찰"인 경우: "비교적 경미하므로 주의관찰을 통한 손상확대시 보수함이 유지관리상 유리할 것으로 판단된다"
   - 다른 보수방안인 경우: "구조물의 내구성 확보를 위해" 또는 "교량의 내구성 확보를 위해" + "{{보수방안}}을 통한 보수조치가 요구된다" 또는 "{{보수방안}}이 필요할 것으로 판단된다"
   - 주의: 보수방안에 따라 조사를 올바르게 사용하세요 (예: "주의관찰이", "표면처리가", "주입보수가")

4. {{name}}과 {{보수방안}} 플레이스홀더는 반드시 그대로 유지해주세요.

5. 참고 문장들의 전문용어와 패턴을 활용하되, {damage_type}에 맞게 내용을 조정해주세요.

**응답 형식:** 한 개의 완성된 문장만 제공해주세요."""
            else:
                # 일반 GPT 프롬프트 (완전히 새로운 손상 유형)
                prompt = f"""당신은 교량 외관조사 전문가입니다. 아래 조건에 맞춰 손상별 원인 및 대책방안을 작성해주세요.

**조건:**
1. 작성할 내용:
   - 손상 유형: {damage_type}
   - 부재명: {component_name}
   - 보수방안: {repair_method}

2. 문장 구조 규칙:
   - "■ {{name}}에 발생한/조사된/확인된 [손상유형]"으로 시작
   - 원인 분석 (장기공용 노후화, 우수유입, 외부충격, 시공미흡 등)
   - "~으로 판단되며" 또는 "~으로 추정되며"로 원인 설명 마무리
   - 보수방안이 "주의관찰"인 경우: "비교적 경미하므로 주의관찰을 통한 손상확대시 보수함이 유지관리상 유리할 것으로 판단된다"
   - 다른 보수방안인 경우: "구조물의 내구성 확보를 위해" 또는 "교량의 내구성 확보를 위해" + "{{보수방안}}을 통한 보수조치가 요구된다" 또는 "{{보수방안}}이 필요할 것으로 판단된다"
   - 주의: 보수방안에 따라 조사를 올바르게 사용하세요 (예: "주의관찰이", "표면처리가", "주입보수가")

3. {{name}}과 {{보수방안}} 플레이스홀더는 반드시 그대로 유지해주세요.

4. 전문적이고 공식적인 어조를 유지하되, 교량 외관조사 보고서에 적합한 문체로 작성해주세요.

**응답 형식:** 한 개의 완성된 문장만 제공해주세요."""

            # ChatGPT API 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 교량 외관조사 전문가입니다. 정확하고 전문적인 손상 분석 문장을 작성합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # 응답에서 텍스트 추출
            generated_text = response.choices[0].message.content.strip()
            
            # 생성된 텍스트가 예상 형식인지 간단한 검증
            if "■" in generated_text and "{name}" in generated_text and "{보수방안}" in generated_text:
                logger.info(f"GPT로 손상 대책방안 생성 완료: {damage_type}")
                return generated_text
            elif "■" in generated_text:
                # 플레이스홀더가 없어도 기본 형식은 맞는 경우
                logger.info(f"GPT로 손상 대책방안 생성 완료 (플레이스홀더 없음): {damage_type}")
                return generated_text
            else:
                logger.warning(f"생성된 텍스트가 예상 형식과 다릅니다: {generated_text}")
                return generated_text  # 형식이 다르더라도 일단 반환
                
        except Exception as e:
            logger.error(f"GPT 생성 중 오류 발생: {str(e)}")
            return self.get_fallback_solution(damage_type, component_name, repair_method)
    
    def get_fallback_solution(self, damage_type: str, component_name: str, repair_method: str) -> str:
        """AI 생성 실패시 기본 문장 제공"""
        import random
        
        # 한국어 어미 처리
        repair_method_with_particle = self._add_korean_particle(repair_method)
        
        # 주의관찰인 경우와 다른 보수방안인 경우를 구분
        if repair_method == "주의관찰":
            # 주의관찰 전용 문장 패턴
            fallback_templates = [
                f"■ {component_name}에 발생한 {damage_type} 손상은 장기공용 노후화, 시공미흡 및 외부환경 요인에 의한 것으로 판단되며, 비교적 경미하므로 주의관찰을 통한 손상확대시 보수함이 유지관리상 유리할 것으로 판단된다.",
                f"■ {component_name}에서 관찰된 {damage_type} 손상은 시공미흡, 반복하중 및 장기공용 노후화 등 복합적 요인에 의해 발생한 것으로 추정되며, 비교적 경미하므로 주의관찰을 통한 손상확대시 보수함이 유지관리상 유리할 것으로 판단된다.",
                f"■ {component_name}에 확인된 {damage_type} 손상은 환경적 요인 및 장기공용 노후화, 시공미흡 등에 기인한 손상으로 판단되며, 비교적 경미하므로 주의관찰을 통한 손상확대시 보수함이 유지관리상 유리할 것으로 사료된다."
            ]
        else:
            # 일반 보수방안용 문장 패턴
            fallback_templates = [
                f"■ {component_name}에 발생한 {damage_type} 손상은 장기공용 노후화, 시공미흡 및 외부환경 요인에 의한 것으로 판단되며, 구조물의 내구성 확보를 위해 {repair_method_with_particle} 필요할 것으로 판단된다.",
                f"■ {component_name}에서 관찰된 {damage_type} 손상은 시공미흡, 반복하중 및 장기공용 노후화 등 복합적 요인에 의해 발생한 것으로 추정되며, 교량의 안전성과 내구성 확보를 위해 {repair_method_with_particle} 요구된다.",
                f"■ {component_name}에 확인된 {damage_type} 손상은 환경적 요인 및 장기공용 노후화, 시공미흡 등에 기인한 손상으로 판단되며, 구조물의 장기적인 성능 유지를 위해 {repair_method_with_particle} 필요할 것으로 사료된다."
            ]
        
        return random.choice(fallback_templates)
    
    def _add_korean_particle(self, repair_method: str) -> str:
        """한국어 조사 처리"""
        # 받침이 있는지 확인하는 함수
        def has_final_consonant(word):
            if not word:
                return False
            last_char = word[-1]
            # 한글 유니코드 범위 확인
            if '가' <= last_char <= '힣':
                # 받침이 있는지 확인 (유니코드 계산)
                return (ord(last_char) - ord('가')) % 28 != 0
            return False
        
        if not repair_method:
            return repair_method
            
        # 특별한 경우들 처리
        special_cases = {
            '주의관찰': '주의관찰이',
            '상태점검 후 결정': '상태점검 후 결정이',
            '청소': '청소가',
            '교체': '교체가',
            '재설치': '재설치가',
            '보강': '보강이',
            '표면보수': '표면보수가',
            '단면보수': '단면보수가',
            '방청처리': '방청처리가',
            '도장보수': '도장보수가',
            '배수관 재설치': '배수관 재설치가'
        }
        
        if repair_method in special_cases:
            return special_cases[repair_method]
        
        # 일반적인 경우: 받침이 있으면 '이', 없으면 '가'
        if has_final_consonant(repair_method):
            return f"{repair_method}이"
        else:
            return f"{repair_method}가"


def get_damage_solution_enhanced(damage_type: str, component_name: str, repair_method: str) -> str:
    """
    상황별 처리 로직을 포함한 향상된 손상 대책방안 생성 함수 (캐싱 적용)
    
    Args:
        damage_type: 손상 유형 (손상내용)
        component_name: 부재명
        repair_method: 보수방안
        
    Returns:
        포맷팅된 손상 대책방안 문장
    """
    try:
        # 1. 캐시에서 먼저 확인
        cached_solution = damage_cache.get(damage_type, component_name, repair_method)
        if cached_solution:
            logger.info(f"캐시에서 '{damage_type}' 대책방안 조회")
            return cached_solution
        
        rag_system = RAGDamageSystem()
        
        # 2. 기존 손상유형 (damage_solutions.py에 있음)
        if damage_type in rag_system.damage_solutions and len(rag_system.damage_solutions[damage_type]) > 0:
            logger.info(f"기존 손상 유형 '{damage_type}' 사용")
            import random
            selected_solution = random.choice(rag_system.damage_solutions[damage_type])
            # 한국어 조사 처리
            repair_method_with_particle = rag_system._add_korean_particle(repair_method)
            formatted_solution = selected_solution.replace('{name}', component_name).replace('{보수방안}', repair_method_with_particle)
            # 캐시에 저장
            damage_cache.set(damage_type, component_name, repair_method, formatted_solution)
            return formatted_solution
        
        # 3. 유사한 손상유형 (80% 이상 유사) - RAG 활용
        similar_damages = rag_system.find_similar_damages(damage_type, threshold=0.8)
        if similar_damages:
            logger.info(f"유사한 손상 유형 발견: {similar_damages[0][0]} (유사도: {similar_damages[0][1]:.2f})")
            generated_text = rag_system.generate_with_rag(damage_type, component_name, repair_method)
            # 캐시에 저장
            damage_cache.set(damage_type, component_name, repair_method, generated_text)
            return generated_text
        
        # 4. 완전히 새로운 손상유형 - GPT 일반 지식 활용
        logger.info(f"완전히 새로운 손상 유형 '{damage_type}' - GPT 일반 지식 활용")
        generated_text = rag_system.generate_with_gpt(damage_type, component_name, repair_method, [])
        # 한국어 조사 처리
        repair_method_with_particle = rag_system._add_korean_particle(repair_method)
        final_solution = generated_text.replace('{name}', component_name).replace('{보수방안}', repair_method_with_particle)
        # 캐시에 저장
        damage_cache.set(damage_type, component_name, repair_method, final_solution)
        return final_solution
        
    except Exception as e:
        logger.error(f"손상 대책방안 생성 중 오류 발생: {str(e)}")
        # 한국어 어미 처리
        rag_system = RAGDamageSystem()
        repair_method_with_particle = rag_system._add_korean_particle(repair_method)
        fallback_solution = f"■ {component_name}에 발생한 {damage_type} 손상에 대해 {repair_method_with_particle} 통한 보수조치가 요구된다."
        # Fallback 솔루션도 캐시에 저장
        damage_cache.set(damage_type, component_name, repair_method, fallback_solution)
        return fallback_solution
