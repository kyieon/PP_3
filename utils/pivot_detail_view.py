import json
import random
import re

from flask import flash, redirect, session, url_for
import pandas as pd
from static.data.damage_solutions import damage_solutions
from utils.common import classify_repair, get_db_connection, normalize_damage, sort_components, clean_dataframe_data
from utils.damage_utils import natural_sort_key
from utils.damage_ai_generator import get_damage_solution
from bs4 import BeautifulSoup

from utils.file_validation import normalize_component_source


def natural_sort_key_positions(positions):
    """부재위치를 자연 정렬 (s1, s2, s3... s10, s11... 순서로)"""
    import re
    def sort_key(position):
        parts = re.split(r'(\d+)', str(position))
        return [int(part) if part.isdigit() else part.lower() for part in parts]
    return sorted(positions, key=sort_key)


def merge_girder_positions_for_pivot(group):
    """거더 내부/외부 데이터를 통합"""
    merged_data = []
    position_map = {}

    for _, row in group.iterrows():
        position = row['부재위치']
        # s1i, s1o -> s1으로 통합
        base_position = re.sub(r'[io]$', '', str(position))

        if base_position not in position_map:
            position_map[base_position] = {
                '부재명': row['부재명'],
                '부재위치': base_position,
                '손상내용': row['손상내용'],
                '단위': row.get('단위', ''),
                '손상물량': 0,
                '개소': 0,
                '점검면적': row.get('점검면적', 0)
            }

        # 데이터 통합
        position_map[base_position]['손상물량'] += row['손상물량']
        position_map[base_position]['개소'] += row['개소']
        position_map[base_position]['점검면적'] = max(
            position_map[base_position]['점검면적'],
            row.get('점검면적', 0)
        )

    # DataFrame으로 변환
    for data in position_map.values():
        merged_data.append(data)

    return pd.DataFrame(merged_data)


COMPONENT_ORDER = [
    "바닥판", "슬래브",
    "거더", "주형",
    "가로보", "세로보", "격벽",
    "교대",
    "교각",
    "교량받침",
    "신축이음", "신축",
    "교면포장", "포장",
    "배수시설", "배수구",
    "난간", "연석", "방호벽", "방호울타리", "중대", "방음벽", "방음판",
    "점검시설", "점검", "점검계단"
]

def sort_components(components):
    def component_key(name):
        for idx, keyword in enumerate(COMPONENT_ORDER):
            if keyword in name:
                return idx
        return len(COMPONENT_ORDER)
    return sorted(components, key=component_key)


