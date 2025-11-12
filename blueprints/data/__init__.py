"""
데이터 처리 Blueprint
"""
from flask import Blueprint

data_bp = Blueprint('data', __name__)

from . import routes
