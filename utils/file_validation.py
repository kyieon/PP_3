"""
파일 검증 유틸리티 모듈
Excel 파일의 구조와 데이터를 검증합니다.
"""

import pandas as pd
import re
import numpy as np
from typing import Dict, List, Tuple, Any
from utils.common import clean_dataframe_data, get_db_connection
from tabulate import tabulate

# 부재명 키워드 캐시 (모듈 레벨)
_component_keywords_cache = None

def load_component_keywords():
    """DB에서 부재명 메타 키워드를 로드 (한 번만 실행)"""
    global _component_keywords_cache

    if _component_keywords_cache is not None:
        return _component_keywords_cache

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT TRIM(keyword), source FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s ORDER BY LENGTH(TRIM(keyword)) DESC", ('200075',))
        keywords = cur.fetchall()
        cur.close()
        conn.close()

        _component_keywords_cache = keywords
        print(f"[FILE_VALIDATION] 부재명 키워드 {len(keywords)}개 로드 완료")
        return keywords
    except Exception as e:
        print(f"[FILE_VALIDATION] 부재명 키워드 로드 실패: {str(e)}")
        return []

class FileValidationResult:
    """파일 검증 결과를 담는 클래스"""

    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.info = {}
        self.df = None  # 검증에 사용된 DataFrame 저장용

    def add_error(self, message: str):
        """오류 메시지 추가"""
        console.log(f"검증 오류 추가: {message}")  # 디버깅 로그
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """경고 메시지 추가"""
        console.log(f"검증 경고 추가: {message}")  # 디버깅 로그
        self.warnings.append(message)

    def add_info(self, key: str, value: Any):
        """정보 추가"""
        console.log(f"검증 정보 추가: {key} = {value}")  # 디버깅 로그
        self.info[key] = value

def validate_excel_file(file_content, file) -> FileValidationResult:
    """
    Excel 파일 검증

    Args:
        file_content: 업로드된 파일 내용

    Returns:
        FileValidationResult: 검증 결과
    """
    result = FileValidationResult()


    try:
        df_result = excel_to_clean_df(file_content, file)
        if isinstance(df_result, FileValidationResult):
            # 에러 상황: 오류 메시지 반환
            return df_result
        df, header_row = df_result

        #result.df = df  # FileValidationResult에 DataFrame 저장
        #result.add_info('df', df.to_dict(orient='records'))  # 이렇게 변환해서 넣으세요.  # info에도 포함(선택)

        console.log(f"파일 읽기 완료: {len(df)}행, {len(df.columns)}열, 헤더 행: {header_row+1}")  # 디버깅 로그
        # 데이터 전처리 - 문자열 컬럼의 앞뒤 공백 제거
        string_columns = ['부재명', '부재위치', '손상내용', '단위','길이','너비','폭']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                console.log(f"{col} 컬럼 공백 제거 완료")  # 디버깅 로그
        # 기본 정보 추가
        result.add_info('total_rows', len(df))
        result.add_info('total_columns', len(df.columns))
        result.add_info('header_row', header_row+1)

        # 보수완료 필터링 정보 추가
        if 'filtered_count' in locals():
            result.add_info('repair_filtered_count', filtered_count)
        # 1. 필수 컬럼 검증 (이미 위에서 체크됨)
        console.log("필수 컬럼 검증 통과")  # 디버깅 로그

        # 2. 데이터 타입 검증
        result = validate_data_types(df, result)

        # 3. 데이터 값 검증
        result = validate_data_values(df, result)

        # 4. 부재명 및 손상내용 검증
        result = validate_component_and_damage(df, result)

        # 5. 상세 손상물량 검증 수행
        console.log("[FILE_VALIDATION] 필수 컬럼 데이터 미리보기:")
        console.log(tabulate(df.head(1000), headers='keys', tablefmt='psql', showindex=True))
        detailed_validation = perform_damage_quantity_validation(df)
        result.add_info('validation_details', detailed_validation)

        # 6. 테이블 미리보기 생성 (오류 행 하이라이트 포함)
        table_preview = generate_table_preview_with_highlighting(df, detailed_validation.get('error_rows', []))
        result.add_info('table_preview', table_preview)

        # 7. 통계 정보 생성
        result = generate_statistics(df, result)

        console.log(f"검증 완료: valid={result.is_valid}, errors={len(result.errors)}, warnings={len(result.warnings)}")  # 디버깅 로그

    except Exception as e:
        console.log(f"검증 중 오류 발생: {str(e)}")  # 디버깅 로그
        result.add_error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

    return result



