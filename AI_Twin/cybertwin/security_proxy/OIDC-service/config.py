# config.py
import logging
import os
import json

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 1. 先把 .env 加载到系统环境变量
load_dotenv()

# 2. 再读取/转换，提供安全的默认值
def safe_json_loads(env_var, default="{}"):
    """安全地解析JSON环境变量"""
    value = os.getenv(env_var)
    if value and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return json.loads(default)
    return json.loads(default)

OIDC_CONFIG = safe_json_loads("OIDC_CONFIG")
JWKS_URI    = os.getenv("JWKS_URI", "")
DATABASE_URI= os.getenv("DATABASE_URI", "")
TRUST_SERVICE_URL = os.getenv("TRUST_SERVICE_URL", "")
LOGIN_PAGE_URL    = os.getenv("LOGIN_PAGE_URL", "")
CLIENTS           = safe_json_loads("CLIENTS")
OPENXG_ADDR       = safe_json_loads("OPENXG_ADDR")
PRIMARY_DB_URI    = os.getenv("MYSQL_DB1_URL", "")
SECONDARY_DB_URI  = os.getenv("MYSQL_DB2_URL", "")

logger.info("配置加载完成: issuer=%s", OIDC_CONFIG.get("issuer", "N/A"))
