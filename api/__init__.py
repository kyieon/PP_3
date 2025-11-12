from flask import Blueprint

# ✅ 1. 블루프린트 생성
api_bp = Blueprint('api', __name__)


# ✅ 2. 엔드포인트 등록을 위한 하위 모듈 import
# ❗ 이 부분은 api_bp 선언 바로 밑에서 즉시 실행되어야 함
from . import auth
from . import file
from . import evaluation
from . import evaluation_data
from . import span_damage
from . import damage_meta
from . import damage_keyword
from . import carbonation_test
from . import bridge
