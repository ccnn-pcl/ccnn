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
A2A协议模块
===========

Agent-to-Agent协议实现，用于智能体间通信。
"""

from .message import A2AMessage, A2ARequest, A2AResponse, A2AError
from .client import A2AClient
from .registry import A2ARegistryClient

__all__ = [
    "A2AMessage",
    "A2ARequest",
    "A2AResponse",
    "A2AError",
    "A2AClient",
    "A2ARegistryClient",
]

