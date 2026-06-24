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
影像分析相关数据模型
====================

定义影像分析相关的数据结构。

作者: QSIR
版本: 1.0
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ImageType(Enum):
    """影像类型枚举"""
    X_RAY = "x_ray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    PET = "pet"
    MAMMOGRAPHY = "mammography"
    ENDOSCOPY = "endoscopy"
    OTHER = "other"


class AnalysisStatus(Enum):
    """分析状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ImageAnalysisResult:
    """
    影像分析结果数据类
    
    用于存储影像分析的结果信息。
    """
    analysis_id: str
    image_id: str
    image_type: ImageType
    analysis_type: str              # 分析类型 (general, local, distributed)
    findings: str                   # 发现结果
    diagnosis: str                  # 诊断建议
    confidence_score: float         # 置信度分数 (0-1)
    abnormalities: List[Dict[str, Any]]  # 异常发现
    measurements: Dict[str, Any]    # 测量数据
    recommendations: str            # 建议
    follow_up_required: bool        # 是否需要随访
    urgent_findings: bool           # 是否有紧急发现
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'analysis_id': self.analysis_id,
            'image_id': self.image_id,
            'image_type': self.image_type.value,
            'analysis_type': self.analysis_type,
            'findings': self.findings,
            'diagnosis': self.diagnosis,
            'confidence_score': self.confidence_score,
            'abnormalities': self.abnormalities,
            'measurements': self.measurements,
            'recommendations': self.recommendations,
            'follow_up_required': self.follow_up_required,
            'urgent_findings': self.urgent_findings,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ImageMetadata:
    """
    影像元数据类
    
    用于存储影像的元数据信息。
    """
    image_id: str
    filename: str
    file_size: int
    image_type: ImageType
    dimensions: Dict[str, int]      # 图像尺寸 {width, height}
    resolution: Dict[str, float]    # 分辨率 {dpi_x, dpi_y}
    color_space: str                # 色彩空间
    bit_depth: int                  # 位深度
    compression: str                # 压缩格式
    created_at: datetime
    uploaded_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.uploaded_at is None:
            self.uploaded_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'image_id': self.image_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'image_type': self.image_type.value,
            'dimensions': self.dimensions,
            'resolution': self.resolution,
            'color_space': self.color_space,
            'bit_depth': self.bit_depth,
            'compression': self.compression,
            'created_at': self.created_at.isoformat(),
            'uploaded_at': self.uploaded_at.isoformat()
        }


@dataclass
class ImageAnalysisRequest:
    """
    影像分析请求数据类
    
    用于存储影像分析请求的信息。
    """
    request_id: str
    user_id: str
    hospital_id: str
    image_ids: List[str]
    analysis_type: str              # 分析类型
    priority: int                   # 优先级 (1-5)
    status: AnalysisStatus
    requested_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'hospital_id': self.hospital_id,
            'image_ids': self.image_ids,
            'analysis_type': self.analysis_type,
            'priority': self.priority,
            'status': self.status.value,
            'requested_at': self.requested_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


@dataclass
class ImageQualityAssessment:
    """
    影像质量评估数据类
    
    用于存储影像质量评估的结果。
    """
    assessment_id: str
    image_id: str
    overall_quality: int            # 整体质量评分 (1-10)
    sharpness: int                  # 清晰度评分 (1-10)
    contrast: int                   # 对比度评分 (1-10)
    brightness: int                 # 亮度评分 (1-10)
    noise_level: int                # 噪声水平评分 (1-10)
    artifacts: List[str]            # 伪影列表
    quality_issues: List[str]       # 质量问题列表
    recommendations: str             # 改进建议
    created_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'assessment_id': self.assessment_id,
            'image_id': self.image_id,
            'overall_quality': self.overall_quality,
            'sharpness': self.sharpness,
            'contrast': self.contrast,
            'brightness': self.brightness,
            'noise_level': self.noise_level,
            'artifacts': self.artifacts,
            'quality_issues': self.quality_issues,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat()
        }
