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

# image_privacy.py
"""
图像隐私管理模块 - 医疗影像隐私保护系统
====================================

这个模块实现了医疗影像的隐私保护功能，确保用户数据的安全性和合规性。

主要功能：
1. 医院配置管理
   - 医院基本信息配置
   - 医院本地数据库管理
   - API端点配置

2. 隐私授权管理
   - 用户隐私授权请求
   - 授权状态检查
   - 授权记录管理

3. 数据库管理
   - 医疗影像数据存储
   - 隐私授权记录存储
   - 数据库连接管理

4. 隐私保护机制
   - 用户授权验证
   - 数据访问控制
   - 审计日志记录

设计模式：
- 数据类模式：使用@dataclass装饰器
- 管理器模式：ImagePrivacyManager管理隐私功能
- 配置模式：HospitalConfig管理医院配置

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from typing import List, Dict
import logging
from datetime import datetime
from pathlib import Path
import os
import sqlite3

@dataclass
class HospitalConfig:
    """
    医院配置数据类
    
    功能：
    - 存储医院基本信息
    - 管理医院本地数据库
    - 配置API端点
    
    设计模式：数据类模式，使用@dataclass装饰器
    """
    hospital_id: str      # 医院ID
    name: str            # 医院名称
    location: str        # 医院位置
    api_endpoint: str    # API端点
    model_config: dict   # 模型配置

    def __post_init__(self):
        """
        初始化医院本地数据库
        
        在数据类初始化后自动调用，用于设置数据库路径和初始化数据库
        """
        self.db_path = Path(f"data/{self.location}/{self.hospital_id}/medical_records.db")
        self.api_endpoint = self.api_endpoint or f"http://{self.hospital_id}.hospital.com/api"  # 添加默认值
        self._init_database()
    
    def _init_database(self):
        """
        初始化医院本地数据库
        
        功能：
        - 创建数据目录结构
        - 创建医疗影像表
        - 创建隐私授权表
        - 设置数据库约束
        
        异常处理：
            - 数据库创建失败时记录错误日志
            - 抛出异常以通知调用者
        """
        try:
            # 确保目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建数据库连接
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建必要的表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    image_data BLOB NOT NULL,
                    image_type TEXT NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS privacy_consents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    hospital_id TEXT NOT NULL,
                    consented BOOLEAN NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, hospital_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info(f"医院数据库初始化成功: {self.db_path}")
            
        except Exception as e:
            logging.error(f"医院数据库初始化失败: {str(e)}")
            raise

@dataclass
class ImagePrivacyConsent:
    """
    图像隐私授权数据类
    
    用于存储用户的隐私授权信息。
    """
    user_id: str         # 用户ID
    hospital_id: str     # 医院ID
    consented: bool      # 是否同意
    timestamp: str       # 授权时间戳

class ImagePrivacyManager:
    """
    图像隐私管理器
    
    功能：
    - 管理用户隐私授权
    - 检查授权状态
    - 记录授权历史
    
    设计模式：管理器模式
    """
    
    def __init__(self):
        """
        初始化图像隐私管理器
        
        功能：
        - 初始化授权存储字典
        - 为每个用户创建独立的授权记录
        """
        self.consents: Dict[str, Dict[str, ImagePrivacyConsent]] = {}
        
    def request_consent(self, user_id: str, hospital_id: str, hospital_name: str) -> bool:
        """
        请求隐私授权 - 在API环境中默认同意
        
        功能：
        - 创建用户授权记录
        - 在API环境中默认同意访问
        - 记录授权日志
        
        参数：
            user_id (str): 用户ID
            hospital_id (str): 医院ID
            hospital_name (str): 医院名称
            
        返回：
            bool: 授权结果，在API环境中默认为True
            
        注意：
            在实际应用中，这里应该通过其他方式获取用户授权
        """
        # 在API环境中，我们默认同意访问
        # 在实际应用中，这里应该通过其他方式获取用户授权
        self.consents.setdefault(user_id, {})[hospital_id] = ImagePrivacyConsent(
            user_id=user_id,
            hospital_id=hospital_id,
            consented=True,
            timestamp=datetime.now().isoformat()
        )
        logging.info(f"用户 {user_id} 同意访问 {hospital_name} 的影像数据")
        return True
        
    def has_consent(self, user_id: str, hospital_id: str) -> bool:
        """
        检查用户是否有授权
        
        功能：
        - 检查用户是否对指定医院有授权
        - 验证授权状态
        
        参数：
            user_id (str): 用户ID
            hospital_id (str): 医院ID
            
        返回：
            bool: 是否有授权
        """
        return (user_id in self.consents and 
                hospital_id in self.consents[user_id] and
                self.consents[user_id][hospital_id].consented)

def get_db_connection():
    """
    获取数据库连接
    
    功能：
    - 确保数据目录存在
    - 创建数据库连接
    - 设置行工厂
    
    返回：
        sqlite3.Connection: 数据库连接对象
    """
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
        conn = sqlite3.connect("data/medical_records.db")
        conn.row_factory = sqlite3.Row

# 配置已迁移到 shared/config/model_config.py
# 请使用 from shared.config.model_config import get_config 来获取配置