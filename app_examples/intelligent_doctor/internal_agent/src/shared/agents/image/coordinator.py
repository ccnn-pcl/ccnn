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
影像分析协调器 (ImageAnalysisCoordinator)
=======================================

负责协调多个影像分析智能体，统一管理影像分析任务。

主要功能：
1. 影像分析任务分发
2. 多智能体协调管理
3. 结果汇总整合
4. 医院影像管理

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.base_agent import BaseAgent
from agents.image.general import ImageAnalysisAgent
from agents.image.local import LocalImageAgent
from agents.image.distributed import DistributedImageAnalysisAgent
from agents.image.smart_retrieval import SmartImageRetrieval


class ImageAnalysisCoordinator(BaseAgent):
    """
    影像分析协调器
    
    负责协调多个影像分析智能体，包括：
    - 影像分析任务分发
    - 多智能体协调管理
    - 结果汇总整合
    - 医院影像管理
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化影像分析协调器
        
        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        super().__init__(model_config)
        self.agent_id = "image_coordinator"
        self.name = "影像分析协调器"
        self.specialization = "影像分析协调"
        
        # 初始化子智能体
        self._init_sub_agents()
        
        # 初始化医院注册表
        self._init_hospital_registry()
        
        # 初始化智能检索系统
        self._init_smart_retrieval()
        
        self.logger.info(f"[{self.name}] 初始化完成")
    
    def _init_sub_agents(self):
        """初始化子智能体"""
        try:
            # 导入模型配置
            from shared.config.model_config import get_config
            
            # 上海医院使用huatuogpt模型，北京医院使用huatuogpt-2模型
            # 默认使用huatuogpt模型
            shanghai_model_config = get_config("huatuo").to_dict()
            beijing_model_config = get_config("huatuo2").to_dict()
            
            # 为不同医院创建不同的智能体实例
            self.general_agent = ImageAnalysisAgent(self.model_config)
            self.local_agent = LocalImageAgent(self.model_config)
            self.distributed_agent = DistributedImageAnalysisAgent(self.model_config)
            
            # 创建医院特定的智能体
            self.shanghai_agent = ImageAnalysisAgent(shanghai_model_config)
            self.beijing_agent = ImageAnalysisAgent(beijing_model_config)
            
            self.logger.info(f"[{self.name}] 子智能体初始化完成")
        except Exception as e:
            self.logger.error(f"[{self.name}] 子智能体初始化失败: {str(e)}")
            raise
    
    def _init_hospital_registry(self):
        """初始化医院注册表"""
        try:
            from hospital_config import HospitalRegistry
            self.hospital_registry = HospitalRegistry()
            self.logger.info(f"[{self.name}] 医院注册表初始化完成")
        except ImportError as e:
            self.logger.warning(f"[{self.name}] 医院注册表初始化失败: {str(e)}")
            self.hospital_registry = None
    
    def _init_smart_retrieval(self):
        """初始化智能检索系统"""
        try:
            self.smart_retrieval = SmartImageRetrieval(self.model_config)
            self.logger.info(f"[{self.name}] 智能检索系统初始化完成")
        except Exception as e:
            self.logger.error(f"[{self.name}] 智能检索系统初始化失败: {str(e)}")
            self.smart_retrieval = None
    
    async def execute(self, user_input: str, user_id: str, user_info: Optional[Dict] = None) -> Any:
        """
        执行影像分析协调
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_info (Dict, optional): 用户信息
            
        返回：
            Any: 影像分析结果
        """
        try:
            # 记录输入参数
            self.logger.info(f"[{self.name}] 开始执行影像分析协调")
            self.logger.info(f"[{self.name}] 输入参数 - 用户ID: {user_id}")
            self.logger.info(f"[{self.name}] 输入参数 - 分析请求: {user_input[:100]}...")
            self.logger.info(f"[{self.name}] 输入参数 - 用户信息: {user_info}")
            
            # 验证输入
            if not self.validate_input(user_input):
                self.logger.warning(f"[{self.name}] 输入验证失败")
                return "[ERROR] 输入无效，请提供有效的影像分析请求。"
            
            # 获取对话历史
            context = self.get_context_from_memory(user_id)
            self.logger.info(f"[{self.name}] 获取对话历史: {context[:100] if context else '无'}...")
            
            # 检查用户影像
            self.logger.info(f"[{self.name}] 开始检查用户影像")
            user_images = await self._get_user_images(user_id)
            self.logger.info(f"[{self.name}] 用户影像检查完成，找到 {len(user_images) if user_images else 0} 张影像")
            
            if not user_images:
                self.logger.warning(f"[{self.name}] 用户 {user_id} 没有影像数据")
                return "[ERROR] 请先上传医学影像进行分析。"
            
            # 选择分析策略
            self.logger.info(f"[{self.name}] 开始选择分析策略")
            analysis_strategy = await self._select_analysis_strategy(user_input, user_images)
            self.logger.info(f"[{self.name}] 分析策略选择完成: {analysis_strategy}")
            
            # 执行影像分析
            self.logger.info(f"[{self.name}] 开始执行影像分析")
            analysis_result = await self._execute_analysis(analysis_strategy, user_input, user_id, user_images)
            self.logger.info(f"[{self.name}] 影像分析执行完成")
            self.logger.info(f"[{self.name}] 分析结果类型: {type(analysis_result)}")
            
            # 记录对话轮次
            self.add_turn_to_memory(user_id, user_input, self.name, f"协调分析了{len(user_images)}张影像")
            
            self.logger.info(f"[{self.name}] 影像分析协调完成")
            self.logger.info(f"[{self.name}] 输出结果 - 分析策略: {analysis_strategy}")
            self.logger.info(f"[{self.name}] 输出结果 - 影像数量: {len(user_images)}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行错误：{str(e)}")
            return f"[ERROR] 影像分析协调错误：{str(e)}"
    
    async def analyze_images(self, user_id: str, user_input: str) -> Any:
        """
        分析用户影像（智能检索版本）
        
        参数：
            user_id (str): 用户ID
            user_input (str): 用户输入
            
        返回：
            Any: 影像分析结果
        """
        try:
            # 使用智能检索系统获取相关影像
            if self.smart_retrieval:
                retrieval_result = await self.smart_retrieval.retrieve_images(
                    user_input, user_id, self.hospital_registry
                )
                
                if not retrieval_result.images:
                    return "[ERROR] 没有找到与您的描述相关的医学影像，请先上传相关影像进行分析。"
                
                user_images = retrieval_result.images
                self.logger.info(f"[{self.name}] 智能检索到{len(user_images)}张相关影像，平均相关性评分: {sum(retrieval_result.relevance_scores)/len(retrieval_result.relevance_scores):.2f}")
            else:
                # 回退到传统检索方式
                user_images = await self._get_user_images(user_id)
                if not user_images:
                    return "[ERROR] 请先上传医学影像进行分析。"
                self.logger.warning(f"[{self.name}] 智能检索系统不可用，使用传统检索方式")
            
            # 选择分析策略
            analysis_strategy = await self._select_analysis_strategy(user_input, user_images)
            
            # 执行影像分析
            analysis_result = await self._execute_analysis(analysis_strategy, user_input, user_id, user_images)
            
            # 添加检索信息到结果中
            if self.smart_retrieval and hasattr(retrieval_result, 'matched_criteria'):
                if isinstance(analysis_result, dict):
                    analysis_result['retrieval_info'] = {
                        'total_found': retrieval_result.total_count,
                        'matched_criteria': retrieval_result.matched_criteria,
                        'retrieval_time': retrieval_result.retrieval_time
                    }
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 影像分析失败: {str(e)}")
            return f"[ERROR] 影像分析失败：{str(e)}"
    
    async def _get_user_images(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户影像
        
        参数：
            user_id (str): 用户ID
            
        返回：
            List[Dict[str, Any]]: 用户影像列表
        """
        try:
            # 首先尝试从medical service获取影像数据
            medical_images = await self._get_medical_service_images(user_id)
            if medical_images:
                self.logger.info(f"[{self.name}] 从medical service获取到{len(medical_images)}张影像")
                return medical_images
            
            # 如果medical service没有数据，尝试从hospital registry获取
            if self.hospital_registry:
                user_images = []
                for hospital in self.hospital_registry.hospitals.values():
                    image = hospital.get_image(user_id)
                    if image:
                        user_images.append({
                            "hospital_id": hospital.hospital_id,
                            "hospital_name": hospital.name,
                            "image": image,
                            "image_type": getattr(image, 'image_type', 'unknown')
                        })
                
                if user_images:
                    self.logger.info(f"[{self.name}] 从hospital registry获取到{len(user_images)}张影像")
                    return user_images
            
            self.logger.warning(f"[{self.name}] 未找到用户{user_id}的影像数据")
            return []
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 获取用户影像失败: {str(e)}")
            return []
    
    async def _get_medical_service_images(self, user_id: str) -> List[Dict[str, Any]]:
        """
        从medical service获取用户影像数据
        
        参数：
            user_id (str): 用户ID
            
        返回：
            List[Dict[str, Any]]: 用户影像列表
        """
        try:
            import sqlite3
            import os
            
            # 连接medical service数据库
            data_dir = "data"
            db_path = os.path.join(data_dir, "chat_history.db")
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            
            # 查询用户影像数据
            query = """
                SELECT id, user_id, hospital_id, image_data, image_type, image_category, 
                       examination_date, description, filename, file_size, timestamp
                FROM medical_images 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            """
            
            cursor = db.cursor()
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            user_images = []
            for row in rows:
                user_images.append({
                    "image_id": str(row[0]),
                    "user_id": row[1],
                    "hospital_id": row[2],
                    "image_data": row[3],
                    "image_type": row[4],
                    "image_category": row[5],
                    "examination_date": row[6],
                    "description": row[7],
                    "filename": row[8],
                    "file_size": row[9],
                    "timestamp": row[10],
                    "hospital_name": f"医院_{row[2]}",  # 默认医院名称
                    "image": (row[3], row[4], row[10])  # 兼容原有格式
                })
            
            db.close()
            return user_images
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 从medical service获取影像失败: {str(e)}")
            return []
    
    async def _select_analysis_strategy(self, user_input: str, user_images: List[Dict[str, Any]]) -> str:
        """
        选择分析策略
        
        参数：
            user_input (str): 用户输入
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            str: 分析策略
        """
        try:
            # 检测用户请求中是否指定了特定医院
            specified_hospital = self._detect_specified_hospital(user_input)
            
            if specified_hospital:
                # 如果指定了特定医院，使用local策略
                self.logger.info(f"[{self.name}] 检测到指定医院: {specified_hospital}，使用local策略")
                return "local"
            else:
                # 如果没有指定医院，检查是否有多个医院的影像
                hospital_count = len(set(img.get('hospital_id', '') for img in user_images))
                if hospital_count > 1:
                    # 多个医院，使用跨医院协作分析
                    self.logger.info(f"[{self.name}] 检测到{hospital_count}个医院，使用cross_hospital策略")
                    return "cross_hospital"
                else:
                    # 单个医院，使用local策略
                    self.logger.info(f"[{self.name}] 检测到单个医院，使用local策略")
                    return "local"
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 选择分析策略失败: {str(e)}")
            return "local"
    
    async def _execute_analysis(self, strategy: str, user_input: str, user_id: str, user_images: List[Dict[str, Any]]) -> Any:
        """
        执行影像分析
        
        参数：
            strategy (str): 分析策略
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            Any: 分析结果
        """
        try:
            if strategy == "cross_hospital":
                # 跨医院协作分析
                return await self._execute_cross_hospital_analysis(user_input, user_id, user_images)
            elif strategy == "local":
                # 本地医院分析
                return await self._execute_local_analysis(user_input, user_id, user_images)
            else:
                # 其他策略（保持原有逻辑）
                return await self._execute_legacy_analysis(strategy, user_input, user_id, user_images)
                
        except Exception as e:
            self.logger.error(f"[{self.name}] 执行影像分析失败: {str(e)}")
            return f"[ERROR] 影像分析执行失败：{str(e)}"
    
    def _detect_specified_hospital(self, user_input: str) -> Optional[str]:
        """
        检测用户请求中是否指定了特定医院
        
        参数：
            user_input (str): 用户输入
            
        返回：
            Optional[str]: 指定的医院名称或ID，如果没有指定则返回None
        """
        try:
            # 定义医院关键词映射
            hospital_keywords = {
                "北京协和医院": ["协和", "协和医院", "北京协和", "PUMCH"],
                "上海瑞金医院": ["瑞金", "瑞金医院", "上海瑞金", "RJH"],
                "北京医院": ["北京医院", "北京", "医院_BJ001", "BJ001"],
                "上海医院": ["上海医院", "上海", "医院_SH001", "SH001"],
                "北京大学第一医院": ["北大一院", "北大医院", "北京大学第一医院"],
                "复旦大学附属华山医院": ["华山医院", "华山", "复旦华山"],
                "北京天坛医院": ["天坛医院", "天坛"],
                "上海中山医院": ["中山医院", "中山", "复旦中山"]
            }
            
            user_input_lower = user_input.lower()
            
            # 检查是否包含医院关键词
            for hospital_name, keywords in hospital_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in user_input_lower:
                        self.logger.info(f"[{self.name}] 检测到指定医院关键词: {keyword} -> {hospital_name}")
                        return hospital_name
            
            # 检查是否包含医院ID模式
            import re
            hospital_id_pattern = r'[A-Z]{2}\d{3}'  # 如 SH001, BJ001
            hospital_ids = re.findall(hospital_id_pattern, user_input.upper())
            if hospital_ids:
                hospital_id = hospital_ids[0]
                self.logger.info(f"[{self.name}] 检测到指定医院ID: {hospital_id}")
                return hospital_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 检测指定医院失败: {str(e)}")
            return None

    def _get_hospital_location_from_images(self, user_images: List[Dict[str, Any]]) -> str:
        """
        从用户影像中获取医院位置
        
        参数：
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            str: 医院位置（"上海"、"北京"或其他）
        """
        try:
            if not user_images:
                return "unknown"
            
            # 从第一张影像中获取医院位置信息
            first_image = user_images[0]
            hospital_name = first_image.get("hospital_name", "")
            hospital_id = first_image.get("hospital_id", "")
            
            # 根据医院名称或ID判断位置
            if "上海" in hospital_name or "SH" in hospital_id:
                return "上海"
            elif "北京" in hospital_name or "BJ" in hospital_id:
                return "北京"
            else:
                return "unknown"
                
        except Exception as e:
            self.logger.error(f"[{self.name}] 获取医院位置失败: {str(e)}")
            return "unknown"
    
    async def _execute_cross_hospital_analysis(self, user_input: str, user_id: str, user_images: List[Dict[str, Any]]) -> Any:
        """
        执行跨医院协作分析
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            Any: 分析结果
        """
        try:
            # 按医院分组影像
            hospital_groups = {}
            for img in user_images:
                hospital_id = img.get('hospital_id', 'unknown')
                if hospital_id not in hospital_groups:
                    hospital_groups[hospital_id] = []
                hospital_groups[hospital_id].append(img)
            
            self.logger.info(f"[{self.name}] 跨医院协作分析：{len(hospital_groups)}个医院，共{len(user_images)}张影像")
            
            # 并行分析各医院影像
            hospital_results = []
            for hospital_id, hospital_images in hospital_groups.items():
                hospital_name = hospital_images[0].get('hospital_name', f'医院_{hospital_id}')
                hospital_location = self._get_hospital_location_from_images(hospital_images)
                
                # 选择对应医院的智能体
                if hospital_location == "上海":
                    agent = self.shanghai_agent
                elif hospital_location == "北京":
                    agent = self.beijing_agent
                else:
                    agent = self.general_agent
                
                # 执行单医院分析
                hospital_result = await agent.safe_execute(user_input, user_id, {"images": hospital_images})
                hospital_results.append({
                    "hospital_id": hospital_id,
                    "hospital_name": hospital_name,
                    "hospital_location": hospital_location,
                    "image_count": len(hospital_images),
                    "analysis": hospital_result
                })
            
            # 综合各医院分析结果
            comprehensive_analysis = await self._synthesize_cross_hospital_results(user_input, hospital_results)
            
            return {
                "analysis_type": "cross_hospital",
                "comprehensive_analysis": comprehensive_analysis,
                "hospital_results": hospital_results,
                "total_hospitals": len(hospital_groups),
                "total_images": len(user_images),
                "specialization": "跨医院协作分析"
            }
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 跨医院协作分析失败: {str(e)}")
            return f"[ERROR] 跨医院协作分析失败：{str(e)}"
    
    async def _execute_local_analysis(self, user_input: str, user_id: str, user_images: List[Dict[str, Any]]) -> Any:
        """
        执行本地医院分析
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            Any: 分析结果
        """
        try:
            # 检测是否指定了特定医院
            specified_hospital = self._detect_specified_hospital(user_input)
            
            if specified_hospital:
                # 如果指定了特定医院，只分析该医院的影像
                filtered_images = []
                
                # 定义医院名称到ID的映射
                hospital_name_to_id = {
                    "北京医院": "BJ001",
                    "上海医院": "SH001",
                    "北京协和医院": "BJ001",
                    "上海瑞金医院": "SH001"
                }
                
                # 获取对应的医院ID
                target_hospital_id = hospital_name_to_id.get(specified_hospital, specified_hospital)
                
                for img in user_images:
                    hospital_name = img.get('hospital_name', '')
                    hospital_id = img.get('hospital_id', '')
                    
                    # 检查是否匹配指定的医院
                    if (specified_hospital in hospital_name or 
                        specified_hospital in hospital_id or
                        target_hospital_id in hospital_id or
                        target_hospital_id in hospital_name or
                        any(keyword in hospital_name for keyword in specified_hospital.split())):
                        filtered_images.append(img)
                
                if not filtered_images:
                    return f"[ERROR] 未找到指定医院 '{specified_hospital}' 的影像数据"
                
                user_images = filtered_images
                self.logger.info(f"[{self.name}] 指定医院分析：{specified_hospital}，{len(user_images)}张影像")
            
            # 根据医院位置选择智能体
            hospital_location = self._get_hospital_location_from_images(user_images)
            
            if hospital_location == "上海":
                agent = self.shanghai_agent
            elif hospital_location == "北京":
                agent = self.beijing_agent
            else:
                agent = self.general_agent
            
            # 执行分析
            result = await agent.safe_execute(user_input, user_id, {"images": user_images})
            
            # 添加分析类型信息
            if isinstance(result, dict):
                result["analysis_type"] = "local"
                result["hospital_location"] = hospital_location
                if specified_hospital:
                    result["specified_hospital"] = specified_hospital
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 本地医院分析失败: {str(e)}")
            return f"[ERROR] 本地医院分析失败：{str(e)}"
    
    async def _execute_legacy_analysis(self, strategy: str, user_input: str, user_id: str, user_images: List[Dict[str, Any]]) -> Any:
        """
        执行传统分析策略（保持向后兼容）
        
        参数：
            strategy (str): 分析策略
            user_input (str): 用户输入
            user_id (str): 用户ID
            user_images (List[Dict[str, Any]]): 用户影像列表
            
        返回：
            Any: 分析结果
        """
        try:
            # 根据医院位置选择相应的智能体
            hospital_location = self._get_hospital_location_from_images(user_images)
            
            if hospital_location == "上海":
                # 上海医院使用huatuogpt模型
                if strategy == "distributed":
                    return await self.distributed_agent.safe_execute(user_input, user_id, {"images": user_images})
                else:
                    return await self.shanghai_agent.safe_execute(user_input, user_id, {"images": user_images})
            elif hospital_location == "北京":
                # 北京医院使用huatuogpt-2模型
                if strategy == "distributed":
                    return await self.distributed_agent.safe_execute(user_input, user_id, {"images": user_images})
                else:
                    return await self.beijing_agent.safe_execute(user_input, user_id, {"images": user_images})
            else:
                # 默认使用通用智能体
                if strategy == "distributed":
                    return await self.distributed_agent.safe_execute(user_input, user_id, {"images": user_images})
                else:
                    return await self.general_agent.safe_execute(user_input, user_id, {"images": user_images})
                
        except Exception as e:
            self.logger.error(f"[{self.name}] 传统分析策略执行失败: {str(e)}")
            return f"[ERROR] 传统分析策略执行失败：{str(e)}"
    
    async def _synthesize_cross_hospital_results(self, user_input: str, hospital_results: List[Dict[str, Any]]) -> str:
        """
        综合跨医院分析结果
        
        参数：
            user_input (str): 用户输入
            hospital_results (List[Dict[str, Any]]): 各医院分析结果
            
        返回：
            str: 综合分析结果
        """
        try:
            # 构建综合分析的提示
            synthesis_prompt = f"""作为医学影像分析专家，请综合以下多个医院的分析结果，提供全面的诊断建议。

重要要求：
1. 必须严格按照指定格式，包含所有emoji标记（📋、🔍、💊、🏥）
2. 每个部分都要有具体内容，不能为空
3. 语言要温暖、专业、条理清晰
4. 报告长度控制在700字以内
5. 使用适当的emoji和分段

用户请求：{user_input}

各医院分析结果：
"""
            
            for i, result in enumerate(hospital_results, 1):
                hospital_name = result.get('hospital_name', f'医院{i}')
                hospital_location = result.get('hospital_location', '未知')
                image_count = result.get('image_count', 0)
                analysis = result.get('analysis', '')
                
                synthesis_prompt += f"""
医院 {i}: {hospital_name} ({hospital_location})
影像数量: {image_count}张
分析结果: {analysis}
"""
            
            synthesis_prompt += """

请严格按照以下格式生成影像分析报告：

**📋 影像分析概述**
- 对患者影像的整体评估
- 各医院分析结果的汇总整合

**[详细诊断分析]**
- 综合诊断结论
- 差异分析和可能原因
- 用患者能理解的语言解释

**💊 治疗建议**
- 综合治疗建议
- 生活方式调整建议
- 注意事项说明

**🏥 进一步检查**
- 推荐的检查项目
- 复查时间安排
- 随访计划"""
            
            # 调用LLM进行综合分析
            comprehensive_analysis = await self.caller(synthesis_prompt, self.model_config)
            
            # 过滤掉"Thinking"内容，只保留最终分析结果
            comprehensive_analysis = self._filter_thinking_content(comprehensive_analysis)
            
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 综合跨医院分析结果失败: {str(e)}")
            return f"[ERROR] 综合分析失败：{str(e)}"
    
    def _filter_thinking_content(self, content: str) -> str:
        """
        过滤掉"Thinking"内容，只保留最终分析结果
        
        参数：
            content (str): 原始LLM响应内容
            
        返回：
            str: 过滤后的内容
        """
        try:
            if not content:
                return content
                
            # 如果包含Thinking标记，尝试提取最终响应
            if "Thinking" in content or "思考" in content:
                lines = content.split('\n')
                filtered_lines = []
                in_thinking = False
                in_final_response = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检测Thinking开始
                    if "Thinking" in line or "思考" in line:
                        in_thinking = True
                        continue
                    
                    # 检测Final Response开始
                    if "Final Response" in line or "最终响应" in line or "最终回答" in line:
                        in_thinking = False
                        in_final_response = True
                        continue
                    
                    # 如果还在Thinking阶段，跳过
                    if in_thinking and not in_final_response:
                        continue
                    # 保留最终响应内容
                    if in_final_response or not in_thinking:
                        filtered_lines.append(line)
                
                # 如果成功提取到最终响应，返回
                if filtered_lines:
                    return '\n'.join(filtered_lines)
                else:
                    # 如果没有找到最终响应，但有Thinking标记，返回空内容
                    return "分析结果生成中，请稍候..."
            
            # 如果没有Thinking标记，直接返回原内容
            return content
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 过滤thinking内容失败: {str(e)}")
            return content
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "description": "专业的影像分析协调器，负责协调多个影像分析智能体，支持智能医院选择和跨医院协作分析",
            "capabilities": [
                "智能影像检索",
                "影像分析任务分发",
                "多智能体协调管理",
                "结果汇总整合",
                "医院影像管理",
                "医院名称检测",
                "跨医院协作分析",
                "指定医院分析",
                "综合分析结果"
            ],
            "sub_agents": [
                "ImageAnalysisAgent",
                "LocalImageAgent",
                "DistributedImageAnalysisAgent",
                "SmartImageRetrieval"
            ],
            "smart_retrieval": {
                "enabled": self.smart_retrieval is not None,
                "features": [
                    "基于用户输入的关键词提取",
                    "影像类型智能识别",
                    "检查部位智能匹配",
                    "医院位置智能筛选",
                    "相关性评分和排序"
                ]
            },
            "supported_strategies": [
                "local",
                "cross_hospital",
                "general",
                "distributed"
            ],
            "hospital_detection": {
                "supported_hospitals": [
                    "北京协和医院", "上海瑞金医院", "北京医院", "上海医院",
                    "北京大学第一医院", "复旦大学附属华山医院", 
                    "北京天坛医院", "上海中山医院"
                ],
                "detection_methods": ["关键词匹配", "医院ID模式识别"]
            }
        }
