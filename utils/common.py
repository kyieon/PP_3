from difflib import get_close_matches
import re
import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv()

# 임시로 하드코딩된 설정 (환경변수 로딩 문제 해결용)
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'bridge_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Maruta82'),
    'host': os.getenv('DB_HOST', 'infrasmart.co.kr'),  # 실제 호스트명으로 변경
    'port': os.getenv('DB_PORT', '5433')
}

# 환경변수 로딩 상태 확인
print(f"환경변수 로딩 상태:")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"실제 사용 설정: {DB_CONFIG}")



def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_sqlalchemy_engine():
    """SQLAlchemy 엔진 생성 (pandas와의 호환성을 위해)"""
    connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    return create_engine(connection_string)

# 대표 손상 키워드 목록
DAMAGE_KEYWORDS = [
    "균열(0.3mm)", "균열(0.2mm)", "균열", "철근노출", "파손", "침식", "세굴", "균열부백태","균열부 백태", "균열/백태", "균열(0.2mm이하)",
    "균열(0.2mm이상)", "균열(0.3mm미만)", "균열(0.3mm이상)", "박리", "들뜸", "박락", "재료분리", "층분리", "백태",
    "누수흔적", "누수오염", "표면오염", "누수", "신축하부누수", "박리/백태", "표면박리", "골재노출", "소성변형",
    "요철", "패임", "파손", "플레이트부식", "난간변형", "난간파손", "난간탈락", "난간대탈락", "방음벽파손",
    "난간지주파손", "지주파손", "교명주파손", "교명주기초파손", "교명판탈락", "설명판탈락", "토사퇴적",
    "토사퇴적/식생", "이물질퇴적", "폐콘크리트퇴적", "폐콘크리트적치", "볼트풀림", "볼트탈락", "마감캡탈락",
    "마감불량", "잡철근노출", "잡철물노출", "이물질삽입", "유송잡물적치", "볼트부식", "난간대탈락", "난간부식",
    "점검로부식", "침식/세굴", "포장파손", "포장패임", "포장균열", "연석균열", "연석박리", "연석박락",
    "연석파손", "배수구막힘", "연석파손", "부식", "도장박리", "도장박락", "배수관이음부누수",
    "배수관탈락", "길이부족", "주의관찰", "청소", "배수관길이부족",
    "방호울타리파손", "방호울타리탈락", "방호울타리변형", "방음벽파손", "방음벽탈락", "방음벽변형",
    "방음판파손", "방음판탈락", "방음판변형", "차광망파손", "차광망탈락", "차광망변형",
    "낙석방지망파손", "낙석방지망탈락", "낙석방지망변형", "낙석방지책파손", "낙석방지책탈락", "낙석방지책변형",
    "중분대파손", "중분대탈락", "중분대변형", "중앙분리대파손", "중앙분리대탈락", "중앙분리대변형",
    "경계석파손", "경계석탈락", "경계석변형", "경계석균열", "경계석박리"
]


# 부재명 순서 정의
COMPONENT_ORDER = [
    '바닥판', '슬래브', '거더', '주형', '가로보', '세로보', '교대', '교각', '기초',
    '교량받침', '신축이음', '교면포장', '포장부', '난간', '연석', '방호벽',
    '배수시설', '점검시설', '점검로'
]

# 부재명 정렬 함수
def sort_components(components):
    normalized_components = [(comp, normalize_component(comp)) for comp in components]
    sorted_components = sorted(normalized_components,
                             key=lambda x: COMPONENT_ORDER.index(x[1]) if x[1] in COMPONENT_ORDER else len(COMPONENT_ORDER))
    return [comp[0] for comp in sorted_components]

def remove_special_characters(desc: str) -> str:
    desc = normalize_damage(desc).replace(" ", "")
    # 소수점과 mm, ㎜ 단위는 보존
    return re.sub(r'[^ㄱ-ㅎ가-힣a-zA-Z0-9().㎜]', '', desc)


# 부재명 정규화 함수
def normalize_component(component):
    component = component.strip()
    # 괄호 안의 내용을 포함하여 정규화
    if '바닥판' in component or '슬래브' in component:
        return '바닥판'
    if '거더' in component or '주형' in component:
        return '거더'
    if '가로보' in component or '세로보' in component:
        return '가로보'
    if '교면포장' in component or '포장부' in component:
        return '교면포장'
    if '난간' in component or '연석' in component or '방호벽' in component or '방호울타리' in component or '방음벽' in component or '방음판' in component or '차광망' in component or '낙석방지망' in component or '낙석방지책' in component or '중분대' in component or '중앙분리대' in component or '경계석' in component:
        return '난간/연석'
    if '점검시설' in component or '점검로' in component:
        return '점검시설'
    if '받침' in component or '교량받침' in component:
        return '교량받침'
    return component


def normalize_damage(desc):
    desc = re.sub(r'\s+', '', desc)
    desc = re.sub(r'\( *', '(', desc)
    desc = re.sub(r' *\)', ')', desc)
    if desc in DAMAGE_KEYWORDS:
        return desc
    match = get_close_matches(desc, DAMAGE_KEYWORDS, n=1, cutoff=0.65)
    return match[0] if match else desc


