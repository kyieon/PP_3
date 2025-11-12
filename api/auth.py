import os
import re
from flask import flash, redirect, render_template, request, jsonify, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from functools import wraps
from api import api_bp
from utils.common import get_db_connection
import jwt
import jwt.jwks_client
from dotenv import load_dotenv
from flask_cors import CORS



load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

# 로그인 체크 데코레이터
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "아이디와 비밀번호를 입력해주세요."}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 사용자 정보 확인
        cur.execute('SELECT * FROM users WHERE username=%s or email = %s', (email,email,))
        user = cur.fetchone()

        if user and check_password_hash(user[2], password):

            # JWT 토큰 생성
            token = jwt.encode({
                "username": user[1],  # username 대신 email을 저장
                "email": user[3],  # username 대신 email을 저장


                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)

            return jsonify({"token": token,"email":email,"username":user[1]}), 200
        else:
            return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401
    except Exception as e:
        return jsonify({"error": f"로그인 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")  # 헤더에서 토큰 가져오기

        if not token:
            return jsonify({"error": "토큰이 필요합니다."}), 401

        try:
            # 토큰 검증
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            session["username"] = data["username"]
            session["email"] = data["email"]  # username 대신 email로 저장
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "토큰이 만료되었습니다."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "유효하지 않은 토큰입니다."}), 401

        return f(*args, **kwargs)
    return decorated

@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json()
    name = data.get('name')
    company = data.get('company')
    email = data.get('email')
    password = data.get('password')

    # 필수 필드 확인
    if not name or not company or not email or not password:
        return jsonify({"error": "모든 필드를 입력해주세요."}), 400

    # 비밀번호 해시 처리
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 이메일 중복 확인
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cur.fetchone():
            return jsonify({"error": "이미 등록된 이메일입니다."}), 400

        # 사용자 등록
        cur.execute(
            '''
            INSERT INTO users (username, company, email, password)
            VALUES (%s, %s, %s, %s)
            ''',
            (name, company, email, hashed_password)
        )
        conn.commit()

        return jsonify({"message": "회원가입이 완료되었습니다."}), 201
    except Exception as e:
        return jsonify({"error": f"회원가입 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@api_bp.route('/delete_account', methods=['DELETE'])
@token_required
def delete_account():
    try:
        # 현재 로그인된 사용자 ID 가져오기
        email = session.get("email")

        if not email:
            return jsonify({"error": "사용자 인증이 필요합니다."}), 401

        conn = get_db_connection()
        cur = conn.cursor()

        # 사용자 삭제
        cur.execute('DELETE FROM users WHERE id = %s', (email,))
        conn.commit()

        return jsonify({"message": "회원 탈퇴가 완료되었습니다."}), 200
    except Exception as e:
        return jsonify({"error": f"회원 탈퇴 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@api_bp.route('/update_account', methods=['PUT'])
@token_required
def update_account():
    data = request.get_json()
    username = data.get('username')
    company = data.get('company')
    email = data.get('email')
    password = data.get('password')

    # 현재 로그인된 사용자 ID 가져오기
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "사용자 인증이 필요합니다."}), 401

    if not username or not company or not email:
        return jsonify({"error": "이름, 회사명, 이메일은 필수 항목입니다."}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 비밀번호가 제공된 경우 해시 처리
        if password:
            hashed_password = generate_password_hash(password)
            cur.execute(
                '''
                UPDATE users
                SET username = %s, company = %s, email = %s, password = %s
                WHERE id = %s
                ''',
                (username, company, email, hashed_password, user_id)
            )
        else:
            cur.execute(
                '''
                UPDATE users
                SET username = %s, company = %s, email = %s
                WHERE id = %s
                ''',
                (username, company, email, user_id)
            )

        conn.commit()
        return jsonify({"message": "회원정보가 성공적으로 수정되었습니다."}), 200
    except Exception as e:
        return jsonify({"error": f"회원정보 수정 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@api_bp.route('/logout', methods=['PUT'])
def logout():
    session.pop('email', None)
    return redirect(url_for('auth.login'))

@api_bp.route('/signup', methods=['PUT'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 비밀번호 확인
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('signup'))

        # 이메일 형식 검증
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('이메일 형식이 올바르지 않습니다.')
            return redirect(url_for('signup'))

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 이메일 중복 확인
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            if cur.fetchone():
                flash('이미 등록된 이메일입니다.')
                return redirect(url_for('signup'))

            # 새 사용자 추가
            hashed_password = generate_password_hash(password)
            cur.execute(
                'INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                (username, hashed_password, email)
            )
            conn.commit()
            flash('계정이 성공적으로 생성되었습니다! 로그인 해주세요.')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash('오류가 발생했습니다. 다시 시도해주세요.')
            return redirect(url_for('signup'))

        finally:
            cur.close()
            conn.close()

    return render_template('signup.html')
