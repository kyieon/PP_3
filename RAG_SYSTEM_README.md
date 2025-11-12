# RAG 기반 손상별 원인 및 대책방안 생성 시스템

## 개요
외관조사 보고서의 부재별 집계표에서 손상별 원인 및 대책방안을 동적으로 생성하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 주요 기능

### 1. 상황별 처리 로직
- **기존 손상유형**: `damage_solutions.py`에 있는 손상유형은 기존 문장 그대로 사용
- **유사한 손상유형** (80% 이상 유사): RAG로 유사 손상의 기존 문장들을 찾아서 참고하여 GPT로 생성
- **완전히 새로운 손상유형**: GPT의 일반 지식 + 기존 문장 템플릿 형태로 생성

### 2. RAG 시스템 특징
- **키워드 기반 유사도 검색**: 손상 관련 키워드(균열, 파손, 박리, 부식 등)를 추출하여 유사도 계산
- **부분 문자열 매칭**: 한쪽이 다른 쪽에 포함되는 경우 높은 유사도 부여
- **참고 문장 추출**: 유사한 손상 유형의 기존 문장들을 참고하여 일관된 문체 유지

### 3. GPT 생성 최적화
- **프롬프트 엔지니어링**: 기존 문장 패턴을 학습하여 일관된 문체 생성
- **플레이스홀더 치환**: `{name}`, `{보수방안}` 자동 치환
- **Fallback 메커니즘**: AI 생성 실패 시 기본 문장 제공

## 파일 구조

```
utils/
├── rag_damage_system.py          # RAG 시스템 메인 모듈
├── damage_ai_generator.py        # 하위 호환성을 위한 래퍼
└── static/data/damage_solutions.py  # 기존 손상 유형 데이터
```

## 사용법

### 1. 환경 변수 설정
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. 기본 사용법
```python
from utils.rag_damage_system import get_damage_solution_enhanced

# 손상 대책방안 생성
solution = get_damage_solution_enhanced(
    damage_type="균열손상",      # 손상 유형
    component_name="바닥판",      # 부재명
    repair_method="표면처리"      # 보수방안
)
print(solution)
```

### 3. 기존 코드와의 호환성
기존 `get_damage_solution` 함수는 그대로 사용 가능하며, 자동으로 새로운 RAG 시스템을 사용합니다.

```python
from utils.damage_ai_generator import get_damage_solution

# 기존 방식과 동일하게 사용
solution = get_damage_solution("균열", "바닥판", "표면처리")
```

## 테스트

### 테스트 실행
```bash
python3 test_rag_system.py
```

### 테스트 케이스
1. **기존 손상유형**: `damage_solutions.py`에 있는 손상유형
2. **유사한 손상유형**: 80% 이상 유사한 손상유형 (RAG 활용)
3. **완전히 새로운 손상유형**: GPT 일반 지식 활용

## 성능 최적화

### 1. 유사도 계산 개선
- 키워드 기반 유사도 검색
- 부분 문자열 매칭
- 가중 평균을 통한 최종 유사도 계산

### 2. API 호출 최적화
- gpt-4o-mini 모델 사용으로 비용 절약
- 참고 문장 제한 (최대 5개)
- Fallback 메커니즘으로 안정성 보장

### 3. 로깅 시스템
- 상세한 로그를 통한 디버깅 지원
- 각 단계별 처리 과정 추적

## 주의사항

1. **API 키 보안**: OpenAI API 키를 안전하게 관리하세요.
2. **비용 관리**: gpt-4o-mini 모델을 사용하지만, 대량 요청 시 비용이 발생할 수 있습니다.
3. **네트워크 연결**: GPT API 호출을 위해 인터넷 연결이 필요합니다.

## 업데이트 내역

### v1.0 (2025-01-27)
- RAG 시스템 초기 구현
- 상황별 처리 로직 구현
- 키워드 기반 유사도 검색 개선
- GPT 프롬프트 엔지니어링 최적화
- 하위 호환성 보장
