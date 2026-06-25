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
专科医生智能体模块
==================

包含按地域划分的专科医生智能体：
- InternalMedicineAgent（内科）
- SurgicalAgent（外科）
# - ImageAnalysisAgent（影像分析）  # 暂时注释掉影像分析

每个专科医生按地域分为：
- beijing（北京）
- shanghai（上海）

作者: QSIR
版本: 2.0 - 重构版
"""

from typing import Dict, Any, Optional, List

# 导入重构后的专科医生类
from .internal_medicine_agent import InternalMedicineAgent
from .surgical_agent import SurgicalAgent
# from .image_analysis_agent import ImageAnalysisAgent  # 暂时注释掉影像分析智能体

__all__ = [
    "InternalMedicineAgent",
    "SurgicalAgent",
    # "ImageAnalysisAgent"  # 暂时注释掉影像分析智能体
]

