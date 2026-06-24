"""
事件发布模块 — 将用户行为事件推送到 Kafka
"""
import json
import logging
import threading
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError

from config import KAFKA_CONFIG

logger = logging.getLogger(__name__)

# 事件 ID 常量
EVENT_LOGIN_SUCCESS         = 1000
EVENT_LOGIN_FAILURE         = 1001
EVENT_LOGOUT                = 1002
EVENT_REGISTER_SUCCESS      = 1003
EVENT_REGISTER_FAILURE      = 1004

# 缓存最近一次登录的位置，key=IP，供 keep-auth 无位置时复用
last_login_location = {}

# 全局 producer（延迟初始化，线程安全）
_producer = None
_producer_lock = threading.Lock()


def _get_producer() -> KafkaProducer | None:
    """获取或创建 KafkaProducer 单例"""
    global _producer
    if _producer is not None:
        return _producer

    with _producer_lock:
        if _producer is not None:
            return _producer
        try:
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
                security_protocol=KAFKA_CONFIG["security_protocol"],
                sasl_mechanism=KAFKA_CONFIG["sasl_mechanism"],
                sasl_plain_username=KAFKA_CONFIG["sasl_plain_username"],
                sasl_plain_password=KAFKA_CONFIG["sasl_plain_password"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=0,              # 不等待确认，追求低延迟
                retries=1,
                max_block_ms=3000,   # 最多阻塞 3s
            )
            logger.info("Kafka producer 初始化成功: %s", KAFKA_CONFIG["bootstrap_servers"])
        except Exception:
            logger.exception("Kafka producer 初始化失败")
            _producer = None
        return _producer


def publish_event(
    event_id: int,
    user_id,
    device: str,
    ip: str,
    location: str,
    message_content=None
):
    """
    异步推送事件到 Kafka（后台线程，不阻塞请求）

    参数:
        event_id: 事件ID (100=登录成功, 101=登录失败, 102=退出)
        user_id: 用户ID
        device: 设备信息字符串
        ip: 客户端IP
        location: 位置字符串 "城市,lat,lng"
        message_content: 附加消息内容 (dict)
    """
    event = {
        "event_id": event_id,
        "user_id": user_id if user_id else 0,
        "device": device,
        "ip": ip,
        "location": location,
        "event_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "message_content": message_content or {},
    }

    def _send():
        producer = _get_producer()
        if producer is None:
            logger.warning("Kafka producer 不可用，丢弃事件: %s", event)
            return
        try:
            future = producer.send(KAFKA_CONFIG["topic"], value=event)
            # 立即等待结果（acks=0 时很快返回）
            future.get(timeout=2)
            logger.info("事件已推送 Kafka: event_id=%d, user_id=%s", event_id, user_id)
        except KafkaError:
            logger.exception("Kafka 推送失败, event_id=%d", event_id)
        except Exception:
            logger.exception("Kafka 推送异常, event_id=%d", event_id)

    t = threading.Thread(target=_send, daemon=True)
    t.start()


# ---------- 工具函数 ----------

def build_device_str(device_info: dict) -> str:
    """根据 deviceInfo 构建设备描述字符串"""
    if not device_info:
        return ""
    os_name = device_info.get('os', '')
    os_ver = device_info.get('osVersion', '')
    if os_name == 'Windows':
        return f"{os_name}{os_ver}"
    else:
        dev = device_info.get('device', {})
        vendor = dev.get('vendor', '')
        model = dev.get('model', '')
        if vendor and model:
            return f"{vendor} {model},{os_name}{os_ver}"
        elif model:
            return f"{model},{os_name}{os_ver}"
        else:
            return f"{os_name}{os_ver}"


def build_location_str(city: str, lat, lng) -> str:
    """构建位置字符串 '城市,lat,lng'"""
    parts = []
    if city:
        parts.append(city)
    if lat is not None and lng is not None:
        parts.append(f"{lat},{lng}")
    elif lat is not None:
        parts.append(str(lat))
    elif lng is not None:
        parts.append(str(lng))
    return ",".join(parts) if parts else ""
