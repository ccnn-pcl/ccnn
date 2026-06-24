import face_recognition
import cv2
import numpy as np
import base64
import logging
import requests
from datetime import datetime
from config import TRUST_SERVICE_URL

logger = logging.getLogger(__name__)


# ============== 图像处理 ==============

def base64_to_image(base64_str):
    """将Base64字符串转换为OpenCV图像"""
    try:
        if 'base64,' in base64_str:
            base64_str = base64_str.split('base64,')[1]

        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            logger.error("无法解码Base64图像数据")
            return None

        logger.info(f"成功转换Base64为图像，尺寸: {img.shape}")
        return img

    except Exception as e:
        logger.exception(f"Base64转换错误: {str(e)}")
        return None


def extract_face_encoding(image):
    """从图片中提取人脸编码"""
    if image is None:
        logger.error("提取人脸编码: 输入图像为空")
        return None

    try:
        if len(image.shape) == 2:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        face_encodings = face_recognition.face_encodings(rgb_image)

        if len(face_encodings) > 0:
            logger.info(f"成功提取到 {len(face_encodings)} 个人脸编码")
            return face_encodings[0].astype(np.float64)
        else:
            logger.warning("图像中未检测到人脸")
            return None

    except Exception as e:
        logger.exception(f"提取人脸编码错误: {str(e)}")
        return None


def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
    """比对人脸编码，返回是否匹配和相似度"""
    if known_encoding is None or unknown_encoding is None:
        logger.warning("比较人脸: 其中一个编码为空")
        return False, 0.0

    try:
        known_arr = np.asarray(known_encoding, dtype=np.float64)
        unknown_arr = np.asarray(unknown_encoding, dtype=np.float64)

        if known_arr.shape != unknown_arr.shape:
            logger.warning(f"编码形状不匹配: {known_arr.shape} vs {unknown_arr.shape}")
            return False, 0.0

        distance = np.linalg.norm(known_arr - unknown_arr)
        similarity = 1 - distance
        match = similarity >= tolerance

        logger.info(f"人脸比对结果: {'匹配' if match else '不匹配'}, 相似度: {similarity:.2f}")
        return match, similarity

    except Exception as e:
        logger.exception(f"人脸比较错误: {str(e)}")
        return False, 0.0


# ============== 客户端 IP 解析 ==============

def resolve_client_ip(request) -> str:
    """从请求头中解析客户端真实IPv4地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        clientip = forwarded.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            clientip = real_ip
        else:
            clientip = request.remote_addr

    if '::ffff:' in clientip:
        ipv4 = clientip.split('ffff:')[-1]
    else:
        ipv4 = clientip

    logger.info("客户端IP: %s (原始: %s)", ipv4, clientip)
    return ipv4


# ============== 信任评分服务调用 ==============

def call_trust_service(ipv4: str, device_info: dict, bio_val: float, has_pws: float) -> float:
    """调用信任评分服务，返回 trust_score，异常时返回 -1"""
    payload = {
        "ipaddress": ipv4,
        "pswd": has_pws,
        "time": datetime.now().hour,
        "bio": float(bio_val),
        "city": "深圳"
    }

    # 构建设备信息字符串
    os_name = device_info.get('os', '')
    if os_name == 'Windows':
        payload["device"] = (
            f"{os_name}{device_info.get('osVersion', '')}-"
            f"{device_info.get('deviceType', '')}-"
            f"{device_info.get('resolution', '')}"
        )
    else:
        dev = device_info.get('device', {})
        payload["device"] = (
            f"{os_name}{device_info.get('osVersion', '')}-"
            f"{dev.get('type', '')}-"
            f"{dev.get('vendor', '')}-"
            f"{dev.get('model', '')}"
        )

    try:
        logger.debug("trust-service payload: %s", payload)
        r = requests.post(TRUST_SERVICE_URL, json=payload, timeout=2)
        r.raise_for_status()
        return r.json().get('trust_score', -1)
    except Exception:
        logger.exception("调用 trust-service 异常")
        return -1