def pivot_detail_view(filename, pivot,detail=True):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT file_data FROM uploaded_files WHERE filename = %s AND user_id = %s",
        (filename, session['user_id'])
    )
    result = cur.fetchone()

    if not result:
        flash('파일을 찾을 수 없습니다.')
        return redirect(url_for('index'))

    # JSON 데이터를 DataFrame으로 변환
    file_data = result[0]
    if isinstance(file_data, str):
        file_data = json.loads(file_data)
    df = pd.DataFrame(file_data)

    # DataFrame 데이터 정리 및 trim 처리
    df = clean_dataframe_data(df)
    crack_cols = [col for col in df.columns if col.startswith('균열폭')]
    # 균열폭 처리 로직
    if detail:
        # detail=True: 균열폭 포함하여 표시
        df['손상내용'] = df['손상내용'].str.replace(r'\(([\d.]+㎜)미만\)', r'(\1)', regex=True)
        df['손상내용'] = df['손상내용'].str.replace(r'\(([\d.]+㎜)이상\)', r'(\1)', regex=True)

        # '균열폭'으로 시작하는 컬럼 찾기

        if crack_cols:
            if '부재위치' in df.columns:
                df['정규화부재명'] = df.apply(lambda row: normalize_component_source(row['부재명'], row['부재위치']), axis=1)
            else:
                df['정규화부재명'] = df['부재명'].apply(normalize_component_source)
            crack_col = crack_cols[0]  # 첫 번째 '균열폭' 컬럼 사용
            # mask_not_sqm = df['단위'] != '㎡'
            # df.loc[mask_not_sqm, '손상내용'] = df.loc[mask_not_sqm, '손상내용'].str.replace(r'\(([\d.]+㎜)미만\)', r'(\1)', regex=True)
            # df.loc[mask_not_sqm, '손상내용'] = df.loc[mask_not_sqm, '손상내용'].str.replace(r'\(([\d.]+㎜)이상\)', r'(\1)', regex=True)



            # 균열 세분화 조건:
            # 1. 손상명이 '균열' 또는 '균열부 백태' 관련 (보수부 균열, 보수부 재균열, 균열/백태, 보수부 균열부 백태, 보수부 균열/백태 등)
            # 2. 단위가 'm'
            # 3. 누수가 포함되지 않은 경우 제외 (균열부 누수/백태, 균열/누수/백태, 균열부 백태/누수 등)

            # 누수가 포함되지 않은 균열 관련 손상
            # 적용된 조건:

            # ✅ 손상명에 '균열'이 포함됨 (균열, 보수부 균열, 보수부 재균열, 균열/백태, 보수부 균열부 백태, 보수부 균열/백태 등 모두 포함)
            # ✅ '누수'가 포함되지 않음 (균열부 누수/백태, 균열/누수/백태, 균열부 백태/누수 등 제외)
            # ✅ 단위가 'm'
            # ✅ 균열폭 데이터가 존재함
            # 처리 결과:

            # 위 조건을 모두 만족하는 행만 '균열(균열폭값mm)' 형식으로 변환됩니다.
            # 예: '보수부 균열' + 단위 'm' + 균열폭 0.3 → '균열(0.3mm)'
            # 예: '균열/백태' + 단위 'm' + 균열폭 0.5 → '균열(0.5mm)'
            # 제외: '균열부 누수/백태' (누수 포함이므로 변환 안됨)
            # 제외: '균열' + 단위 '㎡' (단위가 m가 아니므로 변환 안됨)

            crack_related = df['손상내용'].str.contains(r'균열', na=False, regex=True)
            not_contain_leakage = ~df['손상내용'].str.contains(r'누수', na=False, regex=True)
            is_m_unit = df['단위'] == 'm'
            has_crack_width = df[crack_col].notna()

            # 균열 세분화 적용 가능 부재 리스트 (정규화된 부재명 source 기준)
            allowed_components = ['slab', 'girder', 'crossbeam', 'abutment', 'pier', 'foundation', 'bearing', 'railing']
            is_allowed_component = df['정규화부재명'].apply(lambda x: any(comp in str(x) for comp in allowed_components))

            # 균열 세분화 마스크: 균열 관련 + 누수 없음 + m 단위 + 균열폭 있음 + 허용된 부재
            crack_subdivision_mask = crack_related & not_contain_leakage & is_m_unit & has_crack_width & is_allowed_component
            df['손상내용'] = df['손상내용'].str.replace(r'\([^)]*\)', '', regex=True).str.strip()
            # 균열 세분화 적용
            df.loc[crack_subdivision_mask, '손상내용'] = df['손상내용'] + '(' + df.loc[crack_subdivision_mask, crack_col].astype(str) + 'mm)'



    # else:
    #     # 균열폭이 있는 데이터중 균열이 포함된 경우
    #     # crack_col >0.3 이상인 경우
    #     if crack_cols:
    #         crack_col = crack_cols[0]  # 첫 번째 '균열폭' 컬럼 사용
    #         mask = df['손상내용'].str.contains(r'균열', na=False) & df[crack_col].notna() & (df[crack_col] >= 0.3)
    #         df.loc[mask, '손상내용'] = '균열(0.3mm이상)'
    #         # crack_col >0.3 미만인 경우
    #         mask = df['손상내용'].str.contains(r'균열', na=False) & df[crack_col].notna() & (df[crack_col] < 0.3)
    #         df.loc[mask, '손상내용'] = '균열(0.3mm미만)'

    #     # detail=False: 손상내용을 원래 형태 그대로 유지
    #     # 균열폭 정보가 포함된 손상내용을 변경하지 않음
    #     #pass




    # 손상내용명에 '받침' 또는 '전단키'가 포함된 경우 부재명을 '교량받침'으로 변경
    bearing_damage_mask = (df['손상내용'].str.contains('받침', na=False) |
                          df['손상내용'].str.contains('전단키', na=False))



    # 해당 데이터의 부재명을 '교량받침'으로 변경
    df.loc[bearing_damage_mask, '부재명'] = '교량받침'
    df.loc[df['부재명'].str.contains('받침장치', na=False), '부재명'] = '교량받침'

    # 원본 부재명 사용 (원본부재명 컬럼이 있으면 사용, 없으면 부재명 사용)
    if '원본부재명' in df.columns:
        display_name_col = '원본부재명'  # 화면 표시용은 원본부재명
        group_by_col = '원본부재명'  # 원본 부재명으로 그룹화
    else:
        display_name_col = '부재명'
        group_by_col = '부재명'

    # 부재명 정렬
    unique_components = sort_components(df[group_by_col].unique())
    df = df[df[group_by_col].isin(unique_components)]

    # 데이터 처리 및 HTML 생성
    detail_html = ""
    detail_html_header_link = ""
    for name in unique_components:
        group = df[df[group_by_col] == name]
        if group.empty:
            continue

        # 거더인 경우 내부/외부 데이터 통합
        #if '거더' in name:
        #    group = merge_girder_positions_for_pivot(group)
        #    if group.empty:
        #        continue

        header1 = '부재위치'
        colum1 = '손상내용'
        if pivot:
            header1 = '손상내용'
            colum1 = '부재위치'

        # 자연 정렬 적용
        header1_value = natural_sort_key_positions(group[header1].unique())
        colum1_value = natural_sort_key_positions(group[colum1].unique())  # 경간 데이터도 자연 정렬

        columns = pd.MultiIndex.from_product(
            [header1_value, ['손상물량', '개소']],
        )
        table = pd.DataFrame('', index=colum1_value, columns=columns)

        # 모든 손상물량 합계
        total_dmg_sum = 0
        total_cnt_sum = 0

        for dmg in colum1_value:
            sub = group[group[colum1] == dmg]

            for pos in header1_value:
                match = sub[sub[header1] == pos]

                if not match.empty:
                    dmg_val = round(match['손상물량'].sum(), 2)
                    cnt_val = int(match['개소'].sum())
                    table.loc[dmg, (pos, '손상물량')] = dmg_val
                    table.loc[dmg, (pos, '개소')] = cnt_val
                else:
                    table.loc[dmg, (pos, '손상물량')] = "-"
                    table.loc[dmg, (pos, '개소')] = "-"

            # 위치별 중복 제거 후 합산
            total_dmg = sub.groupby(header1)['손상물량'].sum().sum()
            total_cnt = sub.groupby(header1)['개소'].sum().sum()

            table.loc[dmg, ('합계', '손상물량')] = round(total_dmg, 2)
            table.loc[dmg, ('합계', '개소')] = str(int(total_cnt))

            total_dmg_sum += total_dmg
            total_cnt_sum += total_cnt

        # 단위 값 처리
        try:
            if pivot:
                # 피봇이 활성화된 경우 (손상내용이 컬럼이 됨)
                unit_values = []
                for pos in header1_value:
                    damage_rows = group[group['손상내용'] == pos]
                    if not damage_rows.empty and '단위' in damage_rows.columns:
                        unit_values.append(damage_rows['단위'].values[0])
                    else:
                        unit_values.append('')
            else:
                # 피봇이 비활성화된 경우 (부재위치가 컬럼이 됨)
                unit_values = []
                for dmg in colum1_value:
                    damage_rows = group[group['손상내용'] == dmg]
                    if not damage_rows.empty and '단위' in damage_rows.columns:
                        unit_values.append(damage_rows['단위'].values[0])
                    else:
                        unit_values.append('')
        except Exception as e:
            # 오류 발생 시 빈 값으로 채움
            print(f"단위 값 처리 중 오류 발생: {e}")
            unit_values = ['' for _ in range(len(header1_value) if pivot else len(colum1_value))]

        # 열 이름 리스트 추출
        col_list = list(table.columns)

        # '합계' 관련 컬럼 중 '손상물량'이 있는 첫 위치 찾기
        sum_idx = next((i for i, col in enumerate(col_list)
                        if isinstance(col, tuple) and col[0] == '합계' and col[1] == '손상물량'), len(col_list))
        # 해당 위치에 단위 열 삽입
        if not pivot:
           table.insert(sum_idx, '단위', unit_values)

        # 부재명과 손상내용 열 삽입
        table.insert(0, '부재명', [name] * len(colum1_value))

        if pivot:
            table.insert(1, '경간', colum1_value)
        else:
            table.insert(1, '손상내용', colum1_value)

        # 비어 있는 셀은 - 처리
        table = table.fillna("-")

        table.loc['합계', :] = ['합계'] * len(table.columns)

        for pos in header1_value:
            pos_dmg_sum = 0
            pos_cnt_sum = 0
            for dmg in colum1_value:
                dmg_val = table.loc[dmg, (pos, '손상물량')]
                cnt_val = table.loc[dmg, (pos, '개소')]

                if dmg_val != "-" and dmg_val != "":
                    pos_dmg_sum += float(dmg_val)
                if cnt_val != "-" and cnt_val != "":
                    pos_cnt_sum += int(cnt_val)

            table.loc['합계', (pos, '손상물량')] = round(pos_dmg_sum, 2)
            table.loc['합계', (pos, '개소')] = int(pos_cnt_sum)

        # 전체 합계 칸
        table.loc['합계', ('합계', '손상물량')] = round(total_dmg_sum, 2)
        table.loc['합계', ('합계', '개소')] = int(total_cnt_sum)

        html_table = table.to_html(classes='table-bordered table-striped', index=False, border=0, justify='left')

        soup = BeautifulSoup(html_table, "html.parser")
        rows = soup.find_all('tr')

        first_td = rows[2].find('td')
        first_td['rowspan'] = str(len(table))
        for tr in rows[3:]:
            tr.find('td').decompose()

        # 첫 번째 행의 th 셀들을 가져옵니다.
        first_row_ths = rows[0].find_all("th")

        # 첫 번째 열(th)을 병합
        first_th = first_row_ths[0]
        first_th['rowspan'] = 2

        # 두 번째 열(th)을 병합
        second_th = first_row_ths[1]
        second_th['rowspan'] = 2
        if not pivot:
            end_th = first_row_ths[len(first_row_ths)-2]
            end_th['rowspan'] = 2

        # 두 번째 행의 해당 열(th)들을 제거
        second_row_ths = rows[1].find_all("th")
        second_row_ths[0].decompose()
        second_row_ths[1].decompose()

        if not pivot:
            second_row_ths[len(second_row_ths)-3].decompose()

        html_table = str(soup)
        if pivot:
            soup = BeautifulSoup(html_table, "html.parser")
            rows = soup.find_all('tr')

            first_row_ths = [th for th in rows[1].find_all("th") if "손상물량" in th.get_text(strip=True)]
            i = 0
            z = 0

            for th in first_row_ths[0:len(first_row_ths)-1]:
                header_text = th.get_text(strip=True)
                unit = unit_values[i]
                th.string = f"{header_text} ({unit})"

                #if z % 2 == 0:  # i가 짝수일 때
                i += 1
                z += 1
            html_table = str(soup)

        # 손상내용별 개소수 집계
        damage_counts = group.groupby('손상내용')['개소'].sum().to_dict()

        # 개소수가 포함된 손상내용 텍스트 생성
        damage_texts = []
        for damage, count in damage_counts.items():
            if count > 0:
                damage_texts.append(f"{damage} {int(count)}개소")
            else:
                damage_texts.append(damage)

        damage_text = ', '.join(damage_texts)
        # 원본 부재명 사용
        display_name = group[display_name_col].iloc[0] if not group.empty else name
        summary = f"<p class='observation-summary'>{display_name}에 대한 외관조사결과에서 조사된 바와 같이, {damage_text} 등의 손상이 조사되었다.</p>"
        #detail_html_header_link += f"<a href=\"#header_{name}\">🔗 {name} </a>"
        # ...existing code...
        # 원본 부재명 사용
        display_name = group[display_name_col].iloc[0] if not group.empty else name

        # 첫 번째 부재(바닥판)인 경우 탭 네비게이션으로 이동하도록 특별 처리
        if name == unique_components[0]:  # 첫 번째 부재
            detail_html_header_link += (
                f'<a href="#tab-navigation" '
                'class="btn btn-outline-primary btn-sm m-1" '
                'style="background-color:#1976d2; color:#fff; border:none;">'
                f'{display_name}</a>'
            )
        else:
            detail_html_header_link += (
                f'<a href="#header_{name}" '
                'class="btn btn-outline-primary btn-sm m-1" '
                'style="background-color:#1976d2; color:#fff; border:none;">'
                f'{display_name}</a>'
            )

        #detail_html += f"<h4 id=\"header_{name}\">📌 부재명: {name}</h4>{summary}"

        # ...existing code...
        # ...existing code...
        detail_html += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<h4 id="header_{name}" style="margin-bottom:0; scroll-margin-top:150px;">📌 부재명: {name}</h4>'
            f''
            f'</div>'
            f'{summary}'
        )