def remove_korean(text):
    """문자열에서 한글 제거"""
    if pd.isna(text):
        return text
    import re
    # 한글 제거 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
    text_without_korean = re.sub(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', '', str(text))
    return text_without_korean.strip()

def clean_damage_content(text):
    """손상내용에서 불필요한 접두어 제거 (균열로 시작하는 경우 cw, CW 등 제거)"""
    if pd.isna(text):
        return text
    import re
    text = str(text).strip()

    # "균열"로 시작하는 경우에만 cw 제거
    if text.startswith('균열'):
        # cw, CW, Cw, cW 제거 (대소문자 구분 없이)
        #text = re.sub(r'\bcw\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'cw\s*', '', text, flags=re.IGNORECASE)
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

    return text

def filter_repair_completed_rows(df, file_content):
    """
    엑셀 파일에서 '보수완료'가 표기된 행을 제외하고 필터링

    Args:
        df: 현재 DataFrame
        file_content: 원본 엑셀 파일 내용

    Returns:
        filtered_df: 필터링된 DataFrame
        filtered_count: 제외된 행 수
    """
    try:
        # 원본 엑셀 파일을 다시 읽어서 모든 컬럼 확인
        full_df = pd.read_excel(file_content, header=None)

        # '보수완료' 관련 키워드들
        repair_keywords = ['보수완료', '보수 완료']

        # 비고 열이나 다른 열에서 보수완료 키워드 찾기
        repair_rows = set()

        # 모든 행과 열을 검사
        for row_idx in range(len(full_df)):
            for col_idx in range(len(full_df.columns)):
                cell_value = str(full_df.iloc[row_idx, col_idx]).strip()

                # 보수완료 키워드가 포함된 경우
                for keyword in repair_keywords:
                    if keyword in cell_value:
                        repair_rows.add(row_idx)
                        break

        # DataFrame의 실제 데이터 행 인덱스와 매핑
        # (헤더 행 이후의 데이터만 고려)
        header_row = 0  # 기본값
        for i in range(6):  # 헤더 탐색 범위
            temp_df = pd.read_excel(file_content, header=i)
            if '부재명' in temp_df.columns:
                header_row = i
                break

        data_start_row = header_row + 1
        filtered_indices = []

        # 현재 DataFrame의 각 행이 원본에서 제외되어야 하는지 확인
        for df_idx in range(len(df)):
            original_row_idx = data_start_row + df_idx

            # 해당 행이 보수완료 행에 포함되지 않은 경우만 유지
            if original_row_idx not in repair_rows:
                filtered_indices.append(df_idx)

        # 필터링된 DataFrame 생성
        filtered_df = df.iloc[filtered_indices].reset_index(drop=True)
        filtered_count = len(df) - len(filtered_df)

        console_log(f"보수완료 필터링 완료: {filtered_count}개 행 제외, {len(filtered_df)}개 행 유지")

        return filtered_df, filtered_count

    except Exception as e:
        console_log(f"보수완료 필터링 중 오류 발생: {str(e)}")
        # 오류 발생 시 원본 DataFrame 반환
        return df, 0

def normalize_component_name(text, remove_text=""):
    """부재명을 DB의 메타 키워드와 비교하여 표준 부재명으로 변경"""
    if pd.isna(text) or str(text).strip() == '':
        return text

    text = str(text).strip()
    original_text = text  # 원본 텍스트 저장

    try:
        # 캐시된 키워드 사용 (한 번만 DB 조회)
        keywords = load_component_keywords()

        # 공백 제거 (예: "바닥판 상면 S1" → "바닥판상면S1")
        text_no_space = text.replace(' ', '')

        # 각 키워드와 비교 (LIKE 검색 - 키워드가 부재명에 포함되어 있는지)
        for keyword, source in keywords:
            if keyword and keyword.strip():
                keyword_no_space = keyword.strip().replace(' ', '')
                # 공백 제거한 부재명에 키워드가 포함되어 있으면 source(표준 부재명)로 변경
                if keyword_no_space in text_no_space:
                    console_log(f"부재명 정규화: '{original_text}' → '{source}' (키워드: '{keyword}')")
                    return keyword

        # 매칭되는 키워드가 없으면 공백 제거한 텍스트 반환
        if text_no_space != original_text:
            console_log(f"부재명 공백 제거: '{original_text}' → '{text_no_space}'")
        return text_no_space.replace(remove_text, '')

    except Exception as e:
        console_log(f"부재명 정규화 중 오류: {str(e)}")
        # 오류 발생 시 공백 제거한 텍스트 반환
        return text.replace(' ', '')


def normalize_component_source(text, remove_text=""):
    """부재명을 DB의 메타 키워드와 비교하여 표준 부재명으로 변경"""
    if pd.isna(text) or str(text).strip() == '':
        return text

    text = str(text).strip()
    original_text = text  # 원본 텍스트 저장

    try:
        # 캐시된 키워드 사용 (한 번만 DB 조회)
        keywords = load_component_keywords()

        # 공백 제거 (예: "바닥판 상면 S1" → "바닥판상면S1")
        text_no_space = text.replace(' ', '')

        # 각 키워드와 비교 (LIKE 검색 - 키워드가 부재명에 포함되어 있는지)
        for keyword, source in keywords:
            if keyword and keyword.strip():
                keyword_no_space = keyword.strip().replace(' ', '')
                # 공백 제거한 부재명에 키워드가 포함되어 있으면 source(표준 부재명)로 변경
                if keyword_no_space in text_no_space:
                    console_log(f"부재명 정규화: '{original_text}' → '{source}' (키워드: '{keyword}')")
                    return source

        # 매칭되는 키워드가 없으면 공백 제거한 텍스트 반환
        if text_no_space != original_text:
            console_log(f"부재명 공백 제거: '{original_text}' → '{text_no_space}'")
        return text_no_space.replace(remove_text, '')

    except Exception as e:
        console_log(f"부재명 정규화 중 오류: {str(e)}")
        # 오류 발생 시 공백 제거한 텍스트 반환
        return text.replace(' ', '')

def excel_to_clean_df(file_content,file_original, required_columns=None, header_search_rows=6):
    """
    엑셀 파일에서 필수 컬럼만 추출하여 정제된 DataFrame 반환
    Args:
        file_content: 업로드된 파일 내용
        required_columns: 필수 컬럼 리스트 (기본값: ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위'])
        header_search_rows: 헤더 탐색 행 수 (기본 6)
    Returns:
        df: 정제된 DataFrame
        header_row: 사용된 헤더 행 (최대값)
    """
    console.log("Excel 파일 검증 시작")  # 디버깅 로그
    result = FileValidationResult()


        # 엑셀 파일 헤더가 컬럼별로 서로 다른 행에 있을 경우 처리
        # 1. 헤더 후보 행에서 필수 컬럼 위치 탐색
    required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']

    # OPTIONAL 컬럼 정의 (별칭 포함)
    optional_columns = {
        '길이': ['길이', '길이(m)', 'L', 'length', '연장'],
        '너비': ['너비', '너비(m)', 'W', 'width', 'B'],
        '균열폭': ['폭','균열', '균열폭']
    }

    header_candidates = []
    for i in range(6):
        temp_df = pd.read_excel(file_content, header=i)
        header_candidates.append(temp_df.columns)

    col_header_map = {}

    # 필수 컬럼 매핑 (딕셔너리 형태로 통일)
    for col in required_columns:
        for idx, cols in enumerate(header_candidates):
            if col in cols:
                col_header_map[col] = {'header_row': idx, 'actual_name': col}
                break

    if len(col_header_map) < len(required_columns):
        result.add_error("필수 컬럼 헤더가 1~6행 내에 모두 존재하지 않습니다.")
        return result

    # OPTIONAL 컬럼 매핑 (별칭 중 하나라도 발견되면 추가)
    for standard_name, aliases in optional_columns.items():
        for idx, cols in enumerate(header_candidates):
            for col_name in cols:
                for alias in aliases:
                    # 컬럼명에 alias가 포함되어 있으면 매칭
                    if alias in str(col_name):
                        col_header_map[standard_name] = {'header_row': idx, 'actual_name': col_name}
                        break
                if standard_name in col_header_map:
                    break
            if standard_name in col_header_map:
                break

    # 2. 헤더의 최대 행 번호 찾기 (실제 데이터는 이 다음 행부터 시작)
    max_header_row = max(info['header_row'] for info in col_header_map.values())
    console_log(f"최대 헤더 행: {max_header_row+1}, 데이터 시작 행: {max_header_row+2}")

    # 3. 헤더 없이 전체 엑셀 읽기
    full_df = pd.read_excel(file_content, header=None)
    org_df = pd.read_excel(file_original, header=None)

    # 4. 각 컬럼의 데이터 추출 (모두 동일한 행 범위에서)
    col_data = {}
    col_data_org = {}
    data_start_row = max_header_row + 1  # 데이터 시작 행 (0-based index)

    # 필수 컬럼 데이터 추출
    for col in required_columns:
        col_info = col_header_map[col]
        header_row = col_info['header_row']
        actual_name = col_info['actual_name']

        # 해당 헤더가 있는 행에서 컬럼 인덱스 찾기
        header_row_data = full_df.iloc[header_row]
        col_idx = None
        for idx, val in enumerate(header_row_data):
            if str(val).strip() == actual_name:
                col_idx = idx
                break

        if col_idx is not None:
            # 데이터 시작 행부터 해당 컬럼의 데이터 추출
            if(col =='손상내용'):
                data_series = org_df.iloc[data_start_row:, col_idx].reset_index(drop=True)
            else:
                data_series = full_df.iloc[data_start_row:, col_idx].reset_index(drop=True)
        else:
            data_series = pd.Series(dtype=object)

        col_data[col] = data_series


    # OPTIONAL 컬럼 데이터 추출
    for col in optional_columns.keys():
        if col in col_header_map:
            col_info = col_header_map[col]
            header_row = col_info['header_row']
            actual_name = col_info['actual_name']

            # 해당 헤더가 있는 행에서 컬럼 인덱스 찾기
            header_row_data = full_df.iloc[header_row]
            col_idx = None
            for idx, val in enumerate(header_row_data):
                if str(val).strip() == actual_name:
                    col_idx = idx
                    break

            if col_idx is not None:
                # 데이터 시작 행부터 해당 컬럼의 데이터 추출
                data_series = full_df.iloc[data_start_row:, col_idx].reset_index(drop=True)
            else:
                data_series = pd.Series(dtype=object)

            col_data[col] = data_series

    # 5. DataFrame 생성
    df = pd.DataFrame(col_data)
    df['라인'] = range(data_start_row + 1, data_start_row + len(df) + 1)  # +1은 1-based 및 헤더 고려

    # NaN 값을 적절한 기본값으로 처리
    # 숫자형 컬럼은 0으로, 문자형 컬럼은 빈 문자열로 처리
    numeric_columns = ['길이', '너비', '균열폭']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 문자형 컬럼은 빈 문자열로 처리
    string_columns = ['부재명', '부재위치','손상내용' ,'단위']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].fillna('')



    # 필수 컬럼(부재명, 개소 등)이 비어있거나 잘못된 경우 행 스킵
    def is_valid_row(row):
        # 부재명, 개소가 모두 비어있거나 nan이면 제외
        bjm = str(row['부재명']).strip() if pd.notna(row['부재명']) else ''
        gs = str(row['개소']).strip() if pd.notna(row['개소']) else ''
        if bjm == '' or gs == '':
            return False  # 제외
        # 부재명에 숫자만 들어가면 제외
        if bjm.isdigit():
            return False  # 제외
        return True
    df = df[df.apply(is_valid_row, axis=1)].reset_index(drop=True)

    # 부재위치에서 한글 제거 (먼저 처리)
    if '부재위치' in df.columns:
        df['부재위치'] = df['부재위치'].apply(remove_korean)
        console_log("부재위치에서 한글 제거 완료")

    # 원본 부재명 저장
    if '부재명' in df.columns:
        df['원본부재명'] = df['부재명'].copy()
        console_log("원본 부재명 저장 완료")

    # 부재명 정규화 (DB 메타 키워드와 비교하여 표준 부재명으로 변경, 부재위치 텍스트 제거)
    if '부재명' in df.columns and '부재위치' in df.columns:
        # 각 행을 개별적으로 처리
        for idx, row in df.iterrows():
            if str(row['부재명']).strip() == '방호벽':
                original_name = row['부재명']
                normalized_name = normalize_component_name(row['부재명'], row['부재위치'])
                df.at[idx, '부재명'] = normalized_name
                print(f"방호벽 정규화: 행 {idx+1}, '{original_name}' -> '{normalized_name}'")

        # 전체 부재명 정규화 적용
        df['부재명'] = df.apply(lambda row: normalize_component_name(row['부재명'], row['부재위치']), axis=1)
        console_log("부재명 정규화 완료 (부재위치 텍스트 제거 포함)")
    elif '부재명' in df.columns:
        df['부재명'] = df['부재명'].apply(normalize_component_name)
        console_log("부재명 정규화 완료")

    # 손상내용에서 불필요한 접두어 제거 (cw, CW 등)
    if '손상내용' in df.columns:
        df['손상내용'] = df['손상내용'].apply(clean_damage_content)
        console_log("손상내용에서 불필요한 접두어 제거 완료")

    # 헤더 행 번호는 이미 max_header_row에 저장됨
    header_row = max_header_row
    console_log(f"사용된 최대 헤더 행: {header_row+1}, 유효 데이터 행: {len(df)}")  # 디버깅 로그
    # 필수 컬럼 위치를 테이블 형태로 콘솔에 출력
    try:
        console.log("[FILE_VALIDATION] 필수 컬럼 데이터 미리보기:")
        console.log(tabulate(df.head(1000), headers='keys', tablefmt='psql', showindex=True))
    except ImportError:
        console.log("[FILE_VALIDATION] tabulate 미설치 - 기본 출력")
        console.log(df.head(10))
    #return
    # 이후 데이터 정리 및 검증 로직...
    # DataFrame 데이터 정리 및 trim 처리
    df = clean_dataframe_data(df)

    # 보수완료 행 필터링 적용
    df, filtered_count = filter_repair_completed_rows(df, file_content)

    if filtered_count > 0:
        console_log(f"보수완료로 표기된 {filtered_count}개 행이 제외되었습니다.")

    return df, header_row


