from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from utils.damage_cache import damage_cache
from utils.common import get_db_connection, clean_dataframe_data
from utils.decorators import login_required
from utils.file_validation import normalize_component_name, normalize_component_source
import logging
import os
import json
import pandas as pd

from . import admin_bp

@admin_bp.route('/cache')
def cache_management():
    """캐시 관리 페이지"""
    stats = damage_cache.get_cache_stats()
    return render_template('admin/cache.html', stats=stats)

@admin_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """캐시 초기화"""
    try:
        damage_cache.clear_cache()
        flash('캐시가 성공적으로 초기화되었습니다.', 'success')
    except Exception as e:
        flash(f'캐시 초기화 중 오류가 발생했습니다: {str(e)}', 'error')

    return redirect(url_for('admin.cache_management'))

@admin_bp.route('/cache/stats')
def cache_stats():
    """캐시 통계 API"""
    stats = damage_cache.get_cache_stats()
    return jsonify(stats)


@admin_bp.route('/')
def admin_home():
    return render_template('admin/admin.html', active_tab='meta')

@admin_bp.route('/meta')
def admin_meta():
    return render_template('admin/meta.html', active_tab='meta')

@admin_bp.route('/users')
def admin_users():
    return render_template('admin/users.html', active_tab='users')

@admin_bp.route('/files')
def admin_files():
    return render_template('admin/files.html', active_tab='files')

@admin_bp.route('/settings')
def admin_settings():
    return render_template('admin/settings.html', active_tab='settings')

