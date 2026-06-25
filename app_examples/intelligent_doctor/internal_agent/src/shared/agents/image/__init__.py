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
影像分析智能体模块
==================

这个模块包含所有影像分析相关的智能体实现。

主要组件：
- ImageAnalysisCoordinator: 影像分析协调器
- ImageAnalysisAgent: 通用影像分析智能体
- LocalImageAgent: 本地影像分析智能体
- DistributedImageAnalysisAgent: 分布式影像分析智能体
"""

from .coordinator import ImageAnalysisCoordinator
from .general import ImageAnalysisAgent
from .local import LocalImageAgent
from .distributed import DistributedImageAnalysisAgent

__all__ = [
    'ImageAnalysisCoordinator',
    'ImageAnalysisAgent',
    'LocalImageAgent',
    'DistributedImageAnalysisAgent'
]
