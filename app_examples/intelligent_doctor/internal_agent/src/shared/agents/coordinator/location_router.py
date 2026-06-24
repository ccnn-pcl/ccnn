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
地域路由引擎
============

实现智能路由功能，按地域分组数据地址并路由到对应专科医生。

主要功能：
1. 按地域分组数据地址
2. 根据意图选择专科类型
3. 路由到对应地域的专科医生实例

作者: QSIR
版本: 2.0 - 重构版
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class LocationRouter:
    """
    地域路由引擎
    
    负责：
    1. 按地域分组数据地址
    2. 根据意图选择专科类型
    3. 路由到对应地域的专科医生实例
    """
    
    # 意图到专科类型的映射（简化版）
    INTENT_TO_SPECIALTY = {
        "内科咨询": "internal_medicine",
        "内科": "internal_medicine",
        "外科咨询": "surgical",
        "外科": "surgical",
        "影像分析": "internal_medicine",  # 影像分析暂时路由到内科（待实现ImageAnalysisAgent后改为image_analysis）
        "影像": "internal_medicine",
        "影像诊断": "internal_medicine",
        "药物查询": "internal_medicine",  # 药物查询路由到内科
        "一般问题": "internal_medicine",  # 一般问题路由到内科
        "未知": "internal_medicine",      # 未知意图路由到内科
        # 默认映射
        "default": "internal_medicine"
    }
    
    # 专科类型到类名的映射
    SPECIALTY_TO_CLASS = {
        "internal_medicine": "InternalMedicineAgent",
        "surgical": "SurgicalAgent",
        # "image_analysis": "ImageAnalysisAgent"  # 暂时注释掉影像分析
    }
    
    def __init__(self):
        """初始化地域路由引擎"""
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.logger.info("[LocationRouter] 初始化完成")
    
    def group_data_addresses_by_location(
        self, 
        data_addresses: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按地域分组数据地址
        
        参数：
            data_addresses (List[Dict[str, Any]]): 数据地址列表
            
        返回：
            Dict[str, List[Dict[str, Any]]]: 按地域分组的数据地址字典
            {
                "beijing": [地址1, 地址2, ...],
                "shanghai": [地址3, 地址4, ...]
            }
        """
        if not data_addresses:
            self.logger.warning("[LocationRouter] 数据地址列表为空")
            return {}
        
        grouped = defaultdict(list)
        
        for addr in data_addresses:
            location = addr.get("location", "unknown")
            if location not in ["beijing", "shanghai"]:
                self.logger.warning(f"[LocationRouter] 未知地域: {location}, 跳过")
                continue
            
            grouped[location].append(addr)
            self.logger.debug(f"[LocationRouter] 数据地址 {addr.get('address', 'N/A')} 分组到地域: {location}")
        
        self.logger.info(f"[LocationRouter] 数据地址分组完成: {dict(grouped)}")
        return dict(grouped)
    
    def select_specialty_by_intent(self, intent: str) -> str:
        """
        根据意图选择专科类型（简化版）
        
        参数：
            intent (str): 意图类型（如"内科咨询"、"外科咨询"、"影像分析"、"药物查询"、"一般问题"、"未知"）
            
        返回：
            str: 专科类型（internal_medicine, surgical）
        """
        specialty = self.INTENT_TO_SPECIALTY.get(intent, self.INTENT_TO_SPECIALTY["default"])
        self.logger.info(f"[LocationRouter] 意图 '{intent}' 映射到专科类型: {specialty}")
        return specialty
    
    def route_to_specialists(
        self,
        intent: str,
        data_addresses: List[Dict[str, Any]],
        specialist_instances: Dict[str, Dict[str, Any]]
    ) -> List[Tuple[str, str, List[Dict[str, Any]]]]:
        """
        路由到专科医生实例
        
        参数：
            intent (str): 意图类型
            data_addresses (List[Dict[str, Any]]): 数据地址列表
            specialist_instances (Dict[str, Dict[str, Any]]): 专科医生实例字典
                格式: {
                    "internal_medicine": {
                        "beijing": InternalMedicineAgent实例,
                        "shanghai": InternalMedicineAgent实例
                    },
                    "surgical": {...}
                    # "image_analysis": {...}  # 暂时注释掉影像分析
                }
            
        返回：
            List[Tuple[str, str, List[Dict[str, Any]]]]: 路由结果列表
                每个元素为 (location, specialty, data_addresses)
                例如: [("beijing", "internal_medicine", [地址1, 地址2])]
        """
        # 1. 选择专科类型
        specialty = self.select_specialty_by_intent(intent)
        
        # 2. 按地域分组数据地址
        grouped_addresses = self.group_data_addresses_by_location(data_addresses)
        
        # 3. 构建路由结果
        routing_results = []
        
        # 获取该专科类型的所有实例
        specialty_instances = specialist_instances.get(specialty, {})
        
        for location, addresses in grouped_addresses.items():
            # 检查是否有对应地域的实例
            if location not in specialty_instances:
                self.logger.warning(
                    f"[LocationRouter] 地域 {location} 没有 {specialty} 专科医生实例，跳过"
                )
                continue
            
            routing_results.append((location, specialty, addresses))
            self.logger.info(
                f"[LocationRouter] 路由到: {location} 的 {specialty} 专科医生, "
                f"数据地址数量: {len(addresses)}"
            )
        
        # 如果没有匹配的数据地址，但需要诊断，可以路由到默认地域
        if not routing_results and specialty_instances:
            # 选择第一个可用的地域实例
            default_location = list(specialty_instances.keys())[0]
            routing_results.append((default_location, specialty, []))
            self.logger.info(
                f"[LocationRouter] 没有匹配的数据地址，路由到默认地域: {default_location}"
            )
        
        return routing_results
    
    def get_required_specialists(
        self,
        intent: str
    ) -> List[str]:
        """
        获取所需的专科类型列表
        
        参数：
            intent (str): 意图类型
            
        返回：
            List[str]: 所需的专科类型列表
        """
        specialty = self.select_specialty_by_intent(intent)
        return [specialty]
    
    def validate_routing(
        self,
        routing_results: List[Tuple[str, str, List[Dict[str, Any]]]],
        specialist_instances: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        验证路由结果的有效性
        
        参数：
            routing_results (List[Tuple]): 路由结果列表
            specialist_instances (Dict): 专科医生实例字典
            
        返回：
            bool: 路由结果是否有效
        """
        if not routing_results:
            self.logger.warning("[LocationRouter] 路由结果为空")
            return False
        
        for location, specialty, addresses in routing_results:
            # 检查实例是否存在
            if specialty not in specialist_instances:
                self.logger.error(f"[LocationRouter] 专科类型 {specialty} 不存在实例")
                return False
            
            if location not in specialist_instances[specialty]:
                self.logger.error(
                    f"[LocationRouter] 地域 {location} 的 {specialty} 专科医生实例不存在"
                )
                return False
        
        self.logger.info("[LocationRouter] 路由结果验证通过")
        return True
    
    def get_location_statistics(
        self,
        data_addresses: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        获取地域统计信息
        
        参数：
            data_addresses (List[Dict[str, Any]]): 数据地址列表
            
        返回：
            Dict[str, int]: 各地域的数据地址数量统计
        """
        stats = defaultdict(int)
        
        for addr in data_addresses:
            location = addr.get("location", "unknown")
            if location in ["beijing", "shanghai"]:
                stats[location] += 1
        
        return dict(stats)

