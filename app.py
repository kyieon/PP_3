"""
Flask 애플리케이션 메인 파일
모든 Blueprint가 등록되는 중앙 집중식 관리
"""
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# 환경변수 로딩
load_dotenv()

def create_app():
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)

    # 애플리케이션 설정
    app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')
    app.config['JSON_AS_ASCII'] = False  # 한글이 Unicode escape 되지 않도록 설정

    # CORS 설정
    CORS(app)

    # Blueprint 등록
    from blueprints.auth import auth_bp
    from blueprints.main import main_bp
    from blueprints.data import data_bp
    from blueprints.evaluation import evaluation_bp
    from blueprints.file_management import file_management_bp
    from blueprints.views import views_bp
    from blueprints.admin import admin_bp
    from download.download_file import download_bp
    from api import api_bp
    from api.carbonation_test import carbonation_test_bp
    from api.component_selection import component_selection_bp
    from api.evaluation_weights import evaluation_weights_bp

    # Blueprint 등록
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(data_bp, url_prefix='/data')
    app.register_blueprint(evaluation_bp, url_prefix='/evaluation')
    app.register_blueprint(file_management_bp, url_prefix='/files')
    app.register_blueprint(views_bp, url_prefix='/views')
    app.register_blueprint(admin_bp)  # /admin prefix는 Blueprint 자체에 설정됨
    app.register_blueprint(download_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(carbonation_test_bp, url_prefix="/api")
    app.register_blueprint(component_selection_bp, url_prefix="/api")
    app.register_blueprint(evaluation_weights_bp, url_prefix="/api")

    # Jinja2 필터 등록
    import pandas as pd

    @app.template_filter('evaluate_crack')
    def evaluate_crack(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = float(value)
        if value >= 1.0:
            return 'e'
        elif value >= 0.5:
            return 'd'
        elif value >= 0.3:
            return 'c'
        elif value >= 0.1:
            return 'b'
        else:
            return 'a'

    @app.template_filter('evaluate_spalling')
    def evaluate_spalling(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = float(value)
        if value >= 0.3:
            return 'e'
        elif value >= 0.2:
            return 'd'
        elif value >= 0.1:
            return 'c'
        elif value >= 0.05:
            return 'b'
        else:
            return 'a'

    @app.template_filter('evaluate_rebar_exposure')
    def evaluate_rebar_exposure(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = float(value)
        if value > 0:
            return 'e'
        else:
            return 'a'

    @app.template_filter('evaluate_efflorescence')
    def evaluate_efflorescence(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = float(value)
        if value >= 0.3:
            return 'd'
        elif value >= 0.2:
            return 'c'
        elif value >= 0.1:
            return 'b'
        else:
            return 'a'

    @app.template_filter('evaluate_damage')
    def evaluate_damage(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = float(value)
        if value >= 0.3:
            return 'e'
        elif value >= 0.2:
            return 'd'
        elif value >= 0.1:
            return 'c'
        elif value >= 0.05:
            return 'b'
        else:
            return 'a'

    @app.template_filter('evaluate_count')
    def evaluate_count(value):
        if value == '-' or pd.isna(value):
            return 'a'
        value = int(value)
        if value >= 10:
            return 'e'
        elif value >= 7:
            return 'd'
        elif value >= 4:
            return 'c'
        elif value >= 1:
            return 'b'
        else:
            return 'a'

    return app

# 개발 서버용 소스반영테스트
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8089)
