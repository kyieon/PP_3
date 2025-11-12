#!/bin/bash

# Python 캐시 정리
echo "Python 캐시 파일 정리 중..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

# VS Code 캐시 정리
echo "VS Code 캐시 정리 중..."
if [ -d ".vscode" ]; then
    find .vscode -name "*.log" -delete 2>/dev/null
fi

# 로그 파일 정리 (크기가 10MB 이상인 경우만)
echo "대용량 로그 파일 확인 중..."
if [ -f "server.log" ]; then
    size=$(stat -f%z server.log 2>/dev/null || stat -c%s server.log 2>/dev/null)
    if [ "$size" -gt 10485760 ]; then
        echo "server.log가 10MB 이상입니다. 백업 후 정리합니다."
        mv server.log server.log.backup
        touch server.log
    fi
fi

# cache.csv 파일 확인
if [ -f "cache.csv" ]; then
    size=$(stat -f%z cache.csv 2>/dev/null || stat -c%s cache.csv 2>/dev/null)
    if [ "$size" -gt 5242880 ]; then
        echo "cache.csv가 5MB 이상입니다. 백업 후 정리를 고려하세요."
    fi
fi

# Git 캐시 정리
echo "Git 캐시 최적화 중..."
git gc --prune=now --aggressive 2>/dev/null || echo "Git 리포지토리가 아니거나 Git 최적화를 건너뜁니다."

echo "캐시 정리 완료!"
echo "VS Code를 재시작하면 성능이 개선될 수 있습니다."