def validate_data_types(df: pd.DataFrame, result: FileValidationResult) -> FileValidationResult:
    """데이터 타입 검증"""
    console.log("데이터 타입 검증 시작")  # 디버깅 로그

    # 손상물량 검증
    try:
        damage_quantity = pd.to_numeric(df['손상물량'], errors='coerce')
        invalid_quantity_count = damage_quantity.isna().sum()

        if invalid_quantity_count > 0:
            result.add_error(f"손상물량에 숫자가 아닌 값이 {invalid_quantity_count}개 있습니다.")

        # 음수 검증
        negative_count = (damage_quantity < 0).sum()
        if negative_count > 0:
            result.add_error(f"손상물량에 음수 값이 {negative_count}개 있습니다.")

    except Exception as e:
        result.add_error(f"손상물량 검증 중 오류: {str(e)}")

    # 개소 검증
    try:
        count_values = pd.to_numeric(df['개소'], errors='coerce')
        invalid_count_count = count_values.isna().sum()

        if invalid_count_count > 0:
            result.add_error(f"개소에 숫자가 아닌 값이 {invalid_count_count}개 있습니다.")

        # 음수 검증
        negative_count = (count_values < 0).sum()
        if negative_count > 0:
            result.add_error(f"개소에 음수 값이 {negative_count}개 있습니다.")

    except Exception as e:
        result.add_error(f"개소 검증 중 오류: {str(e)}")

    console.log("데이터 타입 검증 완료")  # 디버깅 로그
    return result

