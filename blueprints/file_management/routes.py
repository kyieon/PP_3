"""
파일 관리 관련 라우트
"""
import json
import pandas as pd
from flask import request, render_template, jsonify, session, flash, redirect, url_for
from utils.common import get_db_connection, clean_dataframe_data, sort_components, normalize_component, COMPONENT_ORDER
from utils.damage_utils import natural_sort_key
from utils.pivot_detail_view import pivot_detail_view
from utils.evaluation import evaluate_slab_condition
from . import file_management_bp

# 원본 generate_repair_tables 함수 import를 위한 임시 해결책
try:
    import sys
    import os
    # 프로젝트 루트 디렉토리를 파이썬 경로에 추가
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from utils.generate_repair_tables import generate_repair_tables
except ImportError as e:
    print(f"generate_repair_tables import 실패: {e}")
    # 대체 함수 정의
    def generate_repair_tables(df, filename):
        return "<p>보수 데이터 로딩 중...</p>", "<p>비용 데이터 로딩 중...</p>", "<p>평가 데이터 로딩 중...</p>"


def login_required(f):
    """로그인 필요 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def console_logdf(df):
    import os
    # DEBUG 환경변수가 설정되어 있거나 Flask 디버그 모드일 때만 실행
    if os.environ.get('DEBUG') == 'True' or os.environ.get('FLASK_DEBUG') == '1':
        if '원본부재명' in df.columns:
            for component in df['원본부재명'].unique():
                component_df = df[df['원본부재명'] == component]
                print(f"\n[{component}] - {len(component_df)}개 데이터")
                print(component_df.to_string(index=True, max_cols=None, max_colwidth=15))
                print("-" * 40)
        else:
            print("[DEBUG] '원본부재명' 컬럼이 없습니다.")



@file_management_bp.route('/view_file/<filename>')
@login_required
def view_file(filename, pivot=False):
    """파일 보기"""
    conn = get_db_connection()
    cur = conn.cursor()
    session['current_filename'] = filename

    try:
        cur.execute(
            "SELECT file_data FROM uploaded_files WHERE filename = %s AND user_id = %s",
            (filename, session['user_id'])
        )
        result = cur.fetchone()

        if not result:
            flash('파일을 찾을 수 없습니다.')
            return redirect(url_for('main.index'))

        # JSON 데이터를 DataFrame으로 변환
        file_data = result[0]
        if isinstance(file_data, str):
            file_data = json.loads(file_data)
        df = pd.DataFrame(file_data)
        console_logdf(df)

        # DataFrame 데이터 정리 및 trim 처리
        df = clean_dataframe_data(df)

        # 부재명 정렬
        unique_components = sort_components(df['부재명'].unique())
        df = df[df['부재명'].isin(unique_components)]

        # 데이터 처리 및 HTML 생성
        detail_html = ""
        detail_html_header_link = "aaaaa"
        overall_html = ""
        repair_html = ""
        cost_html = ""

        detail_html, detail_html_header_link = pivot_detail_view(filename, pivot=True, detail=False)

        # [2] 전체 집계표 생성 (손상내용명에 '받침' 또는 '전단키' 포함 시 교량받침으로 분류)
        # 손상내용명에 '받침' 또는 '전단키'가 포함된 경우 교량받침으로 분류
        df_overall = df.copy()
        bearing_damage_mask = (df_overall['손상내용'].str.contains('받침', na=False) |
                              df_overall['손상내용'].str.contains('전단키', na=False))

        # 교량받침으로 분류될 데이터의 부재명을 교량받침으로 변경
        df_overall.loc[bearing_damage_mask, '부재명'] = '교량받침'

        overall = df_overall.groupby(['부재명', '손상내용', '단위'])[['손상물량', '개소']].sum().reset_index()
        overall['손상물량'] = overall['손상물량'].round(2)

        # 부재명 순서대로 정렬
        overall['부재명_순서'] = overall['부재명'].apply(lambda x: COMPONENT_ORDER.index(normalize_component(x)) if normalize_component(x) in COMPONENT_ORDER else len(COMPONENT_ORDER))
        overall = overall.sort_values('부재명_순서').drop('부재명_순서', axis=1)

        overall_html += '<div id="overall-table-header" class="table-container overall-table"><table class="table-striped">'
        overall_html += ' <thead>'
        overall_html += ' <tr style="text-align: right;">'
        overall_html += ' <th style="width: 150px;" >부재명</th>'
        overall_html += ' <th style="width: 300px;" >손상내용</th>'
        overall_html += ' <th style="width: 150px;">단위</th>'
        overall_html += ' <th style="width: 150px;">손상물량</th>'
        overall_html += ' <th style="width: 150px;">개소</th>'
        overall_html += ' </tr>'
        overall_html += ' </thead>'
        overall_html += '</tbody></table></div>'

        # 데이터 행 생성
        overall_html += '<div class="table-container overall-table"><table id="overall-table" class="table-striped"><thead>'
        overall_html += ' <tr style="display:none" id="overall-print-table-header" style="text-align: right;">'
        overall_html += ' <th style="width: 150px;" >부재명</th>'
        overall_html += ' <th style="width: 300px;" >손상내용</th>'
        overall_html += ' <th style="width: 150px;">단위</th>'
        overall_html += ' <th style="width: 150px;">손상물량</th>'
        overall_html += ' <th style="width: 150px;">개소</th>'
        overall_html += ' </tr>'

        for _, row in overall.iterrows():
            overall_html += '<tr>'
            overall_html += f'<td style="width: 150px;">{row["부재명"]}</td>'
            overall_html += f'<td style="width: 300px;">{row["손상내용"]}</td>'
            overall_html += f'<td style="width: 150px;">{row["단위"]}</td>'
            overall_html += f'<td style="width: 150px;">{row["손상물량"]}</td>'
            overall_html += f'<td style="width: 150px;">{row["개소"]}</td>'
            overall_html += '</tr>'

        overall_html += '</tbody></table></div>'
        overall_html += "</div>"

        repair_html, cost_html, eval_html = generate_repair_tables(df, filename)

        # 할증율과 제경비율 가져오기
        cur.execute('''
        SELECT markup_rate, overhead_rate
        FROM uploaded_files
        WHERE filename = %s AND user_id = %s
        ''', (filename, session['user_id']))

        rates_result = cur.fetchone()
        markup_rate = float(rates_result[0]) if rates_result and rates_result[0] is not None else 20.0
        overhead_rate = float(rates_result[1]) if rates_result and rates_result[1] is not None else 50.0

        # 바닥판 평가
        slab_df = df[df['부재명'] == '바닥판'].copy()
        slab_eval_table = []

        for pos in sorted(slab_df['부재위치'].unique(), key=natural_sort_key):
            sub = slab_df[slab_df['부재위치'] == pos]

            # 점검면적 컬럼이 있는 경우에만 계산, 없으면 0
            if '점검면적' in sub.columns:
                area = sub['점검면적'].sum()
            else:
                area = 0

            # 폭 컬럼이 있는 경우에만 균열폭 계산
            if '폭' in sub.columns:
                crack_width_raw = sub[sub['손상내용'].str.contains('균열', na=False)]['폭'].max()
                # 문자열을 float로 변환 (안전하게 처리)
                if pd.isna(crack_width_raw):
                    crack_width = None
                else:
                    try:
                        crack_width = float(crack_width_raw)
                    except (ValueError, TypeError):
                        crack_width = None
            else:
                crack_width = None

            crack_ratio = sub[sub['손상내용'].str.contains('균열', na=False)]['손상물량'].sum()
            leak_ratio = sub[sub['손상내용'].str.contains('백태|누수', na=False)]['손상물량'].sum()
            surface_damage_ratio = sub[sub['손상내용'].str.contains('박락|파손|재료분리|층분리', na=False)]['손상물량'].sum()
            rebar_ratio = sub[sub['손상내용'].str.contains('철근부식', na=False)]['손상물량'].sum()

            # NaN 값을 None으로 변환하여 evaluate_slab_condition에 전달
            grade = evaluate_slab_condition(
                crack_width=crack_width,
                crack_ratio=None if pd.isna(crack_ratio) or crack_ratio == 0 else crack_ratio,
                leak_ratio=None if pd.isna(leak_ratio) or leak_ratio == 0 else leak_ratio,
                surface_damage_ratio=None if pd.isna(surface_damage_ratio) or surface_damage_ratio == 0 else surface_damage_ratio,
                rebar_corrosion_ratio=None if pd.isna(rebar_ratio) or rebar_ratio == 0 else rebar_ratio
            )

            slab_eval_table.append({
                "구분": pos,
                "점검면적": round(area, 1),
                "균열폭": crack_width if not pd.isna(crack_width) else '-',
                "균열율": round(crack_ratio, 2) if crack_ratio > 0 else '-',
                "백태": round(leak_ratio, 2) if leak_ratio > 0 else '-',
                "표면손상": round(surface_damage_ratio, 3) if surface_damage_ratio > 0 else '-',
                "철근부식": round(rebar_ratio, 2) if rebar_ratio > 0 else '-',
                "등급": grade
            })

        return render_template(
            'index_re.html',
            active_tab=request.args.get('tab', 'detail'),
            detail_html=detail_html,
            detail_html_header_link=detail_html_header_link,
            overall_html=overall_html,
            repair_html=repair_html,
            cost_html=cost_html,
            file_data=file_data,
            slab_eval_table=slab_eval_table,
            error_message=None,
            filename=filename,
            markup_rate=markup_rate,
            overhead_rate=overhead_rate
        )

    except Exception as e:
        flash(f'파일을 불러오는 중 오류가 발생했습니다: {str(e)}')
        return redirect(url_for('main.index'))
    finally:
        cur.close()
        conn.close()


@file_management_bp.route('/delete_file/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """파일 삭제"""
    # TODO: 기존 delete_file 로직을 이곳으로 이동
    return jsonify({'success': True})


@file_management_bp.route('/update_file_damage_details', methods=['POST'])
@login_required
def update_file_damage_details():
    data = request.get_json()
    user_id = session['user_id']
    username = session.get('username', 'unknown')
    filename = session.get('current_filename', 'unnamed_file')  # 현재 열람 중인 파일명

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ 기존 데이터 삭제
        cur.execute('''
            DELETE FROM file_damage_details
            WHERE user_id = %s AND filename = %s
        ''', (user_id, filename))

        # ✅ 새 데이터 삽입
        for key, detail in data.items():
            cur.execute('''
                INSERT INTO file_damage_details (
                    user_id, username, filename,unit,
                    component_name, damage_description,
                    repair_method, priority,damage_quantity,
                    repair_quantity, count, unit_price, estimated_cost
                ) VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s,%s, %s, %s, %s)
            ''', (
                user_id,
                username,
                filename,
                detail["unit"],
                detail["component"],
                detail["damage"],
                detail["method"],
                detail["priority"],
                detail["damage_quantity"],
                detail["quantity"],
                detail["count"],
                detail["unitPrice"],
                detail["totalCost"]
            ))


        conn.commit()

        repair_html, cost_htmlxxxx, _ = generate_repair_tables(None,filename)

        return jsonify({"message": "보수물량 저장 완료","repair_html":repair_html,"cost_html":cost_htmlxxxx})

    except Exception as e:
        print("업데이트 오류:", e)
        conn.rollback()
        return jsonify({"message": "오류 발생", "error": str(e)}), 500

    finally:
        cur.close()
        conn.close()
