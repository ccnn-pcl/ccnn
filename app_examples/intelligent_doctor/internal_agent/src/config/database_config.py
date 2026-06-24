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
数据库配置文件
=============

支持SQLite和MySQL双模式
注意：PostgreSQL支持已迁移到MySQL，相关代码已注释
"""

from typing import Any, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """数据库配置类"""

    DATABASE_TYPE: str = "mysql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "doctor_user"
    DATABASE_PASSWORD: str = "doctor_password"
    DATABASE_DB_NAME: str = "private_doctor_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_CHARSET: str = "utf8m64"
    DATABASE_CONNECTION_TIMEOUT: int = 10
    DATABASE_READ_TIMEOUT: int = 30
    DATABASE_WRITE_TIMEOUT: int = 30
    DATABASE_ECHO: bool = True

    SQLITE_AUTH_DB: str = "data/auth.db"
    SQLITE_CHAT_HISTORY_DB: str = "data/chat_history.db"
    SQLITE_MEDICAL_RECORDS_DB: str = "data/medical_records.db"
    SQLITE_USER_PROFILES_DB: str = "data/user_profiles.db"
    SQLITE_PERMISSIONS_DB: str = "data/permissions.db"
    SQLITE_AUDIT_DB: str = "data/audit.db"

    model_config = SettingsConfigDict(
        extra="allow",  # 默认为 ignore，可改为 allow/forbid
    )

    def _get_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        # PostgreSQL支持已迁移到MySQL，相关代码已注释
        # if self.database_type == 'postgresql':
        #     return self._get_postgresql_config()
        if self.DATABASE_TYPE.lower() == "mysql":
            return self._get_mysql_config()
        else:
            return self._get_sqlite_config()

    def _get_mysql_config(self) -> Dict[str, Any]:
        """MySQL配置"""
        # MySQL地址和端口从环境变量获取，其他信息与PostgreSQL相同
        # 注意：MySQL默认端口是3306，不是PostgreSQL的5432
        if self.DATABASE_TYPE != "mysql":
            raise Exception("is invalid database config no for mysql")
        return {
            "type": "mysql",
            "host": self.DATABASE_HOST,
            "port": self.DATABASE_PORT,
            "database": self.DATABASE_DB_NAME,
            "user": self.DATABASE_USER,
            "password": self.DATABASE_PASSWORD,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "charset": self.DATABASE_CHARSET,
            "connect_timeout": self.DATABASE_CONNECTION_TIMEOUT,
            "read_timeout": self.DATABASE_READ_TIMEOUT,
            "write_timeout": self.DATABASE_WRITE_TIMEOUT,
            "echo": self.DATABASE_ECHO,
        }

    def _get_database_type(self) -> str:
        return self.DATABASE_TYPE

    def _get_sqlite_config(self) -> Dict[str, Any]:
        """SQLite配置"""
        if self.DATABASE_TYPE != "sqlit":
            raise Exception("is invalid database config no for sqlite")
        return {
            "type": "sqlite",
            "databases": {
                "auth": self.SQLITE_AUTH_DB,
                "chat_history": self.SQLITE_CHAT_HISTORY_DB,
                "medical_records": self.SQLITE_MEDICAL_RECORDS_DB,
                "user_profiles": self.SQLITE_USER_PROFILES_DB,
                "permissions": self.SQLITE_PERMISSIONS_DB,
                "audit": self.SQLITE_AUDIT_DB,
            },
        }


# 全局配置实例
db_config = DatabaseConfig()

if __name__ == "__main__":
    config = db_config._get_config()
    print(config)
