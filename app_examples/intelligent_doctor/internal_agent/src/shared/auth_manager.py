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
认证授权管理器 - 完整的用户认证和权限控制系统
==============================================

这个模块实现了完整的用户认证和权限控制功能，包括：

1. 用户认证管理
   - 用户注册、登录、登出
   - 密码加密和验证
   - JWT令牌管理
   - 会话管理

2. 权限控制系统
   - RBAC基于角色的访问控制
   - 智能体访问权限控制
   - 数据访问权限控制
   - 细粒度权限管理

3. 安全特性
   - 密码强度验证
   - 账户锁定机制
   - 会话超时控制
   - 审计日志记录

4. 用户管理
   - 用户角色管理
   - 用户资料管理
   - 用户偏好设置
   - 用户状态管理

作者: QSIR
版本: 2.0
"""

import hashlib
import json
import logging
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import jwt

from src.config.database_config import db_config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "cybertwin_doctor_secret_key_2024"  # 生产环境应使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# 密码配置
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True

# 账户锁定配置
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class UserRole(Enum):
    """用户角色枚举"""

    PATIENT = "patient"  # 患者
    DOCTOR = "doctor"  # 医生
    NURSE = "nurse"  # 护士
    ADMIN = "admin"  # 管理员
    RESEARCHER = "researcher"  # 研究员
    GUEST = "guest"  # 访客


class UserStatus(Enum):
    """用户状态枚举"""

    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    LOCKED = "locked"  # 锁定
    SUSPENDED = "suspended"  # 暂停


@dataclass
class User:
    """用户数据类"""

    user_id: str
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.PATIENT
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime | None = None
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    password_hash: str | None = None
    locked_until: Optional[datetime] = None
    profile: Dict[str, Any] | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.profile is None:
            self.profile = {}


@dataclass
class LoginAttempt:
    """登录尝试记录"""

    user_id: str
    ip_address: str
    success: bool
    timestamp: datetime
    failure_reason: Optional[str] = None


class PasswordManager:
    """密码管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希加密"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return f"{salt}:{password_hash.hex()}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            salt, password_hash = hashed_password.split(":")
            password_hash_bytes = bytes.fromhex(password_hash)
            new_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return secrets.compare_digest(password_hash_bytes, new_hash)
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """验证密码强度"""
        errors = []

        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f"密码长度至少{PASSWORD_MIN_LENGTH}位")

        if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")

        if PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")

        if PASSWORD_REQUIRE_DIGITS and not re.search(r"\d", password):
            errors.append("密码必须包含数字")

        if PASSWORD_REQUIRE_SPECIAL and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors


