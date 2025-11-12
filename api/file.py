
import io
from flask import request, jsonify, send_from_directory, flash, redirect, url_for, session
from api import api_bp
from api.safe_filename import safe_filename
from utils.common import get_db_connection, clean_dataframe_data
import pandas as pd
from werkzeug.utils import secure_filename

from utils.file_validation import excel_to_clean_df, validate_excel_file,perform_detailed_validation, generate_table_preview


def clean_excel_header_newlines(file):
    """
    엑셀 파일의 헤더(1~6행) 컬럼명에서 개행(\n) 제거 후, 새 BytesIO file 객체 반환
    Args:
        file: werkzeug FileStorage 또는 file-like object
    Returns:
        BytesIO: 개행이 제거된 엑셀 파일 객체
    """
    import pandas as pd
    import re
    from pandas import ExcelWriter
    file.seek(0)
    # 1. 엑셀 파일을 DataFrame 리스트로 읽기 (모든 시트, header=None)
    # 반드시 pd.read_excel 사용 (첫 번째 시트만)
    file.seek(0)
    df = pd.read_excel(file, sheet_name=0, header=None, dtype=str)
    first_sheet = 'Sheet1'
    # 수식 문자열(=으로 시작) 셀을 값 또는 빈 값으로 변환
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            val = df.iat[i, j]
            if isinstance(val, str) and val.startswith('='):
                df.iat[i, j] = ''

    print(f"[HEADER_NORMALIZATION] --- 시트: {first_sheet} ---")
    for i in range(min(1000, len(df))):
        for j, val in enumerate(df.iloc[i]):
            if isinstance(val, str):
                original = val
                if len(original) > 20 or original.startswith('='):
                    print(f"  [헤더 {i+1}행] '{original}' -> (skip)")
                    continue
                cleaned = re.sub(r'\(.*?\)', '', original)
                cleaned = re.sub(r'\s+', '', cleaned)
                #cleaned = re.sub(r'[^\uAC00-\uD7A3a-zA-Z0-9.]', '', cleaned)
                cleaned = cleaned.strip()
                print(f"  [헤더 {i+1}행] '{original}' -> '{cleaned}'")
                df.iat[i, j] = cleaned
    print(f"[HEADER_NORMALIZATION] --- 끝 ---")
    # 3. DataFrame을 새 엑셀 파일로 저장 (첫 번째 시트만)
    output = io.BytesIO()
    with ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=first_sheet, header=False, index=False)
    output.seek(0)
    return output
@api_bp.route('/files', methods=['GET'])
def get_files():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM uploaded_files WHERE user_id = %s', (session['user_id'],))
        files = cur.fetchall()
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": f"파일 목록을 가져오는 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@api_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory('uploads', filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"파일 다운로드 중 오류가 발생했습니다: {str(e)}"}), 500



