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
智能体协调器模块
================

这个模块包含所有协调器智能体的实现。

主要组件：
- CybertwinAgent: 数字孪生智能体，负责意图识别和任务分发
"""

# cybertwin_agent 已删除，使用 cybertwin_agent_refactored
from .cybertwin_agent_refactored import CybertwinAgent

__all__ = ['CybertwinAgent']
