#!/bin/bash

# PostgreSQL 백업 스크립트
# 새벽 5시에 실행되어 PostgreSQL을 재시작하고 백업을 생성합니다

# 백업 파일 저장 경로
BACKUP_DIR="/home/skpark/git/infrasmart_work/infrasmart/backups"
LOG_DIR="/home/skpark/git/infrasmart_work/infrasmart/backup_logs"

# 백업 파일명 (날짜 및 시간 포함)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/database_backup_$TIMESTAMP.dump"
LOG_FILE="$LOG_DIR/backup_$TIMESTAMP.log"

# 데이터베이스 이름
DATABASE_NAME="bridge_db"

# PostgreSQL 사용자 (필요한 경우)
PGUSER="postgres"

# 백업 디렉토리 생성 (존재하지 않는 경우)
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

echo "$(date): 백업 시작" >> "$LOG_FILE"

# PostgreSQL 재시작 (sudo 없이 시도)
echo "$(date): PostgreSQL 서비스 상태 확인 중..." >> "$LOG_FILE"
systemctl is-active --quiet postgresql
if [ $? -eq 0 ]; then
    echo "$(date): PostgreSQL이 이미 실행 중입니다." >> "$LOG_FILE"
else
    echo "$(date): PostgreSQL이 중지되어 있습니다. 시작 시도..." >> "$LOG_FILE"
    # sudo 없이 서비스 재시작 시도 (사용자가 postgres 그룹에 속해있어야 함)
    systemctl restart postgresql 2>> "$LOG_FILE" || {
        echo "$(date): PostgreSQL 재시작 실패. 수동으로 재시작하세요." >> "$LOG_FILE"
    }
fi

# 잠시 대기
sleep 5

# PostgreSQL 비밀번호 환경변수 설정 (필요한 경우)
# export PGPASSWORD="your_password_here"

# pg_dump 명령어를 사용하여 백업 (peer 인증 사용)
echo "$(date): 데이터베이스 백업 시작..." >> "$LOG_FILE"
sudo -u postgres pg_dump -Fc "$DATABASE_NAME" > "$BACKUP_FILE" 2>> "$LOG_FILE"

# 백업 결과 확인
if [ $? -eq 0 ] && [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    echo "$(date): 백업 성공: $BACKUP_FILE" >> "$LOG_FILE"
    echo "백업 완료: $BACKUP_FILE"
    
    # 백업 파일 압축 (선택 사항)
    gzip "$BACKUP_FILE"
    echo "$(date): 백업 파일 압축 완료: $BACKUP_FILE.gz" >> "$LOG_FILE"
    
    # 7일 이상 된 백업 파일 삭제
    find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete 2>> "$LOG_FILE"
    echo "$(date): 오래된 백업 파일 정리 완료" >> "$LOG_FILE"
else
    echo "$(date): 백업 실패" >> "$LOG_FILE"
    echo "백업 실패! 로그를 확인하세요: $LOG_FILE"
    exit 1
fi

echo "$(date): 백업 프로세스 완료" >> "$LOG_FILE"