@api_bp.route('/update_file', methods=['POST'])
def update_file():
    file_id = request.form.get('file_id')
    bridge_name = request.form.get('bridge_name')
    structure_type = request.form.get('structure_type', '')
    span_count = request.form.get('span_count', 0)
    length = request.form.get('length', 0)
    width = request.form.get('width', 0)
    expansion_joint_location = request.form.get('expansion_joint_location', '')

    # 수치 값 변환 및 검증
    try:
        span_count = int(span_count) if span_count else 0
        length = float(length) if length else 0
        width = float(width) if width else 0
    except (ValueError, TypeError):
        flash('입력된 수치 값에 오류가 있습니다.', 'error')
        return redirect(url_for('main.index'))

    # 파일 처리
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            try:
                # 원본 파일명 저장 (한글 포함 가능)
                original_filename = file.filename

                # 안전한 파일명 생성
                safe_file_name = safe_filename(file.filename)

                print(f"원본 파일명: {original_filename}")
                print(f"안전한 파일명: {safe_file_name}")

                # 헤더 정규화 적용
                cleaned_file = clean_excel_header_newlines(file)

                # 파일 검증 및 정제
                df_result = excel_to_clean_df(cleaned_file , file)

                # 검증 실패 시 오류 반환
                if hasattr(df_result, 'is_valid'):
                    # FileValidationResult 객체인 경우 (오류 발생)
                    error_messages = '<br>'.join(df_result.errors)
                    flash(f'파일 검증 실패:<br>{error_messages}', 'error')
                    return redirect(url_for('main.index'))

                # 정상적으로 DataFrame과 header_row를 받은 경우
                df, header_row = df_result

                # DataFrame 데이터 정리 및 trim 처리
                df = clean_dataframe_data(df)

                # 필수 컬럼만 필터링
                required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']
                available_columns = [col for col in required_columns if col in df.columns]

                if len(available_columns) < len(required_columns):
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    error_messages = [f'필수 컬럼 누락: {", ".join(missing_cols)}']
                    flash(f'파일 검증 실패:<br>' + '<br>'.join(error_messages), 'error')
                    return redirect(url_for('main.index'))

                # 검증을 통과한 정제된 데이터 사용
                cleaned_data = df.to_dict(orient='records')

                if not cleaned_data:
                    flash('유효한 데이터가 없습니다.', 'error')
                    return redirect(url_for('main.index'))

                # 데이터베이스에 저장
                conn = get_db_connection()
                cur = conn.cursor()

                # 정제된 데이터를 JSON으로 변환
                import json
                file_data = json.dumps(cleaned_data, ensure_ascii=False)

                # file_id가 있으면 업데이트, 없으면 새로 생성
                if file_id and file_id.strip():
                    # 기존 파일 업데이트
                    cur.execute('''
                        UPDATE uploaded_files
                        SET bridge_name = %s, file_data = %s, original_filename = %s,
                            structure_type = %s, span_count = %s, length = %s, width = %s,
                            expansion_joint_location = %s, upload_date = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    ''', (bridge_name, file_data, original_filename, structure_type, span_count,
                          length, width, expansion_joint_location, file_id, session['user_id']))
                else:
                    # 새 파일 생성
                    cur.execute('''
                        INSERT INTO uploaded_files
                        (user_id, filename, original_filename, file_data, bridge_name,
                         structure_type, span_count, length, width, expansion_joint_location)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, filename)
                        DO UPDATE SET
                            file_data = EXCLUDED.file_data,
                            bridge_name = EXCLUDED.bridge_name,
                            original_filename = EXCLUDED.original_filename,
                            structure_type = EXCLUDED.structure_type,
                            span_count = EXCLUDED.span_count,
                            length = EXCLUDED.length,
                            width = EXCLUDED.width,
                            expansion_joint_location = EXCLUDED.expansion_joint_location,
                            upload_date = CURRENT_TIMESTAMP
                    ''', (
                        session['user_id'],
                        safe_file_name,  # 안전한 파일명 사용
                        original_filename,  # 원본 파일명 저장
                        file_data,
                        bridge_name,
                        structure_type,
                        span_count,
                        length,
                        width,
                        expansion_joint_location
                    ))

                conn.commit()
                cur.close()
                conn.close()

                flash('파일이 성공적으로 업로드되었습니다.', 'success')
                return redirect(url_for('main.index'))

            except UnicodeDecodeError as e:
                flash(f'파일명 인코딩 오류: {str(e)}', 'error')
                return redirect(url_for('main.index'))
            except Exception as e:
                print(f"파일 업로드 오류: {str(e)}")
                flash(f'파일 처리 중 오류가 발생했습니다: {str(e)}', 'error')
                return redirect(url_for('main.index'))
    else:
        # 파일 없이 교량 정보만 업데이트하는 경우
        if file_id and file_id.strip():
            conn = get_db_connection()
            cur = conn.cursor()

            try:
                # 교량 정보 업데이트
                cur.execute('''
                    UPDATE uploaded_files
                    SET bridge_name = %s, structure_type = %s, span_count = %s,
                        length = %s, width = %s, expansion_joint_location = %s,
                        upload_date = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                ''', (bridge_name, structure_type, span_count, length, width,
                      expansion_joint_location, file_id, session['user_id']))

                if cur.rowcount == 0:
                    flash('업데이트할 파일을 찾을 수 없습니다.', 'error')
                else:
                    flash('교량 정보가 성공적으로 업데이트되었습니다.', 'success')

                conn.commit()
            except Exception as e:
                print(f"교량 정보 업데이트 오류: {str(e)}")
                flash(f'교량 정보 업데이트 중 오류가 발생했습니다: {str(e)}', 'error')
            finally:
                cur.close()
                conn.close()
        else:
            flash('필요한 정보를 입력해주세요.', 'error')

    return redirect(url_for('main.index'))