# 메타데이터 관리 API
@admin_bp.route('/api/meta', methods=['GET'])
@login_required
def get_meta_data():
    """메타데이터 목록 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, keyword, parent_id, use_yn FROM damage_meta ORDER BY id")
        meta_data = cur.fetchall()

        cur.execute("SELECT id, meta_id, keyword, source, use_yn FROM meta_keyword ORDER BY id")
        keyword_data = cur.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'meta_data': meta_data,
            'keyword_data': keyword_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/meta', methods=['POST'])
@login_required
def add_meta_data():
    """메타데이터 추가"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()

        if data['type'] == 'meta':
            cur.execute(
                "INSERT INTO damage_meta (keyword, parent_id, use_yn) VALUES (%s, %s, %s)",
                (data['keyword'], data.get('parent_id'), data.get('use_yn', 'Y'))
            )
        elif data['type'] == 'keyword':
            cur.execute(
                "INSERT INTO meta_keyword (meta_id, keyword, source, use_yn) VALUES (%s, %s, %s, %s)",
                (data['meta_id'], data['keyword'], data.get('source'), data.get('use_yn', 'Y'))
            )

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/meta/<int:item_id>', methods=['PUT'])
@login_required
def update_meta_data(item_id):
    """메타데이터 수정"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()

        if data['type'] == 'meta':
            cur.execute(
                "UPDATE damage_meta SET keyword=%s, parent_id=%s, use_yn=%s WHERE id=%s",
                (data['keyword'], data.get('parent_id'), data.get('use_yn'), item_id)
            )
        elif data['type'] == 'keyword':
            cur.execute(
                "UPDATE meta_keyword SET meta_id=%s, keyword=%s, source=%s, use_yn=%s WHERE id=%s",
                (data['meta_id'], data['keyword'], data.get('source'), data.get('use_yn'), item_id)
            )

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/meta/<int:item_id>', methods=['DELETE'])
@login_required
def delete_meta_data(item_id):
    """메타데이터 삭제"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()

        if data['type'] == 'meta':
            cur.execute("DELETE FROM damage_meta WHERE id=%s", (item_id,))
        elif data['type'] == 'keyword':
            cur.execute("DELETE FROM meta_keyword WHERE id=%s", (item_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 사용자 관리 API
@admin_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """사용자 목록 조회"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, created_at, is_active FROM users ORDER BY id")
        users = cur.fetchall()
        conn.close()

        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """사용자 정보 수정"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET username=%s, email=%s, is_active=%s WHERE id=%s",
            (data['username'], data['email'], data['is_active'], user_id)
        )

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """사용자 삭제"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 파일 관리 API
@admin_bp.route('/api/files', methods=['GET'])
@login_required
def get_uploaded_files():
    """업로드된 파일 목록 조회 (페이지네이션 및 검색 지원)"""
    try:
        # 쿼리 파라미터 추출
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'upload_date')
        sort_order = request.args.get('sort_order', 'desc')

        # 정렬 컬럼 매핑
        sort_columns = {
            'id': 'uf.id',
            'filename': 'uf.filename',
            'bridge_name': 'uf.bridge_name',
            'upload_date': 'uf.upload_date',
            'username': 'u.username'
        }

        sort_column = sort_columns.get(sort_by, 'uf.upload_date')
        sort_direction = 'ASC' if sort_order == 'asc' else 'DESC'

        conn = get_db_connection()
        cur = conn.cursor()

        # 검색 조건 구성
        where_clause = ""
        params = []

        if search:
            where_clause = """
                WHERE (uf.filename ILIKE %s
                OR uf.bridge_name ILIKE %s
                OR u.username ILIKE %s
                OR uf.original_filename ILIKE %s)
            """
            search_param = f'%{search}%'
            params = [search_param, search_param, search_param, search_param]

        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(*)
            FROM uploaded_files uf
            LEFT JOIN users u ON uf.user_id = u.id
            {where_clause}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()[0]

        # 페이지네이션 계산
        offset = (page - 1) * per_page
        total_pages = (total_count + per_page - 1) // per_page

        # 데이터 조회
        data_query = f"""
            SELECT
                uf.id,
                uf.filename,
                uf.original_filename,
                uf.bridge_name,
                uf.upload_date,
                u.username,
                uf.structure_type,
                uf.span_count,
                uf.length,
                uf.width
            FROM uploaded_files uf
            LEFT JOIN users u ON uf.user_id = u.id
            {where_clause}
            ORDER BY {sort_column} {sort_direction}
            LIMIT %s OFFSET %s
        """

        data_params = params + [per_page, offset]
        cur.execute(data_query, data_params)
        files = cur.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'files': files,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            },
            'search': search,
            'sort_by': sort_by,
            'sort_order': sort_order
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_uploaded_file(file_id):
    """업로드된 파일 삭제"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 파일 정보 조회
        cur.execute("SELECT filename FROM uploaded_files WHERE id=%s", (file_id,))
        file_info = cur.fetchone()

        if file_info:
            # 데이터베이스에서 삭제
            cur.execute("DELETE FROM uploaded_files WHERE id=%s", (file_id,))

            # 실제 파일 삭제 (옵션)
            file_path = os.path.join('uploads', file_info[0])
            if os.path.exists(file_path):
                os.remove(file_path)

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/view_file/<file_id>')
@login_required
def view_file_data(file_id):
    """파일 데이터를 테이블 형태로 보기"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 파일 정보와 데이터 조회
        cur.execute("""
            SELECT uf.filename, uf.bridge_name, uf.file_data, u.username, uf.upload_date
            FROM uploaded_files uf
            LEFT JOIN users u ON uf.user_id = u.id
            WHERE uf.id = %s
        """, (file_id,))
        result = cur.fetchone()

        if not result:
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('admin.admin_files'))

        filename, bridge_name, file_data, username, upload_date = result

        # JSON 데이터를 DataFrame으로 변환
        if isinstance(file_data, str):
            file_data = json.loads(file_data)

        df = pd.DataFrame(file_data)

        # DataFrame 데이터 정리 및 trim 처리
        df = clean_dataframe_data(df)

        # 부재명 정규화 추가 (원본 부재명 보존)
        if '부재명' in df.columns:
            # 원본 부재명 저장 (이미 있으면 유지)
            if '원본부재명' not in df.columns:
                df['원본부재명'] = df['부재명'].copy()

            # 부재위치가 있으면 함께 사용하여 정규화, 없으면 부재명만 정규화
            if '부재위치' in df.columns:
                df['정규화부재명'] = df.apply(lambda row: normalize_component_source(row['부재명'], row['부재위치']), axis=1)
            else:
                df['정규화부재명'] = df['부재명'].apply(normalize_component_source)

            print(f"부재명 정규화 완료: {len(df)}개 행 처리")

        # DataFrame을 HTML 테이블로 변환
        # 컬럼 순서 조정: 부재명 관련 컬럼들을 앞쪽에 배치
        column_order = []

        # 부재명 관련 컬럼들을 먼저 추가
        if '원본부재명' in df.columns:
            column_order.append('원본부재명')
        if '부재명' in df.columns:
            column_order.append('부재명')
        if '정규화부재명' in df.columns:
            column_order.append('정규화부재명')
        if '부재위치' in df.columns:
            column_order.append('부재위치')

        # 나머지 컬럼들 추가 (중복 제거)
        for col in df.columns:
            if col not in column_order:
                column_order.append(col)

        # 컬럼 순서대로 DataFrame 재정렬
        df_ordered = df[column_order]

        table_html = df_ordered.to_html(
            classes='table table-striped table-bordered table-hover',
            table_id='file-data-table',
            escape=False,
            index=True,
            max_rows=1000  # 최대 1000행까지만 표시
        )

        # 파일 통계 정보
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'ordered_columns': column_order,
            'file_info': {
                'filename': filename,
                'bridge_name': bridge_name,
                'username': username,
                'upload_date': upload_date.strftime('%Y-%m-%d %H:%M:%S') if upload_date else 'N/A'
            },
            'component_info': {
                'has_original_component': '원본부재명' in df.columns,
                'has_normalized_component': '정규화부재명' in df.columns,
                'has_position': '부재위치' in df.columns,
                'unique_components': len(df['부재명'].unique()) if '부재명' in df.columns else 0,
                'unique_normalized_components': len(df['정규화부재명'].unique()) if '정규화부재명' in df.columns else 0
            }
        }

        conn.close()

        return render_template('admin/view_file.html',
                             table_html=table_html,
                             stats=stats,
                             file_id=file_id)

    except Exception as e:
        flash(f'파일 데이터 조회 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.admin_files'))