def classify_repair(desc):
    # normalize_damage를 사용하지 않고 직접 처리
    original_desc = desc
    is_pavement = any(keyword in desc for keyword in ["교면포장", "포장", "연석", "신축이음", "포장균열"])

    # 특수문자 제거 (소수점과 mm, ㎜ 단위는 보존)
    desc = re.sub(r'[^ㄱ-ㅎ가-힣a-zA-Z0-9().㎜]', '', desc)
    desc = desc.replace(" ", "")

    desc = (desc.replace("보수부", "")
                .replace("받침콘크리트", "")
                .replace("받침몰탈", "")
                .replace("받침", "")
                .replace("전단키", "")
                .replace("연석", ""))

    # ✅ 명시된 문자열 먼저 우선 처리
    if re.search(r"균열\(0\.3mm\)|균열\(0\.3mm이상\)|균열\(0\.3㎜\)|균열\(0\.3㎜이상\)", desc):
        return "주입보수"
    if re.search(r"균열\(0\.3mm미만\)|균열\(0\.2mm이하\)|균열\(0\.2㎜이하\)|균열\(0\.3㎜미만\)", desc):
        return "표면처리"

    if '균열' in desc:
        # "미만", "이하" 키워드가 있는지 먼저 확인
        if re.search(r'(\d+(\.\d+)?)mm.*(미만|이하)', desc):
            return "표면처리"

        match = re.search(r'(\d+(\.\d+)?)mm', desc)
        if match:
            crack_size = float(match.group(1))
            if crack_size >= 1.0:
                return "충진보수"
            elif crack_size >= 0.3:
                return "주입보수"
            else:
                return "표면처리"
        else:
            return "표면처리"

    if is_pavement:
        if re.search("균열|망상균열", original_desc):
            return "실링보수"
        elif re.search("파손|패임|들뜸", original_desc):
            return "부분재포장"
        else:
            return "주의관찰"

    if re.search("신축이음|이음장치", desc):
    # ✅ '후타재'가 포함되어 있으면 무조건 주의관찰
        if re.search("후타재", desc):
            return "주의관찰"
        # ✅ 그 외 파손/탈락은 신축이음 재설치
        if re.search("본체파손|본체탈락|탈락|파손", desc):
            return "주의관찰"

    if re.search("철근노출", desc): return "단면보수(방청)"
    if re.search("박리|들뜸|박락|재료분리|파손|침식|세굴|층분리", desc): return "단면보수"
    if re.search("백태|누수흔적|오염|망상균열|흔적|균열부백태|누수오염|녹물", desc): return "표면처리"
    if re.search("부식|도장박리|도장박락|도장|플레이트", desc): return "도장보수"
    if re.search("탈락|망실|미설치", desc): return "재설치"
    if re.search("막힘|퇴적|적치", desc): return "청소"
    if re.search("배수관탈락|길이부족", desc): return "배수관 재설치"

    return "주의관찰"

def trim_dataframe_data(df):
    """
    DataFrame 내부의 모든 문자열 데이터를 trim 처리합니다.

    Args:
        df (pd.DataFrame): 처리할 DataFrame

    Returns:
        pd.DataFrame: trim 처리된 DataFrame
    """
    if df is None or df.empty:
        return df

    # DataFrame의 복사본 생성
    df_trimmed = df.copy()

    # 모든 컬럼에 대해 trim 처리
    for column in df_trimmed.columns:
        # 문자열 컬럼인 경우에만 trim 처리
        if df_trimmed[column].dtype == 'object':
            df_trimmed[column] = df_trimmed[column].astype(str).str.strip()

    return df_trimmed

def trim_dataframe_numeric_columns(df):
    """
    DataFrame의 숫자 컬럼들을 정리하고 trim 처리합니다.

    Args:
        df (pd.DataFrame): 처리할 DataFrame

    Returns:
        pd.DataFrame: 처리된 DataFrame
    """
    if df is None or df.empty:
        return df

    df_processed = df.copy()

    # 손상물량과 개소 컬럼이 있는 경우 숫자로 변환하고 NaN을 0으로 채움
    if '손상물량' in df_processed.columns:
        df_processed['손상물량'] = pd.to_numeric(df_processed['손상물량'], errors='coerce').fillna(0)

    if '개소' in df_processed.columns:
        df_processed['개소'] = pd.to_numeric(df_processed['개소'], errors='coerce').fillna(0)

    # 부재위치 컬럼이 있는 경우 문자열로 변환
    if '부재위치' in df_processed.columns:
        df_processed['부재위치'] = df_processed['부재위치'].astype(str)

    return df_processed

def clean_dataframe_data(df):
    """
    DataFrame의 모든 데이터를 정리하고 trim 처리합니다.

    Args:
        df (pd.DataFrame): 처리할 DataFrame

    Returns:
        pd.DataFrame: 정리된 DataFrame
    """
    if df is None or df.empty:
        return df

    # 1. 기본 trim 처리
    df_cleaned = trim_dataframe_data(df)

    # 2. 숫자 컬럼 처리
    df_cleaned = trim_dataframe_numeric_columns(df_cleaned)

    # 3. 빈 값들을 빈 문자열로 통일
    df_cleaned = df_cleaned.fillna('')

    return df_cleaned



