"""
웹 캡처 프로그램 설정 파일
필요에 따라 이 값들을 수정하여 사용하세요.
"""

# 화면 캡처 관련 설정
CAPTURE_SETTINGS = {
    # 보고서 영역 좌표 (left, top, width, height) - 기존 방식용
    "report_area": {
        "left": 531,
        "top": 209,
        "width": 1878 - 531,  # 1347
        "height": 930 - 209   # 721
    },
    
    # 세로 보고서 캡처 영역
    "portrait_area": {
        "left": 959,
        "top": 207,
        "width": 1458 - 959,  # 499
        "height": 910 - 207   # 703
    },
    
    # 가로 보고서 캡처 영역
    "landscape_area": {
        "left": 702,
        "top": 211, 
        "width": 1712 - 702,  # 1010
        "height": 923 - 211   # 712
    },
    
    # 세로에서 가로로 전환될 때 사용할 캡처 영역
    "portrait_to_landscape_area": {
        "left": 855,
        "top": 209,
        "width": 1561 - 855,  # 706
        "height": 708 - 209   # 499
    },
    
    # 가로에서 세로로 전환될 때 사용할 캡처 영역 (미정)
    "landscape_to_portrait_area": {
        "left": 900,          # 임시값 - 추후 설정
        "top": 200,           # 임시값 - 추후 설정
        "width": 600,         # 임시값 - 추후 설정
        "height": 500         # 임시값 - 추후 설정
    },
    
    # 방향 확인 설정
    "orientation_detection": {
        "click_coord": [1279, 177],  # 더블클릭할 좌표
        "template_area": {           # 템플릿 매칭할 영역
            "left": 1270,
            "top": 160,
            "width": 50,
            "height": 35
        }
    },
    
    # 페이지별 방향 감지 설정 (새로 추가)
    "page_orientation_detection": {
        "check_area_1": {           # 첫 번째 방향 확인 영역
            "left": 913,
            "top": 479,
            "width": 933 - 913,     # 20
            "height": 501 - 479     # 22
        },
        "check_area_2": {           # 두 번째 방향 확인 영역
            "left": 1473,
            "top": 361,
            "width": 1492 - 1473,   # 19
            "height": 374 - 361     # 13
        },
        "gray_threshold": 50,       # 회색 판단 임계값 (사용 안함)
        "gray_tolerance": 10        # RGB(250,250,250) 허용 오차 (각 채널별)
    },
    
    # 페이지 네비게이션 설정
    "navigation": {
        "next_page_coord": [894, 176],      # 다음 페이지 버튼 좌표
        "prepare_click_coord": [1359, 180]  # 가로 보고서 준비용 클릭 좌표
    },
    
    # 스크롤 설정
    "scroll": {
        "amount": 5,              # 스크롤 양 (양수로 변경)
        "max_scrolls": 50,        # 최대 스크롤 횟수
        "default_delay": 1500,    # 기본 딜레이 (ms) - 더 길게 설정
        "similarity_threshold": 0.90  # 이미지 유사도 임계값 (더 낮게 설정)
    }
}

# PDF 생성 관련 설정
PDF_SETTINGS = {
    # 페이지 크기 설정
    "page_size": "A4",  # A4, Letter, Legal 등
    
    # 방향 감지 키워드
    "orientation_keywords": {
        "portrait": "63%",   # 세로 방향을 나타내는 텍스트
        "landscape": "120%"  # 가로 방향을 나타내는 텍스트
    },
    
    # 이미지 품질 설정
    "image_quality": {
        "dpi": 300,           # 해상도 (150 → 300으로 증가)
        "compression": False, # 압축 비활성화 (품질 우선)
        "scale_factor": 2.0,  # 이미지 확대 배율 (2배)
        "use_lanczos": True,  # LANCZOS 리샘플링 사용 (고품질)
        "sharpness": 1.3,     # 선명도 향상 (1.3배)
        "contrast": 1.1,      # 대비 향상 (1.1배)
        "brightness": 1.05    # 밝기 조정 (1.05배)
    }
}

# UI 관련 설정
UI_SETTINGS = {
    # 윈도우 크기
    "window": {
        "width": 600,
        "height": 500,
        "title": "웹 페이지 PDF 캡처 도구"
    },
    
    # 기본값
    "defaults": {
        "scroll_delay": 1500,   # 기본 스크롤 딜레이 (더 길게)
        "page_height": 1000,    # 기본 페이지 높이
        "output_format": "capture_{timestamp}.pdf"  # 출력 파일명 형식
    },
    
    # 입력 범위
    "ranges": {
        "scroll_delay": {"min": 100, "max": 5000},
        "page_height": {"min": 500, "max": 3000}
    }
}

# 디버그 및 로깅 설정
DEBUG_SETTINGS = {
    "enable_debug": True,       # 디버그 모드
    "save_temp_images": True,   # 임시 이미지 저장 여부
    "log_level": "INFO",        # 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    "temp_dir": "temp_capture"  # 임시 파일 디렉토리
}

# 안전장치 설정
SAFETY_SETTINGS = {
    "max_capture_time": 600,    # 최대 캡처 시간 (초)
    "min_image_size": 10000,    # 최소 이미지 크기 (바이트)
    "max_pdf_pages": 100        # 최대 PDF 페이지 수
} 