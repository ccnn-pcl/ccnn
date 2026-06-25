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
用户信息辅助工具
================

提供用户信息自动补全功能，从医疗档案中补全缺失的用户信息。

作者: QSIR
版本: 1.0
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def auto_complete_user_info(user_id: str, user_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    自动补全用户信息（从医疗档案）
    
    如果关键字段缺失，从医疗档案中补全 user_info。
    
    参数：
        user_id (str): 用户ID
        user_info (Dict, optional): 用户信息（可能不完整）
        
    返回：
        Dict[str, Any]: 补全后的用户信息
    """
    try:
        # 判断是否需要补全
        needs_profile = (
            user_info is None or
            any(k not in user_info or user_info.get(k) in (None, "", []) 
                for k in ["age", "gender", "medical_history"])  # 关键字段
        )
        
        if not needs_profile:
            # 不需要补全，直接返回
            return user_info or {}
        
        # 从医疗档案补全
        try:
            from backend.services.medical_profile_service import medical_profile_service
            profile = await medical_profile_service.get_medical_profile(user_id)
            
            if profile:
                base = user_info or {}
                # 合并为新的 user_info（以已有信息为主，缺失才补）
                completed_info = {
                    **base,
                    "age": base.get("age") or profile.age,
                    "gender": base.get("gender") or profile.gender,
                    "medical_history": base.get("medical_history") or profile.medical_history,
                    "family_history": base.get("family_history") or profile.family_history,
                    "allergies": base.get("allergies") or profile.allergies,
                    "medications": base.get("medications") or profile.medications,
                    "medical_conditions": base.get("medical_conditions") or profile.medical_conditions,
                    "birth_date": base.get("birth_date") or profile.birth_date,
                    "last_update": base.get("last_update") or profile.last_update,
                }
                logger.info(f"[UserInfoHelper] 成功补全用户信息，用户ID: {user_id}")
                return completed_info
            else:
                logger.warning(f"[UserInfoHelper] 未找到医疗档案，用户ID: {user_id}")
                return user_info or {}
                
        except ImportError:
            logger.warning(f"[UserInfoHelper] medical_profile_service 未找到，跳过自动补全")
            return user_info or {}
        except Exception as e:
            logger.warning(f"[UserInfoHelper] 自动补全user_info失败: {str(e)}")
            return user_info or {}
            
    except Exception as e:
        logger.error(f"[UserInfoHelper] 自动补全过程出错: {str(e)}")
        return user_info or {}

