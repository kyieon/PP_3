"""
교량 상태평가 가중치 관리 모듈
"""
import json
from datetime import datetime
import os
from utils.common import get_db_connection

class EvaluationWeightManager:
    def __init__(self):
        """
        평가 가중치 관리자 초기화 (PostgreSQL 사용)
        """
        self.init_database()
    
    def init_database(self):
        """
        evaluation_weight 테이블 생성
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluation_weight (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    slab DECIMAL(5,2) DEFAULT 0,
                    girder DECIMAL(5,2) DEFAULT 0,
                    crossbeam DECIMAL(5,2) DEFAULT 0,
                    pavement DECIMAL(5,2) DEFAULT 0,
                    drainage DECIMAL(5,2) DEFAULT 0,
                    railing DECIMAL(5,2) DEFAULT 0,
                    expansion_joint DECIMAL(5,2) DEFAULT 0,
                    bearing DECIMAL(5,2) DEFAULT 0,
                    abutment DECIMAL(5,2) DEFAULT 0,
                    pier DECIMAL(5,2) DEFAULT 0,
                    foundation DECIMAL(5,2) DEFAULT 0,
                    carbonation_upper DECIMAL(5,2) DEFAULT 0,
                    carbonation_lower DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filename)
                )
            ''')
            conn.commit()
            conn.close()
            print("evaluation_weight 테이블이 생성되었습니다.")
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
import psycopg2
import json
from datetime import datetime
import os

class EvaluationWeightManager:
    def __init__(self):
        """
        평가 가중치 관리자 초기화
        """
        self.init_database()
    
    def init_database(self):
        """
        evaluation_weight 테이블 생성
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluation_weight (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    slab DECIMAL(5,2) DEFAULT 0,
                    girder DECIMAL(5,2) DEFAULT 0,
                    crossbeam DECIMAL(5,2) DEFAULT 0,
                    pavement DECIMAL(5,2) DEFAULT 0,
                    drainage DECIMAL(5,2) DEFAULT 0,
                    railing DECIMAL(5,2) DEFAULT 0,
                    expansion_joint DECIMAL(5,2) DEFAULT 0,
                    bearing DECIMAL(5,2) DEFAULT 0,
                    abutment DECIMAL(5,2) DEFAULT 0,
                    pier DECIMAL(5,2) DEFAULT 0,
                    foundation DECIMAL(5,2) DEFAULT 0,
                    carbonation_upper DECIMAL(5,2) DEFAULT 0,
                    carbonation_lower DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filename)
                )
            ''')
            conn.commit()
            conn.close()
            print("evaluation_weight 테이블이 생성되었습니다.")
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
            if 'conn' in locals():
                conn.close()
    
    def save_weights(self, filename, weights):
        """
        교량별 가중치 저장
        
        Args:
            filename (str): 교량 파일명
            weights (dict): 가중치 딕셔너리
            
        Returns:
            dict: 결과 정보
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 기존 데이터 확인
            cursor.execute('SELECT id FROM evaluation_weight WHERE filename = %s', (filename,))
            existing = cursor.fetchone()
            
            if existing:
                # 업데이트
                cursor.execute('''
                    UPDATE evaluation_weight SET
                        slab = %s, girder = %s, crossbeam = %s, pavement = %s,
                        drainage = %s, railing = %s, expansion_joint = %s, bearing = %s,
                        abutment = %s, pier = %s, foundation = %s, 
                        carbonation_upper = %s, carbonation_lower = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE filename = %s
                ''', (
                    weights.get('slab', 0),
                    weights.get('girder', 0),
                    weights.get('crossbeam', 0),
                    weights.get('pavement', 0),
                    weights.get('drainage', 0),
                    weights.get('railing', 0),
                    weights.get('expansionJoint', 0),
                    weights.get('bearing', 0),
                    weights.get('abutment', 0),
                    weights.get('pier', 0),
                    weights.get('foundation', 0),
                    weights.get('carbonation_upper', 0),
                    weights.get('carbonation_lower', 0),
                    filename
                ))
                action = "업데이트"
            else:
                # 새로 삽입
                cursor.execute('''
                    INSERT INTO evaluation_weight (
                        filename, slab, girder, crossbeam, pavement,
                        drainage, railing, expansion_joint, bearing,
                        abutment, pier, foundation, carbonation_upper, carbonation_lower
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    filename,
                    weights.get('slab', 0),
                    weights.get('girder', 0),
                    weights.get('crossbeam', 0),
                    weights.get('pavement', 0),
                    weights.get('drainage', 0),
                    weights.get('railing', 0),
                    weights.get('expansionJoint', 0),
                    weights.get('bearing', 0),
                    weights.get('abutment', 0),
                    weights.get('pier', 0),
                    weights.get('foundation', 0),
                    weights.get('carbonation_upper', 0),
                    weights.get('carbonation_lower', 0)
                ))
                action = "저장"
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'가중치가 성공적으로 {action}되었습니다.',
                'filename': filename
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'가중치 저장 중 오류 발생: {str(e)}'
            }
    
    def load_weights(self, filename):
        """
        교량별 가중치 불러오기
        
        Args:
            filename (str): 교량 파일명
            
        Returns:
            dict: 가중치 정보
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT slab, girder, crossbeam, pavement, drainage, railing,
                       expansion_joint, bearing, abutment, pier, foundation,
                       carbonation_upper, carbonation_lower, updated_at
                FROM evaluation_weight 
                WHERE filename = %s
            ''', (filename,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                weights = {
                    'slab': float(result[0]) if result[0] is not None else 0,
                    'girder': float(result[1]) if result[1] is not None else 0,
                    'crossbeam': float(result[2]) if result[2] is not None else 0,
                    'pavement': float(result[3]) if result[3] is not None else 0,
                    'drainage': float(result[4]) if result[4] is not None else 0,
                    'railing': float(result[5]) if result[5] is not None else 0,
                    'expansionJoint': float(result[6]) if result[6] is not None else 0,
                    'bearing': float(result[7]) if result[7] is not None else 0,
                    'abutment': float(result[8]) if result[8] is not None else 0,
                    'pier': float(result[9]) if result[9] is not None else 0,
                    'foundation': float(result[10]) if result[10] is not None else 0,
                    'carbonation_upper': float(result[11]) if result[11] is not None else 0,
                    'carbonation_lower': float(result[12]) if result[12] is not None else 0,
                    'updated_at': result[13]
                }
                
                return {
                    'success': True,
                    'weights': weights,
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'error': '저장된 가중치가 없습니다.',
                    'weights': None
                }
                
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'가중치 불러오기 중 오류 발생: {str(e)}'
            }
    
    def get_default_weights(self, structure_type="일반"):
        """
        구조형식에 따른 기본 가중치 반환
        
        Args:
            structure_type (str): 구조형식
            
        Returns:
            dict: 기본 가중치
        """
        # 구조형식별 기본 가중치 정의
        default_weights = {
            "일반": {
                'slab': 25,
                'girder': 20,
                'crossbeam': 15,
                'pavement': 10,
                'drainage': 5,
                'railing': 5,
                'expansionJoint': 10,
                'bearing': 10,
                'abutment': 0,
                'pier': 0,
                'foundation': 0,
                'carbonation_upper': 0,
                'carbonation_lower': 0
            },
            "강교": {
                'slab': 20,
                'girder': 25,
                'crossbeam': 15,
                'pavement': 10,
                'drainage': 5,
                'railing': 5,
                'expansionJoint': 10,
                'bearing': 10,
                'abutment': 0,
                'pier': 0,
                'foundation': 0,
                'carbonation_upper': 0,
                'carbonation_lower': 0
            },
            "콘크리트교": {
                'slab': 25,
                'girder': 20,
                'crossbeam': 15,
                'pavement': 10,
                'drainage': 5,
                'railing': 5,
                'expansionJoint': 10,
                'bearing': 10,
                'abutment': 0,
                'pier': 0,
                'foundation': 0,
                'carbonation_upper': 0,
                'carbonation_lower': 0
            }
        }
        
        return default_weights.get(structure_type, default_weights["일반"])
    
    def delete_weights(self, filename):
        """
        교량별 가중치 삭제
        
        Args:
            filename (str): 교량 파일명
            
        Returns:
            dict: 결과 정보
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM evaluation_weight WHERE filename = %s', (filename,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {
                    'success': True,
                    'message': '가중치가 삭제되었습니다.'
                }
            else:
                conn.close()
                return {
                    'success': False,
                    'error': '삭제할 가중치가 없습니다.'
                }
                
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'가중치 삭제 중 오류 발생: {str(e)}'
            }
    
    def list_all_weights(self):
        """
        모든 교량의 가중치 목록 조회
        
        Returns:
            dict: 가중치 목록
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT filename, slab, girder, crossbeam, pavement, drainage, 
                       railing, expansion_joint, bearing, abutment, pier, foundation,
                       carbonation_upper, carbonation_lower, updated_at
                FROM evaluation_weight 
                ORDER BY updated_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            weights_list = []
            
            for row in results:
                weights_list.append({
                    'filename': row[0],
                    'weights': {
                        'slab': float(row[1]) if row[1] is not None else 0,
                        'girder': float(row[2]) if row[2] is not None else 0,
                        'crossbeam': float(row[3]) if row[3] is not None else 0,
                        'pavement': float(row[4]) if row[4] is not None else 0,
                        'drainage': float(row[5]) if row[5] is not None else 0,
                        'railing': float(row[6]) if row[6] is not None else 0,
                        'expansionJoint': float(row[7]) if row[7] is not None else 0,
                        'bearing': float(row[8]) if row[8] is not None else 0,
                        'abutment': float(row[9]) if row[9] is not None else 0,
                        'pier': float(row[10]) if row[10] is not None else 0,
                        'foundation': float(row[11]) if row[11] is not None else 0,
                        'carbonation_upper': float(row[12]) if row[12] is not None else 0,
                        'carbonation_lower': float(row[13]) if row[13] is not None else 0
                    },
                    'updated_at': row[14]
                })
            
            return {
                'success': True,
                'weights_list': weights_list
            }
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {
                'success': False,
                'error': f'가중치 목록 조회 중 오류 발생: {str(e)}'
            }


def create_weight_manager():
    """
    가중치 관리자 인스턴스 생성
    
    Returns:
        EvaluationWeightManager: 가중치 관리자 인스턴스
    """
    return EvaluationWeightManager()


# 사용 예제
if __name__ == "__main__":
    # 가중치 관리자 생성
    weight_manager = create_weight_manager()
    
    # 테스트 가중치 데이터
    test_weights = {
        'slab': 25,
        'girder': 20,
        'crossbeam': 15,
        'pavement': 10,
        'drainage': 5,
        'railing': 5,
        'expansionJoint': 10,
        'bearing': 10,
        'abutment': 0,
        'pier': 0,
        'foundation': 0,
        'carbonation_upper': 0,
        'carbonation_lower': 0
    }
    
    # 가중치 저장 테스트
    result = weight_manager.save_weights("test_bridge.xlsx", test_weights)
    print("저장 결과:", result)
    
    # 가중치 불러오기 테스트
    result = weight_manager.load_weights("test_bridge.xlsx")
    print("불러오기 결과:", result)
    
    # 모든 가중치 목록 조회 테스트
    result = weight_manager.list_all_weights()
    print("목록 조회 결과:", result)