@api_bp.route('/update_bridge_info', methods=['POST'])
def update_bridge_info():
    try:
        # JSON 데이터 받기
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': '요청 데이터가 없습니다.'}), 400

        filename = data.get('filename')
        bridge_name = data.get('bridge_name')
        structure_type = data.get('structure_type', '')
        span_count = data.get('span_count', 0)
        length = data.get('length', 0)
        width = data.get('width', 0)
        expansion_joint_location = data.get('expansion_joint_location', '')

        # 필수 필드 검증
        if not filename or not filename.strip():
            return jsonify({'success': False, 'error': '파일명이 필요합니다.'}), 400

        if not bridge_name or not bridge_name.strip():
            return jsonify({'success': False, 'error': '교량명이 필요합니다.'}), 400

        if not structure_type or not structure_type.strip():
            return jsonify({'success': False, 'error': '구조형식이 필요합니다.'}), 400

        # 수치 값 변환 및 검증
        try:
            span_count = int(span_count) if span_count else 0
            length = float(length) if length else 0
            width = float(width) if width else 0

            if span_count < 1:
                return jsonify({'success': False, 'error': '경간 수는 1 이상이어야 합니다.'}), 400
            if length <= 0:
                return jsonify({'success': False, 'error': '연장은 0보다 커야 합니다.'}), 400
            if width <= 0:
                return jsonify({'success': False, 'error': '폭은 0보다 커야 합니다.'}), 400

        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '입력된 수치 값에 오류가 있습니다.'}), 400

        # 데이터베이스 업데이트
        conn = get_db_connection()
        cur = conn.cursor()

        # 먼저 해당 파일이 현재 사용자의 것인지 확인
        cur.execute('''
            SELECT id FROM uploaded_files
            WHERE filename = %s AND user_id = %s
        ''', (filename, session.get('user_id')))

        file_record = cur.fetchone()

        if not file_record:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': '파일을 찾을 수 없거나 권한이 없습니다.'}), 404

        # 교량 정보 업데이트
        cur.execute('''
            UPDATE uploaded_files
            SET bridge_name = %s, structure_type = %s, span_count = %s,
                length = %s, width = %s, expansion_joint_location = %s,
                upload_date = CURRENT_TIMESTAMP
            WHERE filename = %s AND user_id = %s
        ''', (bridge_name, structure_type, span_count, length, width,
              expansion_joint_location, filename, session.get('user_id')))

        # 업데이트된 행 수 확인
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': '업데이트할 데이터가 없습니다.'}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': '교량 정보가 성공적으로 업데이트되었습니다.',
            'data': {
                'filename': filename,
                'bridge_name': bridge_name,
                'structure_type': structure_type,
                'span_count': span_count,
                'length': length,
                'width': width
            }
        }), 200

    except Exception as e:
        print(f"update_bridge_info 오류: {str(e)}")
        return jsonify({'success': False, 'error': f'서버 오류가 발생했습니다: {str(e)}'}), 500


