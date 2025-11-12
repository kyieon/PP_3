"""
교량 상태평가 가중치 API 엔드포인트
"""
from flask import Blueprint, request, jsonify
from utils.evaluation_weights import create_weight_manager
import logging

# 블루프린트 생성
evaluation_weights_bp = Blueprint('evaluation_weights', __name__)

# 로깅 설정
logger = logging.getLogger(__name__)

@evaluation_weights_bp.route('/save_evaluation_weights', methods=['POST'])
def save_evaluation_weights():
    """
    교량별 평가 가중치 저장 API
    
    Request Body:
    {
        "filename": "bridge_name.xlsx",
        "weights": {
            "slab": 25,
            "girder": 20,
            "crossbeam": 15,
            ...
        }
    }
    
    Returns:
        JSON: 저장 결과
    """
    try:
        # 요청 데이터 검증
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type이 application/json이어야 합니다.'
            }), 400
        
        data = request.get_json()
        
        # 필수 필드 확인
        if 'filename' not in data:
            return jsonify({
                'success': False,
                'error': 'filename이 필요합니다.'
            }), 400
        
        if 'weights' not in data:
            return jsonify({
                'success': False,
                'error': 'weights가 필요합니다.'
            }), 400
        
        filename = data['filename']
        weights = data['weights']
        
        # 가중치 데이터 유효성 검사
        required_weight_fields = [
            'slab', 'girder', 'crossbeam', 'pavement', 'drainage', 'railing',
            'expansionJoint', 'bearing', 'abutment', 'pier', 'foundation',
            'carbonation_upper', 'carbonation_lower'
        ]
        
        # 가중치 저장
        weight_manager = create_weight_manager()
        result = weight_manager.save_weights(filename, weights)
        
        if result['success']:
            logger.info(f"가중치 저장 성공 - 파일명: {filename}")
            return jsonify(result), 200
        else:
            logger.error(f"가중치 저장 실패 - 파일명: {filename}, 오류: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"가중치 저장 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500


@evaluation_weights_bp.route('/load_evaluation_weights', methods=['GET'])
def load_evaluation_weights():
    """
    교량별 평가 가중치 불러오기 API
    
    Query Parameters:
        filename (str): 교량 파일명
    
    Returns:
        JSON: 가중치 데이터
    """
    try:
        # 쿼리 파라미터에서 filename 가져오기
        filename = request.args.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'error': 'filename 파라미터가 필요합니다.'
            }), 400
        
        # 가중치 불러오기
        weight_manager = create_weight_manager()
        result = weight_manager.load_weights(filename)
        
        if result['success']:
            logger.info(f"가중치 불러오기 성공 - 파일명: {filename}")
            return jsonify(result), 200
        else:
            # 저장된 가중치가 없는 경우는 정상 케이스로 처리
            logger.info(f"저장된 가중치 없음 - 파일명: {filename}")
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"가중치 불러오기 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500


@evaluation_weights_bp.route('/get_default_weights', methods=['GET'])
def get_default_weights():
    """
    구조형식별 기본 가중치 반환 API
    
    Query Parameters:
        structure_type (str, optional): 구조형식 (기본값: "일반")
    
    Returns:
        JSON: 기본 가중치 데이터
    """
    try:
        structure_type = request.args.get('structure_type', '일반')
        
        # 기본 가중치 가져오기
        # 기본 가중치 조회
        weight_manager = create_weight_manager()
        default_weights = weight_manager.get_default_weights(structure_type)
        
        logger.info(f"기본 가중치 조회 성공 - 구조형식: {structure_type}")
        return jsonify({
            'success': True,
            'weights': default_weights,
            'structure_type': structure_type
        }), 200
        
    except Exception as e:
        logger.error(f"기본 가중치 조회 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500


@evaluation_weights_bp.route('/delete_evaluation_weights', methods=['DELETE'])
def delete_evaluation_weights():
    """
    교량별 평가 가중치 삭제 API
    
    Query Parameters:
        filename (str): 교량 파일명
    
    Returns:
        JSON: 삭제 결과
    """
    try:
        filename = request.args.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'error': 'filename 파라미터가 필요합니다.'
            }), 400
        
        # 가중치 삭제
        weight_manager = create_weight_manager()
        result = weight_manager.delete_weights(filename)
        
        if result['success']:
            logger.info(f"가중치 삭제 성공 - 파일명: {filename}")
            return jsonify(result), 200
        else:
            logger.warning(f"가중치 삭제 실패 - 파일명: {filename}, 오류: {result.get('error')}")
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"가중치 삭제 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500


@evaluation_weights_bp.route('/list_evaluation_weights', methods=['GET'])
def list_evaluation_weights():
    """
    모든 교량의 평가 가중치 목록 조회 API
    
    Returns:
        JSON: 가중치 목록
    """
    try:
        # 목록 조회
        result = weight_manager.list_all_weights()
        
        if result['success']:
            logger.info("가중치 목록 조회 성공")
            return jsonify(result), 200
        else:
            logger.error(f"가중치 목록 조회 실패: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"가중치 목록 조회 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500


@evaluation_weights_bp.route('/validate_weights', methods=['POST'])
def validate_weights():
    """
    가중치 데이터 유효성 검사 API
    
    Request Body:
    {
        "weights": {
            "slab": 25,
            "girder": 20,
            ...
        }
    }
    
    Returns:
        JSON: 유효성 검사 결과
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type이 application/json이어야 합니다.'
            }), 400
        
        data = request.get_json()
        weights = data.get('weights', {})
        
        # 가중치 유효성 검사
        validation_errors = []
        total_weight = 0
        
        required_fields = [
            'slab', 'girder', 'crossbeam', 'pavement', 'drainage', 'railing',
            'expansionJoint', 'bearing', 'abutment', 'pier', 'foundation',
            'carbonation_upper', 'carbonation_lower'
        ]
        
        for field in required_fields:
            value = weights.get(field, 0)
            
            # 숫자 타입 검사
            try:
                float_value = float(value)
                if float_value < 0:
                    validation_errors.append(f'{field}: 가중치는 0 이상이어야 합니다.')
                elif float_value > 100:
                    validation_errors.append(f'{field}: 가중치는 100 이하여야 합니다.')
                else:
                    total_weight += float_value
            except (ValueError, TypeError):
                validation_errors.append(f'{field}: 유효한 숫자여야 합니다.')
        
        # 총 가중치 검사 (상부구조 요소들만)
        superstructure_fields = ['slab', 'girder', 'crossbeam', 'pavement', 'drainage', 'railing', 'expansionJoint', 'bearing']
        superstructure_total = sum(float(weights.get(field, 0)) for field in superstructure_fields if weights.get(field, 0))
        
        if abs(superstructure_total - 100) > 0.01 and superstructure_total > 0:
            validation_errors.append(f'상부구조 가중치 합계가 100%가 아닙니다. (현재: {superstructure_total}%)')
        
        result = {
            'success': len(validation_errors) == 0,
            'total_weight': total_weight,
            'superstructure_weight': superstructure_total,
            'errors': validation_errors
        }
        
        logger.info(f"가중치 유효성 검사 - 결과: {'성공' if result['success'] else '실패'}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"가중치 유효성 검사 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'서버 내부 오류가 발생했습니다: {str(e)}'
        }), 500
