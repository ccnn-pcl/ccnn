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
配置模块
========

包含系统配置相关的类和函数
"""

from .model_config import ModelConfig, DEFAULT_CONFIG, MEDICAL_CONFIG, CHAT_CONFIG, HUATUO_CONFIG, HUATUO2_CONFIG, QWEN_CONFIG, get_config

__all__ = [
    'ModelConfig',
    'DEFAULT_CONFIG', 
    'MEDICAL_CONFIG',
    'CHAT_CONFIG',
    'HUATUO_CONFIG',
    'HUATUO2_CONFIG',
    'QWEN_CONFIG',
    'get_config'
]
