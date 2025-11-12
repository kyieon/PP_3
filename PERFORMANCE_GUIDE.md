# 성능 최적화 가이드

## 적용된 최적화 사항

### 1. VS Code 설정 최적화 (.vscode/settings.json)

- 파일 감시 제외: **pycache**, .venv, cache.csv, server.log
- 검색 제외: Git, Python 캐시, 가상환경
- Python 분석 최적화: 인덱싱 깊이 제한
- 불필요한 기능 비활성화: codeLens, telemetry

### 2. Git 추적 최적화 (.gitignore)

- 대용량 파일 제외: cache.csv, server.log
- Python 바이트코드 완전 제외
- 가상환경 디렉토리 제외

### 3. 캐시 정리 자동화 (cleanup_cache.sh)

- Python **pycache** 정리
- VS Code 캐시 정리
- 대용량 로그 파일 백업
- Git 저장소 최적화

## 추가 성능 개선 권장사항

### 1. VS Code 확장 프로그램 관리

- 사용하지 않는 확장 프로그램 비활성화
- Python 관련 필수 확장만 유지:
  - Python (Microsoft)
  - Pylance (Microsoft)

### 2. 하드웨어 최적화

- SSD 디스크 사용 권장
- 충분한 RAM (최소 8GB, 권장 16GB)
- Python 가상환경을 SSD에 생성

### 3. 개발 환경 최적화

- 대용량 데이터 파일은 별도 디렉토리에 저장
- 로그 파일 정기적 관리
- Git 저장소 크기 모니터링

### 4. 정기 유지보수

```bash
# 주간 실행 권장
./cleanup_cache.sh

# 월간 실행 권장
git gc --aggressive
pip cache purge
```

### 5. 모니터링

- Activity Monitor에서 VS Code 프로세스 확인
- 메모리 사용량이 높은 확장 프로그램 식별
- 디스크 I/O 모니터링

## 즉시 적용 가능한 개선사항

1. VS Code 재시작
2. 불필요한 파일/탭 닫기
3. 가상환경 활성화 확인
4. Python 인터프리터 경로 확인