def trim_dataframe_str_columns(df: pd.DataFrame) -> pd.DataFrame:
    # 문자열 컬럼 trim 처리
    df = trim_dataframe_str_columns(df)
    # ...기존 코드...

    """
    DataFrame의 모든 문자열(object) 컬럼에 대해 strip()을 적용하여 공백을 제거합니다.
    """
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def get_meta_keywords_by_meta_id(meta_id):
    """meta_keyword 테이블에서 meta_id로 keyword 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT TRIM(keyword) FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s ORDER BY LENGTH(TRIM(keyword)) DESC", (meta_id,))
    keywords = [row[0] for row in cur.fetchall()]
    #use_yn = [row[1] for row in cur.fetchall()]
    conn.close()
    return keywords


def get_meta(parent_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT keyword FROM damage_meta WHERE use_yn='Y' AND parent_id=%s", (parent_id,))
    rows = cur.fetchall()
    print("조회 결과:", rows)
    keywords = [row[0] for row in rows]
    conn.close()
    return keywords




def convert_component_name_to_key(component_name):
    """부재명을 API 키로 변환"""

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT TRIM(keyword), source FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s ORDER BY LENGTH(TRIM(keyword)) DESC", ('200075',))
    rows = cur.fetchall()
    keywords = [row[0] for row in rows]
    sources = [row[1] for row in rows]
    mapping = {keyword: source for keyword, source in zip(keywords, sources)}

    # mapping = {
    #     '바닥판': 'slab',
    #     '거더': 'girder',
    #     '가로보': 'crossbeam',
    #     '세로보': 'crossbeam',
    #     '격벽': 'crossbeam',
    #     '교대': 'abutment',
    #     '교각': 'pier',
    #     '기초': 'foundation',
    #     '받침': 'bearing',
    #     '교량받침': 'bearing',
    #     '받침장치': 'bearing',
    #     '탄성받침': 'bearing',
    #     '고무받침': 'bearing',
    #     '강재받침': 'bearing',
    #     '베어링': 'bearing',
    #     '신축이음': 'expansionJoint',
    #     '이음장치': 'expansionJoint',
    #     '신축이음장치': 'expansionJoint',
    #     '이음부': 'expansionJoint',
    #     '교면포장': 'pavement',
    #     '포장': 'pavement',
    #     '배수시설': 'drainage',
    #     '배수구': 'drainage',
    #     '난간': 'railing',
    #     '연석': 'railing',
    #     '난간연석': 'railing',
    #     '난간/연석': 'railing',
    #     '방호울타리': 'railing',
    #     '방호벽': 'railing',
    #     '방음벽': 'railing',
    #     '방음판': 'railing',
    #     '방음': 'railing',
    #     '방호': 'railing',
    #     '차광망': 'railing',
    #     '차광': 'railing',
    #     '낙석방지망': 'railing',
    #     '낙석방지책': 'railing',
    #     '낙석': 'railing',
    #     '중분대': 'railing',
    #     '중앙분리대': 'railing',
    #     '경계석': 'railing',
    #     '가드레일': 'railing',
    #     '레일': 'railing',
    #     '울타리': 'railing',
    #     '보호': 'railing',
    #     '안전': 'railing'
    # }

    # 정확한 매칭 먼저 시도
    if component_name in mapping:
        return mapping[component_name]

    # 부분 매칭 시도 (더 포괄적으로)
    for key, value in mapping.items():
        if key in component_name:
            return value

    # 난간 관련 키워드 추가 검색
    railing_keywords = get_meta_keywords_by_meta_id(200017)  # 예시로 parent_id가 100001인 메타데이터 키워드 목록을 가져옴
    if any(keyword in component_name for keyword in railing_keywords):
        return 'railing'

    print(f"Unknown component name: {component_name}")
    return None
def get_source_by_meta_id_and_keyword(meta_id, keyword):
    """
    meta_keyword 테이블에서 meta_id와 keyword로 source 값 조회
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT source FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s AND keyword=%s",
        (meta_id, keyword)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return None


def get_keyword_by_meta_id_and_source(meta_id, source):
    """
    meta_keyword 테이블에서 meta_id와 keyword로 source 값 조회
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT keyword FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s AND source=%s",
        (meta_id, source)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return None


def get_circled_number(number):
    """
    주어진 숫자를 유니코드 동그라미 숫자 문자로 변환합니다.
    예: 1 -> ①, 2 -> ② 등
    """
    if 1 <= number <= 10:
        # 1부터 10까지의 숫자에 해당하는 유니코드 코드를 사용합니다.
        # 9312 (①) 에서 9321 (⑩) 입니다.
        return chr(9311 + number)
    elif 11 <= number <= 20:
        # 11부터 20까지는 9322 (⑪) 에서 9331 (⑳) 입니다.
        return chr(9311 + number)
    else:
        # 20보다 크거나 0 이하인 숫자는 변환하지 않습니다.
        return str(number)
