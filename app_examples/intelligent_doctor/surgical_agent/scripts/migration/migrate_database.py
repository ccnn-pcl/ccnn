#!/usr/bin/env python3
# Copyright (c) 2026 PCL-CCNN
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-
"""
数据库迁移脚本
=============

用于更新现有数据库表结构，确保所有表结构一致

"""

import sqlite3
import os
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_medical_records_table(db_path: str):
    """
    迁移医疗记录表结构
    
    参数:
        db_path: 数据库文件路径
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medical_records'")
        if not cursor.fetchone():
            logger.info(f"表 medical_records 不存在于 {db_path}，跳过迁移")
            return
        
        # 检查现有列
        cursor.execute("PRAGMA table_info(medical_records)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"现有列: {columns}")
        
        # 添加缺失的列
        missing_columns = []
        
        if 'description' not in columns:
            missing_columns.append("ADD COLUMN description TEXT")
        
        if 'filename' not in columns:
            missing_columns.append("ADD COLUMN filename TEXT")
        
        if 'file_size' not in columns:
            missing_columns.append("ADD COLUMN file_size INTEGER")
        
        if missing_columns:
            for column_sql in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE medical_records {column_sql}")
                    logger.info(f"添加列: {column_sql}")
                except sqlite3.Error as e:
                    logger.warning(f"添加列失败: {column_sql}, 错误: {e}")
        
        # 更新UNIQUE约束
        try:
            # 删除旧的UNIQUE约束（如果存在）
            cursor.execute("CREATE TABLE medical_records_new AS SELECT * FROM medical_records")
            cursor.execute("DROP TABLE medical_records")
            cursor.execute("ALTER TABLE medical_records_new RENAME TO medical_records")
            
            # 添加新的UNIQUE约束
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_medical_records_unique 
                ON medical_records(user_id, hospital_id, record_type)
            """)
            logger.info("更新UNIQUE约束成功")
        except sqlite3.Error as e:
            logger.warning(f"更新UNIQUE约束失败: {e}")
        
        conn.commit()
        logger.info(f"数据库迁移完成: {db_path}")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {db_path}, 错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    logger.info("开始数据库迁移...")
    
    # 主数据库
    main_db_path = "data/medical_records.db"
    if os.path.exists(main_db_path):
        logger.info(f"迁移主数据库: {main_db_path}")
        migrate_medical_records_table(main_db_path)
    
    # 医院数据库
    data_dir = Path("data")
    if data_dir.exists():
        for city_dir in data_dir.iterdir():
            if city_dir.is_dir() and not city_dir.name.startswith('.'):
                for hospital_dir in city_dir.iterdir():
                    if hospital_dir.is_dir():
                        hospital_db_path = hospital_dir / "medical_records.db"
                        if hospital_db_path.exists():
                            logger.info(f"迁移医院数据库: {hospital_db_path}")
                            migrate_medical_records_table(str(hospital_db_path))
    
    logger.info("数据库迁移完成")

if __name__ == "__main__":
    main()
