"""
관리자 페이지 Blueprint
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from . import routes
