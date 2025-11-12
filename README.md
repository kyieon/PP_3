# InfraSmart - 교량 외관조사 관리 시스템

## 📋 프로젝트 개요

InfraSmart는 교량 외관조사 데이터를 체계적으로 관리하고 분석하여 보고서를 자동 생성하는 웹 기반 시스템입니다. Excel 파일을 업로드하면 부재별 손상 현황을 분석하고 보수 계획 및 공사비를 자동 산출합니다.

## ✨ 주요 기능

### 🔐 사용자 관리

- 로그인/로그아웃 기능
- 사용자별 데이터 격리
- 세션 기반 인증

### 📊 파일 관리

- Excel 파일 업로드 및 검증
- 파일 목록 관리
- 파일별 보기/삭제 기능

### 🏗️ 교량 정보 관리

- 교량 기본 정보 입력 (교량명, 연장, 폭 등)
- 6가지 구조형식 지원
- 경간 수 및 신축이음 위치 관리

### 📋 보고서 생성

- **부재별 집계표**: 부재별 손상 현황 상세 분석
- **외관조사 총괄표**: 전체 손상 현황 테이블
- **보수물량표**: 보수 필요 물량 계산
- **개략공사비표**: 공사비 추정 및 우선순위 분류

### 🔄 고급 기능

- **경간위치 변경**: 경간별 데이터 표시 전환
- **균열 세분화**: 균열 유형별 상세 분석
- **실시간 업데이트**: Ajax 기반 동적 데이터 업데이트
- **Word 다운로드**: 보고서 문서 다운로드

## 🛠️ 기술 스택

### Backend

- **Python 3.x**
- **Flask** - 웹 애플리케이션 프레임워크
- **PostgreSQL** - 관계형 데이터베이스
- **psycopg2** - PostgreSQL 어댑터
- **pandas** - 데이터 처리
- **python-docx** - Word 문서 생성

### Frontend

- **HTML5/CSS3**
- **JavaScript (Vanilla)**
- **Bootstrap** - UI 프레임워크
- **Ajax** - 비동기 통신

### 보안

- **JWT** - 토큰 기반 인증
- **werkzeug** - 비밀번호 해싱
- **Flask-CORS** - CORS 처리

## 📂 프로젝트 구조

```
infrasmart/
├── app.py                 # 메인 애플리케이션
├── config.py              # 설정 파일
├── requirements.txt       # 종속성 목록
├── api/                   # API 엔드포인트
│   ├── auth.py           # 인증 관련
│   ├── file.py           # 파일 처리
│   ├── evaluation.py     # 평가 관련
│   └── span_damage.py    # 손상 데이터 처리
├── static/               # 정적 파일
│   ├── css/             # 스타일시트
│   ├── js/              # JavaScript
│   └── data/            # 데이터 파일
├── templates/            # HTML 템플릿
├── utils/                # 유틸리티 함수
│   ├── common.py        # 공통 함수
│   ├── evaluation.py    # 평가 로직
│   └── file_validation.py # 파일 검증
└── docs/                 # 문서
    ├── project_plan.md
    ├── system_design.md
    ├── feature_specification.md
    └── code_cleanup_plan.md
```

## 🚀 설치 및 실행

### 1. 요구사항

- Python 3.7+
- PostgreSQL 10+
- Git

### 2. 설치

```bash
# 프로젝트 클론
git clone https://github.com/kkim1983/infrasmart.git
cd infrasmart/infrasmart

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE bridge_db;

# 사용자 생성 (옵션)
CREATE USER bridge_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bridge_db TO bridge_user;
```

### 4. 환경변수 설정

```bash
# .env 파일 생성
SECRET_KEY=your-secret-key-here
DB_NAME=bridge_db
DB_USER=postgres
DB_PASSWORD=your-password-here
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET=your-jwt-secret-here
JWT_ALGORITHM=HS256
```

### 5. 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5001` 접속

## 📊 지원 데이터

### 교량 부재 (10개)

- 바닥판하면, 거더(외부/내부), 가로보
- 교대, 교량받침, 신축이음
- 교면포장, 방호벽, 점검시설, 점검통로

### 손상 유형 (50+개)

