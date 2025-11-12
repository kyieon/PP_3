from flask import Blueprint, app, request, jsonify
import pandas as pd
import sqlite3

from utils.common import get_db_connection, get_sqlalchemy_engine
from . import api_bp


# --- meta_keyword CRUD API ---

@api_bp.route('/meta_keyword', methods=['GET'])
def get_meta_keywords():
    """meta_id로 meta_keyword 목록 조회 (쿼리스트링 meta_id 사용 가능)"""
    meta_id = request.args.get('meta_id', type=int)
    engine = get_sqlalchemy_engine()
    if meta_id is not None:
        df = pd.read_sql("SELECT * FROM meta_keyword WHERE use_yn='Y' AND meta_id=%s", engine, params=(meta_id,))
    else:
        df = pd.read_sql("SELECT * FROM meta_keyword WHERE use_yn='Y'", engine)
    engine.dispose()
    return jsonify(df.to_dict(orient='records'))

@api_bp.route('/meta_keyword/<int:keyword_id>', methods=['GET'])
def get_meta_keyword(keyword_id):
    """특정 meta_keyword 조회"""
    engine = get_sqlalchemy_engine()
    df = pd.read_sql("SELECT * FROM meta_keyword WHERE id=%s", engine, params=(keyword_id,))
    engine.dispose()
    if df.empty:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(df.iloc[0].to_dict())

@api_bp.route('/meta_keyword', methods=['POST'])
def create_meta_keyword():
    """meta_keyword 신규 등록 (meta_id, file, line, etc 컬럼 포함)"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meta_keyword (keyword, use_yn, source, meta_id, file, line, etc) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            data.get('keyword'),
            data.get('use_yn', 'Y'),
            data.get('source'),
            data.get('meta_id'),
            data.get('file'),
            data.get('line'),
            data.get('etc')
        )
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'id': new_id}), 201

@api_bp.route('/meta_keyword/<int:keyword_id>', methods=['PUT'])
def update_meta_keyword(keyword_id):
    """meta_keyword 수정 (file, line, etc 컬럼 포함)"""
    data = request.json 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE meta_keyword SET keyword=%s, use_yn=%s, source=%s, file=%s, line=%s, etc=%s WHERE id=%s",
        (
            data.get('keyword'),
            data.get('use_yn', 'Y'),
            data.get('source'),
            data.get('file'),
            data.get('line'),
            data.get('etc'),
            keyword_id
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'result': 'ok'})  

@api_bp.route('/meta_keyword/<int:keyword_id>', methods=['DELETE'])
def delete_meta_keyword(keyword_id):
    """meta_keyword 삭제(사용안함 처리)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE meta_keyword SET use_yn='N' WHERE id=%s", (keyword_id,))
    conn.commit()
    conn.close() 
    return jsonify({'result': 'ok'})

@api_bp.route('/meta_keyword/bulk', methods=['POST'])
def bulk_save_meta_keywords():
    """meta_keyword 일괄 저장 (등록/수정, file/line/etc 포함)"""
    data = request.json
    keywords = data.get('keywords', [])
    conn = get_db_connection()
    cur = conn.cursor()
    for row in keywords:
        if row.get('id'):  # 기존 데이터면 update
            cur.execute(
                "UPDATE meta_keyword SET keyword=%s, use_yn=%s, source=%s, meta_id=%s, file=%s, line=%s, etc=%s WHERE id=%s",
                (
                    row.get('keyword'),
                    row.get('use_yn', 'Y'),
                    row.get('source'),
                    row.get('meta_id'),
                    row.get('file'),
                    row.get('line'),
                    row.get('etc'),
                    row['id']
                )
            )
        else:  # 신규 데이터면 insert
            cur.execute(
                "INSERT INTO meta_keyword (keyword, use_yn, source, meta_id, file, line, etc) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    row.get('keyword'),
                    row.get('use_yn', 'Y'),
                    row.get('source'),
                    row.get('meta_id'),
                    row.get('file'),
                    row.get('line'),
                    row.get('etc')
                )
            )
    conn.commit()
    conn.close()
    return jsonify({'result': 'ok'})
