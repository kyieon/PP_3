import pandas as pd
from flask import session
from utils.common import COMPONENT_ORDER, normalize_component, sort_components, get_db_connection, get_circled_number
from utils.evaluation import classify_repair, match_priority, match_unit_price, adjust

# 보수물량표 및 개략공사비표 생성


# 보수물량표 및 개략공사비표 생성
def generate_repair_tables(df, filename):
    conn = get_db_connection()
    cur = conn.cursor()
    repair = None
    repair_html = ""
    cost_html = ""

    # df가 None이 아닌 경우에만 DataFrame 조작 수행
    if df is not None:
        df.loc[df['부재명'].str.contains('받침장치', na=False), '부재명'] = '교량받침'
        print(df['부재명'].unique())


    # 할증율, 제경비율, 부대공사비 가져오기
    cur.execute('''
    SELECT markup_rate, overhead_rate, subsidiary_cost
    FROM uploaded_files
    WHERE filename = %s AND user_id = %s
    ''', (filename, session['user_id']))

    rates_result = cur.fetchone()
    # 할증율, 제경비율, 부대공사비를 float로 변환하여 타입 통일
    markup_rate = float(rates_result[0]) if rates_result and rates_result[0] is not None else 20.0
    overhead_rate = float(rates_result[1]) if rates_result and rates_result[1] is not None else 50.0
    subsidiary_cost = float(rates_result[2]) if rates_result and rates_result[2] is not None else 0.0

    cur.execute('''
    SELECT COUNT(*)
    FROM file_damage_details
    WHERE user_id = %s AND filename = %s
    ''', (session['user_id'], filename))

    count = cur.fetchone()[0]

    if count > 0:
        # ✅ 해당 조건에 맞는 데이터가 존재할 때 실행할 코드
        print(f"{count}개의 보수물량 데이터가 존재합니다.")
        # 예: 업데이트나 출력 처리
    else:
        print("해당 사용자 파일에 대한 데이터가 존재하지 않습니다.")
        # 예: 새로 계산하거나



    # [1] df가 주어진 경우: 계산 및 생성 (손상내용명에 '받침' 또는 '전단키' 포함 시 교량받침으로 분류)
    if df is not None:
        # 손상내용명에 '받침' 또는 '전단키'가 포함된 경우 교량받침으로 분류
        df_repair = df.copy()
        bearing_damage_mask = (df_repair['손상내용'].str.contains('받침', na=False) |
                              df_repair['손상내용'].str.contains('전단키', na=False))

        # 교량받침으로 분류될 데이터의 부재명을 교량받침으로 변경
        df_repair.loc[bearing_damage_mask, '부재명'] = '교량받침'
        # 부재명이 '받침장치'인 경우도 교량받침으로 치환
        #수정사항 0818
        unique_components = sort_components(df_repair['부재명'].unique())
        df_repair = df_repair[df_repair['부재명'].isin(unique_components)]

        repair = df_repair.groupby(['부재명', '손상내용', '단위'])[['손상물량', '개소']].sum().reset_index()
        repair['보수방안'] = repair['손상내용'].apply(classify_repair)
        repair['우선순위'] = repair.apply(lambda row: match_priority(row['손상내용'], repair_method=row['보수방안']), axis=1)
        repair['단가'] = repair['손상내용'].apply(match_unit_price)
        # 보수방안이 '주의관찰'인 경우 단가를 0으로 설정
        repair.loc[repair['보수방안'] == '주의관찰', '단가'] = 0

        # 데이터 타입 변환 및 검증
        repair['손상물량'] = pd.to_numeric(repair['손상물량'], errors='coerce')
        repair = repair.dropna(subset=['손상물량'])  # NaN 제거

        # 보수물량 계산 (안전율 1.2 적용, 할증율 전달)
        try:
            repair['보수물량'] = repair.apply(
                lambda row: adjust(row, markup_rate ),
                axis=1
            )
        except Exception as e:
            print(f"보수물량 계산 오류: {e}")
            print(f"DataFrame 열: {repair.columns.tolist()}")
            print(f"데이터 샘플:\n{repair.head()}")
            # 기본값으로 대체
            repair['보수물량'] = repair['손상물량'] * 1.2

        # 할증율을 적용한 개략공사비 계산 (데이터 타입 통일)
        # 모든 숫자 컬럼을 float로 변환하여 안전한 연산 보장
        repair['보수물량_notAdd'] = repair['보수물량'].copy()
        #repair['적용할증율'] = repair['단위'].apply(lambda x: 0 if x in ['ea', 'EA', '개소'] else (markup_rate if x is not None else markup_rate))
        #repair['보수물량'] = (repair['보수물량'] * (1 + repair['적용할증율'] / 100)).round(2)

        repair['단가'] = pd.to_numeric(repair['단가'], errors='coerce')
        repair['개략공사비'] = (repair['보수물량'] * repair['단가'] ).round(0)

    if count > 0:
        # [2] df가 없을 경우 DB에서 불러오기
        cur.execute('''
            SELECT component_name, damage_description, repair_method, priority, damage_quantity,
                repair_quantity, count, unit_price, estimated_cost, unit
            FROM file_damage_details
            WHERE user_id = %s AND filename = %s
        ''', (session['user_id'], filename))
        rows = cur.fetchall()
        columns = ['부재명', '손상내용', '보수방안', '우선순위', '손상물량', '보수물량', '개소', '단가', '개략공사비', '단위']
        if rows:
            repair = pd.DataFrame(rows, columns=columns)
            # 할증율을 적용한 보수물량 재계산
            repair['보수물량_notAdd'] = pd.to_numeric(repair['보수물량'], errors='coerce')  # 할증율 적용 전 원본

            # 단위별 할증율 적용
            #repair['적용할증율'] = repair['단위'].apply(lambda x: 0 if x in ['ea', 'EA', '개소'] else markup_rate)
            #repair['보수물량'] = (repair['보수물량'] * (1 + repair['적용할증율'] / 100)).round(2)

            # 데이터 타입 변환 및 검증
            repair['손상물량'] = pd.to_numeric(repair['손상물량'], errors='coerce')
            repair = repair.dropna(subset=['손상물량'])  # NaN 제거

            #보수물량 재계산
            try:
                repair['보수물량'] = repair.apply(
                    lambda row: adjust(row, markup_rate ),
                    axis=1
                )
            except Exception as e:
                print(f"DB 보수물량 계산 오류: {e}")
                print(f"DataFrame 열: {repair.columns.tolist()}")
                # 기본값으로 대체
                repair['보수물량'] = repair['손상물량'] * 1.2

            repair['단가'] = pd.to_numeric(repair['단가'], errors='coerce')
            repair['개략공사비'] = (repair['보수물량'] * repair['단가']).round(0)
        else:
            cur.close()
            conn.close()
            return "", "", "<p>📭 저장된 데이터가 없습니다.</p>"

    cur.close()
    conn.close()

    # repair가 None인 경우 처리
    if repair is None:
        return "", "", "<p>📭 데이터가 없습니다.</p>"

    # [3] 보수물량표 생성
    repair_html += f'''<div style="padding:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <label for="repairMethodSelect" style="margin:0;">보수방안:</label>
                <select id="repairMethodSelect" style="width:150px; padding:5px;">
                    <option value="">보수방안 선택</option>
                </select>
                <label for="unitPriceInput" style="margin:0;">단가:</label>
                <input type="number" id="unitPriceInput" placeholder="단가 입력" style="width:120px; padding:5px;">
                <button type="button" id="updateUnitPriceBtn" class="btn btn-primary" style="padding:5px 10px;">단가 일괄 수정</button>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <label style="width:100px" for="markup_rate">할증율 : </label>
                <input type="number" id="markup_rate" value="{markup_rate}" min="0" max="100" step="0.1" style="width:80px; text-align:center;"/> %
                <input type="button" class="btn btn-secondary" value="할증율 저장" onclick="saveMarkupRate('{filename}')"/>
                <input type="button" class="btn btn-secondary" value="보수물량표 저장" onclick="saveCostTable()"/>
            </div>
        </div>
        <div style="background-color:#e3f2fd; border:1px solid #2196f3; border-radius:4px; padding:8px; text-align:center; color:#1976d2; font-size:14px;">
            <i class="fas fa-info-circle" style="margin-right:5px;"></i>
            보수물량표 수정하고 보수물량표 저장 버튼을 눌러야 개략공사비표에 반영됩니다.
        </div>
    </div>'''
    repair_html += '<div class="table-container repair-table"><table class="table-striped"><thead><tr>'
    repair_html += '<th>부재명</th><th>손상내용</th><th>단위</th><th>손상물량</th><th>보수물량</th><th>개소</th>'
    repair_html += '<th>보수방안</th><th>우선순위</th><th>단가</th><th>개략공사비</th></tr></thead><tbody>'

    repair['부재명_순서'] = repair['부재명'].apply(lambda x: COMPONENT_ORDER.index(normalize_component(x)) if normalize_component(x) in COMPONENT_ORDER else len(COMPONENT_ORDER))


    repair=repair.sort_values('부재명_순서').drop('부재명_순서', axis=1)

    for idx, row in repair.iterrows():
        repair_html += f'''
        <tr>
            <td>{row["부재명"]}</td>
            <td>{row["손상내용"]}</td>
            <td>{row["단위"]}</td>
            <td>{row["손상물량"]:.2f}</td>
            <td notadd="{row["보수물량_notAdd"]:.2f}">{row["보수물량"]:.2f}</td>
            <td>{int(row["개소"])}</td>
            <td><input type="text" class="form-control repair-method" name="repair_method_{idx}" value="{row["보수방안"]}"></td>
            <td><input type="text" class="form-control priority" name="priority_{idx}" value="{row["우선순위"]}"></td>
            <td><input type="number" class="form-control unit-price" name="unit_price_{idx}" value="{int(row["단가"])}" step="1"></td>
            <td class="total-cost" style="text-align:right">{int(row["개략공사비"]):,}</td>
        </tr>
        '''

    repair_html += '</tbody></table></div>'

    # [4] 개략공사비 요약표
    filtered = repair[repair['보수방안'] != '주의관찰'].copy()
    result = filtered.groupby(['부재명', '보수방안', '우선순위'], dropna=False).agg({
        '보수물량': 'sum',
        '개소': 'sum',
        '손상내용': lambda x: ', '.join(sorted(set(x))),
        '단가': 'first',
        '개략공사비': 'sum'
    }).reset_index()

    result['부재명_순서'] = result['부재명'].apply(lambda x: COMPONENT_ORDER.index(normalize_component(x)) if normalize_component(x) in COMPONENT_ORDER else len(COMPONENT_ORDER))
    result = result.sort_values('부재명_순서').drop('부재명_순서', axis=1)

    cost_html += '<div class="table-container cost-table"><table class="table-striped"><thead><tr>'
    cost_html += '<th>부재명</th><th>손상내용</th><th>보수방안</th><th>우선순위</th><th>보수물량</th><th>개소</th><th>단가</th><th>개략공사비</th></tr></thead><tbody>'

    total_cost = 0
    for _, row in result.iterrows():
        cost_html += f'''
        <tr>
            <td>{row["부재명"]}</td>
            <td>{row["손상내용"]}</td>
            <td>{row["보수방안"]}</td>
            <td>{row["우선순위"]}</td>
            <td>{row["보수물량"]:.2f}</td>
            <td>{int(row["개소"])}</td>
            <td class="cost-amount">{int(row["단가"]):,}</td>
            <td class="cost-amount">{int(row["개략공사비"]):,}</td>
        </tr>
        '''
        total_cost += row["개략공사비"]

    # 총계 및 우선순위 요약
    cost_html += f'''
        <tr class="table-primary">
            <td colspan="7" class="text-end"><strong>총계</strong></td>
            <td class="cost-amount"><strong id="costTotal_text">{int(total_cost):,}</strong></td>
        </tr>
        </tbody></table></div>
    '''

    cost_html += '<div style="display: flex; justify-content: space-between; align-items: center;"> <h4 class="mt-4">우선순위별 공사비 요약</h4>'



    cost_html += '   <div>    <span>부대공:<input '
    cost_html += '              type="text" '
    cost_html += '              id="subsidiary_cost" '
    cost_html += f'              value="{subsidiary_cost:,.0f}" '
    cost_html += '              placeholder="부대공사비를 입력하세요" '
    cost_html += '              style="width:200px; text-align:center;" '
    cost_html += '            />원'
    cost_html += '            <button '
    cost_html += '              type="button" style="width:100px; margin-left:4px;padding:0px" '
    cost_html += '              class="btn btn-secondary form-control" '

    cost_html += '              onkeypress="return isNumber(event)" '
    cost_html += '              oninput="formatNumberInput(this)" '
    cost_html += '              onclick="saveSubsidiaryCost(window.currentFilename)" '
    cost_html += '            > 부대공 저장 '
    cost_html += '            </button> </span>'

    cost_html += '       <span>제경비: <input '
    cost_html += '              type="number" '
    cost_html += '              id="overhead_rate" '
    cost_html += f'              value="{ overhead_rate:.0f}" '
    cost_html += '              min="0" '
    cost_html += '              max="1000" '
    cost_html += '              step="0.1" '
    cost_html += '              placeholder="제경비율을 입력하세요" '
    cost_html += '              style="width:80px; text-align:center;" '
    cost_html += '            />%'
    cost_html += '            <button '
    cost_html += '              type="button" style="width:100px; margin-left:4px;padding:0px" '
    cost_html += '              class="btn btn-secondary form-control" '
    cost_html += '              onclick="saveOverheadRate(window.currentFilename)" '
    cost_html += '            > 재경비 저장 '
    cost_html += '            </button> </span> </div></div>'



    cost_html += '<table id="cost_sum" class="table table-striped"><thead><tr>'
    cost_html += f'<th>우선순위</th><th>순공사비</th><th>제경비'
    cost_html += f' ({overhead_rate}%)</th><th>전체 공사비</th></tr></thead><tbody>'

    total_sum = 0
    overhead_ratio = overhead_rate / 100  # 백분율을 소수로 변환
    for prio, amount in result.groupby('우선순위')['개략공사비'].sum().items():
        soft = int(amount)
        indirect = int(soft * overhead_ratio)
        total = soft + indirect
        total_sum += total
        prio_circled = get_circled_number(int(prio))
        cost_html += f'<tr><td>{prio_circled}</td><td style="text-align:right;">{int(soft):,}</td><td style="text-align:right;">{int(indirect):,}</td><td style="text-align:right;">{int(total):,}</td></tr>'


    cost_html += f'<tr><td>부대공사비</td><td></td>'

    cost_html += f'<td style="text-align:right;">가설 안전 환경 실시설계등</td>'
    cost_html += f'<td style="text-align:right;">{int(subsidiary_cost):,}</td>'


    cost_html += '</tr>'


    # 총괄 개략공사비 = 우선순위별 공사비 합계 + 부대공사비
    final_total = total_sum + subsidiary_cost
    cost_html += f'''
        <tr class="table-primary">
            <td><strong>총괄 개략공사비</strong></td>
            <td></td><td> 우선순위(① + ② + ③) + 부대공사비</td>
            <td style="text-align:right;"><strong>{int(final_total):,}</strong></td>
        </tr>
        </tbody></table>
    '''

    # 상태평가표는 삭제됨

    return repair_html, cost_html, ""
