# JSON 직렬화를 위한 수정된 상태평가 함수

def convert_numpy_types(obj):
    """numpy/pandas 타입을 Python 네이티브 타입으로 변환"""
    import numpy as np
    import pandas as pd
    
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

# 이 함수를 app.py의 condition_evaluation 라우트에 추가
