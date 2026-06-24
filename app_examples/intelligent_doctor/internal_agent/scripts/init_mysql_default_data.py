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
初始化MySQL默认数据脚本
======================

初始化MySQL数据库中的默认数据（医院、权限等）
"""

import asyncio
import sys
import os
import logging
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mysql_database_manager import mysql_db_manager
import aiomysql

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_default_data():
    """初始化默认数据"""
    logger.info("=" * 60)
    logger.info("初始化MySQL默认数据")
    logger.info("=" * 60)
    
    try:
        await mysql_db_manager.initialize()
        
        async with mysql_db_manager.pool.get_connection() as conn:
            async with conn.cursor() as cursor:
                # 初始化医院数据
                logger.info("\n初始化医院数据...")
                await cursor.execute("""
                    INSERT INTO hospitals (hospital_id, hospital_name, location, status) VALUES
                    ('BJ001', '北京医院', '北京', 'active'),
                    ('SH001', '上海医院', '上海', 'active'),
                    ('TEST001', '测试医院', '测试城市', 'active')
                    ON DUPLICATE KEY UPDATE
                        hospital_name = VALUES(hospital_name),
                        location = VALUES(location),
                        status = VALUES(status)
                """)
                await conn.commit()
                logger.info("✅ 医院数据初始化成功")
                
                # 检查权限数据
                await cursor.execute("SELECT COUNT(*) as count FROM permissions")
                row = await cursor.fetchone()
                perm_count = row[0] if row else 0
                
                if perm_count == 0:
                    logger.info("\n初始化权限数据...")
                    await cursor.execute("""
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
                            granted = VALUES(granted)
                    """)
                    await conn.commit()
                    logger.info("✅ 权限数据初始化成功")
                else:
                    logger.info(f"✅ 权限数据已存在（{perm_count}条记录），跳过初始化")
        
        # 验证数据
        logger.info("\n验证初始化结果...")
        hospitals = await mysql_db_manager.get_hospitals()
        logger.info(f"✅ 医院数据: {len(hospitals)} 条记录")
        for hospital in hospitals:
            logger.info(f"  - {hospital.get('hospital_name')} ({hospital.get('location')})")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 默认数据初始化完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ 初始化失败: {str(e)}")
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
    asyncio.run(init_default_data())

