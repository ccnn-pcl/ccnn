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
智能影像检索系统 (SmartImageRetrieval)
=====================================

提供基于用户输入、医院位置、影像类型、检查部位的智能影像检索功能。

主要功能：
1. 关键词提取和匹配
2. 影像类型智能识别
3. 检查部位智能匹配
4. 医院位置智能筛选
5. 相关性评分和排序

作者: QSIR
版本: 1.0
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
import os


class ImageType(Enum):
    """影像类型枚举"""
    X_RAY = "X光"
    CT = "CT"
    MRI = "MRI"
    ULTRASOUND = "超声"
    PET = "PET"
    SPECT = "SPECT"
    MAMMOGRAPHY = "乳腺X光"
    DENTAL = "牙科X光"
    FLUOROSCOPY = "透视"
    ANGIOGRAPHY = "血管造影"
    ENDOSCOPY = "内镜"
    OTHER = "其他"


class BodyPart(Enum):
    """检查部位枚举"""
    HEAD = "头部"
    NECK = "颈部"
    CHEST = "胸部"
    ABDOMEN = "腹部"
    PELVIS = "盆腔"
    SPINE = "脊柱"
    LIMBS = "四肢"
    HEART = "心脏"
    LUNG = "肺部"
    LIVER = "肝脏"
    KIDNEY = "肾脏"
    BRAIN = "脑部"
    EYE = "眼部"
    EAR = "耳部"
    NOSE = "鼻部"
    MOUTH = "口腔"
    THROAT = "咽喉"
    OTHER = "其他"


@dataclass
class RetrievalCriteria:
    """检索条件"""
    keywords: List[str]
    image_types: List[ImageType]
    body_parts: List[BodyPart]
    hospital_locations: List[str]
    time_range: Optional[Tuple[str, str]] = None
    priority: str = "medium"  # high, medium, low


@dataclass
class RetrievalResult:
    """检索结果"""
    images: List[Dict[str, Any]]
    relevance_scores: List[float]
    total_count: int
    matched_criteria: Dict[str, Any]
    retrieval_time: float


