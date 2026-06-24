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
检查MySQL默认数据脚本
====================

检查MySQL数据库中是否需要初始化默认数据
"""

import asyncio
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mysql_database_manager import mysql_db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_default_data():
    """检查默认数据"""
    logger.info("=" * 60)
    logger.info("检查MySQL默认数据")
    logger.info("=" * 60)
    
    try:
        await mysql_db_manager.initialize()
        
        # 检查医院数据
        hospitals = await mysql_db_manager.get_hospitals()
        logger.info(f"\n医院数据: {len(hospitals)} 条记录")
        
        if len(hospitals) == 0:
            logger.warning("⚠️ hospitals表为空，需要初始化默认数据")
            logger.info("\n执行以下SQL初始化默认数据:")
            logger.info("""
INSERT INTO hospitals (hospital_id, hospital_name, location, status) VALUES
('BJ001', '北京医院', '北京', 'active'),
('SH001', '上海医院', '上海', 'active'),
('TEST001', '测试医院', '测试城市', 'active')
ON DUPLICATE KEY UPDATE
    hospital_name = VALUES(hospital_name),
    location = VALUES(location),
    status = VALUES(status);
            """)
        else:
            logger.info("✅ hospitals表已有数据:")
            for hospital in hospitals:
                logger.info(f"  - {hospital.get('hospital_name')} ({hospital.get('location')})")
        
        # 检查权限数据
        async with mysql_db_manager.pool.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT COUNT(*) as count FROM permissions")
                row = await cursor.fetchone()
                perm_count = row['count'] if row else 0
        
        logger.info(f"\n权限数据: {perm_count} 条记录")
        
        if perm_count == 0:
            logger.warning("⚠️ permissions表为空，需要初始化默认数据")
            logger.info("\n执行以下SQL初始化默认数据:")
            logger.info("""
INSERT INTO permissions (role, resource, action, granted) VALUES
('patient', 'medical_records', 'read', TRUE),
('patient', 'medical_images', 'read', TRUE),
('patient', 'chat_history', 'read', TRUE),
('patient', 'chat_history', 'write', TRUE),
('doctor', 'medical_records', 'read', TRUE),
('doctor', 'medical_records', 'write', TRUE),
('doctor', 'medical_images', 'read', TRUE),
('doctor', 'medical_images', 'write', TRUE),
('doctor', 'chat_history', 'read', TRUE),
('doctor', 'chat_history', 'write', TRUE),
('admin', '*', '*', TRUE)
ON DUPLICATE KEY UPDATE
    granted = VALUES(granted);
            """)
        else:
            logger.info("✅ permissions表已有数据")
        
        logger.info("\n" + "=" * 60)
        logger.info("检查完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ 检查失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        try:
            await mysql_db_manager.close()
        except:
            pass
    
    return True

if __name__ == "__main__":
    import aiomysql
    asyncio.run(check_default_data())