def validate_data_values(df: pd.DataFrame, result: FileValidationResult) -> FileValidationResult:
    """데이터 값 검증"""
    console.log("데이터 값 검증 시작")  # 디버깅 로그

    # 빈 값 검증
    empty_component = df['부재명'].isna() | (df['부재명'] == '')
    empty_position = df['부재위치'].isna() | (df['부재위치'] == '')
    empty_damage = df['손상내용'].isna() | (df['손상내용'] == '')

    if empty_component.sum() > 0:
        result.add_error(f"부재명이 비어있는 행이 {empty_component.sum()}개 있습니다.")

    if empty_position.sum() > 0:
        result.add_error(f"부재위치가 비어있는 행이 {empty_position.sum()}개 있습니다.")

    if empty_damage.sum() > 0:
        result.add_error(f"손상내용이 비어있는 행이 {empty_damage.sum()}개 있습니다.")

    # 단위 검증 (경고 대신 오류로 처리)
    valid_units = ['m', 'mm', 'm²', '㎡', 'm2', 'cm', 'ea', 'EA', '개소', '개', '식', 'set']
    invalid_units = df[~df['단위'].isin(valid_units)]['단위'].unique()

    if len(invalid_units) > 0:
        result.add_error(f"지원되지 않는 단위가 사용되었습니다: {', '.join(invalid_units)}")

    console.log("데이터 값 검증 완료")  # 디버깅 로그
    return result

def validate_component_and_damage(df: pd.DataFrame, result: FileValidationResult) -> FileValidationResult:
    """부재명 및 손상내용 검증"""
    console.log("부재명 및 손상내용 검증 시작")  # 디버깅 로그

    # 표준 부재명 목록
    standard_components = [
        '바닥판', '거더', '가로보', '세로보', '격벽',
        '교대', '교각', '기초', '받침', '신축이음',
        '교면포장', '배수시설', '난간', '방호벽'
    ]

    # 부재명 검증 - 공백 제거 후 unique 확인
    unique_components = df['부재명'].dropna().unique()
    console.log(f"유니크 부재명 개수: {len(unique_components)}")  # 디버깅 로그

    non_standard_components = []

    for component in unique_components:
        if pd.isna(component) or str(component).strip() == '':
            non_standard_components.append('빈값 또는 NaN')
        else:
            cleaned_component = str(component).strip()
            is_standard = any(std in cleaned_component for std in standard_components)
            if not is_standard:
                non_standard_components.append(cleaned_component)

    # 경고 메시지 삭제됨 - 표준 부재명이 아니어도 오류로 처리하지 않음

    # 손상내용 키워드 검증 - 경고 메시지 삭제
    console.log("부재명 및 손상내용 검증 완료")  # 디버깅 로그
    return result

def generate_statistics(df: pd.DataFrame, result: FileValidationResult) -> FileValidationResult:
    """통계 정보 생성"""
    console.log("통계 정보 생성 시작")  # 디버깅 로그

    try:
        # 부재별 통계는 삭제됨 - 부재별 데이터 수 표시하지 않음

        # 손상내용별 통계 - 상위 10개만
        damage_stats = df['손상내용'].value_counts().head(10).to_dict()
        result.add_info('damage_count', damage_stats)

        # 부재위치별 통계
        position_stats = df['부재위치'].value_counts().to_dict()
        result.add_info('position_count', position_stats)

        # 중복 부재명 확인 (공백 차이로 인한)
        component_duplicates = check_component_duplicates(df)
        if component_duplicates:
            result.add_warning(f"띄어쓰기 차이로 인한 중복 부재명 발견: {component_duplicates}")
            result.add_info('duplicate_components', component_duplicates)

        # 손상물량 통계
        damage_quantity = pd.to_numeric(df['손상물량'], errors='coerce').fillna(0)
        result.add_info('total_damage_quantity', float(damage_quantity.sum()))
        result.add_info('average_damage_quantity', float(damage_quantity.mean()))

        # 개소 통계
        count_values = pd.to_numeric(df['개소'], errors='coerce').fillna(0)
        result.add_info('total_count', int(count_values.sum()))
        result.add_info('average_count', float(count_values.mean()))

        console.log("통계 정보 생성 완료")  # 디버깅 로그

    except Exception as e:
        console.log(f"통계 정보 생성 중 오류: {str(e)}")  # 디버깅 로그
        result.add_warning(f"통계 정보 생성 중 오류가 발생했습니다: {str(e)}")

    return result

