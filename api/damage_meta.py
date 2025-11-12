from flask import Blueprint, app, request, jsonify
import pandas as pd
import sqlite3

from utils.common import get_db_connection, get_sqlalchemy_engine
from . import api_bp

 

@api_bp.route('/damage_meta/tree', methods=['GET'])
def get_damage_meta_tree():
    """손상유형 메타데이터 트리 구조 반환"""
    engine = get_sqlalchemy_engine()
    # DataFrame으로 바로 읽기
    df = pd.read_sql("SELECT * FROM damage_meta WHERE use_yn='Y'", engine)
    engine.dispose()

    if df.empty:
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

    # 트리 구조로 변환
    def build_tree(parent_id=None):
        nodes = []
        # parent_id가 None일 때는 isnull(), 아닐 때는 == parent_id
        if parent_id is None:
            children = df[df['parent_id'].isnull()]
        else:
            children = df[df['parent_id'] == parent_id]
        for _, row in children.iterrows():
            node = {
                'id': row['id'],
                'category': row['category'],
                'keyword': row['keyword'],
                'description': row['description'],
                'children': build_tree(row['id'])
            }
            nodes.append(node)
        return nodes

    tree = build_tree(None)
    return jsonify(tree)

@api_bp.route('/damage_meta/<int:meta_id>', methods=['GET'])
def get_damage_meta(meta_id):
    """특정 메타데이터 상세 조회"""
    engine = get_sqlalchemy_engine()
    row = pd.read_sql("SELECT * FROM damage_meta WHERE id=%s", engine, params=(meta_id,))
    engine.dispose()
    if row.empty:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(row.iloc[0].to_dict())

@api_bp.route('/damage_meta', methods=['POST'])
def create_damage_meta():
    """메타데이터 신규 등록"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO damage_meta (category, keyword, description, parent_id, use_yn) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (data.get('category'), data.get('keyword'), data.get('description'), data.get('parent_id'), data.get('use_yn', 'Y'))
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({'id': new_id}), 201

@api_bp.route('/damage_meta/<int:meta_id>', methods=['PUT'])
def update_damage_meta(meta_id):
    """메타데이터 수정"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE damage_meta SET category=%s, keyword=%s, description=%s, parent_id=%s, use_yn=%s WHERE id=%s",
        (data.get('category'), data.get('keyword'), data.get('description'), data.get('parent_id'), data.get('use_yn', 'Y'), meta_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'result': 'ok'})

@api_bp.route('/damage_meta/<int:meta_id>', methods=['DELETE'])
def delete_damage_meta(meta_id):
    """메타데이터 삭제(사용안함 처리)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE damage_meta SET use_yn='N' WHERE id=%s", (meta_id,))
    conn.commit()
    conn.close()
    return jsonify({'result': 'ok'})