@api_bp.route('/save_markup_rate', methods=['POST'])
def save_markup_rate():
    """할증율 저장 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        markup_rate = data.get('markup_rate')

        if not filename:
            return jsonify({
                'success': False,
                'error': '파일명이 필요합니다.'
            }), 400

        if markup_rate is None:
            return jsonify({
                'success': False,
                'error': '할증율이 필요합니다.'
            }), 400

        # 할증율 유효성 검사 (0~100% 범위)
        try:
            markup_rate = float(markup_rate)
            if markup_rate < 0 or markup_rate > 100:
                return jsonify({
                    'success': False,
                    'error': '할증율은 0~100% 범위여야 합니다.'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': '유효한 할증율을 입력해주세요.'
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 할증율 업데이트
        cur.execute(
            "UPDATE uploaded_files SET markup_rate = %s WHERE filename = %s AND user_id = %s",
            (markup_rate, filename, session['user_id'])
        )

        if cur.rowcount == 0:
            return jsonify({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'할증율 {markup_rate}%가 저장되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'할증율 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


@api_bp.route('/save_overhead_rate', methods=['POST'])
def save_overhead_rate():
    """제경비율 저장 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        overhead_rate = data.get('overhead_rate')

        if not filename:
            return jsonify({
                'success': False,
                'error': '파일명이 필요합니다.'
            }), 400

        if overhead_rate is None:
            return jsonify({
                'success': False,
                'error': '제경비율이 필요합니다.'
            }), 400

        # 제경비율 유효성 검사 (0~100% 범위)
        try:
            overhead_rate = float(overhead_rate)
            if overhead_rate < 0 or overhead_rate > 100:
                return jsonify({
                    'success': False,
                    'error': '제경비율은 0~100% 범위여야 합니다.'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': '유효한 제경비율을 입력해주세요.'
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 제경비율 업데이트
        cur.execute(
            "UPDATE uploaded_files SET overhead_rate = %s WHERE filename = %s AND user_id = %s",
            (overhead_rate, filename, session['user_id'])
        )

        if cur.rowcount == 0:
            return jsonify({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'제경비율 {overhead_rate}%가 저장되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'제경비율 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


@api_bp.route('/save_subsidiary_cost', methods=['POST'])
def save_subsidiary_cost():
    """부대공사비 저장 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        subsidiary_cost = data.get('subsidiary_cost')

        if not filename:
            return jsonify({
                'success': False,
                'error': '파일명이 필요합니다.'
            }), 400

        if subsidiary_cost is None:
            return jsonify({
                'success': False,
                'error': '부대공사비가 필요합니다.'
            }), 400

        # 부대공사비 유효성 검사 (0 이상)
        try:
            subsidiary_cost = float(subsidiary_cost)
            if subsidiary_cost < 0:
                return jsonify({
                    'success': False,
                    'error': '부대공사비는 0 이상이어야 합니다.'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': '유효한 부대공사비를 입력해주세요.'
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # 부대공사비 업데이트
        cur.execute(
            "UPDATE uploaded_files SET subsidiary_cost = %s WHERE filename = %s AND user_id = %s",
            (subsidiary_cost, filename, session['user_id'])
        )

        if cur.rowcount == 0:
            return jsonify({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'부대공사비 {subsidiary_cost:,.0f}원이 저장되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'부대공사비 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


@api_bp.route('/reload_repair_table', methods=['POST'])
def reload_repair_table():
    """보수물량표 다시 로드 API"""
    conn = None
    cur = None

    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({
                'success': False,
                'error': '파일명이 필요합니다.'
            }), 400

        # 세션에 현재 파일명 설정
        session['current_filename'] = filename

        # 파일 데이터 가져오기
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT file_data FROM uploaded_files WHERE filename = %s AND user_id = %s",
            (filename, session['user_id'])
        )
        result = cur.fetchone()

        if not result:
            return jsonify({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }), 404

        # JSON 데이터를 DataFrame으로 변환
        file_data = result[0]
        if isinstance(file_data, str):
            import json
            file_data = json.loads(file_data)
        df = pd.DataFrame(file_data)

        # DataFrame 데이터 정리
        df = clean_dataframe_data(df)

        # generate_repair_tables 함수를 임시로 import하여 사용
        try:
            import sys
            import os
            # 프로젝트 루트 디렉토리를 파이썬 경로에 추가
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from utils.generate_repair_tables import generate_repair_tables

            # 보수물량표와 개략공사비표 재생성
            repair_html, cost_html, eval_html = generate_repair_tables(df, filename)

            return jsonify({
                'success': True,
                'message': '보수물량표가 다시 로드되었습니다.',
                'repair_html': repair_html,
                'cost_html': cost_html
            })

        except ImportError as e:
            return jsonify({
                'success': False,
                'error': f'보수물량표 생성 함수를 불러올 수 없습니다: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'보수물량표 로드 중 오류가 발생했습니다: {str(e)}'
        }), 500

    finally:
        # 데이터베이스 연결 정리
        if cur:
            cur.close()
        if conn:
            conn.close()


@api_bp.route('/validate_file', methods=['POST'])
def validate_file():
    """파일 검증 API - 개선된 검증 로직 포함"""
    try:
        print("파일 검증 요청 수신")  # 디버깅 로그

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '파일이 선택되지 않았습니다.'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '파일이 선택되지 않았습니다.'
            }), 400

        if not file.filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'error': 'Excel 파일(.xlsx)만 업로드 가능합니다.'
            }), 400

        print(f"검증할 파일: {file.filename}")  # 디버깅 로그


        # 헤더 정규화 적용
        cleaned_file = clean_excel_header_newlines(file)

        # 파일 검증 및 정제
        # df_result = excel_to_clean_df(cleaned_file, file)

        # # 검증 실패 시 오류 반환
        # if hasattr(df_result, 'is_valid'):
        #     # FileValidationResult 객체인 경우 (오류 발생)
        #     error_messages = '<br>'.join(df_result.errors)
        #     flash(f'파일 검증 실패:<br>{error_messages}', 'error')
        #     return redirect(request.url)

        # # 정상적으로 DataFrame과 header_row를 받은 경우
        # df, header_row = df_result

        validation_result = validate_excel_file(cleaned_file,file)
        # df = clean_dataframe_data(df)

        print(f"검증 결과: valid={validation_result.is_valid}, errors={len(validation_result.errors)}")  # 디버깅 로그

        # 검증 결과에 추가적인 상세 정보 포함
        response_data = {
            'success': True,
            'is_valid': validation_result.is_valid,
            'errors': validation_result.errors,
            'warnings': [],  # 경고 메시지 삭제
            'info': validation_result.info
        }

        # 보수완료 필터링 정보 추가
        if 'repair_filtered_count' in validation_result.info:
            filtered_count = validation_result.info['repair_filtered_count']
            if filtered_count > 0:
                response_data['repair_filtered_message'] = f"보수완료로 표기된 {filtered_count}개 행이 자동으로 제외되었습니다."

        # 추가 검증 수행 - 손상물량 계산 검증
        # if validation_result.is_valid:
        #     try:
        #         # import pandas as pd
        #         # file.seek(0)
        #         # df = pd.read_excel(validation_result.df)

        #         # 상세 검증 결과 생성

        #         #detailed_validation = perform_detailed_validation(df)
        #         #response_data['validation_details'] = detailed_validation
        #         #response_data['table_preview'] = generate_table_preview(df)
        #     except Exception as e:
        #         print(f"상세 검증 중 오류: {str(e)}")
        #         response_data['warnings'].append(f"상세 검증 중 오류가 발생했습니다646: {str(e)}")

        # NaN 값을 None으로 변환 (JSON 직렬화 가능하도록)
        import math
        import json

        def convert_nan_to_none(obj):
            """NaN, Infinity 값을 JSON 직렬화 가능한 값으로 변환"""
            if isinstance(obj, dict):
                return {k: convert_nan_to_none(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_nan_to_none(item) for item in obj]
            elif isinstance(obj, float):
                if math.isnan(obj):
                    return None
                elif math.isinf(obj):
                    return None
            return obj

        response_data = convert_nan_to_none(response_data)

        return jsonify(response_data)

    except Exception as e:
        print(f"파일 검증 중 오류: {str(e)}")  # 디버깅 로그
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'파일 검증 중 오류가 발생했습니다: {str(e)}'
        }), 500