def check_component_duplicates(df: pd.DataFrame) -> list:
    """
    공백 차이로 인한 중복 부재명 확인

    Returns:
        list: 중복 부재명 그룹 리스트
    """
    component_groups = {}
    duplicates = []

    # 부재명을 정규화하여 그룹화
    for component in df['부재명'].dropna().unique():
        if pd.notna(component):
            # 공백을 모두 제거한 정규화된 이름
            normalized = str(component).replace(' ', '').replace('\t', '')

            if normalized not in component_groups:
                component_groups[normalized] = []
            component_groups[normalized].append(str(component))

    # 중복이 있는 그룹 찾기
    for normalized, variants in component_groups.items():
        if len(variants) > 1:
            # 실제로 다른 변형들이 있는지 확인
            unique_variants = list(set(variants))
            if len(unique_variants) > 1:
                duplicates.append(unique_variants)

    return duplicates

def console_log(message: str):
    """JavaScript 스타일 콘솔 로그 (Python에서는 print 사용)"""
    #print(f"[FILE_VALIDATION] {message}")

def perform_damage_quantity_validation(df: pd.DataFrame) -> dict:
    """
    손상물량 계산 검증 수행

    Args:
        df: 검증할 DataFrame

    Returns:
        dict: 검증 결과
    """
    console.log("손상물량 계산 검증 시작")

    error_rows = []
    valid_rows = 0

    # 필수 컬럼 체크
    required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return {
            'error_rows': [],
            'valid_rows': 0,
            'total_rows': len(df),
            'missing_columns': missing_columns
        }

    # 길이/너비 컬럼 찾기 (선택적)
    length_columns = ['길이', '길이(m)', 'L', 'length', '연장']
    width_columns = [ '너비', '너비(m)', 'W', 'width', 'B']
    count_columns =  ['ea', 'EA', '개', '개소']

    available_length_col = None
    available_width_col = None
    available_count_col = None

    # 부분일치(포함)로 길이 컬럼 찾기
    for col in df.columns:
        for key in length_columns:
            if key in str(col):
                available_length_col = col
                break
        if available_length_col:
            break

    # 부분일치(포함)로 너비 컬럼 찾기
    for col in df.columns:
        for key in width_columns:
            if key in str(col):
                available_width_col = col
                break
        if available_width_col:
            break


    print(f"사용 가능한 길이 컬럼: {available_length_col}, 너비 컬럼: {available_width_col}")  # 디버깅 로그
    # 부분일치(포함)로 길이 컬럼 찾기
    for col in df.columns:
        if any(key in col for key in count_columns):
            available_count_col = col
            break



    for idx, row in df.iterrows():
        row_errors = []

        try:
            # 기본 데이터 체크
            if pd.isna(row['부재명']) or str(row['부재명']).strip() == '':
                row_errors.append("부재명이 비어있음")

            if pd.isna(row['부재위치']) or str(row['부재위치']).strip() == '':
                row_errors.append("부재위치가 비어있음")

            if pd.isna(row['손상내용']) or str(row['손상내용']).strip() == '':
                row_errors.append("손상내용이 비어있음")

            if pd.isna(row['손상물량']):
                row_errors.append("손상물량이 비어있음")

            if pd.isna(row['개소']):
                row_errors.append("개소가 비어있음")

            if pd.isna(row['단위']) or str(row['단위']).strip() == '':
                row_errors.append("단위가 비어있음")

            # 손상물량 계산 검증 - 필수 데이터 체크 후 계산
            unit = str(row['단위']).strip() if pd.notna(row['단위']) else ''
            damage_quantity = pd.to_numeric(row['손상물량'], errors='coerce') if pd.notna(row['손상물량']) else None
            count = pd.to_numeric(row[available_count_col], errors='coerce') if pd.notna(row[available_count_col]) else None

            if pd.notna(damage_quantity) and pd.notna(count) and unit:
                # 길이 및 너비 정보 추출
                length = None
                width = None

                if available_length_col and available_length_col in row.index and pd.notna(row[available_length_col]):
                    length = pd.to_numeric(row[available_length_col], errors='coerce')

                if available_width_col and available_width_col in row.index and pd.notna(row[available_width_col]):
                    width = pd.to_numeric(row[available_width_col], errors='coerce')

                if available_count_col and available_count_col in row.index and pd.notna(row[available_count_col]):
                    count = pd.to_numeric(row[available_count_col], errors='coerce')

                # 단위별 검증 - 계산값과 손상물량이 다르면 오류 처리
                if unit == 'm':
                    # m 단위: 길이 × 개소 = 손상물  량
                    if pd.notna(length) and pd.notna(count):
                        expected_quantity = length * count
                        if abs(damage_quantity - expected_quantity) > 0.01:  # 오차 허용
                            row_errors.append(f"m 단위 손상물량 계산 오류1: 현재 {damage_quantity}, 올바른 값 {expected_quantity:.2f} (길이 {length} × 개소 {count})")
                    else:
                        missing_info = []
                        if pd.isna(length):
                            missing_info.append("길이")
                        if pd.isna(count):
                            missing_info.append("개소")
                        if missing_info:
                            row_errors.append(f"m 단위 검증을 위한 정보가 없음: {', '.join(missing_info)}")

                elif unit in ['㎡', 'm²', 'm2']:

                    #=IF(unit="m",length*count,IF(unit="㎡",length*width*count,IF(unit="EA",count,"")))

                    # ㎡ 단위: 길이 × 너비 × 개소 = 손상물량
                    if pd.notna(length) and pd.notna(width) and pd.notna(count):
                        expected_quantity = length * width * count
                        if abs(damage_quantity - expected_quantity) > 0.01:  # 오차 허용
                            row_errors.append(f"㎡ 단위 손상물량 계산 오류2: 현재 {damage_quantity}, 올바른 값 {expected_quantity:.2f} (길이 {length} × 너비 {width} × 개소 {count})")
                    else:
                        missing_info = []
                        if pd.isna(length):
                            missing_info.append("길이")
                        if pd.isna(width):
                            missing_info.append("너비")
                        if pd.isna(count):
                            missing_info.append("개소")
                        if missing_info:
                            row_errors.append(f"㎡ 단위 검증을 위한 정보가 없음2: {', '.join(missing_info)}")

                elif unit.lower() in ['ea', 'EA', '개', '개소']:
                    # ea/EA/개 단위: 개소 = 손상물량
                    if abs(damage_quantity - count) > 0.01:  # 오차 허용
                        row_errors.append(f"개수 단위 손상물량 계산 오류3: 현재 {damage_quantity}, 올바른 값 {count} (개소와 동일해야 함)")

                # 음수 검증
                if damage_quantity < 0:
                    row_errors.append("손상물량이 음수임")

                if count < 0:
                    row_errors.append("개소가 음수임")


                # expected_quantity = 0;
                # if unit == 'm':
                #     if pd.notna(length) and pd.notna(count):
                #         expected_quantity = length * count
                #         if abs(damage_quantity - expected_quantity) > 0.01:
                #             row_errors.append(f"m 단위 손상물량 계산 오류: 현재 {damage_quantity}, 올바른 값 {expected_quantity:.2f}")
                # elif unit in ['㎡', 'm²', 'm2']:
                #     if pd.notna(length) and pd.notna(width) and pd.notna(count):
                #         expected_quantity = length * width * count
                #         if abs(damage_quantity - expected_quantity) > 0.01:
                #             row_errors.append(f"㎡ 단위 손상물량 계산 오류: 현재 {damage_quantity}, 올바른 값 {expected_quantity:.2f}")
                # elif unit.lower() in ['ea', '개', '개소']:
                #     if abs(damage_quantity - count) > 0.01:
                #         row_errors.append(f"개수 단위 손상물량 계산 오류: 현재 {damage_quantity}, 올바른 값 {count} (개소와 동일해야 함)")


        except Exception as e:
            row_errors.append(f"검증 중 오류 발생: {str(e)}")

        if row_errors:
            error_rows.append({
                'row_index': idx + 2,  # Excel 행 번호 (헤더 포함)
                'errors': row_errors,
                'data': {
                    '부재명': str(row['부재명']) if pd.notna(row['부재명']) else '',
                    '부재위치': str(row['부재위치']) if pd.notna(row['부재위치']) else '',
                    '손상내용': str(row['손상내용']) if pd.notna(row['손상내용']) else '',
                    '손상물량': str(row['손상물량']) if pd.notna(row['손상물량']) else '',
                    '개소': str(row['개소']) if pd.notna(row['개소']) else '',
                    '단위': str(row['단위']) if pd.notna(row['단위']) else ''
                }
            })
        else:
            valid_rows += 1

    console.log(f"손상물량 계산 검증 완료: 총 {len(df)}행 중 {len(error_rows)}개 오류")

    return {
        'error_rows': error_rows,
        'valid_rows': valid_rows,
        'total_rows': len(df)
    }

