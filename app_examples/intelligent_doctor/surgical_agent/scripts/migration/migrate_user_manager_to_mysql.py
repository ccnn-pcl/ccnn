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
user_manager.py 数据迁移脚本
===========================

将SQLite数据库中的用户资料、偏好设置和活动记录迁移到MySQL

使用方法:
    python scripts/migration/migrate_user_manager_to_mysql.py
"""

import sys
import os
import json
import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
import aiomysql
from config.database_config import db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_user_profiles():
    """迁移用户资料数据"""
    try:
        # 连接SQLite
        sqlite_path = project_root / "data" / "user_profiles.db"
        if not sqlite_path.exists():
            print(f"SQLite数据库不存在: {sqlite_path}")
            return 0
        
        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_cursor = sqlite_conn.cursor()
        
        # 连接MySQL
        mysql_pool = await aiomysql.create_pool(
            host=db_config.config['host'],
            port=db_config.config['port'],
            db=db_config.config['database'],
            user=db_config.config['user'],
            password=db_config.config['password'],
            charset=db_config.config.get('charset', 'utf8mb4'),
            minsize=1,
            maxsize=5
        )
        
        count = 0
        async with mysql_pool.acquire() as mysql_conn:
            async with mysql_conn.cursor() as mysql_cursor:
                # 读取SQLite数据
                sqlite_cursor.execute("""
                    SELECT user_id, full_name, avatar, phone, address, birth_date, gender,
                           emergency_contact, medical_conditions, allergies, medications, preferences
                    FROM user_profiles
                """)
                
                rows = sqlite_cursor.fetchall()
                print(f"找到 {len(rows)} 条用户资料记录")
                
                for row in rows:
                    try:
                        await mysql_cursor.execute("""
                            INSERT INTO user_profiles 
                            (user_id, full_name, avatar, phone, address, birth_date, gender,
                             emergency_contact, medical_conditions, allergies, medications, preferences)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                full_name = VALUES(full_name),
                                avatar = VALUES(avatar),
                                phone = VALUES(phone),
                                address = VALUES(address),
                                birth_date = VALUES(birth_date),
                                gender = VALUES(gender),
                                emergency_contact = VALUES(emergency_contact),
                                medical_conditions = VALUES(medical_conditions),
                                allergies = VALUES(allergies),
                                medications = VALUES(medications),
                                preferences = VALUES(preferences),
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                            row[7], row[8], row[9], row[10], row[11]
                        ))
                        count += 1
                    except Exception as e:
                        print(f"迁移用户资料失败 {row[0]}: {str(e)}")
                
                await mysql_conn.commit()
        
        mysql_pool.close()
        await mysql_pool.wait_closed()
        sqlite_conn.close()
        
        print(f"成功迁移 {count} 条用户资料记录")
        return count
        
    except Exception as e:
        print(f"迁移用户资料失败: {str(e)}")
        return 0

async def migrate_user_preferences():
    """迁移用户偏好设置数据"""
    try:
        sqlite_path = project_root / "data" / "user_profiles.db"
        if not sqlite_path.exists():
            print(f"SQLite数据库不存在: {sqlite_path}")
            return 0
        
        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_cursor = sqlite_conn.cursor()
        
        # 检查表是否存在
        sqlite_cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'
        """)
        if not sqlite_cursor.fetchone():
            print("user_preferences 表不存在，跳过迁移")
            sqlite_conn.close()
            return 0
        
        mysql_pool = await aiomysql.create_pool(
            host=db_config.config['host'],
            port=db_config.config['port'],
            db=db_config.config['database'],
            user=db_config.config['user'],
            password=db_config.config['password'],
            charset=db_config.config.get('charset', 'utf8mb4'),
            minsize=1,
            maxsize=5
        )
        
        count = 0
        async with mysql_pool.acquire() as mysql_conn:
            async with mysql_conn.cursor() as mysql_cursor:
                sqlite_cursor.execute("""
                    SELECT user_id, language, timezone, theme, notifications, 
                           privacy_settings, display_settings
                    FROM user_preferences
                """)
                
                rows = sqlite_cursor.fetchall()
                print(f"找到 {len(rows)} 条用户偏好设置记录")
                
                for row in rows:
                    try:
                        await mysql_cursor.execute("""
                            INSERT INTO user_preferences 
                            (user_id, language, timezone, theme, notifications, privacy_settings, display_settings)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                language = VALUES(language),
                                timezone = VALUES(timezone),
                                theme = VALUES(theme),
                                notifications = VALUES(notifications),
                                privacy_settings = VALUES(privacy_settings),
                                display_settings = VALUES(display_settings),
                                updated_at = CURRENT_TIMESTAMP
                        """, row)
                        count += 1
                    except Exception as e:
                        print(f"迁移用户偏好设置失败 {row[0]}: {str(e)}")
                
                await mysql_conn.commit()
        
        mysql_pool.close()
        await mysql_pool.wait_closed()
        sqlite_conn.close()
        
        print(f"成功迁移 {count} 条用户偏好设置记录")
        return count
        
    except Exception as e:
        print(f"迁移用户偏好设置失败: {str(e)}")
        return 0

async def migrate_user_activities():
    """迁移用户活动记录"""
    try:
        sqlite_path = project_root / "data" / "user_profiles.db"
        if not sqlite_path.exists():
            print(f"SQLite数据库不存在: {sqlite_path}")
            return 0
        
        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_cursor = sqlite_conn.cursor()
        
        mysql_pool = await aiomysql.create_pool(
            host=db_config.config['host'],
            port=db_config.config['port'],
            db=db_config.config['database'],
            user=db_config.config['user'],
            password=db_config.config['password'],
            charset=db_config.config.get('charset', 'utf8mb4'),
            minsize=1,
            maxsize=5
        )
        
        count = 0
        async with mysql_pool.acquire() as mysql_conn:
            async with mysql_conn.cursor() as mysql_cursor:
                sqlite_cursor.execute("""
                    SELECT user_id, activity_type, description, timestamp, ip_address, user_agent, metadata
                    FROM user_activities
                """)
                
                rows = sqlite_cursor.fetchall()
                print(f"找到 {len(rows)} 条用户活动记录")
                
                for row in rows:
                    try:
                        await mysql_cursor.execute("""
                            INSERT INTO user_activities 
                            (user_id, activity_type, description, timestamp, ip_address, user_agent, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, row)
                        count += 1
                    except Exception as e:
                        print(f"迁移用户活动记录失败 {row[0]}: {str(e)}")
                
                await mysql_conn.commit()
        
        mysql_pool.close()
        await mysql_pool.wait_closed()
        sqlite_conn.close()
        
        print(f"成功迁移 {count} 条用户活动记录")
        return count
        
    except Exception as e:
        print(f"迁移用户活动记录失败: {str(e)}")
        return 0

async def main():
    """主函数"""
    print("=" * 60)
    print("user_manager.py 数据迁移脚本")
    print("=" * 60)
    print()
    
    # 检查数据库配置
    if not db_config or db_config.database_type != 'mysql':
        print("错误: 未配置MySQL数据库")
        print("请设置环境变量: DATABASE_TYPE=mysql")
        return
    
    print(f"MySQL配置: {db_config.config['host']}:{db_config.config['port']}/{db_config.config['database']}")
    print()
    
    # 执行迁移
    total = 0
    total += await migrate_user_profiles()
    total += await migrate_user_preferences()
    total += await migrate_user_activities()
    
    print()
    print("=" * 60)
    print(f"迁移完成！总共迁移 {total} 条记录")
    print("=" * 60)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

