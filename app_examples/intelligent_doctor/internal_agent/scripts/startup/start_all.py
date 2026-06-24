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
全服务启动脚本
==============

同时启动前端和后端服务

作者: QSIR
版本: 1.0
"""

import subprocess
import sys
import os
import time
import threading

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

def start_backend():
    """启动后端服务"""
    print("启动后端服务...")
    subprocess.run([
        sys.executable, "-u", "scripts/startup/start_backend.py"  # -u 参数禁用输出缓冲
    ], stdout=sys.stdout, stderr=sys.stderr, bufsize=0)  # bufsize=0 禁用缓冲

def start_frontend():
    """启动前端服务"""
    print("启动前端服务...")
    # 等待后端服务启动
    time.sleep(3)
    subprocess.run([
        sys.executable, "-u", "scripts/startup/start_frontend.py"  # -u 参数禁用输出缓冲
    ])

if __name__ == "__main__":
    print("Cybertwin私人医生系统启动中...")
    print("=" * 50)
    
    # 创建线程启动服务
    backend_thread = threading.Thread(target=start_backend)
    frontend_thread = threading.Thread(target=start_frontend)
    
    # 启动后端服务
    backend_thread.start()
    
    # 启动前端服务
    frontend_thread.start()
    
    print("服务启动完成！")
    print("前端地址: http://localhost:8501")
    print("后端API: http://localhost:8000")
    print("API文档: http://localhost:8000/api/docs")
    
    try:
        # 等待线程完成
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        sys.exit(0)
