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
MySQL数据库连接测试脚本
=====================

测试MySQL数据库连接和基本操作
"""

import asyncio
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database_config import db_config
from shared.mysql_database_manager import mysql_db_manager
import aiomysql

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_connection():
    """测试数据库连接"""
    logger.info("=" * 60)
    logger.info("MySQL数据库连接测试")
    logger.info("=" * 60)
    
    try:
        # 显示配置信息
        logger.info(f"\n数据库配置:")
        logger.info(f"  类型: {db_config.database_type}")
        logger.info(f"  主机: {db_config.config.get('host')}")
        logger.info(f"  端口: {db_config.config.get('port')}")
        logger.info(f"  数据库: {db_config.config.get('database')}")
        logger.info(f"  用户: {db_config.config.get('user')}")
        logger.info(f"  字符集: {db_config.config.get('charset', 'utf8mb4')}")
        
        # 初始化数据库管理器
        logger.info("\n初始化MySQL数据库管理器...")
        await mysql_db_manager.initialize()
        logger.info("✅ MySQL数据库管理器初始化成功")
        
        # 测试连接
        logger.info("\n测试数据库连接...")
        stats = await mysql_db_manager.get_statistics()
        logger.info("✅ 数据库连接成功")
        
        # 显示统计信息
        logger.info("\n数据库统计信息:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # 测试创建用户
        logger.info("\n测试创建用户...")
        test_user_id = "test_mysql_user_001"
        success = await mysql_db_manager.create_user(
            user_id=test_user_id,
            username="test_mysql_user",
            email="test@example.com",
            password_hash="test_hash",
            role="patient"
        )
        if success:
            logger.info("✅ 创建用户成功")
        else:
            logger.warning("⚠️ 创建用户失败（可能已存在）")
        
        # 测试获取用户
        logger.info("\n测试获取用户...")
        user = await mysql_db_manager.get_user(test_user_id)
        if user:
            logger.info(f"✅ 获取用户成功: {user.get('username')}")
        else:
            logger.warning("⚠️ 获取用户失败")
        
        # 测试存储聊天消息
        logger.info("\n测试存储聊天消息...")
        success = await mysql_db_manager.store_chat_message(
            user_id=test_user_id,
            role="user",
            content="这是一条测试消息",
            session_id="test_session_001",
            agent_name="test_agent"
        )
        if success:
            logger.info("✅ 存储聊天消息成功")
        else:
            logger.warning("⚠️ 存储聊天消息失败")
        
        # 测试获取聊天历史
        logger.info("\n测试获取聊天历史...")
        history = await mysql_db_manager.get_chat_history(test_user_id, limit=10)
        logger.info(f"✅ 获取聊天历史成功，共 {len(history)} 条记录")
        
        # 测试获取医院信息
        logger.info("\n测试获取医院信息...")
        hospitals = await mysql_db_manager.get_hospitals()
        logger.info(f"✅ 获取医院信息成功，共 {len(hospitals)} 家医院")
        for hospital in hospitals[:3]:  # 只显示前3个
            logger.info(f"  - {hospital.get('hospital_name')} ({hospital.get('location')})")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有测试通过！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # 关闭连接
        try:
            await mysql_db_manager.close()
            logger.info("\n数据库连接已关闭")
        except:
            pass
    
    return True

async def test_table_structure():
    """测试表结构"""
    logger.info("\n" + "=" * 60)
    logger.info("测试表结构")
    logger.info("=" * 60)
    
    try:
        await mysql_db_manager.initialize()
        
        # 测试各个表
        tables_to_test = [
            ('users', 'user_id'),
            ('chat_history', 'user_id'),
            ('medical_images', 'user_id'),
            ('medical_records', 'user_id'),
            ('hospitals', 'hospital_id'),
        ]
        
        async with mysql_db_manager.pool.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                for table_name, key_field in tables_to_test:
                    try:
                        await cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                        row = await cursor.fetchone()
                        count = row['count'] if row else 0
                        logger.info(f"✅ 表 {table_name} 存在，记录数: {count}")
                    except Exception as e:
                        logger.error(f"❌ 表 {table_name} 测试失败: {str(e)}")
        
        await mysql_db_manager.close()
        
    except Exception as e:
        logger.error(f"❌ 表结构测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # 检查数据库类型
    if db_config.database_type != 'mysql':
        logger.error(f"❌ 当前数据库类型为 {db_config.database_type}，不是 mysql")
        logger.info("请设置环境变量: DATABASE_TYPE=mysql")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(test_connection())
    asyncio.run(test_table_structure())