class SmartImageRetrieval:
    """
    智能影像检索系统
    
    提供基于多维度条件的智能影像检索功能：
    - 关键词提取和匹配
    - 影像类型智能识别
    - 检查部位智能匹配
    - 医院位置智能筛选
    - 相关性评分和排序
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化智能影像检索系统
        
        参数：
            model_config (Dict[str, Any]): 模型配置
        """
        self.model_config = model_config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化关键词映射
        self._init_keyword_mappings()
        
        # 初始化医院位置映射
        self._init_hospital_location_mappings()
        
        self.logger.info(f"[{self.__class__.__name__}] 初始化完成")
    
    def _init_keyword_mappings(self):
        """初始化关键词映射"""
        # 影像类型关键词映射
        self.image_type_keywords = {
            ImageType.X_RAY: ["X光", "X线", "胸片", "骨片", "平片", "x-ray", "xray"],
            ImageType.CT: ["CT", "ct", "计算机断层", "断层扫描", "螺旋CT"],
            ImageType.MRI: ["MRI", "mri", "磁共振", "核磁共振", "磁共振成像", "核磁", "核磁影像"],
            ImageType.ULTRASOUND: ["超声", "B超", "彩超", "多普勒", "ultrasound", "US"],
            ImageType.PET: ["PET", "pet", "正电子", "PET-CT"],
            ImageType.SPECT: ["SPECT", "spect", "单光子", "核医学"],
            ImageType.MAMMOGRAPHY: ["乳腺", "钼靶", "mammography", "乳房"],
            ImageType.DENTAL: ["牙科", "牙齿", "口腔", "dental", "牙齿X光"],
            ImageType.FLUOROSCOPY: ["透视", "荧光", "fluoroscopy"],
            ImageType.ANGIOGRAPHY: ["血管造影", "造影", "angiography", "DSA"],
            ImageType.ENDOSCOPY: ["内镜", "胃镜", "肠镜", "endoscopy", "内窥镜"]
        }
        
        # 检查部位关键词映射
        self.body_part_keywords = {
            BodyPart.HEAD: ["头部", "头颅", "头", "脑", "head", "skull", "cranium"],
            BodyPart.NECK: ["颈部", "脖子", "颈", "neck", "cervical"],
            BodyPart.CHEST: ["胸部", "胸", "肺", "心脏", "chest", "thorax", "lung", "heart"],
            BodyPart.ABDOMEN: ["腹部", "腹", "肚子", "腹腔", "abdomen", "abdominal"],
            BodyPart.PELVIS: ["盆腔", "骨盆", "pelvis", "pelvic"],
            BodyPart.SPINE: ["脊柱", "脊椎", "背部", "spine", "vertebral", "back"],
            BodyPart.LIMBS: ["四肢", "手臂", "腿部", "手", "脚", "膝盖", "膝关节", "膝盖", "limbs", "arm", "leg", "knee", "joint"],
            BodyPart.HEART: ["心脏", "心", "cardiac", "heart"],
            BodyPart.LUNG: ["肺部", "肺", "lung", "pulmonary"],
            BodyPart.LIVER: ["肝脏", "肝", "liver", "hepatic"],
            BodyPart.KIDNEY: ["肾脏", "肾", "kidney", "renal"],
            BodyPart.BRAIN: ["脑部", "大脑", "脑", "brain", "cerebral"],
            BodyPart.EYE: ["眼部", "眼睛", "眼", "eye", "ocular"],
            BodyPart.EAR: ["耳部", "耳朵", "耳", "ear", "auditory"],
            BodyPart.NOSE: ["鼻部", "鼻子", "鼻", "nose", "nasal"],
            BodyPart.MOUTH: ["口腔", "嘴", "口", "mouth", "oral"],
            BodyPart.THROAT: ["咽喉", "喉咙", "咽", "throat", "pharyngeal"]
        }
        
        # 症状关键词映射
        self.symptom_keywords = {
            "疼痛": ["疼", "痛", "疼痛", "ache", "pain"],
            "肿胀": ["肿", "胀", "肿胀", "swelling", "edema"],
            "炎症": ["炎", "炎症", "发炎", "inflammation"],
            "感染": ["感染", "发炎", "infection"],
            "出血": ["出血", "血", "bleeding", "hemorrhage"],
            "骨折": ["骨折", "断", "裂", "fracture", "break"],
            "肿瘤": ["肿瘤", "瘤", "癌", "tumor", "cancer", "neoplasm"],
            "结石": ["结石", "石", "stone", "calculus"],
            "囊肿": ["囊肿", "囊", "cyst"],
            "积液": ["积液", "水", "fluid", "effusion"]
        }
    
    def _init_hospital_location_mappings(self):
        """初始化医院位置映射"""
        self.hospital_location_keywords = {
            "北京": ["北京", "beijing", "首都", "京"],
            "上海": ["上海", "shanghai", "沪", "申"],
            "广州": ["广州", "guangzhou", "穗"],
            "深圳": ["深圳", "shenzhen", "深"],
            "杭州": ["杭州", "hangzhou", "杭"],
            "南京": ["南京", "nanjing", "宁"],
            "成都": ["成都", "chengdu", "蓉"],
            "武汉": ["武汉", "wuhan", "汉"],
            "西安": ["西安", "xian", "西"],
            "重庆": ["重庆", "chongqing", "渝"]
        }
    
    async def retrieve_images(self, user_input: str, user_id: str, 
                            hospital_registry=None) -> RetrievalResult:
        """
        智能检索影像
        
        参数：
            user_input (str): 用户输入
            user_id (str): 用户ID
            hospital_registry: 医院注册表
            
        返回：
            RetrievalResult: 检索结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 提取检索条件
            criteria = await self._extract_retrieval_criteria(user_input)
            self.logger.info(f"[{self.__class__.__name__}] 提取检索条件: {criteria}")
            
            # 2. 从数据库检索影像
            images = await self._query_images_from_database(user_id, criteria)
            self.logger.info(f"[{self.__class__.__name__}] 从数据库检索到{len(images)}张影像")
            
            # 3. 从医院注册表检索影像
            if hospital_registry:
                hospital_images = await self._query_images_from_hospitals(
                    user_id, criteria, hospital_registry
                )
                images.extend(hospital_images)
                self.logger.info(f"[{self.__class__.__name__}] 从医院注册表检索到{len(hospital_images)}张影像")
            
            # 4. 计算相关性评分
            relevance_scores = await self._calculate_relevance_scores(images, criteria, user_input)
            
            # 5. 排序和筛选
            sorted_images = self._sort_and_filter_images(images, relevance_scores, criteria)
            
            retrieval_time = time.time() - start_time
            
            return RetrievalResult(
                images=sorted_images,
                relevance_scores=relevance_scores,
                total_count=len(sorted_images),
                matched_criteria=self._format_matched_criteria(criteria),
                retrieval_time=retrieval_time
            )
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 智能检索失败: {str(e)}")
            return RetrievalResult(
                images=[],
                relevance_scores=[],
                total_count=0,
                matched_criteria={},
                retrieval_time=0
            )
    
    async def _extract_retrieval_criteria(self, user_input: str) -> RetrievalCriteria:
        """
        从用户输入中提取检索条件
        
        参数：
            user_input (str): 用户输入
            
        返回：
            RetrievalCriteria: 检索条件
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords(user_input)
            
            # 识别影像类型
            image_types = self._identify_image_types(user_input)
            
            # 识别检查部位
            body_parts = self._identify_body_parts(user_input)
            
            # 识别医院位置
            hospital_locations = self._identify_hospital_locations(user_input)
            
            return RetrievalCriteria(
                keywords=keywords,
                image_types=image_types,
                body_parts=body_parts,
                hospital_locations=hospital_locations
            )
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 提取检索条件失败: {str(e)}")
            return RetrievalCriteria(
                keywords=[],
                image_types=[],
                body_parts=[],
                hospital_locations=[]
            )
    
    def _extract_keywords(self, user_input: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 提取症状关键词
        for symptom, variants in self.symptom_keywords.items():
            for variant in variants:
                if variant in user_input.lower():
                    keywords.append(symptom)
                    break
        
        # 提取其他关键词（长度大于1的词，但排除过长的词）
        words = re.findall(r'\b\w+\b', user_input)
        for word in words:
            if len(word) > 1 and len(word) < 10 and word not in keywords:
                keywords.append(word)
        
        return keywords
    
    def _identify_image_types(self, user_input: str) -> List[ImageType]:
        """识别影像类型"""
        identified_types = []
        user_input_lower = user_input.lower()
        
        for image_type, keywords in self.image_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    identified_types.append(image_type)
                    break
        
        return identified_types
    
    def _identify_body_parts(self, user_input: str) -> List[BodyPart]:
        """识别检查部位"""
        identified_parts = []
        user_input_lower = user_input.lower()
        
        for body_part, keywords in self.body_part_keywords.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    identified_parts.append(body_part)
                    break
        
        return identified_parts
    
    def _identify_hospital_locations(self, user_input: str) -> List[str]:
        """识别医院位置"""
        identified_locations = []
        user_input_lower = user_input.lower()
        
        for location, keywords in self.hospital_location_keywords.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    identified_locations.append(location)
                    break
        
        return identified_locations
    
    async def _query_images_from_database(self, user_id: str, criteria: RetrievalCriteria) -> List[Dict[str, Any]]:
        """
        从数据库查询影像（优化版本）
        
        参数：
            user_id (str): 用户ID
            criteria (RetrievalCriteria): 检索条件
            
        返回：
            List[Dict[str, Any]]: 影像列表
        """
        try:
            # 连接数据库
            data_dir = "data"
            db_path = os.path.join(data_dir, "chat_history.db")
            
            if not os.path.exists(db_path):
                return []
            
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            params = [user_id]
            
            # 如果有检查部位条件，优先使用检查部位匹配
            if criteria.body_parts:
                part_conditions = []
                for body_part in criteria.body_parts:
                    # 简化的部位匹配逻辑
                    part_conditions.append("""
                        (description LIKE ? OR 
                         image_type LIKE ? OR 
                         filename LIKE ?)
                    """)
                    params.extend([
                        f"%{body_part.value}%",  # description匹配
                        f"%{body_part.value}%",  # image_type匹配
                        f"%{body_part.value}%",  # filename匹配
                    ])
                where_conditions.append(f"({' OR '.join(part_conditions)})")
            
            # 添加影像类型条件（精确匹配）
            if criteria.image_types:
                type_conditions = []
                for image_type in criteria.image_types:
                    # 支持多种匹配方式
                    type_conditions.append("(image_type LIKE ? OR image_type = ?)")
                    params.extend([f"%{image_type.value}%", image_type.value])
                where_conditions.append(f"({' OR '.join(type_conditions)})")
            
            # 添加关键词条件（灵活匹配，但优先级较低）
            if criteria.keywords:
                keyword_conditions = []
                for keyword in criteria.keywords:
                    # 只匹配描述和文件名，避免误匹配
                    keyword_conditions.append("(description LIKE ? OR filename LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
                # 使用OR连接关键词条件，而不是AND
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # 执行查询
            # 如果有检查部位条件，优先使用检查部位匹配，忽略关键词条件
            if criteria.body_parts:
                # 只使用检查部位条件
                body_part_conditions = []
                body_part_params = [user_id]
                for body_part in criteria.body_parts:
                    body_part_conditions.append("""
                        (description LIKE ? OR 
                         image_type LIKE ? OR 
                         filename LIKE ?)
                    """)
                    body_part_params.extend([
                        f"%{body_part.value}%",  # description匹配
                        f"%{body_part.value}%",  # image_type匹配
                        f"%{body_part.value}%",  # filename匹配
                    ])
                
                query = f"""
                    SELECT id, user_id, hospital_id, image_data, image_type, image_category, 
                           examination_date, description, filename, file_size, timestamp
                    FROM medical_images 
                    WHERE user_id = ? AND ({' OR '.join(body_part_conditions)})
                    ORDER BY timestamp DESC
                """
                params = body_part_params
            else:
                # 使用所有条件
                query = f"""
                    SELECT id, user_id, hospital_id, image_data, image_type, image_category, 
                           examination_date, description, filename, file_size, timestamp
                    FROM medical_images 
                    WHERE {' AND '.join(where_conditions)}
                    ORDER BY timestamp DESC
                """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            images = []
            for row in rows:
                images.append({
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
                    "hospital_name": f"医院_{row[2]}",
                    "image": (row[3], row[4], row[10])
                })
            
            db.close()
            return images
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 数据库查询失败: {str(e)}")
            return []
    
    async def _query_images_from_hospitals(self, user_id: str, criteria: RetrievalCriteria, 
                                         hospital_registry) -> List[Dict[str, Any]]:
        """
        从医院注册表查询影像
        
        参数：
            user_id (str): 用户ID
            criteria (RetrievalCriteria): 检索条件
            hospital_registry: 医院注册表
            
        返回：
            List[Dict[str, Any]]: 影像列表
        """
        try:
            images = []
            
            for hospital in hospital_registry.hospitals.values():
                # 检查医院位置匹配
                if criteria.hospital_locations:
                    hospital_location = getattr(hospital, 'location', '')
                    if not any(loc in hospital_location for loc in criteria.hospital_locations):
                        continue
                
                # 获取影像
                image = hospital.get_image(user_id)
                if image:
                    images.append({
                        "hospital_id": hospital.hospital_id,
                        "hospital_name": hospital.name,
                        "image": image,
                        "image_type": getattr(image, 'image_type', 'unknown'),
                        "hospital_location": getattr(hospital, 'location', '未知')
                    })
            
            return images
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 医院注册表查询失败: {str(e)}")
            return []
    
    async def _calculate_relevance_scores(self, images: List[Dict[str, Any]], 
                                        criteria: RetrievalCriteria, 
                                        user_input: str) -> List[float]:
        """
        计算相关性评分
        
        参数：
            images (List[Dict[str, Any]]): 影像列表
            criteria (RetrievalCriteria): 检索条件
            user_input (str): 用户输入
            
        返回：
            List[float]: 相关性评分列表
        """
        try:
            scores = []
            
            for image in images:
                score = 0.0
                
                # 影像类型匹配评分
                image_type = image.get('image_type', '')
                for img_type in criteria.image_types:
                    if img_type.value in image_type:
                        score += 0.3
                        break
                
                # 检查部位匹配评分
                description = image.get('description') or ''
                filename = image.get('filename') or ''
                for body_part in criteria.body_parts:
                    if (body_part.value in description or 
                        body_part.value in filename):
                        score += 0.3
                        break
                
                # 关键词匹配评分
                for keyword in criteria.keywords:
                    if (keyword in description or 
                        keyword in filename or 
                        keyword in user_input):
                        score += 0.2
                
                # 医院位置匹配评分
                hospital_location = image.get('hospital_location', '')
                for location in criteria.hospital_locations:
                    if location in hospital_location:
                        score += 0.1
                        break
                
                # 时间新鲜度评分（越新的影像评分越高）
                timestamp = image.get('timestamp', '')
                if timestamp:
                    try:
                        from datetime import datetime
                        image_time = datetime.fromisoformat(timestamp)
                        now = datetime.now()
                        days_diff = (now - image_time).days
                        freshness_score = max(0, 1 - days_diff / 365)  # 一年内线性衰减
                        score += freshness_score * 0.1
                    except:
                        pass
                
                scores.append(min(score, 1.0))  # 限制最高分为1.0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 计算相关性评分失败: {str(e)}")
            return [0.0] * len(images)
    
    def _sort_and_filter_images(self, images: List[Dict[str, Any]], 
                              relevance_scores: List[float], 
                              criteria: RetrievalCriteria) -> List[Dict[str, Any]]:
        """
        排序和筛选影像（优化版本）
        
        参数：
            images (List[Dict[str, Any]]): 影像列表
            relevance_scores (List[float]): 相关性评分
            criteria (RetrievalCriteria): 检索条件
            
        返回：
            List[Dict[str, Any]]: 排序后的影像列表
        """
        try:
            # 将评分添加到影像数据中
            for i, image in enumerate(images):
                image['relevance_score'] = relevance_scores[i]
            
            # 按相关性评分排序
            sorted_images = sorted(images, key=lambda x: x['relevance_score'], reverse=True)
            
            # 智能筛选逻辑
            filtered_images = []
            
            # 1. 优先保留高相关性影像（评分 >= 0.3）
            high_relevance = [img for img in sorted_images if img['relevance_score'] >= 0.3]
            filtered_images.extend(high_relevance)
            
            # 2. 如果有检查部位条件，进一步筛选
            if criteria.body_parts:
                # 只保留与检查部位相关的影像
                body_part_related = []
                for img in sorted_images:
                    if img['relevance_score'] >= 0.2:  # 降低阈值但仍有筛选
                        # 检查是否与检查部位相关
                        is_related = False
                        for body_part in criteria.body_parts:
                            if (body_part.value in (img.get('description') or '') or
                                body_part.value in (img.get('image_type') or '') or
                                body_part.value in (img.get('filename') or '') or
                                self._is_image_type_related_to_body_part(img.get('image_type') or '', body_part)):
                                is_related = True
                                break
                        
                        if is_related:
                            body_part_related.append(img)
                
                # 如果找到相关影像，只返回相关影像
                if body_part_related:
                    filtered_images = body_part_related
                else:
                    # 如果没有找到相关影像，返回高相关性影像
                    filtered_images = high_relevance
            else:
                # 3. 没有检查部位条件时，使用原有逻辑
                filtered_images = [img for img in sorted_images if img['relevance_score'] >= 0.1]
            
            # 4. 限制返回数量（最多10张，提高精度）
            return filtered_images[:10]
            
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] 排序筛选失败: {str(e)}")
            return images
    
    def _is_image_type_related_to_body_part(self, image_type: str, body_part: BodyPart) -> bool:
        """
        检查影像类型是否与检查部位相关
        
        参数：
            image_type (str): 影像类型
            body_part (BodyPart): 检查部位
            
        返回：
            bool: 是否相关
        """
        # 定义影像类型与检查部位的映射关系
        type_part_mapping = {
            BodyPart.CHEST: ['chest', 'lung', 'heart', 'thorax'],
            BodyPart.HEAD: ['head', 'brain', 'skull', 'cranium'],
            BodyPart.ABDOMEN: ['abdominal', 'liver', 'kidney', 'stomach'],
            BodyPart.LIMBS: ['joint', 'bone', 'arm', 'leg', 'hand', 'foot', 'knee', 'knee'],
            BodyPart.SPINE: ['spine', 'vertebral', 'back'],
            BodyPart.HEART: ['heart', 'cardiac'],
            BodyPart.LUNG: ['lung', 'pulmonary', 'chest'],
            BodyPart.LIVER: ['liver', 'hepatic'],
            BodyPart.KIDNEY: ['kidney', 'renal'],
            BodyPart.BRAIN: ['brain', 'cerebral', 'head']
        }
        
        if body_part not in type_part_mapping:
            return False
        
        image_type_lower = image_type.lower()
        for keyword in type_part_mapping[body_part]:
            if keyword in image_type_lower:
                return True
        
        return False
    
    def _format_matched_criteria(self, criteria: RetrievalCriteria) -> Dict[str, Any]:
        """格式化匹配条件"""
        return {
            "keywords": criteria.keywords,
            "image_types": [t.value for t in criteria.image_types],
            "body_parts": [p.value for p in criteria.body_parts],
            "hospital_locations": criteria.hospital_locations,
            "priority": criteria.priority
        }
    
    def get_retrieval_info(self) -> Dict[str, Any]:
        """获取检索系统信息"""
        return {
            "name": "智能影像检索系统",
            "version": "1.0",
            "supported_image_types": [t.value for t in ImageType],
            "supported_body_parts": [p.value for p in BodyPart],
            "supported_locations": list(self.hospital_location_keywords.keys()),
            "features": [
                "关键词提取和匹配",
                "影像类型智能识别",
                "检查部位智能匹配",
                "医院位置智能筛选",
                "相关性评分和排序"
            ]
        }
