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
项目启动脚本
============

简化项目启动流程，自动检查环境和依赖。

作者: QSIR
版本: 1.0
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ProjectStarter:
    """项目启动器"""
    
    def __init__(self):
        """初始化启动器"""
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.config_file = self.project_root / "config.json"
        self.data_dir = self.project_root / "data"
        
    def check_python_version(self):
        """检查Python版本"""
        logger.info("检查Python版本...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"❌ Python版本过低: {version.major}.{version.minor}")
            logger.error("要求: Python 3.8+")
            return False
        
        logger.info(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_dependencies(self):
        """检查依赖"""
        logger.info("检查依赖...")
        
        if not self.requirements_file.exists():
            logger.error("❌ requirements.txt 文件不存在")
            return False
        
        try:
            # 检查关键依赖
            import streamlit
            import sqlite3
            import asyncio
            logger.info("✅ 核心依赖已安装")
            return True
        except ImportError as e:
            logger.error(f"❌ 缺少依赖: {e}")
            logger.info("请运行: pip install -r requirements.txt")
            return False
    
    def create_config(self):
        """创建配置文件"""
        logger.info("检查配置文件...")
        
        if not self.config_file.exists():
            logger.info("创建默认配置文件...")
            
            config = {
                "model": {
                    "provider": "qwen",
                    "api_key": "your-api-key-here",
                    "model": "qwen-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "database": {
                    "global_db_path": "data/global.db",
                    "user_db_path": "data/user.db",
                    "medical_db_path": "data/medical.db"
                },
                "auth": {
                    "enable_auth": False,
                    "session_timeout": 3600
                },
                "memory": {
                    "enable_cache": True,
                    "cache_size": 1000
                }
            }
            
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ 配置文件已创建")
        else:
            logger.info("✅ 配置文件已存在")
        
        return True
    
    def create_data_directories(self):
        """创建数据目录"""
        logger.info("检查数据目录...")
        
        directories = [
            self.data_dir,
            self.data_dir / "backups",
            self.data_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 目录已创建: {directory}")
        
        return True
    
    def check_agents_module(self):
        """检查智能体模块"""
        logger.info("检查智能体模块...")
        
        agents_dir = self.project_root / "agents"
        if not agents_dir.exists():
            logger.error("❌ agents目录不存在")
            return False
        
        # 检查关键文件
        key_files = [
            "agents/__init__.py",
            "agents/base_agent.py",
            "agents/coordinator/cybertwin_agent.py",
            "agents/medical/internal_medicine.py",
            "agents/llm/caller.py"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.error(f"❌ 缺少文件: {file_path}")
                return False
        
        logger.info("✅ 智能体模块完整")
        return True
    
    def run_quick_test(self):
        """运行快速测试"""
        logger.info("运行快速测试...")
        
        try:
            # 导入测试模块
            from quick_test import quick_test
            
            # 运行测试
            import asyncio
            result = asyncio.run(quick_test())
            
            if result:
                logger.info("✅ 快速测试通过")
                return True
            else:
                logger.error("❌ 快速测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 快速测试出错: {str(e)}")
            return False
    
    def start_streamlit(self):
        """启动Streamlit应用"""
        logger.info("启动Streamlit应用...")
        
        try:
            # 设置环境变量
            os.environ["PYTHONPATH"] = str(self.project_root)
            
            # 启动Streamlit
            cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
            
            logger.info("正在启动应用...")
            logger.info("访问地址: http://localhost:8501")
            logger.info("按 Ctrl+C 停止应用")
            
            subprocess.run(cmd, cwd=self.project_root)
            
        except KeyboardInterrupt:
            logger.info("应用已停止")
        except Exception as e:
            logger.error(f"❌ 启动失败: {str(e)}")
            return False
        
        return True
    
    def start(self):
        """启动项目"""
        logger.info("=" * 60)
        logger.info("医疗智能体项目启动器")
        logger.info("=" * 60)
        
        # 检查环境
        if not self.check_python_version():
            return False
        
        if not self.check_dependencies():
            return False
        
        if not self.check_agents_module():
            return False
        
        # 创建必要文件
        if not self.create_config():
            return False
        
        if not self.create_data_directories():
            return False
        
        # 运行测试
        if not self.run_quick_test():
            logger.warning("⚠️ 快速测试失败，但继续启动...")
        
        # 启动应用
        logger.info("=" * 60)
        logger.info("环境检查完成，启动应用...")
        logger.info("=" * 60)
        
        return self.start_streamlit()


def main():
    """主函数"""
    starter = ProjectStarter()
    
    try:
        success = starter.start()
        if success:
            logger.info("🎉 项目启动成功！")
        else:
            logger.error("❌ 项目启动失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断启动")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 启动出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