# ...existing code...
        # ...existing code...

        detail_html += "<style>table.table-bordered { margin-left: 0 !important; width: auto !important; } table.table-bordered td { text-align: center !important; }</style><div class='table-container' >"
        detail_html += html_table
        detail_html += "</div><br>"
        # 손상내용별 설명 추가
        detail_html += "<h5>🛠 손상별 원인 및 대책방안</h5><ul>"

        for dmg in group['손상내용'].unique():
            repair_method = classify_repair(dmg)
            detail_html += f"<p><strong>🔸 손상내용: {dmg} (보수방안: {repair_method})</strong></p><ul>"
            try:
                # 손상내용 정규화 (띄어쓰기 제거 및 유사어 처리)
                normalized_dmg = normalize_damage(dmg)

                # 균열 관련 처리
                if '균열' in normalized_dmg and not any(x in normalized_dmg for x in ['백태', '누수', '부']):
                    # 균열 크기 패턴 확인 (숫자 + mm 또는 ㎜, cw 등 접두사와 등호 포함)
                    if re.search(r'균열\(?[a-zA-Z]*=?[\d.]+(mm|㎜)', normalized_dmg):
                        # 균열로 처리
                        formatted_solution = get_damage_solution("균열", name, repair_method)
                        formatted_solution = formatted_solution.replace("■ ", "")  # "■ " 제거
                        detail_html += f"<li>{formatted_solution}</li>"
                    else:
                        # 일반 균열 처리
                        formatted_solution = get_damage_solution("균열", name, repair_method)
                        formatted_solution = formatted_solution.replace("■ ", "")  # "■ " 제거
                        detail_html += f"<li>{formatted_solution}</li>"
                else:
                    # 다른 손상 유형 처리 (damage_solutions에 없는 경우 AI로 생성)
                    formatted_solution = get_damage_solution(normalized_dmg, name, repair_method)
                    formatted_solution = formatted_solution.replace("■ ", "")  # "■ " 제거
                    detail_html += f"<li>{formatted_solution}</li>"
            except Exception:
                pass
            detail_html += "</ul>"
            detail_html += "<hr>"

        detail_html += "</ul>"

    return detail_html, detail_html_header_link


