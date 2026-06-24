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
后端服务启动脚本
================

启动FastAPI后端服务

作者: QSIR
版本: 1.0
"""

import uvicorn
import sys
import os
import logging

# 禁用 Python 输出缓冲，确保日志实时输出
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 启动后端服务...")
    print("=" * 80)
    
    # 配置日志输出到控制台，禁用缓冲
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True  # 重新配置日志
    )
    
    # 设置所有日志处理器都不缓冲
    for handler in logging.root.handlers:
        handler.flush()
    
    # 设置各个模块的日志级别
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    
    # 设置共享模块和智能体的日志级别
    logging.getLogger('shared').setLevel(logging.INFO)
    logging.getLogger('shared.agents').setLevel(logging.INFO)
    logging.getLogger('shared.llm_caller').setLevel(logging.INFO)
    
    # 设置智能体的详细日志级别
    agent_loggers = [
        'BaseAgent', 'CybertwinAgent', 'QuestioningAgent', 'InternalMedicineAgent', 
        'SurgicalAgent', 'SummaryAgent', 'TriageAgent', 'HistoryAgent',
        'ComprehensiveAgent', 'ImageAnalysisCoordinator', 'IntentRecognition'
    ]
    for agent_name in agent_loggers:
        logging.getLogger(agent_name).setLevel(logging.INFO)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,  # 启用访问日志
        use_colors=True   # 启用颜色输出
    )
