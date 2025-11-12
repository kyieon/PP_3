"""
인증 관련 라우트
"""
from flask import request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.common import get_db_connection
import re
import requests
import os
from . import auth_bp
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute('SELECT * FROM users WHERE   email = %s', (email,))
            user = cur.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['email'] = user[3]
                flash('로그인 성공!', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
        except Exception as e:
            flash(f'로그인 중 오류가 발생했습니다: {str(e)}', 'error')
        finally:
            cur.close()
            conn.close()

    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    kakao_client_id = os.environ.get('KAKAO_CLIENT_ID')
    kakao_redirect_uri = os.environ.get('KAKAO_REDIRECT_URI')
    return render_template('login.html', google_client_id=google_client_id, google_redirect_uri=google_redirect_uri, kakao_client_id=kakao_client_id, kakao_redirect_uri=kakao_redirect_uri)


@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth.login'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 비밀번호 확인
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('auth.signup'))

        # 이메일 형식 검증
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('이메일 형식이 올바르지 않습니다.')
            return redirect(url_for('auth.signup'))

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 사용자 이름 중복 확인
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                flash('이미 사용 중인 사용자명입니다.')
                return redirect(url_for('auth.signup'))

            # 이메일 중복 확인
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            if cur.fetchone():
                flash('이미 등록된 이메일입니다.')
                return redirect(url_for('auth.signup'))

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
            flash('An error occurred. Please try again.')
            return redirect(url_for('auth.signup'))

        finally:
            cur.close()
            conn.close()

    return render_template('signup.html')


@auth_bp.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('세션이 만료되었습니다. 다시 로그인 해주세요.', 'error')
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        username = request.form['username']
        company = request.form['company']
        try:
            cur.execute('UPDATE users SET username=%s, company=%s WHERE id=%s', (username, company, user_id))
            conn.commit()
            session['username'] = username
            # 회사명은 필요시 세션에 저장 가능
            flash('정보가 저장되었습니다!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'정보 저장 중 오류: {str(e)}', 'error')
        finally:
            cur.close()
            conn.close()
        return render_template('complete_profile.html', username=username, company=company)
    else:
        # 기존 값 불러오기
        cur.execute('SELECT username, company FROM users WHERE id=%s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        username = user[0] if user else ''
        company = user[1] if user and user[1] is not None else ''
        return render_template('complete_profile.html', username=username, company=company)


@auth_bp.route('/callback/google')
def google_callback():
    code = request.args.get('code')
    if not code:
        flash("인증 코드가 없습니다.", "error")
        return redirect(url_for('auth.login'))

    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    token_res = requests.post(token_url, data=data)
    if not token_res.ok:
        flash("구글 토큰 요청 실패", "error")
        return redirect(url_for('auth.login'))
    token_json = token_res.json()
    access_token = token_json.get('access_token')

    userinfo_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
    userinfo_res = requests.get(userinfo_url)
    if not userinfo_res.ok:
        flash("구글 사용자 정보 요청 실패", "error")
        return redirect(url_for('auth.login'))
    userinfo = userinfo_res.json()

    # 사용자 테이블 체크 및 자동 등록
    email = userinfo.get('email')
    name = userinfo.get('name')
    picture = userinfo.get('picture')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        if not user:
            temp_password = generate_password_hash(os.urandom(16).hex())
            now = datetime.now()
            cur.execute(
                'INSERT INTO users (username, password, email, created_at, company) VALUES (%s, %s, %s, %s, %s)',
                (name, temp_password, email, now, None)
            )
            conn.commit()
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            # 신규 사용자는 추가 정보 입력 페이지로 이동
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[3]
            session['google_name'] = name
            session['google_picture'] = picture
            return redirect(url_for('auth.complete_profile'))
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['email'] = user[3]
        session['google_name'] = name
        session['google_picture'] = picture
    except Exception as e:
        flash(f'구글 사용자 DB 처리 오류: {str(e)}', 'error')
        return redirect(url_for('auth.login'))
    finally:
        cur.close()
        conn.close()

    flash("구글 로그인 성공!", "success")
    return redirect(url_for('main.index'))


@auth_bp.route('/callback/kakao')
def kakao_callback():
    code = request.args.get('code')
    if not code:
        flash("인증 코드가 없습니다.", "error")
        return redirect(url_for('auth.login'))

    kakao_client_id = os.environ.get('KAKAO_CLIENT_ID')
    kakao_client_secret = os.environ.get('KAKAO_CLIENT_SECRET')
    kakao_redirect_uri = os.environ.get('KAKAO_REDIRECT_URI')

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': kakao_client_id,
        'client_secret': kakao_client_secret,
        'redirect_uri': kakao_redirect_uri,
        'code': code
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_res = requests.post(token_url, data=data, headers=headers)
    if not token_res.ok:
        flash("카카오 토큰 요청 실패", "error")
        return redirect(url_for('auth.login'))
    token_json = token_res.json()
    access_token = token_json.get('access_token')
    if not access_token:
        flash(f"카카오 토큰 요청 실패: {token_json}", "error")
        return redirect(url_for('auth.login'))

    # 사용자 정보 요청
    userinfo_url = "https://kapi.kakao.com/v2/user/me"
    userinfo_headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_res = requests.get(userinfo_url, headers=userinfo_headers)
    if not userinfo_res.ok:
        flash("카카오 사용자 정보 요청 실패", "error")
        return redirect(url_for('auth.login'))
    userinfo = userinfo_res.json()

    email = userinfo.get('kakao_account', {}).get('email', '')
    name = userinfo.get('properties', {}).get('nickname', '')
    if not email:
        flash("카카오 계정에 이메일 정보가 없습니다.", "error")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[3]
            session['kakao_name'] = name
            flash('카카오 로그인 성공!', 'success')
            return redirect(url_for('main.index'))
        else:
            now = datetime.now()
            cur.execute(
                'INSERT INTO users (username, password, email, created_at, company) VALUES (%s, %s, %s, %s, %s)',
                (name, '', email, now, None)
            )
            conn.commit()
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['email'] = user[3]
            session['kakao_name'] = name
            return redirect(url_for('auth.complete_profile'))
    except Exception as e:
        flash(f'카카오 사용자 DB 처리 오류: {str(e)}', 'error')
        return redirect(url_for('auth.login'))
    finally:
        cur.close()
        conn.close()
