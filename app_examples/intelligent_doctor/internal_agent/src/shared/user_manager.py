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

"""
用户管理模块 - 完整的用户管理功能
===============================

这个模块提供了完整的用户管理功能，包括：

1. 用户资料管理
   - 个人资料编辑
   - 头像上传管理
   - 偏好设置管理
   - 隐私设置管理

2. 用户状态管理
   - 用户状态跟踪
   - 在线状态管理
   - 活动记录管理
   - 用户统计信息

3. 用户数据管理
   - 医疗数据管理
   - 聊天记录管理
   - 文件上传管理
   - 数据导出功能

4. 用户服务管理
   - 用户服务订阅
   - 功能权限管理
   - 使用配额管理
   - 服务状态跟踪

注意：已迁移到MySQL数据库，不再使用SQLite

作者: QSIR
版本: 3.0 (MySQL版本)
"""

import asyncio
import base64
import io
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

# 尝试导入数据库配置
try:
    from src.config.database_config import db_config
except (ImportError, ModuleNotFoundError):
    db_config = None

logger = logging.getLogger(__name__)


# 辅助函数：在同步方法中运行异步代码
def _run_async(coro):
    """在同步方法中运行异步代码"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # 如果事件循环已经在运行，使用 nest_asyncio
        try:
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        except ImportError:
            # 如果没有 nest_asyncio，创建一个新的事件循环
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
    else:
        return loop.run_until_complete(coro)


@dataclass
class UserProfile:
    """用户资料数据类"""

    user_id: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None  # Base64编码的头像
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_conditions: List[str] | None = None
    allergies: List[str] | None = None
    medications: List[str] | None = None
    preferences: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.medical_conditions is None:
            self.medical_conditions = []
        if self.allergies is None:
            self.allergies = []
        if self.medications is None:
            self.medications = []
        if self.preferences is None:
            self.preferences = {}


@dataclass
class UserPreferences:
    """用户偏好设置数据类"""

    user_id: str
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    theme: str = "light"
    notifications: Dict[str, bool] | None = None
    privacy_settings: Dict[str, bool] | None = None
    display_settings: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.notifications is None:
            self.notifications = {
                "email_notifications": True,
                "push_notifications": True,
                "sms_notifications": False,
                "system_notifications": True,
            }
        if self.privacy_settings is None:
            self.privacy_settings = {
                "profile_public": False,
                "data_sharing": False,
                "analytics_tracking": True,
                "marketing_emails": False,
            }
        if self.display_settings is None:
            self.display_settings = {
                "font_size": "medium",
                "color_scheme": "default",
                "layout": "standard",
            }


@dataclass
class UserActivity:
    """用户活动记录数据类"""

    user_id: str
    activity_type: str
    description: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UserProfileManager:
    """用户资料管理器 - 已迁移到MySQL"""

    def __init__(self):
        """初始化用户资料管理器"""
        self._db_manager = None
        self._init_database()

    def _init_database(self):
        """初始化数据库连接"""
        try:
            # 检查是否使用MySQL
            if db_config and db_config._get_database_type() == "mysql":
                from .mysql_database_manager import mysql_db_manager

                self._db_manager = mysql_db_manager
                # 确保连接池已初始化
                _run_async(self._db_manager.initialize())
                logger.info("用户资料管理器已连接到MySQL数据库")
            else:
                # 回退到SQLite（仅用于开发/测试）
                logger.warning("未配置MySQL，使用SQLite（仅用于开发/测试）")
                self._db_manager = None
                self._use_sqlite = True
                self._init_sqlite()
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            # 回退到SQLite
            self._db_manager = None
            self._use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        """初始化SQLite数据库（回退模式）"""
        try:
            import sqlite3

            db_path = "data/user_profiles.db"
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            # 创建表（如果不存在）
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    full_name TEXT,
                    avatar TEXT,
                    phone TEXT,
                    address TEXT,
                    birth_date TEXT,
                    gender TEXT,
                    emergency_contact TEXT,
                    medical_conditions TEXT,
                    allergies TEXT,
                    medications TEXT,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            logger.info("SQLite数据库初始化完成（回退模式）")
        except Exception as e:
            logger.error(f"SQLite数据库初始化失败: {str(e)}")
            raise

    def create_user_profile(self, profile: UserProfile) -> bool:
        """创建用户资料"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            # 使用MySQL
            return _run_async(self._create_user_profile_mysql(profile))
        else:
            # 使用SQLite（回退模式）
            return self._create_user_profile_sqlite(profile)

    async def _create_user_profile_mysql(self, profile: UserProfile) -> bool:
        """使用MySQL创建用户资料"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                        INSERT INTO user_profiles 
                        (user_id, full_name, avatar, phone, address, birth_date, gender, 
                         emergency_contact, medical_conditions, allergies, medications, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            full_name = VALUES(full_name),
                            avatar = VALUES(avatar),
                            phone = VALUES(phone),
                            address = VALUES(address),
                            birth_date = VALUES(birth_date),
                            gender = VALUES(gender),
                            emergency_contact = VALUES(emergency_contact),
                            medical_conditions = VALUES(medical_conditions),
                            allergies = VALUES(allergies),
                            medications = VALUES(medications),
                            preferences = VALUES(preferences),
                            updated_at = CURRENT_TIMESTAMP
                    """,
                (
                    profile.user_id,
                    profile.full_name,
                    profile.avatar,
                    profile.phone,
                    profile.address,
                    profile.birth_date,
                    profile.gender,
                    profile.emergency_contact,
                    json.dumps(profile.medical_conditions)
                    if profile.medical_conditions
                    else None,
                    json.dumps(profile.allergies) if profile.allergies else None,
                    json.dumps(profile.medications) if profile.medications else None,
                    json.dumps(profile.preferences) if profile.preferences else None,
                ),
            )
            logger.info(f"用户资料创建成功: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户资料创建失败: {str(e)}")
            return False

    def _create_user_profile_sqlite(self, profile: UserProfile) -> bool:
        """使用SQLite创建用户资料（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO user_profiles 
                (user_id, full_name, avatar, phone, address, birth_date, gender, 
                 emergency_contact, medical_conditions, allergies, medications, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    profile.user_id,
                    profile.full_name,
                    profile.avatar,
                    profile.phone,
                    profile.address,
                    profile.birth_date,
                    profile.gender,
                    profile.emergency_contact,
                    json.dumps(profile.medical_conditions),
                    json.dumps(profile.allergies),
                    json.dumps(profile.medications),
                    json.dumps(profile.preferences),
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"用户资料创建成功: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户资料创建失败: {str(e)}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户资料"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            # 使用MySQL
            return _run_async(self._get_user_profile_mysql(user_id))
        else:
            # 使用SQLite（回退模式）
            return self._get_user_profile_sqlite(user_id)

    async def _get_user_profile_mysql(self, user_id: str) -> Optional[UserProfile]:
        """使用MySQL获取用户资料"""
        try:
            if not self._db_manager:
                return None

            rows = await self._db_manager.execute_query(
                """
                        SELECT user_id, full_name, avatar, phone, address, birth_date, gender,
                               emergency_contact, medical_conditions, allergies, medications, preferences
                        FROM user_profiles WHERE user_id = %s
                    """,
                (user_id,),
            )

            if rows and len(rows) > 0:
                return UserProfile(
                    user_id=rows[0]["user_id"],
                    full_name=rows[0].get("full_name"),
                    avatar=rows[0].get("avatar"),
                    phone=rows[0].get("phone"),
                    address=rows[0].get("address"),
                    birth_date=str(rows[0]["birth_date"])
                    if rows[0].get("birth_date")
                    else None,
                    gender=rows[0].get("gender"),
                    emergency_contact=rows[0].get("emergency_contact"),
                    medical_conditions=json.loads(rows[0]["medical_conditions"])
                    if rows[0].get("medical_conditions")
                    else [],
                    allergies=json.loads(rows[0]["allergies"])
                    if rows[0].get("allergies")
                    else [],
                    medications=json.loads(rows[0]["medications"])
                    if rows[0].get("medications")
                    else [],
                    preferences=json.loads(rows[0]["preferences"])
                    if rows[0].get("preferences")
                    else {},
                )
            return None
        except Exception as e:
            logger.error(f"获取用户资料失败: {str(e)}")
            return None

    def _get_user_profile_sqlite(self, user_id: str) -> Optional[UserProfile]:
        """使用SQLite获取用户资料（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                SELECT user_id, full_name, avatar, phone, address, birth_date, gender,
                       emergency_contact, medical_conditions, allergies, medications, preferences
                FROM user_profiles WHERE user_id = ?
            """,
                (user_id,),
            )
            row = c.fetchone()
            conn.close()

            if row:
                return UserProfile(
                    user_id=row[0],
                    full_name=row[1],
                    avatar=row[2],
                    phone=row[3],
                    address=row[4],
                    birth_date=row[5],
                    gender=row[6],
                    emergency_contact=row[7],
                    medical_conditions=json.loads(row[8]) if row[8] else [],
                    allergies=json.loads(row[9]) if row[9] else [],
                    medications=json.loads(row[10]) if row[10] else [],
                    preferences=json.loads(row[11]) if row[11] else {},
                )
            return None
        except Exception as e:
            logger.error(f"获取用户资料失败: {str(e)}")
            return None

    def update_user_profile(self, profile: UserProfile) -> bool:
        """更新用户资料"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._update_user_profile_mysql(profile))
        else:
            return self._update_user_profile_sqlite(profile)

    async def _update_user_profile_mysql(self, profile: UserProfile) -> bool:
        """使用MySQL更新用户资料"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                        UPDATE user_profiles SET 
                            full_name = %s, avatar = %s, phone = %s, address = %s, birth_date = %s,
                            gender = %s, emergency_contact = %s, medical_conditions = %s, 
                            allergies = %s, medications = %s, preferences = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """,
                (
                    profile.full_name,
                    profile.avatar,
                    profile.phone,
                    profile.address,
                    profile.birth_date,
                    profile.gender,
                    profile.emergency_contact,
                    json.dumps(profile.medical_conditions)
                    if profile.medical_conditions
                    else None,
                    json.dumps(profile.allergies) if profile.allergies else None,
                    json.dumps(profile.medications) if profile.medications else None,
                    json.dumps(profile.preferences) if profile.preferences else None,
                    profile.user_id,
                ),
            )
            logger.info(f"用户资料更新成功: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户资料更新失败: {str(e)}")
            return False

    def _update_user_profile_sqlite(self, profile: UserProfile) -> bool:
        """使用SQLite更新用户资料（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                UPDATE user_profiles SET 
                    full_name = ?, avatar = ?, phone = ?, address = ?, birth_date = ?,
                    gender = ?, emergency_contact = ?, medical_conditions = ?, allergies = ?,
                    medications = ?, preferences = ?, updated_at = ?
                WHERE user_id = ?
            """,
                (
                    profile.full_name,
                    profile.avatar,
                    profile.phone,
                    profile.address,
                    profile.birth_date,
                    profile.gender,
                    profile.emergency_contact,
                    json.dumps(profile.medical_conditions),
                    json.dumps(profile.allergies),
                    json.dumps(profile.medications),
                    json.dumps(profile.preferences),
                    datetime.now(),
                    profile.user_id,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"用户资料更新成功: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户资料更新失败: {str(e)}")
            return False

    def upload_avatar(
        self, user_id: str, image_data: bytes
    ) -> Tuple[bool, str, Optional[str]]:
        """上传用户头像"""
        try:
            # 验证图片格式和大小
            image = Image.open(io.BytesIO(image_data))

            # 检查图片大小（最大2MB）
            if len(image_data) > 2 * 1024 * 1024:
                return False, "图片大小不能超过2MB", None

            # 调整图片大小
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)

            # 转换为Base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            avatar_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # 更新用户资料
            profile = self.get_user_profile(user_id)
            if not profile:
                profile = UserProfile(user_id=user_id)

            profile.avatar = f"data:image/png;base64,{avatar_base64}"

            if self.update_user_profile(profile):
                return True, "头像上传成功", profile.avatar
            else:
                return False, "头像上传失败", None

        except Exception as e:
            logger.error(f"头像上传失败: {str(e)}")
            return False, f"头像上传失败: {str(e)}", None

    def record_user_activity(self, activity: UserActivity) -> bool:
        """记录用户活动"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._record_user_activity_mysql(activity))
        else:
            return self._record_user_activity_sqlite(activity)

    async def _record_user_activity_mysql(self, activity: UserActivity) -> bool:
        """使用MySQL记录用户活动"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                        INSERT INTO user_activities 
                        (user_id, activity_type, description, timestamp, ip_address, user_agent, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                (
                    activity.user_id,
                    activity.activity_type,
                    activity.description,
                    activity.timestamp,
                    activity.ip_address,
                    activity.user_agent,
                    json.dumps(activity.metadata) if activity.metadata else None,
                ),
            )
            return True
        except Exception as e:
            logger.error(f"记录用户活动失败: {str(e)}")
            return False

    def _record_user_activity_sqlite(self, activity: UserActivity) -> bool:
        """使用SQLite记录用户活动（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO user_activities 
                (user_id, activity_type, description, timestamp, ip_address, user_agent, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    activity.user_id,
                    activity.activity_type,
                    activity.description,
                    activity.timestamp,
                    activity.ip_address,
                    activity.user_agent,
                    json.dumps(activity.metadata),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"记录用户活动失败: {str(e)}")
            return False

    def get_user_activities(self, user_id: str, limit: int = 50) -> List[UserActivity]:
        """获取用户活动记录"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._get_user_activities_mysql(user_id, limit))
        else:
            return self._get_user_activities_sqlite(user_id, limit)

    async def _get_user_activities_mysql(
        self, user_id: str, limit: int
    ) -> List[UserActivity]:
        """使用MySQL获取用户活动记录"""
        try:
            import aiomysql

            async with self._db_manager.pool.get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT user_id, activity_type, description, timestamp, ip_address, user_agent, metadata
                        FROM user_activities 
                        WHERE user_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """,
                        (user_id, limit),
                    )
                    rows = await cursor.fetchall()

                    return [
                        UserActivity(
                            user_id=row["user_id"],
                            activity_type=row["activity_type"],
                            description=row.get("description", ""),
                            timestamp=row["timestamp"]
                            if isinstance(row["timestamp"], datetime)
                            else datetime.fromisoformat(str(row["timestamp"])),
                            ip_address=row.get("ip_address"),
                            user_agent=row.get("user_agent"),
                            metadata=json.loads(row["metadata"])
                            if row.get("metadata")
                            else {},
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"获取用户活动失败: {str(e)}")
            return []

    def _get_user_activities_sqlite(
        self, user_id: str, limit: int
    ) -> List[UserActivity]:
        """使用SQLite获取用户活动记录（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                SELECT user_id, activity_type, description, timestamp, ip_address, user_agent, metadata
                FROM user_activities 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """,
                (user_id, limit),
            )
            rows = c.fetchall()
            conn.close()

            return [
                UserActivity(
                    user_id=row[0],
                    activity_type=row[1],
                    description=row[2],
                    timestamp=datetime.fromisoformat(row[3])
                    if isinstance(row[3], str)
                    else row[3],
                    ip_address=row[4],
                    user_agent=row[5],
                    metadata=json.loads(row[6]) if row[6] else {},
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"获取用户活动失败: {str(e)}")
            return []


class UserPreferencesManager:
    """用户偏好设置管理器 - 已迁移到MySQL"""

    def __init__(self):
        """初始化用户偏好设置管理器"""
        self._db_manager = None
        self._init_database()

    def _init_database(self):
        """初始化数据库连接"""
        try:
            if db_config and db_config._get_database_type() == "mysql":
                from .mysql_database_manager import mysql_db_manager

                self._db_manager = mysql_db_manager
                _run_async(self._db_manager.initialize())
                logger.info("用户偏好设置管理器已连接到MySQL数据库")
            else:
                self._db_manager = None
                self._use_sqlite = True
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            self._db_manager = None
            self._use_sqlite = True

    def create_user_preferences(self, preferences: UserPreferences) -> bool:
        """创建用户偏好设置"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._create_user_preferences_mysql(preferences))
        else:
            return self._create_user_preferences_sqlite(preferences)

    async def _create_user_preferences_mysql(
        self, preferences: UserPreferences
    ) -> bool:
        """使用MySQL创建用户偏好设置"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                        INSERT INTO user_preferences 
                        (user_id, language, timezone, theme, notifications, privacy_settings, display_settings)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            language = VALUES(language),
                            timezone = VALUES(timezone),
                            theme = VALUES(theme),
                            notifications = VALUES(notifications),
                            privacy_settings = VALUES(privacy_settings),
                            display_settings = VALUES(display_settings),
                            updated_at = CURRENT_TIMESTAMP
                    """,
                (
                    preferences.user_id,
                    preferences.language,
                    preferences.timezone,
                    preferences.theme,
                    json.dumps(preferences.notifications)
                    if preferences.notifications
                    else None,
                    json.dumps(preferences.privacy_settings)
                    if preferences.privacy_settings
                    else None,
                    json.dumps(preferences.display_settings)
                    if preferences.display_settings
                    else None,
                ),
            )
            logger.info(f"用户偏好设置创建成功: {preferences.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户偏好设置创建失败: {str(e)}")
            return False

    def _create_user_preferences_sqlite(self, preferences: UserPreferences) -> bool:
        """使用SQLite创建用户偏好设置（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO user_preferences 
                (user_id, language, timezone, theme, notifications, privacy_settings, display_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    preferences.user_id,
                    preferences.language,
                    preferences.timezone,
                    preferences.theme,
                    json.dumps(preferences.notifications),
                    json.dumps(preferences.privacy_settings),
                    json.dumps(preferences.display_settings),
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"用户偏好设置创建成功: {preferences.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户偏好设置创建失败: {str(e)}")
            return False

    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """获取用户偏好设置"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._get_user_preferences_mysql(user_id))
        else:
            return self._get_user_preferences_sqlite(user_id)

    async def _get_user_preferences_mysql(
        self, user_id: str
    ) -> Optional[UserPreferences]:
        """使用MySQL获取用户偏好设置"""
        try:
            if not self._db_manager:
                return None

            rows = await self._db_manager.execute_query(
                """
                        SELECT user_id, language, timezone, theme, notifications, 
                               privacy_settings, display_settings
                        FROM user_preferences WHERE user_id = %s
                    """,
                (user_id,),
            )

            if rows and len(rows) > 0:
                return UserPreferences(
                    user_id=rows[0]["user_id"],
                    language=rows[0].get("language", "zh-CN"),
                    timezone=rows[0].get("timezone", "Asia/Shanghai"),
                    theme=rows[0].get("theme", "light"),
                    notifications=json.loads(rows[0]["notifications"])
                    if rows[0].get("notifications")
                    else {},
                    privacy_settings=json.loads(rows[0]["privacy_settings"])
                    if rows[0].get("privacy_settings")
                    else {},
                    display_settings=json.loads(rows[0]["display_settings"])
                    if rows[0].get("display_settings")
                    else {},
                )
            return None
        except Exception as e:
            logger.error(f"获取用户偏好设置失败: {str(e)}")
            return None

    def _get_user_preferences_sqlite(self, user_id: str) -> Optional[UserPreferences]:
        """使用SQLite获取用户偏好设置（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                SELECT user_id, language, timezone, theme, notifications, 
                       privacy_settings, display_settings
                FROM user_preferences WHERE user_id = ?
            """,
                (user_id,),
            )
            row = c.fetchone()
            conn.close()

            if row:
                return UserPreferences(
                    user_id=row[0],
                    language=row[1],
                    timezone=row[2],
                    theme=row[3],
                    notifications=json.loads(row[4]) if row[4] else {},
                    privacy_settings=json.loads(row[5]) if row[5] else {},
                    display_settings=json.loads(row[6]) if row[6] else {},
                )
            return None
        except Exception as e:
            logger.error(f"获取用户偏好设置失败: {str(e)}")
            return None

    def update_user_preferences(self, preferences: UserPreferences) -> bool:
        """更新用户偏好设置"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._update_user_preferences_mysql(preferences))
        else:
            return self._update_user_preferences_sqlite(preferences)

    async def _update_user_preferences_mysql(
        self, preferences: UserPreferences
    ) -> bool:
        """使用MySQL更新用户偏好设置"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                        UPDATE user_preferences SET 
                            language = %s, timezone = %s, theme = %s, notifications = %s,
                            privacy_settings = %s, display_settings = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """,
                (
                    preferences.language,
                    preferences.timezone,
                    preferences.theme,
                    json.dumps(preferences.notifications)
                    if preferences.notifications
                    else None,
                    json.dumps(preferences.privacy_settings)
                    if preferences.privacy_settings
                    else None,
                    json.dumps(preferences.display_settings)
                    if preferences.display_settings
                    else None,
                    preferences.user_id,
                ),
            )
            logger.info(f"用户偏好设置更新成功: {preferences.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户偏好设置更新失败: {str(e)}")
            return False

    def _update_user_preferences_sqlite(self, preferences: UserPreferences) -> bool:
        """使用SQLite更新用户偏好设置（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_profiles.db")
            c = conn.cursor()
            c.execute(
                """
                UPDATE user_preferences SET 
                    language = ?, timezone = ?, theme = ?, notifications = ?,
                    privacy_settings = ?, display_settings = ?, updated_at = ?
                WHERE user_id = ?
            """,
                (
                    preferences.language,
                    preferences.timezone,
                    preferences.theme,
                    json.dumps(preferences.notifications),
                    json.dumps(preferences.privacy_settings),
                    json.dumps(preferences.display_settings),
                    datetime.now(),
                    preferences.user_id,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"用户偏好设置更新成功: {preferences.user_id}")
            return True
        except Exception as e:
            logger.error(f"用户偏好设置更新失败: {str(e)}")
            return False


class UserDataManager:
    """用户数据管理器 - 已迁移到MySQL"""

    def __init__(self):
        """初始化用户数据管理器"""
        self._db_manager = None
        self._init_database()

    def _init_database(self):
        """初始化数据库连接"""
        try:
            if db_config and db_config._get_database_type() == "mysql":
                from .mysql_database_manager import mysql_db_manager

                self._db_manager = mysql_db_manager
                _run_async(self._db_manager.initialize())
                logger.info("用户数据管理器已连接到MySQL数据库")
            else:
                self._db_manager = None
                self._use_sqlite = True
                self._init_sqlite()
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            self._db_manager = None
            self._use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        """初始化SQLite数据库（回退模式）"""
        try:
            import sqlite3

            db_path = "data/user_data.db"
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_data_stats (
                    user_id TEXT PRIMARY KEY,
                    total_chat_messages INTEGER DEFAULT 0,
                    total_medical_images INTEGER DEFAULT 0,
                    total_medical_records INTEGER DEFAULT 0,
                    last_activity TIMESTAMP,
                    data_usage_mb REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            logger.info("SQLite数据库初始化完成（回退模式）")
        except Exception as e:
            logger.error(f"SQLite数据库初始化失败: {str(e)}")
            raise

    def get_user_data_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户数据统计"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._get_user_data_stats_mysql(user_id))
        else:
            return self._get_user_data_stats_sqlite(user_id)

    async def _get_user_data_stats_mysql(self, user_id: str) -> Dict[str, Any]:
        """使用MySQL获取用户数据统计"""
        try:
            if not self._db_manager:
                return {}

            rows = await self._db_manager.execute_query(
                """
                    SELECT total_chat_messages, total_medical_images, total_medical_records,
                        last_activity, data_usage_mb
                        FROM user_data_stats WHERE user_id = %s
                """,
                (user_id,),
            )

            if rows and len(rows) > 0:
                return {
                    "total_chat_messages": rows[0].get("total_chat_messages", 0),
                    "total_medical_images": rows[0].get("total_medical_images", 0),
                    "total_medical_records": rows[0].get("total_medical_records", 0),
                    "last_activity": str(rows[0]["last_activity"])
                    if rows[0].get("last_activity")
                    else None,
                    "data_usage_mb": float(rows[0].get("data_usage_mb", 0.0)),
                }
            return {
                "total_chat_messages": 0,
                "total_medical_images": 0,
                "total_medical_records": 0,
                "last_activity": None,
                "data_usage_mb": 0.0,
            }
        except Exception as e:
            logger.error(f"获取用户数据统计失败: {str(e)}")
            return {}

    def _get_user_data_stats_sqlite(self, user_id: str) -> Dict[str, Any]:
        """使用SQLite获取用户数据统计（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_data.db")
            c = conn.cursor()
            c.execute(
                """
                SELECT total_chat_messages, total_medical_images, total_medical_records,
                       last_activity, data_usage_mb
                FROM user_data_stats WHERE user_id = ?
            """,
                (user_id,),
            )
            row = c.fetchone()
            conn.close()

            if row:
                return {
                    "total_chat_messages": row[0],
                    "total_medical_images": row[1],
                    "total_medical_records": row[2],
                    "last_activity": row[3],
                    "data_usage_mb": row[4],
                }
            return {
                "total_chat_messages": 0,
                "total_medical_images": 0,
                "total_medical_records": 0,
                "last_activity": None,
                "data_usage_mb": 0.0,
            }
        except Exception as e:
            logger.error(f"获取用户数据统计失败: {str(e)}")
            return {}

    def update_user_data_stats(self, user_id: str, stats: Dict[str, Any]) -> bool:
        """更新用户数据统计"""
        if self._db_manager and not getattr(self, "_use_sqlite", False):
            return _run_async(self._update_user_data_stats_mysql(user_id, stats))
        else:
            return self._update_user_data_stats_sqlite(user_id, stats)

    async def _update_user_data_stats_mysql(
        self, user_id: str, stats: Dict[str, Any]
    ) -> bool:
        """使用MySQL更新用户数据统计"""
        try:
            if not self._db_manager:
                return False

            await self._db_manager.execute_query(
                """
                    INSERT INTO user_data_stats 
                    (user_id, total_chat_messages, total_medical_images, total_medical_records,
                        last_activity, data_usage_mb, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        total_chat_messages = VALUES(total_chat_messages),
                        total_medical_images = VALUES(total_medical_images),
                        total_medical_records = VALUES(total_medical_records),
                        last_activity = VALUES(last_activity),
                        data_usage_mb = VALUES(data_usage_mb),
                        updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    stats.get("total_chat_messages", 0),
                    stats.get("total_medical_images", 0),
                    stats.get("total_medical_records", 0),
                    stats.get("last_activity"),
                    stats.get("data_usage_mb", 0.0),
                ),
            )
            return True
        except Exception as e:
            logger.error(f"更新用户数据统计失败: {str(e)}")
            return False

    def _update_user_data_stats_sqlite(
        self, user_id: str, stats: Dict[str, Any]
    ) -> bool:
        """使用SQLite更新用户数据统计（回退模式）"""
        try:
            import sqlite3

            conn = sqlite3.connect("data/user_data.db")
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO user_data_stats 
                (user_id, total_chat_messages, total_medical_images, total_medical_records,
                 last_activity, data_usage_mb, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    stats.get("total_chat_messages", 0),
                    stats.get("total_medical_images", 0),
                    stats.get("total_medical_records", 0),
                    stats.get("last_activity"),
                    stats.get("data_usage_mb", 0.0),
                    datetime.now(),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新用户数据统计失败: {str(e)}")
            return False


class UserManager:
    """用户管理器 - 统一用户管理接口"""

    def __init__(self):
        self.profile_manager = UserProfileManager()
        self.preferences_manager = UserPreferencesManager()
        self.data_manager = UserDataManager()

    def create_user_profile(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """创建用户资料"""
        try:
            profile = UserProfile(
                user_id=user_id,
                full_name=profile_data.get("full_name"),
                phone=profile_data.get("phone"),
                address=profile_data.get("address"),
                birth_date=profile_data.get("birth_date"),
                gender=profile_data.get("gender"),
                emergency_contact=profile_data.get("emergency_contact"),
                medical_conditions=profile_data.get("medical_conditions", []),
                allergies=profile_data.get("allergies", []),
                medications=profile_data.get("medications", []),
            )

            if self.profile_manager.create_user_profile(profile):
                # 创建默认偏好设置
                preferences = UserPreferences(user_id=user_id)
                self.preferences_manager.create_user_preferences(preferences)

                return True, "用户资料创建成功"
            else:
                return False, "用户资料创建失败"

        except Exception as e:
            logger.error(f"创建用户资料失败: {str(e)}")
            return False, f"创建用户资料失败: {str(e)}"

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户资料"""
        return self.profile_manager.get_user_profile(user_id)

    def update_user_profile(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """更新用户资料"""
        try:
            profile = self.profile_manager.get_user_profile(user_id)
            if not profile:
                return False, "用户资料不存在"

            # 更新资料字段
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            if self.profile_manager.update_user_profile(profile):
                return True, "用户资料更新成功"
            else:
                return False, "用户资料更新失败"

        except Exception as e:
            logger.error(f"更新用户资料失败: {str(e)}")
            return False, f"更新用户资料失败: {str(e)}"

    def upload_user_avatar(
        self, user_id: str, image_data: bytes
    ) -> Tuple[bool, str, Optional[str]]:
        """上传用户头像"""
        return self.profile_manager.upload_avatar(user_id, image_data)

    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """获取用户偏好设置"""
        return self.preferences_manager.get_user_preferences(user_id)

    def update_user_preferences(
        self, user_id: str, preferences_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """更新用户偏好设置"""
        try:
            preferences = self.preferences_manager.get_user_preferences(user_id)
            if not preferences:
                preferences = UserPreferences(user_id=user_id)

            # 更新偏好设置
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)

            if self.preferences_manager.update_user_preferences(preferences):
                return True, "偏好设置更新成功"
            else:
                return False, "偏好设置更新失败"

        except Exception as e:
            logger.error(f"更新偏好设置失败: {str(e)}")
            return False, f"更新偏好设置失败: {str(e)}"

    def record_user_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> bool:
        """记录用户活动"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
        return self.profile_manager.record_user_activity(activity)

    def get_user_activities(self, user_id: str, limit: int = 50) -> List[UserActivity]:
        """获取用户活动记录"""
        return self.profile_manager.get_user_activities(user_id, limit)

    def get_user_data_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户数据统计"""
        return self.data_manager.get_user_data_stats(user_id)

    def update_user_data_stats(self, user_id: str, stats: Dict[str, Any]) -> bool:
        """更新用户数据统计"""
        return self.data_manager.update_user_data_stats(user_id, stats)

    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """获取用户仪表板数据"""
        try:
            profile = self.get_user_profile(user_id)
            preferences = self.get_user_preferences(user_id)
            data_stats = self.get_user_data_stats(user_id)
            activities = self.get_user_activities(user_id, 10)

            return {
                "profile": asdict(profile) if profile else None,
                "preferences": asdict(preferences) if preferences else None,
                "data_stats": data_stats,
                "recent_activities": [asdict(activity) for activity in activities],
            }

        except Exception as e:
            logger.error(f"获取用户仪表板数据失败: {str(e)}")
            return {}


# 全局实例
user_manager = UserManager()

# 导出主要类和实例
__all__ = [
    "UserProfile",
    "UserPreferences",
    "UserActivity",
    "UserProfileManager",
    "UserPreferencesManager",
    "UserDataManager",
    "UserManager",
    "user_manager",
]