def generate_table_preview_with_highlighting(df: pd.DataFrame, error_rows: list = None) -> str:
    """
    전체 테이블 미리보기 생성 (오류 행 하이라이트 포함)

    Args:
        df: 미리보기할 DataFrame
        error_rows: 오류 행 정보 리스트

    Returns:
        str: HTML 테이블 문자열
    """
    try:
        # 전체 데이터 표시 (최대 500행까지)
        max_rows = 500
        preview_df = df.head(max_rows).copy()

        # 필수 컬럼만 선택
        required_columns = ['부재명', '부재위치', '손상내용','개소', '단위','손상물량']

        # 추가 컬럼도 포함 (길이, 너비 등)
        length_columns = ['길이', '길이(m)', 'L', 'length', '연장']
        width_columns = ['폭', '너비', '너비(m)', 'W', 'width', 'B']

        available_columns = []
        for col in required_columns:
            if col in preview_df.columns:
                available_columns.append(col)

        # 길이/너비 컬럼 추가
        for length_key in length_columns:
            for col in preview_df.columns:
                if length_key in str(col) and col not in available_columns:
                    available_columns.append(col)
                    break

        for width_key in width_columns:
            for col in preview_df.columns:
                if width_key in str(col) and col not in available_columns:
                    available_columns.append(col)
                    break

        if available_columns:
            preview_df = preview_df[available_columns]

        # 오류 행 정보 매핑
        error_row_indices = set()
        if error_rows:
            for error_row in error_rows:
                # Excel 행 번호를 DataFrame 인덱스로 변환 (헤더 제외하고 -2)
                df_index = error_row['row_index'] - 2
                if 0 <= df_index < len(preview_df):
                    error_row_indices.add(df_index)

        # HTML 테이블 생성
        html = '<table class="table table-striped table-bordered table-hover" id="preview-table" style="font-size: 12px;">'

        # 헤더 생성
        html += '<thead class="table-dark"><tr><th style="position: sticky; top: 0; z-index: 10;">행번호</th>'
        for col in preview_df.columns:
            if col in ['개소', '단위']:
                html += f'<th style="position: sticky; top: 0; z-index: 10; min-width: 50px; text-align: left;">{col}</th>'
            else:
                html += f'<th style="position: sticky; top: 0; z-index: 10; min-width: 100px;">{col}</th>'
        html += '</tr></thead>'

        # 데이터 행 생성
        html += '<tbody>'
        for idx, (df_idx, row) in enumerate(preview_df.iterrows()):
            row_class = 'table-danger' if idx in error_row_indices else ''
            error_title = ''
            error_cols = set()

            if idx in error_row_indices and error_rows:
                for error_row in error_rows:
                    if error_row['row_index'] - 2 == idx:
                        error_title = f'title="오류: {" | ".join(error_row["errors"])}"'
                        for col in preview_df.columns:
                            if any(col in err for err in error_row["errors"]):
                                error_cols.add(col)
                        break

            html += f'<tr class="{row_class}" {error_title}>'
            html += f'<td><strong>{idx + 2}</strong></td>'  # Excel 행 번호 (헤더 포함)

            for col in preview_df.columns:
                cell_value = str(row[col]) if pd.notna(row[col]) else ''
                if len(cell_value) > 30:
                    cell_value = cell_value[:30] + '...'

                # 왼쪽 정렬 및 50px 컬럼 스타일 적용
                if col in ['개소', '단위']:
                    style = 'text-align: left; min-width: 50px;'
                else:
                    style = ''

                # 해당 셀의 컬럼명이 오류 메시지에 포함되어 있으면 강조
                if idx in error_row_indices and col in error_cols:
                    html += f'<td style="background-color: #f8d7da; color: #721c24;{style}"><i class="fas fa-exclamation-triangle text-danger me-1"></i>{cell_value}</td>'
                else:
                    html += f'<td style="{style}">{cell_value}</td>'
            html += '</tr>'

        html += '</tbody></table>'

        # 추가 정보 표시
        if len(df) > max_rows:
            html += f'<div class="alert alert-info mt-2"><small><i class="fas fa-info-circle"></i> 전체 {len(df)}행 중 처음 {max_rows}행만 표시됩니다.</small></div>'

        return html

    except Exception as e:
        console.log(f"테이블 미리보기 생성 중 오류: {str(e)}")
        return "<p>테이블 미리보기를 생성할 수 없습니다.</p>"

