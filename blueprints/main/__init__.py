"""
메인 페이지 Blueprint
"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)

from . import routes
