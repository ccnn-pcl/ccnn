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
执行 user_manager.py MySQL迁移
==============================

自动执行表结构更新和数据迁移
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import aiomysql
from config.database_config import db_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def execute_sql_file(sql_file_path: Path):
    """执行SQL文件"""
    try:
        # 读取SQL文件
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割，但要注意字符串中的分号）
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        
        for char in sql_content:
            current_statement += char
            
            if char in ("'", '"', '`') and (not current_statement or current_statement[-2] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            if not in_string and char == ';':
                stmt = current_statement.strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
                current_statement = ""
        
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # 连接MySQL并执行
        pool = await aiomysql.create_pool(
            host=db_config.config['host'],
            port=db_config.config['port'],
            db=db_config.config['database'],
            user=db_config.config['user'],
            password=db_config.config['password'],
            charset=db_config.config.get('charset', 'utf8mb4'),
            minsize=1,
            maxsize=5
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for i, statement in enumerate(statements, 1):
                    if not statement or statement.startswith('--'):
                        continue
                    
                    try:
                        await cursor.execute(statement)
                        logger.info(f"执行SQL语句 {i}/{len(statements)}: 成功")
                    except Exception as e:
                        # 忽略"字段已存在"等错误
                        error_msg = str(e).lower()
                        if 'duplicate column' in error_msg or 'already exists' in error_msg:
                            logger.warning(f"执行SQL语句 {i}/{len(statements)}: 跳过（{str(e)}）")
                        else:
                            logger.error(f"执行SQL语句 {i}/{len(statements)}: 失败 - {str(e)}")
                            raise
                
                await conn.commit()
        
        pool.close()
        await pool.wait_closed()
        return True
        
    except Exception as e:
        logger.error(f"执行SQL文件失败: {str(e)}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("user_manager.py MySQL迁移执行脚本")
    print("=" * 60)
    print()
    
    # 检查数据库配置
    if not db_config or db_config.database_type != 'mysql':
        print("❌ 错误: 未配置MySQL数据库")
        print("请设置环境变量: DATABASE_TYPE=mysql")
        print("并配置MySQL连接信息（MYSQL_HOST, MYSQL_PORT等）")
        return 1
    
    print(f"✅ MySQL配置: {db_config.config['host']}:{db_config.config['port']}/{db_config.config['database']}")
    print()
    
    # 步骤1: 执行表结构更新
    print("步骤1: 更新MySQL表结构...")
    sql_file = project_root / "scripts" / "migrate_user_manager_tables.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL文件不存在: {sql_file}")
        return 1
    
    success = await execute_sql_file(sql_file)
    if not success:
        print("❌ 表结构更新失败")
        return 1
    
    print("✅ 表结构更新完成")
    print()
    
    # 步骤2: 检查是否有SQLite数据需要迁移
    print("步骤2: 检查SQLite数据...")
    sqlite_path = project_root / "data" / "user_profiles.db"
    
    if sqlite_path.exists():
        print(f"✅ 发现SQLite数据库: {sqlite_path}")
        print("执行数据迁移...")
        
        # 导入并运行迁移脚本
        try:
            from scripts.migration.migrate_user_manager_to_mysql import (
                migrate_user_profiles,
                migrate_user_preferences,
                migrate_user_activities
            )
            
            total = 0
            total += await migrate_user_profiles()
            total += await migrate_user_preferences()
            total += await migrate_user_activities()
            
            print(f"✅ 数据迁移完成，共迁移 {total} 条记录")
        except Exception as e:
            print(f"⚠️ 数据迁移失败: {str(e)}")
            print("可以稍后手动执行: python scripts/migration/migrate_user_manager_to_mysql.py")
    else:
        print("ℹ️ 未发现SQLite数据库，跳过数据迁移")
    
    print()
    print("=" * 60)
    print("✅ 迁移执行完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 测试用户资料管理功能")
    print("2. 验证数据是否正确迁移")
    print("3. 如果一切正常，可以删除SQLite数据库文件（可选）")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

