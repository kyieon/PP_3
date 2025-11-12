"""
파일 관리 Blueprint
"""
from flask import Blueprint

file_management_bp = Blueprint('file_management', __name__)

from . import routes