def generate_table_preview(df):
    """테이블 미리보기 생성 - HTML 테이블 형태로 반환"""
    try:
        # 최대 20행까지만 미리보기
        #preview_df = df.head(20)
        preview_df = df

        # 필수 컬럼만 선택
        required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']
        available_columns = [col for col in required_columns if col in preview_df.columns]

        if available_columns:
            preview_df = preview_df[available_columns]

        # HTML 테이블로 변환
        table_html = preview_df.to_html(
            classes='table table-striped table-bordered',
            table_id='preview-table',
            escape=False,
            index=True  # 행 번호 포함
        )

        return table_html
    except Exception as e:
        print(f"테이블 미리보기 생성 중 오류: {str(e)}")
        return "<p>테이블 미리보기를 생성할 수 없습니다.</p>"

# console 객체 시뮬레이션
class Console:
    def log(self, message: str):
        print(f"[FILE_VALIDATION] {message}")

console = Console()

def perform_detailed_validation(df):
    """상세 검증 수행 - 손상물량 계산 검증 포함"""
    print("상세 검증 시작")

    # 숫자 변환 헬퍼 함수 (함수 시작 부분에 정의)
    def safe_float(value, default=0):
        """안전하게 float로 변환 (빈 문자열 처리)"""
        if pd.isna(value):
            return default
        if isinstance(value, str) and value.strip() == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # 단위 표준화 딕셔너리
    def normalize_unit(unit_str):
        """단위를 표준화하는 함수"""
        if pd.isna(unit_str) or str(unit_str).strip() == '':
            return ''

        unit = str(unit_str).strip().lower()

        # 단위 표준화 매핑
        unit_mapping = {
            # 미터 단위
            'm': 'm',
            'meter': 'm',
            '미터': 'm',

            # 제곱미터 단위
            '㎡': '㎡',
            'm²': '㎡',
            'm2': '㎡',
            'sqm': '㎡',
            'square meter': '㎡',
            '제곱미터': '㎡',

            # 개수 단위
            'ea': 'EA',
            'EA': 'EA',
            'each': 'EA',
            '개': 'EA',
            '개소': 'EA',
            'pcs': 'EA',
            'piece': 'EA',

            # 밀리미터 단위
            'mm': 'mm',
            '㎜': 'mm',
            'millimeter': 'mm',
            '밀리미터': 'mm',

            # 센티미터 단위
            'cm': 'cm',
            'centimeter': 'cm',
            '센티미터': 'cm',

            # 식 단위
            '식': '식',
            'set': '식',
            'lot': '식'
        }

        return unit_mapping.get(unit, unit_str.strip())  # 매핑되지 않으면 원본 반환

    # NaN 처리 헬퍼 함수
    def convert_nan_to_none(obj):
        """NaN과 Infinity를 None으로 변환"""
        import math
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        elif isinstance(obj, dict):
            return {k: convert_nan_to_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_nan_to_none(item) for item in obj]
        return obj

    try:
        validation_errors = []

        #필수 컬럼 체크
        required_columns = ['부재명', '부재위치', '손상내용', '손상물량', '개소', '단위']
        missing_columns = [col for col in required_columns if col not in df.columns]



        if missing_columns:
            return {
                'errors': [f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"],
                'error_rows': [],
                'total_rows': len(df),
                'cleaned_data': []
            }

        error_rows = []
        cleaned_data = []  # 정제된 데이터를 저장할 리스트

        for idx, row in df.iterrows():
            row_errors = []

            # 1. 필수 데이터 체크
            if pd.isna(row['부재명']) or str(row['부재명']).strip() == '':
                row_errors.append("부재명이 비어있음")
            if pd.isna(row['부재위치']) or str(row['부재위치']).strip() == '':
                row_errors.append("부재위치가 비어있음")
            if pd.isna(row['손상내용']) or str(row['손상내용']).strip() == '':
                row_errors.append("손상내용이 비어있음")
            if pd.isna(row['손상물량']):
                row_errors.append("손상물량이 비어있음")
            if pd.isna(row['개소']):
                row_errors.append("개소가 비어있음")
            if pd.isna(row['단위']) or str(row['단위']).strip() == '':
                row_errors.append("단위가 비어있음")

        # 2. 손상물량 계산 검증
            try:
                unit = str(row['단위']).strip()
                damage_quantity = pd.to_numeric(row['손상물량'], errors='coerce')
                count = pd.to_numeric(row['개소'], errors='coerce')

                if pd.notna(damage_quantity) and pd.notna(count) and unit:
                    # 길이 및 너비 정보가 있는지 확인
                    length = None
                    width = None

                    # 길이/너비 정보를 다양한 컬럼에서 찾기
                    length_columns = ['길이', '길이(m)', 'L', 'length', '연장']
                    width_columns = [  '너비', '너비(m)', 'W', 'width', 'B']

                    for col in length_columns:
                        for df_col in df.columns:
                            if col in str(df_col) and pd.notna(row[df_col]):
                                length = pd.to_numeric(row[df_col], errors='coerce')
                                break
                        if length is not None:
                            break

                    for col in width_columns:
                        for df_col in df.columns:
                            if col in str(df_col) and pd.notna(row[df_col]):
                                width = pd.to_numeric(row[df_col], errors='coerce')
                                break
                        if width is not None:
                            break

                   # 단위별 검증
                    if unit == 'm' and pd.notna(length) and pd.notna(count):
                        expected_quantity = length * count
                        if abs(damage_quantity - expected_quantity) > 0.01:  # 오차 허용
                            row_errors.append(f"m 단위 손상물량 불일치: 실제 {damage_quantity}, 예상 {expected_quantity:.2f} (길이 {length} × 개소 {count})")

                    elif unit in ['㎡', 'm²', 'm2'] and pd.notna(length) and pd.notna(width) and pd.notna(count):
                        expected_quantity = length * width * count
                        if abs(damage_quantity - expected_quantity) > 0.01:  # 오차 허용
                            row_errors.append(f"㎡ 단위 손상물량 불일치: 실제 {damage_quantity}, 예상 {expected_quantity:.2f} (길이 {length} × 너비 {width} × 개소 {count})")

                    elif unit.lower() in ['ea', 'EA', '개', '개소']:
                        if abs(damage_quantity - count) > 0.01:  # 오차 허용
                            row_errors.append(f"개수 단위 손상물량 불일치: 실제 {damage_quantity}, 예상 {count} (개소와 동일해야 함)")

            except Exception as e:
                row_errors.append(f"손상물량 계산 검증 중 오류: {str(e)}")

        # 3. 데이터 타입 검증
            try:
                if pd.notna(row['손상물량']):
                    damage_qty = pd.to_numeric(row['손상물량'], errors='coerce')
                    if pd.isna(damage_qty):
                        row_errors.append("손상물량이 숫자가 아님")
                    elif damage_qty < 0:
                        row_errors.append("손상물량이 음수임")
            except:
                row_errors.append("손상물량 형식 오류")

            try:
                if pd.notna(row['개소']):
                    count_val = pd.to_numeric(row['개소'], errors='coerce')
                    if pd.isna(count_val):
                        row_errors.append("개소가 숫자가 아님")
                    elif count_val < 0:
                        row_errors.append("개소가 음수임")
            except:
                row_errors.append("개소 형식 오류")

        # 정제된 데이터 생성 (오류 여부와 관계없이)
            cleaned_row = {
                '부재명': str(row['부재명']).replace(' ', '') if pd.notna(row['부재명']) else '',
                '부재위치': str(row['부재위치']).replace(' ', '') if pd.notna(row['부재위치']) else '',
                '손상내용': str(row['손상내용']).replace(' ', '') if pd.notna(row['손상내용']) else '',
                '손상물량': safe_float(row.get('손상물량', 0)),
                '개소': safe_float(row.get('개소', 0)),
                '단위': normalize_unit(row.get('단위', ''))  # 단위 표준화 적용
            }

            # OPTIONAL 컬럼 추가 (항상 추가하되, NaN은 0으로 처리)
            if '길이' in row.index:
                길이_값 = row.get('길이')
                cleaned_row['길이'] = safe_float(길이_값, 0)

            if '너비' in row.index:
                너비_값 = row.get('너비')
                cleaned_row['너비'] = safe_float(너비_값, 0)

            if '균열폭' in row.index:
                균열폭_값 = row.get('균열폭')
                cleaned_row['균열폭'] = safe_float(균열폭_값, 0)
            elif '폭' in row.index:
                폭_값 = row.get('폭')
                cleaned_row['균열폭'] = safe_float(폭_값, 0)

            # 원본부재명 추가 (있으면)
            if '원본부재명' in row.index:
                원본부재명_값 = row.get('원본부재명')
                cleaned_row['원본부재명'] = str(원본부재명_값).strip() if pd.notna(원본부재명_값) else ''

            # NaN 처리 (None 대신 적절한 기본값으로)
            for key, value in cleaned_row.items():
                if pd.isna(value):
                    if key in ['길이', '너비', '균열폭', '손상물량', '개소']:
                        cleaned_row[key] = 0
                    else:
                        cleaned_row[key] = ''

            if row_errors:
                error_rows.append({
                    'row_index': row['라인'],  # 1부터 시작하는 행 번호
                    'errors': row_errors,
                    'data': {
                        '부재명': str(row['부재명']).replace(' ', '') if pd.notna(row['부재명']) else '',
                        '부재위치': str(row['부재위치']).replace(' ', '') if pd.notna(row['부재위치']) else '',
                        '손상내용': str(row['손상내용']).replace(' ', '') if pd.notna(row['손상내용']) else '',
                        '손상물량': str(row['손상물량']) if pd.notna(row['손상물량']) else '',
                        '개소': str(row['개소']) if pd.notna(row['개소']) else '',
                        '단위': str(row['단위']) if pd.notna(row['단위']) else ''
                    }
                })
            else:
                # 오류가 없는 행만 정제된 데이터에 추가
                cleaned_data.append(cleaned_row)

        print(f"상세 검증 완료: {len(error_rows)}개 오류 행 발견, {len(cleaned_data)}개 유효 행")

        # 오류가 있는 행에 대한 상세 정보 추가
        for error_row in error_rows:
            row_index = error_row['row_index']
            errors = error_row['errors']

            # 각 오류에 대한 설명 추가
            for i, error in enumerate(errors):
                if '손상물량 불일치' in error:
                    errors[i] = f"손상물량 불일치: {error}"
                if '비어있음' in error:
                    errors[i] = f"필수 데이터 누락: {error}"
                if '숫자가 아님' in error:
                    errors[i] = f"유효하지 않은 값: {error}"

        return {
            'errors': [f"총 {len(error_rows)}개 행에서 오류 발견"] if error_rows else [],
            'error_rows': error_rows,
            'total_rows': len(df),
            'valid_rows': len(df) - len(error_rows),
            'cleaned_data': cleaned_data  # 정제된 데이터 반환
        }

    except Exception as e:
        print(f"상세 검증 중 오류가 발생했습니다935: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'errors': [f"상세 검증 중 오류가 발생했습니다939: {str(e)}"],
            'error_rows': [],
            'total_rows': len(df) if df is not None else 0,
            'valid_rows': 0,
            'cleaned_data': []
        }
