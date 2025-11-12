"""
메인 페이지 라우트
"""
import pandas as pd
import uuid
from flask import request, render_template, redirect, url_for, session, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from api.file import clean_excel_header_newlines
from utils.common import get_db_connection, clean_dataframe_data
from utils.file_validation import validate_excel_file, excel_to_clean_df, perform_detailed_validation
from utils.decorators import login_required
from . import main_bp


@main_bp.route('/')
@main_bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.')
        return redirect(url_for('auth.login'))

    """메인 페이지 - 파일 업로드 및 목록"""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('파일이 선택되지 않았습니다.', 'error')
                return redirect(request.url)

            if file and file.filename.endswith('.xlsx'):
                try:
                    cleaned_file = clean_excel_header_newlines(file)
                    # 파일 검증 및 정제 엑셀 헤더가 유효한지 확인 특히 곤지암교의 경우 헤더가 병합되어 오류 발생 수정
                    df_result = excel_to_clean_df(cleaned_file, file)

                    # 검증 실패 시 오류 반환
                    if hasattr(df_result, 'is_valid'):
                        # FileValidationResult 객체인 경우 (오류 발생)
                        error_messages = '<br>'.join(df_result.errors)
                        flash(f'파일 검증 실패:<br>{error_messages}', 'error')
                        return redirect(request.url)

                    # 정상적으로 DataFrame과 header_row를 받은 경우
                    df, header_row = df_result

                    # DataFrame 데이터 정리 및 trim 처리
                    df = clean_dataframe_data(df)

                    # 필수 컬럼만 필터링
                    # required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']
                    # available_columns = [col for col in required_columns if col in df.columns]

                    # if len(available_columns) < len(required_columns):
                    #     missing_cols = [col for col in required_columns if col not in df.columns]
                    #     flash(f'필수 컬럼이 누락되었습니다: {", ".join(missing_cols)}', 'error')
                    #     return redirect(request.url)

                    # 상세 검증 수행 (손상물량 계산 검증 포함)
                    validation_result = perform_detailed_validation(df)

                    # 검증 오류가 있으면 중단
                    if validation_result.get('error_rows'):
                        error_count = len(validation_result['error_rows'])
                        error_messages = []

                        # 최대 10개의 오류만 표시
                        for error_row in validation_result['error_rows'][:10]:
                            row_num = error_row['row_index']
                            errors = ', '.join(error_row['errors'])
                            error_messages.append(f"행 {row_num}: {errors}")

                        if error_count > 10:
                            error_messages.append(f"... 외 {error_count - 10}개 오류")

                        flash(f'파일 검증 실패 (총 {error_count}개 오류):<br>' + '<br>'.join(error_messages), 'error')
                        return redirect(request.url)

                    # 검증을 통과한 정제된 데이터 사용
                    cleaned_data = validation_result.get('cleaned_data', [])

                    if not cleaned_data:
                        flash('유효한 데이터가 없습니다.', 'error')
                        return redirect(request.url)

                    # 데이터베이스에 저장
                    conn = get_db_connection()
                    cur = conn.cursor()

                    # 정제된 데이터를 JSON으로 변환 (NaN 처리)
                    import json
                    import math

                    def convert_nan_to_none(obj):
                        """NaN과 Infinity를 None으로 변환"""
                        if isinstance(obj, float):
                            if math.isnan(obj) or math.isinf(obj):
                                return None
                        elif isinstance(obj, dict):
                            return {k: convert_nan_to_none(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_nan_to_none(item) for item in obj]
                        return obj

                    cleaned_data = convert_nan_to_none(cleaned_data)
                    file_data = json.dumps(cleaned_data, ensure_ascii=False)

                    # 파일 정보 저장
                    bridge_name = request.form.get('bridge_name', '')
                    structure_type = request.form.get('structure_type', '')
                    span_count = request.form.get('span_count', '')
                    length = request.form.get('length', '')
                    width = request.form.get('width', '')
                    expansion_joint_location = request.form.get('expansion_joint_location', '')

                    # 숫자형 데이터 변환
                    try:
                        span_count = int(span_count) if span_count else None
                        length = float(length) if length else None
                        width = float(width) if width else None
                    except (ValueError, TypeError):
                        span_count = None
                        length = None
                        width = None

                    cur.execute(
                        '''
                        INSERT INTO uploaded_files
                        (user_id, filename, original_filename, file_data, bridge_name,
                         structure_type, span_count, length, width, expansion_joint_location)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, filename)
                        DO UPDATE SET file_data = EXCLUDED.file_data, bridge_name = EXCLUDED.bridge_name,
                                     structure_type = EXCLUDED.structure_type, span_count = EXCLUDED.span_count,
                                     length = EXCLUDED.length, width = EXCLUDED.width,
                                     expansion_joint_location = EXCLUDED.expansion_joint_location
                        ''',
                        (
                            session['user_id'],
                            str(uuid.uuid4()),  # UUID로 파일명 생성
                            file.filename,
                            file_data,
                            bridge_name,
                            structure_type,
                            span_count,
                            length,
                            width,
                            expansion_joint_location
                        )
                    )

                    conn.commit()
                    cur.close()
                    conn.close()

                    flash('파일이 성공적으로 업로드되었습니다.', 'success')
                    return redirect(url_for('main.index'))

                except Exception as e:
                    flash(f'파일 처리 중 오류가 발생했습니다: {str(e)}', 'error')
                    return redirect(request.url)
            else:
                flash('올바른 Excel 파일(.xlsx)을 업로드해주세요.', 'error')
                return redirect(request.url)

    # 사용자의 최근 업로드 파일 목록 가져오기
    conn = get_db_connection()
    cur = conn.cursor()

    # 모든 컬럼 가져오기
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'uploaded_files'
    """)
    columns = [row[0] for row in cur.fetchall()]

    # 데이터 가져오기
    cur.execute(f"""
        SELECT {', '.join(columns)}
        FROM uploaded_files
        WHERE user_id = %s
        ORDER BY upload_date DESC
    """, (session['user_id'],))

    # 데이터를 files에 담기
    files = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('files.html', files=files)


@main_bp.route('/index_re')
@login_required
def index_re():
    """새로운 인덱스 페이지"""
    from utils.slab_processing import process_slab_damage_data

    conn = get_db_connection()
    cursor = conn.cursor()

    # 부재별 집계표 데이터 조회
    cursor.execute('''
        SELECT 부재명, 손상내용, 단위, SUM(손상물량) as 총손상물량, SUM(개소) as 총개소
        FROM file_damage_details
        WHERE user_id = %s
        GROUP BY 부재명, 손상내용, 단위
        ORDER BY 부재명, 손상내용
    ''', (session['user_id'],))
    component_data = cursor.fetchall()

    # 데이터 가공
    processed_data = []
    for row in component_data:
        processed_data.append({
            '부재명': row[0],
            '손상내용': row[1],
            '단위': row[2],
            '손상물량': row[3] if row[3] is not None else 0,
            '개소': row[4] if row[4] is not None else 0
        })

    # 사용자 정의 손상 매핑 설정
    custom_damage_mapping = {
        '균열': {
            '1방향': {
                'keywords': ['균열부백태', '균열'],
                'length_factor': 0.25
            },
            '2방향': {
                'keywords': ['망상균열', '균열'],
                'length_factor': 0.25
            }
        },
        '누수': {
            'keywords': ['누수', '백태']
        },
        '표면손상': {
            'keywords': ['박리', '박락', '파손']
        },
        '철근부식': {
            'keywords': ['철근노출']
        }
    }

    # 콘크리트 바닥판 데이터 처리
    slab_data = process_slab_damage_data(processed_data, custom_damage_mapping)

    conn.close()

    return render_template('index_re.html', slab_data=slab_data)


@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')


@main_bp.route('/style.css')
def style():
    return send_from_directory('static/css', 'style.css')


@main_bp.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('static/js', filename)


@main_bp.route('/download/<filename>')
def download_file(filename):
    """파일 다운로드"""
    return send_from_directory('data', filename, as_attachment=True)


@main_bp.route('/pricing')
@login_required
def pricing():
    """가격 정책 페이지"""
    return render_template('pricing.html')


@main_bp.route('/files/delete_file/<filename>', methods=['POST', 'GET'])
@login_required
def delete_file(filename):
    """파일 삭제 및 JSON 응답"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM uploaded_files WHERE user_id = %s AND filename = %s",
        (session['user_id'], filename)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})