- 균열, 부식, 누수, 백태, 박리, 박락
- 층분리, 재료분리, 파손, 철근노출
- 도장탈락, 볼트부식, 토사퇴적 등

### 구조형식 (6개)

- PSC 박스거더교
- PSC 빔교
- 강박스거더교
- 강플레이트거더교
- RC 슬래브교
- 라멘교

### 보수 방안 (7개)

- 주의관찰, 청소, 표면처리
- 충진보수, 도장보수, 단면보수
- 단면보수(방청)

## 🔧 주요 기능 설명

### 파일 업로드 프로세스

1. 교량 정보 입력 (교량명, 구조형식, 경간수 등)
2. Excel 파일 선택 및 업로드
3. 파일 구조 검증
4. 데이터 파싱 및 저장
5. 보고서 생성

### 보고서 생성 로직

1. 업로드된 데이터 조회
2. 부재별, 손상별 집계
3. 손상 등급 평가 (a~e 등급)
4. 보수 물량 계산 (할증율 20% 적용)
5. 공사비 산출 (우선순위별 분류)
6. HTML 테이블 생성 및 표시

### 공사비 계산 규칙

- **할증율**: 20% 기본 적용
- **우선순위**:
  - 1순위 (긴급): 철근노출 등 구조적 위험
  - 2순위 (일반): 일반적인 보수 필요 항목
  - 3순위 (예방): 예방적 보수 항목
- **제경비**: 순공사비의 50% 적용

## 📚 문서

### 설계 문서

- **프로젝트 계획서** (`docs/project_plan.md`)
- **시스템 설계서** (`docs/system_design.md`)
- **기능 명세서** (`docs/feature_specification.md`)
- **코드 정리 계획서** (`docs/code_cleanup_plan.md`)

### API 문서

- 로그인: `POST /api/login`
- 파일 목록: `GET /api/files`
- 파일 업로드: `POST /upload`
- 보고서 데이터: `GET /api/bridge_data`

## 🧪 테스트

### 테스트 계정

- 아이디: `admin`
- 비밀번호: `admin123`

### 테스트 데이터

프로젝트에 포함된 샘플 Excel 파일을 이용하여 테스트 가능

## 🔧 개발 환경

### 권장 개발 도구

- **IDE**: PyCharm, VS Code
- **데이터베이스**: pgAdmin, DBeaver
- **HTTP 클라이언트**: Postman, HTTPie
- **버전 관리**: Git

### 코드 스타일

- **Python**: PEP 8 준수
- **JavaScript**: ES6+ 문법 사용
- **HTML/CSS**: 시맨틱 마크업

## 🐛 알려진 이슈

### 현재 제한사항

1. Excel 파일만 지원 (CSV 미지원)
2. 대용량 파일 처리 시 성능 저하
3. 모바일 환경 최적화 부족
4. 실시간 협업 기능 없음

### 개선 계획

1. 파일 형식 확대 (CSV, JSON 등)
2. 성능 최적화 (캐싱, 인덱싱)
3. 반응형 디자인 적용
4. 실시간 알림 시스템 구축

## 🤝 기여 방법

### 개발 참여

1. 이슈 등록 및 확인
2. 브랜치 생성 및 개발
3. 테스트 코드 작성
4. 풀 리퀘스트 제출

### 코드 리뷰 가이드라인

- 코드 품질 및 스타일 확인
- 테스트 커버리지 확인
- 문서 업데이트 여부 확인
- 성능 영향 검토

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 있습니다.

## 📞 연락처

- **개발자**: 김경태
- **이메일**: kkim1983@example.com
- **GitHub**: https://github.com/kkim1983/infrasmart

## 🎯 향후 계획

### 단기 계획 (1-2개월)

- 코드 리팩토링 및 정리
- 성능 최적화
- 테스트 코드 작성
- 문서화 보완

### 중장기 계획 (3-6개월)

- 모바일 앱 개발
- 클라우드 배포
- AI/ML 기능 추가
- 다국어 지원

---

**InfraSmart**는 교량 인프라 관리를 위한 혁신적인 솔루션입니다. 지속적인 개선을 통해 더 나은 시스템으로 발전시켜 나가겠습니다.
