from flask import Blueprint

# ✅ 1. 블루프린트 생성
api_bp = Blueprint('download', __name__)


# ✅ 2. 엔드포인트 등록을 위한 하위 모듈 import
# ❗ 이 부분은 api_bp 선언 바로 밑에서 즉시 실행되어야 함
from . import download_file
