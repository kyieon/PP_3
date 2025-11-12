from werkzeug.utils import secure_filename
import uuid
import os

def safe_filename(filename):
    """한글 파일명을 안전하게 처리"""
    if not filename:
        return None
    
    # 파일 확장자 분리
    name, ext = os.path.splitext(filename)
    
    # 한글이 포함된 경우 UUID로 변경
    try:
        # ASCII로 인코딩 시도
        name.encode('ascii')
        # ASCII로 인코딩 가능하면 기존 방식 사용
        return str(uuid.uuid4())
    except UnicodeEncodeError:
        # 한글이 포함된 경우 UUID 사용
        unique_name = str(uuid.uuid4())
        return f"{unique_name}"