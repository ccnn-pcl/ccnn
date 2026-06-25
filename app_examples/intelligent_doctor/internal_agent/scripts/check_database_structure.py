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
数据库表结构检查脚本
==================

检查项目中的所有数据库文件，并输出详细的表结构信息
"""

import sqlite3
import os
import json
from pathlib import Path

def check_sqlite_database(db_path):
    """检查SQLite数据库的表结构"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        db_info = {
            "database_path": db_path,
            "database_type": "SQLite",
            "tables": {}
        }
        
        for table_name in tables:
            table_name = table_name[0]
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 获取表的行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # 获取示例数据（前3行）
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()
            
            db_info["tables"][table_name] = {
                "columns": columns,
                "row_count": row_count,
                "sample_data": sample_data
            }
        
        conn.close()
        return db_info
        
    except Exception as e:
        print(f"检查数据库 {db_path} 时出错: {str(e)}")
        return None

def main():
    """主函数"""
    print("="*80)
    print("项目数据库详细检查报告")
    print("="*80)
    
    # 检查data目录下的所有数据库文件
    data_dir = Path("data")
    db_files = []
    
    # 查找所有.db文件
    for file_path in data_dir.rglob("*.db"):
        db_files.append(str(file_path))
    
    print(f"\n发现 {len(db_files)} 个数据库文件:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    print("\n" + "="*80)
    print("数据库详细结构分析")
    print("="*80)
    
    for db_file in db_files:
        print(f"\n数据库: {db_file}")
        print("-" * 60)
        
        db_info = check_sqlite_database(db_file)
        if db_info:
            print(f"数据库类型: {db_info['database_type']}")
            print(f"表数量: {len(db_info['tables'])}")
            
            for table_name, table_info in db_info['tables'].items():
                print(f"\n表名: {table_name}")
                print(f"  行数: {table_info['row_count']}")
                print(f"  列数: {len(table_info['columns'])}")
                
                print(f"\n  列结构:")
                for col in table_info['columns']:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    pk_str = " (主键)" if pk else ""
                    not_null_str = " NOT NULL" if not_null else ""
                    default_str = f" DEFAULT {default_val}" if default_val else ""
                    print(f"    {col_id}: {col_name} {col_type}{not_null_str}{default_str}{pk_str}")
                
                if table_info['sample_data']:
                    print(f"\n  示例数据 (前3行):")
                    for i, row in enumerate(table_info['sample_data'], 1):
                        print(f"    行{i}: {row}")
                else:
                    print(f"\n  示例数据: 无数据")
        else:
            print("  无法读取数据库文件")
    
    # 生成PostgreSQL表结构信息
    print("\n" + "="*80)
    print("PostgreSQL数据库表结构 (从SQL脚本)")
    print("="*80)
    
    postgresql_tables = {
        "users": {
            "description": "用户认证表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户唯一ID"),
                ("username", "VARCHAR(100)", "用户名"),
                ("email", "VARCHAR(255)", "邮箱"),
                ("password_hash", "VARCHAR(255)", "密码哈希"),
                ("role", "VARCHAR(50)", "用户角色"),
                ("status", "VARCHAR(20)", "用户状态"),
                ("created_at", "TIMESTAMP", "创建时间"),
                ("updated_at", "TIMESTAMP", "更新时间")
            ]
        },
        "user_profiles": {
            "description": "用户档案表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("full_name", "VARCHAR(200)", "全名"),
                ("phone", "VARCHAR(20)", "电话"),
                ("address", "TEXT", "地址"),
                ("birth_date", "DATE", "出生日期"),
                ("gender", "VARCHAR(10)", "性别"),
                ("emergency_contact", "VARCHAR(200)", "紧急联系人"),
                ("allergies", "TEXT[]", "过敏史"),
                ("medications", "TEXT[]", "用药记录"),
                ("medical_conditions", "TEXT[]", "医疗条件"),
                ("created_at", "TIMESTAMP", "创建时间"),
                ("updated_at", "TIMESTAMP", "更新时间")
            ]
        },
        "chat_history": {
            "description": "聊天历史表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("role", "VARCHAR(20)", "角色"),
                ("content", "TEXT", "内容"),
                ("timestamp", "TIMESTAMP", "时间戳"),
                ("session_id", "VARCHAR(100)", "会话ID"),
                ("agent_name", "VARCHAR(100)", "智能体名称")
            ]
        },
        "medical_images": {
            "description": "医疗影像表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("hospital_id", "VARCHAR(50)", "医院ID"),
                ("image_data", "BYTEA", "图像数据"),
                ("image_type", "VARCHAR(50)", "图像类型"),
                ("image_category", "VARCHAR(50)", "图像分类"),
                ("examination_date", "DATE", "检查日期"),
                ("description", "TEXT", "描述"),
                ("filename", "VARCHAR(255)", "文件名"),
                ("file_size", "INTEGER", "文件大小"),
                ("file_path", "VARCHAR(500)", "文件路径"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "medical_records": {
            "description": "医疗记录表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("hospital_id", "VARCHAR(50)", "医院ID"),
                ("record_data", "TEXT", "记录数据"),
                ("record_type", "VARCHAR(50)", "记录类型"),
                ("description", "TEXT", "描述"),
                ("filename", "VARCHAR(255)", "文件名"),
                ("file_size", "INTEGER", "文件大小"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "hospitals": {
            "description": "医院信息表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("hospital_id", "VARCHAR(50)", "医院ID"),
                ("hospital_name", "VARCHAR(200)", "医院名称"),
                ("location", "VARCHAR(100)", "位置"),
                ("api_endpoint", "VARCHAR(500)", "API端点"),
                ("model_config", "JSONB", "模型配置"),
                ("status", "VARCHAR(20)", "状态"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "permissions": {
            "description": "权限表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("role", "VARCHAR(50)", "角色"),
                ("resource", "VARCHAR(100)", "资源"),
                ("action", "VARCHAR(50)", "操作"),
                ("granted", "BOOLEAN", "是否授权"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "audit_logs": {
            "description": "审计日志表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID"),
                ("action", "VARCHAR(100)", "操作"),
                ("resource", "VARCHAR(100)", "资源"),
                ("details", "JSONB", "详细信息"),
                ("ip_address", "INET", "IP地址"),
                ("user_agent", "TEXT", "用户代理"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "user_activities": {
            "description": "用户活动表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("activity_type", "VARCHAR(50)", "活动类型"),
                ("activity_data", "JSONB", "活动数据"),
                ("created_at", "TIMESTAMP", "创建时间")
            ]
        },
        "user_vitals": {
            "description": "体征数据表",
            "columns": [
                ("id", "SERIAL", "主键"),
                ("user_id", "VARCHAR(50)", "用户ID (外键)"),
                ("systolic_pressure", "INTEGER", "收缩压"),
                ("diastolic_pressure", "INTEGER", "舒张压"),
                ("heart_rate", "INTEGER", "心率"),
                ("temperature", "DECIMAL(4,1)", "体温"),
                ("weight", "DECIMAL(5,2)", "体重"),
                ("height", "DECIMAL(5,2)", "身高"),
                ("recorded_at", "TIMESTAMP", "记录时间")
            ]
        }
    }
    
    for table_name, table_info in postgresql_tables.items():
        print(f"\n表名: {table_name}")
        print(f"  描述: {table_info['description']}")
        print(f"  列数: {len(table_info['columns'])}")
        
        print(f"\n  列结构:")
        for col_name, col_type, col_desc in table_info['columns']:
            print(f"    {col_name}: {col_type} - {col_desc}")
    
    # 生成总结报告
    print("\n" + "="*80)
    print("数据库总结")
    print("="*80)
    
    print(f"\n数据库统计:")
    print(f"  SQLite数据库文件: {len(db_files)} 个")
    print(f"  PostgreSQL表数量: {len(postgresql_tables)} 个")
    
    print(f"\n数据库类型:")
    print(f"  1. SQLite数据库 (用于认证和缓存)")
    print(f"  2. PostgreSQL数据库 (主要业务数据库)")
    
    print(f"\n主要表分类:")
    print(f"  - 用户管理: users, user_profiles, permissions")
    print(f"  - 医疗数据: medical_images, medical_records, user_vitals")
    print(f"  - 系统功能: chat_history, hospitals, audit_logs, user_activities")
    
    # 保存报告到文件
    report_file = f"database_structure_report_{Path().cwd().name}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("项目数据库详细结构报告\n")
        f.write("="*50 + "\n\n")
        f.write(f"生成时间: {Path().cwd()}\n")
        f.write(f"SQLite数据库文件: {len(db_files)} 个\n")
        f.write(f"PostgreSQL表数量: {len(postgresql_tables)} 个\n\n")
        
        f.write("SQLite数据库文件列表:\n")
        for db_file in db_files:
            f.write(f"  - {db_file}\n")
        
        f.write("\nPostgreSQL表列表:\n")
        for table_name in postgresql_tables.keys():
            f.write(f"  - {table_name}\n")
    
    print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    main()
