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
配置管理器 - 智能检测环境并设置API端点
====================================

这个模块提供了智能的配置管理功能，能够自动检测运行环境并设置合适的API端点。

主要功能：
1. 环境检测
   - 检测Kubernetes环境
   - 检测Docker环境
   - 检测本地开发环境

2. API端点管理
   - 自动设置合适的API端点
   - 测试API端点连通性
   - 提供备用端点

3. 配置优化
   - 根据环境自动选择最优配置
   - 支持环境变量覆盖
   - 提供配置验证

设计模式：静态方法模式

作者: QSIR
版本: 1.0
"""

import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ConfigManager:
    """
    配置管理器 - 智能检测环境并设置合适的配置

    功能：
    - 自动检测运行环境（Kubernetes/Docker/本地）
    - 根据环境设置合适的API端点
    - 测试API端点连通性
    - 提供备用端点机制

    设计模式：静态方法模式，所有方法都是静态方法
    """

    @staticmethod
    def detect_environment() -> str:
        """
        检测当前运行环境

        功能：
        - 检查Kubernetes环境标志
        - 检查Docker环境标志
        - 检查本地开发环境标志
        - 返回环境类型字符串

        返回：
            str: 环境类型，可能的值：
                - "kubernetes": Kubernetes环境
                - "docker": Docker环境
                - "local": 本地开发环境
        """
        # 检查是否在Kubernetes中运行
        if os.path.exists("/var/run/secrets/kubernetes.io/"):
            return "kubernetes"

        # 检查是否在Docker中运行
        if os.path.exists("/.dockerenv"):
            return "docker"

        # 检查是否在本地开发环境
        if os.getenv("STREAMLIT_SERVER_PORT"):
            return "local"

        # 默认返回本地环境
        return "local"

    @staticmethod
    def get_api_endpoint() -> str:
        """
        获取合适的API端点

        功能：
        - 检查环境变量中的API端点
        - 根据环境自动设置默认端点
        - 记录端点选择日志

        返回：
            str: API端点URL

        优先级：
            1. 环境变量 HOSPITAL_API_ENDPOINT
            2. 根据环境自动设置的端点
        """
        # 如果环境变量已设置，直接使用
        env_endpoint = os.getenv("HOSPITAL_API_ENDPOINT")
        if env_endpoint:
            logging.info(f"使用环境变量中的API端点: {env_endpoint}")
            return env_endpoint

        # 根据环境自动设置
        environment = ConfigManager.detect_environment()

        if environment == "kubernetes":
            endpoint = "http://main-app.private-doctor-system.svc.cluster.local:80"
            logging.info(f"Kubernetes环境，使用API端点: {endpoint}")
        elif environment == "docker":
            endpoint = "http://main-app:80"
            logging.info(f"Docker环境，使用API端点: {endpoint}")
        else:  # local
            endpoint = "http://localhost:8501"
            logging.info(f"本地开发环境，使用API端点: {endpoint}")

        return endpoint

    @staticmethod
    def test_api_connectivity(endpoint: str) -> bool:
        """
        测试API端点连通性

        功能：
        - 发送HTTP请求测试端点连通性
        - 检查响应状态码
        - 处理各种连接异常

        参数：
            endpoint (str): 要测试的API端点URL

        返回：
            bool: 连通性测试结果，True表示连通，False表示不连通

        异常处理：
            - ConnectionError: 连接错误
            - Timeout: 连接超时
            - 其他异常
        """
        try:
            from urllib.parse import urlparse

            import requests

            parsed_url = urlparse(endpoint)
            test_url = f"{endpoint}/_stcore/health"

            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                logging.info(f"API端点连通性测试成功: {endpoint}")
                return True
            else:
                logging.warning(f"API端点返回非200状态码: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            logging.warning(f"无法连接到API端点: {endpoint}")
            return False
        except requests.exceptions.Timeout:
            logging.warning(f"API端点连接超时: {endpoint}")
            return False
        except Exception as e:
            logging.error(f"API端点测试异常: {str(e)}")
            return False

    @staticmethod
    def get_optimal_api_endpoint() -> str:
        """
        获取最优的API端点

        功能：
        - 获取默认API端点
        - 测试默认端点连通性
        - 如果默认端点不可用，尝试备用端点
        - 返回可用的最优端点

        返回：
            str: 可用的API端点URL

        备用端点策略：
            1. 尝试默认端点
            2. 尝试localhost:8501
            3. 尝试localhost:80
            4. 返回默认端点（即使不可用）
        """
        # 获取默认端点
        default_endpoint = ConfigManager.get_api_endpoint()

        # 测试连通性
        if ConfigManager.test_api_connectivity(default_endpoint):
            return default_endpoint

        # 如果默认端点不可用，尝试备用端点
        backup_endpoints = [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://main-app:80",
            "http://main-app.private-doctor-system.svc.cluster.local:80",
        ]

        for backup_endpoint in backup_endpoints:
            if (
                backup_endpoint != default_endpoint
                and ConfigManager.test_api_connectivity(backup_endpoint)
            ):
                logging.info(f"使用备用API端点: {backup_endpoint}")
                return backup_endpoint

        # 如果所有端点都不可用，返回默认端点
        logging.warning(f"所有API端点都不可用，使用默认端点: {default_endpoint}")
        return default_endpoint


# 全局配置函数
def get_hospital_api_endpoint() -> str:
    """获取医院API端点的全局函数"""
    return ConfigManager.get_optimal_api_endpoint()


def print_environment_info():
    """打印环境信息"""
    print("=" * 60)
    print("环境检测结果")
    print("=" * 60)

    environment = ConfigManager.detect_environment()
    api_endpoint = ConfigManager.get_optimal_api_endpoint()

    print(f"检测到的环境: {environment}")
    print(f"使用的API端点: {api_endpoint}")
    print(
        f"环境变量HOSPITAL_API_ENDPOINT: {os.getenv('HOSPITAL_API_ENDPOINT', '未设置')}"
    )

    # 测试连通性
    is_connectable = ConfigManager.test_api_connectivity(api_endpoint)
    print(f"API端点连通性: {'✅ 正常' if is_connectable else '❌ 异常'}")

    print("=" * 60)


if __name__ == "__main__":
    print_environment_info()
