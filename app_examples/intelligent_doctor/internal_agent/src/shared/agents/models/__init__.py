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
数据模型模块
============

这个模块包含所有智能体相关的数据模型。

主要组件：
- DialogueTurn: 对话轮次数据类
- ExpertAdvice: 专家建议数据类
- ImageAnalysisResult: 影像分析结果数据类
- AgentResponse: 智能体响应数据类
"""

from .dialogue import DialogueTurn
from .medical import ExpertAdvice, MedicalRecord
from .image import ImageAnalysisResult
from .agent import AgentResponse, AgentStatus

__all__ = [
    'DialogueTurn',
    'ExpertAdvice',
    'MedicalRecord',
    'ImageAnalysisResult',
    'AgentResponse',
    'AgentStatus'
]
