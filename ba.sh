#!/bin/bash

# PostgreSQL 백업 스크립트
# 새벽 5시에 실행되어 PostgreSQL을 재시작하고 백업을 생성합니다
# 로그 파일 설정
BACKUP_DIR="/home/skpark/git/infrasmart_work/infrasmart/backups"
LOG_DIR="/home/skpark/git/infrasmart_work/infrasmart/backup_logs"

DB_NAME="infrasmart"  # 실제 데이터베이스 이름으로 변경하세요
DATE=$(date +%Y%m%d_%H%M%S)
echo " ddddddd"
# 백업 디렉토리 생성

# 데이터베이스 이름
DATABASE_NAME="bridge_db"

# PostgreSQL 사용자 (필요한 경우)
PGUSER="postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/database_backup_$TIMESTAMP.dump"
LOG_FILE="$LOG_DIR/backup_$TIMESTAMP.log"
echo "$(date): 백업 시작" >> $LOG_FILE

