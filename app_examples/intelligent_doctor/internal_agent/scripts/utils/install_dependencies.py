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

"""
安装PostgreSQL迁移所需依赖
========================
"""

import subprocess
import sys
import os

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[OK] {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {package} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("开始安装PostgreSQL迁移所需依赖...")
    
    # 需要安装的包
    packages = [
        "asyncpg",           # PostgreSQL异步驱动
        "psycopg2-binary",   # PostgreSQL同步驱动
        "python-dotenv",     # 环境变量管理
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n安装完成: {success_count}/{total_count} 个包安装成功")
    
    if success_count == total_count:
        print("[SUCCESS] 所有依赖安装成功！")
        return True
    else:
        print("[ERROR] 部分依赖安装失败，请手动安装")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