class JWTManager:
    """JWT令牌管理器"""

    @staticmethod
    def generate_token(user: User) -> str:
        """生成JWT令牌"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "status": user.status.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的JWT令牌")
            return None

    @staticmethod
    def refresh_token(token: str) -> Optional[str]:
        """刷新JWT令牌"""
        payload = JWTManager.verify_token(token)
        if payload:
            # 创建新的用户对象
            user = User(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                status=UserStatus(payload["status"]),
            )
            return JWTManager.generate_token(user)
        return None


class AuthDatabaseManager:
    """认证数据库管理器"""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化认证数据库"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # 创建用户表
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    profile TEXT
                )
            """)

            # 创建登录尝试表
            c.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    ip_address TEXT,
                    success BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failure_reason TEXT
                )
            """)

            # 创建会话表
            c.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)

            # 创建审计日志表
            c.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            """)

            conn.commit()
            conn.close()
            logger.info("认证数据库初始化完成")

        except Exception as e:
            logger.error(f"认证数据库初始化失败: {str(e)}")
            raise

    def create_user(self, user: User, password: str) -> bool:
        """创建用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            password_hash = PasswordManager.hash_password(password)
            profile_json = json.dumps(user.profile) if user.profile else None

            c.execute(
                """
                INSERT INTO users (user_id, username, email, password_hash, role, status, 
                                 created_at, last_login, login_attempts, locked_until, profile)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.user_id,
                    user.username,
                    user.email,
                    password_hash,
                    user.role.value,
                    user.status.value,
                    user.created_at,
                    user.last_login,
                    user.login_attempts,
                    user.locked_until,
                    profile_json,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"用户创建成功: {user.username}")
            return True

        except Exception as e:
            logger.error(f"用户创建失败: {str(e)}")
            return False

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                SELECT user_id, username, email, password_hash, role, status, created_at,
                       last_login, login_attempts, locked_until, profile
                FROM users WHERE username = ?
            """,
                (username,),
            )

            row = c.fetchone()
            conn.close()

            if row:
                profile = json.loads(row[10]) if row[10] else {}
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    role=UserRole(row[4]),
                    status=UserStatus(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    login_attempts=row[8],
                    locked_until=datetime.fromisoformat(row[9]) if row[9] else None,
                    profile=profile,
                )
            return None

        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                SELECT user_id, username, email, password_hash, role, status, created_at,
                       last_login, login_attempts, locked_until, profile
                FROM users WHERE user_id = ?
            """,
                (user_id,),
            )

            row = c.fetchone()
            conn.close()

            if row:
                profile = json.loads(row[10]) if row[10] else {}
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    role=UserRole(row[4]),
                    status=UserStatus(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    login_attempts=row[8],
                    locked_until=datetime.fromisoformat(row[9]) if row[9] else None,
                    profile=profile,
                )
            return None

        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            profile_json = json.dumps(user.profile) if user.profile else None

            c.execute(
                """
                UPDATE users SET username = ?, email = ?, role = ?, status = ?,
                               last_login = ?, login_attempts = ?, locked_until = ?, profile = ?
                WHERE user_id = ?
            """,
                (
                    user.username,
                    user.email,
                    user.role.value,
                    user.status.value,
                    user.last_login,
                    user.login_attempts,
                    user.locked_until,
                    profile_json,
                    user.user_id,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"用户更新成功: {user.username}")
            return True

        except Exception as e:
            logger.error(f"用户更新失败: {str(e)}")
            return False

    def verify_password(self, username: str, password: str) -> bool:
        """验证用户密码"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            conn.close()

            if row:
                stored_hash = row[0]
                # 检查是否是加盐格式（包含冒号）
                if ":" in stored_hash:
                    # 使用PBKDF2验证
                    return PasswordManager.verify_password(password, stored_hash)
                else:
                    # 使用简单SHA256验证（向后兼容）
                    import hashlib

                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    return password_hash == stored_hash
            return False

        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    def record_login_attempt(self, attempt: LoginAttempt) -> bool:
        """记录登录尝试"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO login_attempts (user_id, ip_address, success, timestamp, failure_reason)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    attempt.user_id,
                    attempt.ip_address,
                    attempt.success,
                    attempt.timestamp,
                    attempt.failure_reason,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"记录登录尝试失败: {str(e)}")
            return False

    def create_session(
        self,
        session_id: str,
        user_id: str,
        token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """创建会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO sessions (session_id, user_id, token, created_at, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    user_id,
                    token,
                    datetime.now(),
                    expires_at,
                    ip_address,
                    user_agent,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                SELECT session_id, user_id, token, created_at, expires_at, ip_address, user_agent
                FROM sessions WHERE session_id = ? AND expires_at > ?
            """,
                (session_id, datetime.now()),
            )

            row = c.fetchone()
            conn.close()

            if row:
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "token": row[2],
                    "created_at": row[3],
                    "expires_at": row[4],
                    "ip_address": row[5],
                    "user_agent": row[6],
                }
            return None

        except Exception as e:
            logger.error(f"获取会话失败: {str(e)}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            return False

    def log_audit_event(
        self,
        user_id: str,
        action: str,
        resource: str | None = None,
        ip_address: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> bool:
        """记录审计日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            details_json = json.dumps(details) if details else None

            c.execute(
                """
                INSERT INTO audit_logs (user_id, action, resource, ip_address, timestamp, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_id, action, resource, ip_address, datetime.now(), details_json),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
            return False

    def update_password(self, user_id: str, new_password_hash: str) -> bool:
        """更新密码"""
        try:
            # 更新密码
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (new_password_hash, user_id),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"密码修改失败: {str(e)}")
            return False

    def execute_query(
        self, sql: str, params: Tuple | None = None, database: str | None = None
    ):
        try:
            if database:
                db_path = f"data/{database}.db"
            else:
                db_path = self.db_path

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            result = cursor.fetchall()
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            return None

    def close(self):
        pass


class AuthManager:
    """认证管理器 - 单例模式"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return

        if db_config._get_database_type() == "mysql":
            try:
                from src.shared.mysql_auth_manager import MySQLAuthAdapter

                self.db_manager = MySQLAuthAdapter(db_config._get_mysql_config())
                logger.info("认证管理器初始化完成 - 使用 MySQL")
            except Exception as e:
                logger.error(f"MySQL认证适配器初始化失败: {str(e)}，回退到SQLite")
                self.db_manager = AuthDatabaseManager()
                logger.info("认证管理器初始化完成 - 使用 SQLite (回退模式)")
        else:
            self.db_manager = AuthDatabaseManager()
            logger.info("认证管理器初始化完成 - 使用 SQLite")

        self.active_sessions = {}  # 内存中的活跃会话
        self.initialized = True

    def register_user(
        self,
        username: str,
        password: str,
        email: str | None = None,
        role: UserRole = UserRole.PATIENT,
    ) -> Tuple[bool, str, Optional[User]]:
        """用户注册"""
        try:
            # 验证用户名
            if not username or len(username) < 3:
                return False, "用户名至少3个字符", None

            # 验证密码强度
            is_valid, errors = PasswordManager.validate_password_strength(password)
            if not is_valid:
                return False, f"密码强度不足: {', '.join(errors)}", None

            # 检查用户是否已存在
            existing_user = self.db_manager.get_user_by_username(username)
            if existing_user:
                return False, "用户名已存在", None

            # 创建用户
            user_id = secrets.token_urlsafe(16)
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                status=UserStatus.ACTIVE,
            )

            # 保存用户到数据库
            if self.db_manager.create_user(user, password):
                # 记录审计日志
                self.db_manager.log_audit_event(
                    user_id, "USER_REGISTERED", "user", details={"username": username}
                )
                logger.info(f"用户注册成功: {username}")
                return True, "注册成功", user
            else:
                return False, "用户创建失败", None

        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            return False, f"注册失败: {str(e)}", None

    def authenticate_user(
        self, username: str, password: str, ip_address: str | None = None
    ) -> Tuple[bool, str, Optional[User], Optional[str]]:
        """用户认证"""
        try:
            # 获取用户信息
            user = self.db_manager.get_user_by_username(username)
            if not user:
                return False, "用户不存在", None, None

            # 检查用户状态
            if user.status == UserStatus.LOCKED:
                if user.locked_until and datetime.now() < user.locked_until:
                    return (
                        False,
                        f"账户已锁定，请{user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}后重试",
                        None,
                        None,
                    )
                else:
                    # 解锁账户
                    user.status = UserStatus.ACTIVE
                    user.login_attempts = 0
                    user.locked_until = None
                    self.db_manager.update_user(user)

            if user.status != UserStatus.ACTIVE:
                return False, "账户状态异常", None, None

            # 验证密码
            if self.db_manager.verify_password(username, password):
                # 登录成功
                user.last_login = datetime.now()
                user.login_attempts = 0
                user.locked_until = None
                self.db_manager.update_user(user)

                # 生成JWT令牌
                token = JWTManager.generate_token(user)

                # 创建会话
                session_id = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)
                self.db_manager.create_session(
                    session_id, user.user_id, token, expires_at, ip_address
                )
                self.active_sessions[session_id] = user.user_id

                # 记录审计日志
                self.db_manager.log_audit_event(
                    user.user_id,
                    "USER_LOGIN",
                    "auth",
                    ip_address=ip_address,
                    details={"username": username},
                )

                logger.info(f"用户登录成功: {username}")
                return True, "登录成功", user, token
            else:
                # 登录失败
                user.login_attempts += 1
                if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.status = UserStatus.LOCKED
                    user.locked_until = datetime.now() + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )

                self.db_manager.update_user(user)

                # 记录失败的登录尝试
                attempt = LoginAttempt(
                    user_id=user.user_id,
                    ip_address=ip_address or "unknown",
                    success=False,
                    timestamp=datetime.now(),
                    failure_reason="invalid_password",
                )
                self.db_manager.record_login_attempt(attempt)

                return False, "密码错误", None, None

        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return False, f"认证失败: {str(e)}", None, None

    def verify_token(self, token: str) -> Optional[User]:
        """验证JWT令牌"""
        try:
            payload = JWTManager.verify_token(token)
            if payload:
                user = self.db_manager.get_user_by_id(payload["user_id"])
                if user and user.status == UserStatus.ACTIVE:
                    return user
            return None
        except Exception as e:
            logger.error(f"令牌验证失败: {str(e)}")
            return None

    def logout_user(self, token: str) -> bool:
        """用户登出"""
        try:
            payload = JWTManager.verify_token(token)
            if payload:
                # 删除会话
                for session_id, user_id in list(self.active_sessions.items()):
                    if user_id == payload["user_id"]:
                        self.db_manager.delete_session(session_id)
                        del self.active_sessions[session_id]

                # 记录审计日志
                self.db_manager.log_audit_event(
                    payload["user_id"], "USER_LOGOUT", "auth"
                )
                logger.info(f"用户登出: {payload['username']}")
                return True
            return False
        except Exception as e:
            logger.error(f"用户登出失败: {str(e)}")
            return False

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """修改密码"""
        try:
            user = self.db_manager.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在"

            # 验证旧密码
            if not self.db_manager.verify_password(user.username, old_password):
                return False, "旧密码错误"

            # 验证新密码强度
            is_valid, errors = PasswordManager.validate_password_strength(new_password)
            if not is_valid:
                return False, f"新密码强度不足: {', '.join(errors)}"

            # 更新密码
            password_hash = PasswordManager.hash_password(new_password)
            self.db_manager.update_password(
                user_id=user_id, new_password_hash=password_hash
            )

            # 记录审计日志
            self.db_manager.log_audit_event(user_id, "PASSWORD_CHANGED", "user")
            logger.info(f"用户密码修改成功: {user.username}")
            return True, "密码修改成功"

        except Exception as e:
            logger.error(f"密码修改失败: {str(e)}")
            return False, f"密码修改失败: {str(e)}"

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        try:
            return self.db_manager.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    def update_user_profile(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """更新用户资料"""
        try:
            user = self.db_manager.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在"

            # 更新用户资料
            if not user.profile:
                user.profile = profile_data
            else:
                user.profile.update(profile_data)
            if self.db_manager.update_user(user):
                # 记录审计日志
                self.db_manager.log_audit_event(
                    user_id, "PROFILE_UPDATED", "user", details=profile_data
                )
                logger.info(f"用户资料更新成功: {user.username}")
                return True, "资料更新成功"
            else:
                return False, "资料更新失败"

        except Exception as e:
            logger.error(f"资料更新失败: {str(e)}")
            return False, f"资料更新失败: {str(e)}"


class AuthorizationManager:
    """授权管理器 - 权限控制"""

    def __init__(self):
        # 导入权限数据库管理器
        try:
            from permission_database import permission_db

            self.permission_db = permission_db
            self.use_database_permissions = True
            logger.info("使用数据库权限管理")
        except ImportError:
            logger.warning("权限数据库不可用，使用默认权限配置")
            self.permission_db = None
            self.use_database_permissions = False
            # 保留原有的硬编码权限作为后备
            self.role_permissions = {
                UserRole.PATIENT: {
                    "agent_access": [
                        "CybertwinAgent",
                        "InternalMedicineAgent",
                        "SurgicalAgent",
                        "SummaryAgent",
                        "TriageAgent",
                    ],
                    "data_access": ["own_data"],
                    "action": ["view", "upload_medical_data"],
                },
                UserRole.DOCTOR: {
                    "agent_access": [
                        "CybertwinAgent",
                        "InternalMedicineAgent",
                        "SurgicalAgent",
                        "HistoryAgent",
                        "SummaryAgent",
                        "TriageAgent",
                        "ImageAnalysisAgent",
                        "ComprehensiveAgent",
                    ],
                    "data_access": ["own_data", "patient_data"],
                    "action": [
                        "view",
                        "upload_medical_data",
                        "analyze_medical_data",
                        "diagnose",
                    ],
                },
                UserRole.NURSE: {
                    "agent_access": [
                        "CybertwinAgent",
                        "InternalMedicineAgent",
                        "SummaryAgent",
                        "TriageAgent",
                    ],
                    "data_access": ["own_data", "patient_data"],
                    "action": ["view", "upload_medical_data", "basic_care"],
                },
                UserRole.ADMIN: {
                    "agent_access": ["*"],  # 所有智能体
                    "data_access": ["*"],  # 所有数据
                    "action": ["*"],  # 所有操作
                },
                UserRole.RESEARCHER: {
                    "agent_access": ["SummaryAgent", "ComprehensiveAgent"],
                    "data_access": ["anonymized_data"],
                    "action": ["view", "analyze_anonymized_data"],
                },
                UserRole.GUEST: {
                    "agent_access": ["CybertwinAgent"],
                    "data_access": ["none"],
                    "action": ["basic_consultation"],
                },
            }

    def check_agent_access(
        self, user_role: UserRole, agent_name: str, user_id: str | None = None
    ) -> bool:
        """检查智能体访问权限"""
        if self.use_database_permissions and self.permission_db:
            return self.permission_db.check_permission(
                user_id or "system", user_role.value, "agent_access", agent_name
            )
        else:
            # 使用硬编码权限
            if user_role not in self.role_permissions:
                return False

            permissions = self.role_permissions[user_role]
            agents = permissions.get("agent_access", [])

            # 管理员可以访问所有智能体
            if "*" in agents:
                return True

            return agent_name in agents

    def check_data_access(
        self, user_role: UserRole, data_type: str, user_id: str | None = None
    ) -> bool:
        """检查数据访问权限"""
        if self.use_database_permissions and self.permission_db:
            return self.permission_db.check_permission(
                user_id or "system", user_role.value, "data_access", data_type
            )
        else:
            # 使用硬编码权限
            if user_role not in self.role_permissions:
                return False

            permissions = self.role_permissions[user_role]
            data_access = permissions.get("data_access", [])

            # 管理员可以访问所有数据
            if "*" in data_access:
                return True

            return data_type in data_access

    def check_action_permission(
        self, user_role: UserRole, action: str, user_id: str | None = None
    ) -> bool:
        """检查操作权限"""
        if self.use_database_permissions and self.permission_db:
            return self.permission_db.check_permission(
                user_id or "system", user_role.value, "action", action
            )
        else:
            # 使用硬编码权限
            if user_role not in self.role_permissions:
                return False

            permissions = self.role_permissions[user_role]
            actions = permissions.get("action", [])

            # 管理员可以执行所有操作
            if "*" in actions:
                return True

            return action in actions

    def get_user_permissions(
        self, user_role: UserRole, user_id: str | None = None
    ) -> Dict[str, List[str]]:
        """获取用户权限列表"""
        if self.use_database_permissions and self.permission_db and user_id:
            return self.permission_db.get_user_permissions(user_id, user_role.value)
        else:
            # 使用硬编码权限
            if self.use_database_permissions and self.permission_db:
                return self.permission_db.get_role_permissions(user_role.value)
            else:
                return self.role_permissions.get(user_role, {})

    def grant_user_permission(
        self,
        user_id: str,
        permission_type: str,
        resource: str,
        expires_at: datetime | None = None,
        reason: str | None = None,
        granted_by: str | None = None,
    ) -> bool:
        """授予用户权限"""
        if self.use_database_permissions and self.permission_db:
            return self.permission_db.grant_user_permission(
                user_id, permission_type, resource, expires_at, reason, granted_by
            )
        else:
            logger.warning("数据库权限管理不可用，无法授予用户权限")
            return False

    def revoke_user_permission(
        self,
        user_id: str,
        permission_type: str,
        resource: str,
        reason: str | None = None,
        revoked_by: str | None = None,
    ) -> bool:
        """撤销用户权限"""
        if self.use_database_permissions and self.permission_db:
            return self.permission_db.revoke_user_permission(
                user_id, permission_type, resource, reason, revoked_by
            )
        else:
            logger.warning("数据库权限管理不可用，无法撤销用户权限")
            return False


class AuditManager:
    """审计管理器"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str | None = None,
        ip_address: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> bool:
        """记录用户操作"""
        return self.db_manager.log_audit_event(
            user_id, action, resource, ip_address, details
        )

    def get_audit_logs(
        self,
        user_id: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            c = conn.cursor()

            query = "SELECT user_id, action, resource, ip_address, timestamp, details FROM audit_logs WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if action:
                query += " AND action = ?"
                params.append(action)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT 1000"

            c.execute(query, params)
            rows = c.fetchall()
            conn.close()

            return [
                {
                    "user_id": row[0],
                    "action": row[1],
                    "resource": row[2],
                    "ip_address": row[3],
                    "timestamp": row[4],
                    "details": row[5],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取审计日志失败: {str(e)}")
            return []


# 全局实例
auth_manager = AuthManager()
authz_manager = AuthorizationManager()
audit_manager = AuditManager(auth_manager.db_manager)

# 导出主要类和实例
__all__ = [
    "User",
    "UserRole",
    "UserStatus",
    "LoginAttempt",
    "PasswordManager",
    "JWTManager",
    "AuthManager",
    "AuthorizationManager",
    "AuditManager",
    "auth_manager",
    "authz_manager",
    "audit_manager",
]
