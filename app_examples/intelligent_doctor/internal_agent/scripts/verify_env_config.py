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
"""验证.env文件配置"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database_config import load_env_file, db_config

# 加载.env文件
load_env_file()

print("=" * 60)
print("环境变量配置验证")
print("=" * 60)
print()

print(f"✅ DATABASE_TYPE: {db_config.database_type}")
print()

if db_config.database_type == 'mysql':
    print("MySQL配置:")
    print(f"  - Host: {db_config.config.get('host', 'N/A')}")
    print(f"  - Port: {db_config.config.get('port', 'N/A')}")
    print(f"  - Database: {db_config.config.get('database', 'N/A')}")
    print(f"  - User: {db_config.config.get('user', 'N/A')}")
    print(f"  - Pool Size: {db_config.config.get('pool_size', 'N/A')}")
    print(f"  - Charset: {db_config.config.get('charset', 'N/A')}")
    print()
    print("✅ MySQL配置已正确加载")
else:
    print(f"⚠️ 当前数据库类型: {db_config.database_type}")
    print("请确保 .env 文件中设置了 DATABASE_TYPE=mysql")

print()
print("=" * 60)