def generate_crack_subdivision_view(df):
    """균열 세분화 뷰 생성 - 기존 테이블 형태 유지하면서 균열만 세분화"""
    try:
        # 부재별 집계표 생성 (기존 방식)
        unique_components = sort_components(df['부재명'].unique())
        html_output = ""

        for component in unique_components:
            component_df = df[df['부재명'] == component]

            if component_df.empty:
                continue

            # 원본 부재명 사용
            if '원본부재명' in df.columns:
                display_name = component_df['원본부재명'].iloc[0] if not component_df.empty else component
            else:
                display_name = component

            # 손상내용별 집계
            damage_summary = component_df.groupby(['손상내용', '단위'])[['손상물량', '개소']].sum().reset_index()

            # 부재위치별 정렬
            try:
                positions = sorted(component_df['부재위치'].unique(), key=natural_sort_key)
            except NameError:
                positions = sorted(component_df['부재위치'].unique())

            html_output += f'<h4>{display_name}</h4>'
            html_output += '<div class="table-container">'
            html_output += '<table class="table table-striped">'

            # 헤더 생성 - 균열 헤더만 세분화
            html_output += '<thead><tr>'
            html_output += '<th>손상내용</th><th>단위</th>'

            for pos in positions:
                html_output += f'<th colspan="2">{pos}</th>'

            html_output += '<th colspan="2">합계</th>'
            html_output += '</tr>'

            # 서브헤더
            html_output += '<tr><th></th><th></th>'
            for pos in positions:
                html_output += '<th>손상물량</th><th>개소</th>'
            html_output += '<th>손상물량</th><th>개소</th>'
            html_output += '</tr></thead>'

            html_output += '<tbody>'

            # 데이터 행 생성 - 균열만 세분화 처리
            for _, damage_row in damage_summary.iterrows():
                damage_type = damage_row['손상내용']
                unit = damage_row['단위']

                # 균열인 경우 세분화하여 여러 행으로 표시
                if '균열' in damage_type:
                    crack_subdivisions = subdivide_crack_data(component_df, damage_type, positions)

                    for sub_damage, sub_data in crack_subdivisions.items():
                        if sub_data['total_quantity'] > 0 or sub_data['total_count'] > 0:
                            html_output += '<tr>'
                            html_output += f'<td>{sub_damage}</td><td>{unit}</td>'

                            for pos in positions:
                                pos_quantity = sub_data['positions'].get(pos, {}).get('quantity', 0)
                                pos_count = sub_data['positions'].get(pos, {}).get('count', 0)

                                if pos_quantity > 0 or pos_count > 0:
                                    html_output += f'<td>{pos_quantity:.2f}</td><td>{pos_count}</td>'
                                else:
                                    html_output += '<td>-</td><td>-</td>'

                            # 합계 데이터 추가
                            html_output += f'<td><strong>{sub_data["total_quantity"]:.2f}</strong></td><td><strong>{sub_data["total_count"]}</strong></td>'
                            html_output += '</tr>'
                else:
                    # 균열이 아닌 경우 기존 방식 그대로
                    html_output += '<tr>'
                    html_output += f'<td>{damage_type}</td><td>{unit}</td>'

                    total_quantity = 0
                    total_count = 0

                    for pos in positions:
                        pos_data = component_df[
                            (component_df['손상내용'] == damage_type) &
                            (component_df['부재위치'] == pos)
                        ]

                        if not pos_data.empty:
                            quantity = pos_data['손상물량'].sum()
                            count = pos_data['개소'].sum()
                            html_output += f'<td>{quantity:.2f}</td><td>{count}</td>'
                            total_quantity += quantity
                            total_count += count
                        else:
                            html_output += '<td>-</td><td>-</td>'

                    # 합계
                    html_output += f'<td><strong>{total_quantity:.2f}</strong></td><td><strong>{total_count}</strong></td>'
                    html_output += '</tr>'

            html_output += '</tbody></table></div>'

            # 개소수가 포함된 손상내용 요약 텍스트 추가
            damage_counts = component_df.groupby('손상내용')['개소'].sum().to_dict()
            damage_texts = []
            for damage, count in damage_counts.items():
                if count > 0:
                    damage_texts.append(f"{damage} {int(count)}개소")
                else:
                    damage_texts.append(damage)

            damage_text = ', '.join(damage_texts)
            summary = f"<p class='observation-summary'>{display_name}에 대한 외관조사결과에서 조사된 바와 같이, {damage_text} 등의 손상이 조사되었다.</p>"
            html_output += summary + '<br>'

        return html_output

    except Exception as e:
        print(f"generate_crack_subdivision_view 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<p>균열 세분화 처리 중 오류가 발생했습니다: {str(e)}</p>"


def subdivide_crack_data(component_df, original_damage_type, positions):
    """균열 데이터를 세분화하여 리턴"""
    crack_subdivisions = {
        '균열(0.1mm)': {'total_quantity': 0, 'total_count': 0, 'positions': {}},
        '균열(0.2mm)': {'total_quantity': 0, 'total_count': 0, 'positions': {}},
        '균열(0.3mm)': {'total_quantity': 0, 'total_count': 0, 'positions': {}},
        '균열(0.4mm)': {'total_quantity': 0, 'total_count': 0, 'positions': {}},
        '균열(0.5mm이상)': {'total_quantity': 0, 'total_count': 0, 'positions': {}}
    }

    # 해당 손상내용에 해당하는 데이터 필터링
    crack_data = component_df[component_df['손상내용'] == original_damage_type]

    for _, row in crack_data.iterrows():
        # 손상내용에서 균열폭 추출
        crack_width = extract_crack_width(row['손상내용'])

        # 균열폭에 따라 분류
        if crack_width <= 0.1:
            category = '균열(0.1mm)'
        elif crack_width <= 0.2:
            category = '균열(0.2mm)'
        elif crack_width <= 0.3:
            category = '균열(0.3mm)'
        elif crack_width <= 0.4:
            category = '균열(0.4mm)'
        else:
            category = '균열(0.5mm이상)'

        position = row['부재위치']
        quantity = float(row['손상물량'])
        count = int(row['개소'])

        # 데이터 누적
        crack_subdivisions[category]['total_quantity'] += quantity
        crack_subdivisions[category]['total_count'] += count

        if position not in crack_subdivisions[category]['positions']:
            crack_subdivisions[category]['positions'][position] = {'quantity': 0, 'count': 0}

        crack_subdivisions[category]['positions'][position]['quantity'] += quantity
        crack_subdivisions[category]['positions'][position]['count'] += count

    return crack_subdivisions


def extract_crack_width(damage_description):
    """손상내용에서 균열폭 추출"""
    # 기존 균열 분류에 따라 반환
    if '균열(0.3mm미만)' in damage_description or '균열(0.3㏼미만)' in damage_description:
        return 0.2  # 0.3mm 미만은 0.2mm로 처리
    elif '균열(0.3mm이상)' in damage_description or '균열(0.3㏼이상)' in damage_description:
        return 0.3  # 0.3mm 이상은 0.3mm로 처리

    # 정규식으로 균열폭 추출
    width_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:mm|㏼)',  # 숫자mm 또는 숫자㏼
        r'(\d+(?:\.\d+)?)\s*(?:m[mM])',     # 숫자mM
        r'(パ|파)\s*(\d+(?:\.\d+)?)' # 파 + 숫자
    ]

    for pattern in width_patterns:
        match = re.search(pattern, damage_description)
        if match:
            try:
                if 'パ' in pattern or '파' in pattern:
                    return float(match.group(2))
                else:
                    return float(match.group(1))
            except (ValueError, IndexError):
                continue

    # 기본값 반환 (균열이라는 단어만 있는 경우)
    return 0.15  # 기본값을 0.15mm로 수정하여 0.2mm 범위에 포함되도록 설정
