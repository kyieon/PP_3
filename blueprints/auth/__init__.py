"""
인증 관련 Blueprint
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import routes
