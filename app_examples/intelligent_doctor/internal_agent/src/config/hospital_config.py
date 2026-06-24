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

# 添加到项目中
# filepath: hospital_config.py
"""
医院配置管理模块 - 多医院数据隔离和管理
====================================

这个模块实现了医院配置管理功能，支持多医院数据隔离和独立管理。

主要功能：
1. 医院实体管理
   - 医院基本信息配置
   - 医院本地数据库管理
   - 医院API端点配置

2. 数据存储管理
   - 医疗影像存储和检索
   - 病历记录存储和检索
   - 数据分类和索引

3. 医院注册管理
   - 医院注册表管理
   - 医院实例获取
   - 单例模式确保全局唯一

设计模式：
- 数据类模式：使用@dataclass装饰器
- 单例模式：HospitalRegistry使用单例模式

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from typing import Dict, Optional
import sqlite3
import logging
import os
from pathlib import Path
import datetime

@dataclass
class Hospital:
    """
    医院配置数据类
    
    功能：
    - 存储医院基本信息
    - 管理医院本地数据库
    - 提供数据存储和检索接口
    
    设计模式：数据类模式，使用@dataclass装饰器
    """
    id: str              # 医院ID
    name: str            # 医院名称
    location: str        # 医院位置
    api_endpoint: str    # API端点
    model_config: dict   # 模型配置
    
    def __post_init__(self):
        """
        初始化医院本地数据库
        
        在数据类初始化后自动调用，用于设置数据库路径和初始化数据库
        """
        self.db_path = Path(f"data/{self.location}/{self.id}/medical_records.db")
        self._init_database()
    
    def _init_database(self):
        """
        初始化数据库
        
        功能：
        - 创建数据目录结构
        - 创建影像表
        - 创建病历表
        - 设置数据库约束
        
        异常处理：
            - 数据库创建失败时记录错误日志
            - 抛出异常以通知调用者
        """
        try:
            # 确保数据目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            # 创建影像表
            c.execute('''CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                hospital_id TEXT NOT NULL,
                image_data BLOB NOT NULL,
                image_type TEXT NOT NULL,
                image_category TEXT NOT NULL,
                examination_date DATE NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, hospital_id, image_type, examination_date))''')
            
            # 创建病历表
            c.execute('''CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                hospital_id TEXT NOT NULL,
                record_data TEXT NOT NULL,
                record_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, hospital_id))''')
                
            conn.commit()
            conn.close()
            logging.info(f"初始化医院数据库成功: {self.name}")
            
        except Exception as e:
            logging.error(f"初始化医院数据库失败: {str(e)}")
            raise
    
    def store_image(self, user_id: str, image_bytes: bytes, image_type: str, examination_date: str = None, description: str = None) -> bool:
        """
        存储影像到本地数据库
        
        功能：
        - 解析影像类别
        - 存储影像数据到数据库
        - 处理重复数据（使用INSERT OR REPLACE）
        - 记录操作日志
        
        参数：
            user_id (str): 用户ID
            image_bytes (bytes): 影像数据
            image_type (str): 影像类型
            examination_date (str, optional): 检查日期，默认为当前日期
            description (str, optional): 影像描述
            
        返回：
            bool: 存储成功返回True，失败返回False
            
        影像分类：
            - radiology: 放射影像（X-ray, CT等）
            - ultrasound: 超声影像
            - dermatology: 皮肤科影像
            - endoscopy: 内窥镜影像
            - electrophysiology: 电生理影像
            - other: 其他类型
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            # 如果没有提供检查日期，使用当前日期
            if not examination_date:
                examination_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # 解析影像类别
            image_category = "other"
            if image_type in ["chest_xray", "chest_ct", "heart_ct", "head_ct", "abdominal_ct", "bone_xray", "bone_ct"]:
                image_category = "radiology"
            elif image_type in ["ultrasound", "color_ultrasound", "heart_ultrasound", "abdominal_ultrasound"]:
                image_category = "ultrasound"
            elif image_type in ["skin_photo", "dermoscopy"]:
                image_category = "dermatology"
            elif image_type in ["gastroscopy", "colonoscopy", "endoscopy"]:
                image_category = "endoscopy"
            elif image_type in ["ecg", "eeg", "emg"]:
                image_category = "electrophysiology"
            
            c.execute("""INSERT OR REPLACE INTO images 
                        (user_id, hospital_id, image_data, image_type, image_category, examination_date, description) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                     (user_id, self.id, image_bytes, image_type, image_category, examination_date, description))
            
            conn.commit()
            conn.close()
            
            logging.info(f"影像存储成功: {self.name}, user_id={user_id}, type={image_type}, date={examination_date}")
            return True
            
        except Exception as e:
            logging.error(f"[{self.name}] 存储影像失败: {str(e)}")
            return False
    
    def get_image(self, user_id: str, image_type: str = None) -> Optional[tuple]:
        """
        获取本地影像数据
        
        功能：
        - 查询指定用户的影像数据
        - 支持按影像类型过滤
        - 返回最新的影像数据
        - 记录查询日志
        
        参数：
            user_id (str): 用户ID
            image_type (str, optional): 影像类型，可选
            
        返回：
            Optional[tuple]: (image_bytes, image_type, timestamp) 或 None
            
        查询策略：
            - 如果指定了影像类型，只查询该类型的影像
            - 按时间降序排序，返回最新的影像
            - 限制返回1条记录
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            # 构建查询
            query = """
                SELECT image_data, image_type, timestamp 
                FROM images 
                WHERE user_id = ? AND hospital_id = ?
            """
            params = [user_id, self.id]
            
            # 如果指定了影像类型，添加类型过滤
            if image_type:
                query += " AND image_type = ?"
                params.append(image_type)
                logging.info(f"[{self.name}] 查询特定类型影像: type={image_type}")
            
            # 按时间降序排序，获取最新的影像
            query += " ORDER BY timestamp DESC LIMIT 1"
            
            c.execute(query, params)
            result = c.fetchone()
            conn.close()
            
            if result:
                logging.info(f"[{self.name}] 找到影像: type={result[1]}, time={result[2]}")
                return result
            else:
                logging.warning(f"[{self.name}] 未找到影像: user_id={user_id}, type={image_type}")
                return None
                
        except Exception as e:
            logging.error(f"[{self.name}] 获取影像失败: {str(e)}")
            return None
    
    def store_medical_record(self, user_id: str, record_data: str, record_type: str = "pdf") -> bool:
        """
        存储病历到本地数据库
        
        功能：
        - 存储病历数据到数据库
        - 处理重复数据（使用INSERT OR REPLACE）
        - 记录操作日志
        
        参数：
            user_id (str): 用户ID
            record_data (str): 病历数据
            record_type (str): 病历类型，默认为"pdf"
            
        返回：
            bool: 存储成功返回True，失败返回False
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            c.execute("""INSERT OR REPLACE INTO medical_records 
                        (user_id, hospital_id, record_data, record_type) 
                        VALUES (?, ?, ?, ?)""", 
                     (user_id, self.id, record_data, record_type))
            
            conn.commit()
            conn.close()
            
            logging.info(f"病历存储成功: {self.name}, user_id={user_id}")
            return True
            
        except Exception as e:
            logging.error(f"[{self.name}] 存储病历失败: {str(e)}")
            return False
    
    def get_medical_record(self, user_id: str) -> Optional[tuple]:
        """
        获取本地病历数据
        
        功能：
        - 查询指定用户的病历数据
        - 返回病历记录
        - 记录查询日志
        
        参数：
            user_id (str): 用户ID
            
        返回：
            Optional[tuple]: (record_data, record_type, timestamp) 或 None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            c.execute("""SELECT record_data, record_type, timestamp 
                        FROM medical_records WHERE user_id = ? AND hospital_id = ?""", (user_id, self.id))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                logging.info(f"获取病历成功: {self.name}, user_id={user_id}")
                return result
            else:
                logging.warning(f"未找到病历: {self.name}, user_id={user_id}")
                return None
                
        except Exception as e:
            logging.error(f"[{self.name}] 获取病历失败: {str(e)}")
            return None

class HospitalRegistry:
    """
    医院注册表单例
    
    功能：
    - 管理所有医院实例
    - 提供医院注册和获取接口
    - 确保全局唯一实例
    
    设计模式：单例模式
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.hospitals = {}
        return cls._instance
    
    def register_hospital(self, hospital: Hospital):
        """
        注册医院
        
        参数：
            hospital (Hospital): 医院实例
        """
        self.hospitals[hospital.id] = hospital
    
    def get_hospital(self, hospital_id: str) -> Optional[Hospital]:
        """
        获取医院实例
        
        参数：
            hospital_id (str): 医院ID
            
        返回：
            Optional[Hospital]: 医院实例或None
        """
        return self.hospitals.get(hospital_id)