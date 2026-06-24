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

# OIDC 配置 — 只需环境变量 OIDC_ISSUER，其余端点自动派生
_OIDC_ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:5000")
OIDC_CONFIG = {
    "issuer": _OIDC_ISSUER,
    "authorization_endpoint": f"{_OIDC_ISSUER}/authorize",
    "token_endpoint": f"{_OIDC_ISSUER}/token",
    "userinfo_endpoint": f"{_OIDC_ISSUER}/userinfo",
    "jwks_uri": f"{_OIDC_ISSUER}/.well-known/jwks.json",
    "end_session_endpoint": f"{_OIDC_ISSUER}/endsession",
    "scopes_supported": ["openid", "profile", "email"],
    "response_types_supported": ["code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
}
JWKS_URI = OIDC_CONFIG["jwks_uri"]
DATABASE_URI= os.getenv("DATABASE_URI", "")
TRUST_SERVICE_URL = os.getenv("TRUST_SERVICE_URL", "")
LOGIN_PAGE_URL    = os.getenv("LOGIN_PAGE_URL", "")
CLIENTS           = safe_json_loads("CLIENTS")
OPENXG_ADDR       = safe_json_loads("OPENXG_ADDR")
PRIMARY_DB_URI    = os.getenv("MYSQL_DB1_URL", "")
SECONDARY_DB_URI  = os.getenv("MYSQL_DB2_URL", "")

# Kafka 事件推送配置
KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BROKER", "192.168.193.82:31493"),
    "topic": os.getenv("KAFKA_TOPIC", "_cybertwin_event_"),
    "group_id": os.getenv("KAFKA_GROUP_ID", "cybertwin_event_sr_group"),
    "security_protocol": "SASL_PLAINTEXT",
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": os.getenv("KAFKA_USERNAME", "admin"),
    "sasl_plain_password": os.getenv("KAFKA_PASSWORD", "pcnl@2026"), 
}

logger.info("配置加载完成: issuer=%s", OIDC_CONFIG.get("issuer", "N/A"))
