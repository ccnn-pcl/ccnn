
# models.py
from sqlalchemy import Column, Integer, String, PickleType
from .database import Base
import bcrypt
import pickle
import numpy as np
import time
import threading
import logging

logger = logging.getLogger(__name__)

# ---------- 8 位 ID 生成器 ----------
class ShortID:
    """秒级压缩 + 2 位循环序号，保证 8 位数字以内"""
    def __init__(self):
        self.counter = 0
        self.lock = threading.Lock()
        self.last_sec = 0

    def gen(self) -> int:
        with self.lock:
            sec = int(time.time())
            if sec != self.last_sec:
                self.counter = 0
                self.last_sec = sec
            else:
                self.counter = (self.counter + 1) % 100
                if self.counter == 0:          # 00-99 用完，等下一秒
                    time.sleep(1)
                    sec = int(time.time())
                    self.counter = 0
                    self.last_sec = sec
            suffix = sec % 1_000_000          # 后 6 位秒
            return suffix * 100 + self.counter # 共 8 位

short_id = ShortID()  # 全局单例

# ---------- 数据库模型 ----------
class User(Base):
    __tablename__ = "users"

    # 主键：userid（使用随机算法生成）
    userid = Column(Integer, primary_key=True, nullable=False, unique=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    face_encoding = Column(PickleType)
    email = Column(String(120), unique=True, nullable=True)
    role = Column(String(30), nullable=False, default="user")

    # --- 密码 ---
    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # --- 人脸 ---
    def set_face_encoding(self, encoding):
        if not isinstance(encoding, np.ndarray):
            encoding = np.array(encoding, dtype=np.float64)
        self.face_encoding = pickle.dumps(encoding)

    def get_face_encoding(self):
        if self.face_encoding:
            enc = pickle.loads(self.face_encoding)
            if not isinstance(enc, np.ndarray):
                logger.warning(f"Face encoding not ndarray, got {type(enc)}")
                enc = np.array(enc, dtype=np.float64)
            if enc.dtype != np.float64:
                enc = enc.astype(np.float64)
            return enc
        return None

    # --- 主键生成 ---
    @staticmethod
    def generate_id() -> int:
        return short_id.gen()   # 8 位以内


def find_user_by_face_optimized(unknown_encoding, db, tolerance=0.6):
    """优化版的人脸查找"""
    import numpy as np
    from scipy.spatial.distance import cdist

    # 只查询必要的字段
    users = db.query(User.userid, User.face_encoding).filter(
        User.face_encoding.isnot(None)
    ).all()
    logger.info("开始识别人脸信息")
    if not users:
        return None, 0.0

    # 批量处理编码
    known_encodings = []
    user_ids = []

    for user in users:
        try:
            # 批量反序列化
            enc = pickle.loads(user.face_encoding)
            if not isinstance(enc, np.ndarray):
                enc = np.array(enc, dtype=np.float64)
            elif enc.dtype != np.float64:
                enc = enc.astype(np.float64)
            logger.info(f"依次识别人脸信息: {user}")
            known_encodings.append(enc)
            user_ids.append(user.userid)
        except Exception as e:
            logger.warning(f"反序列化用户 {user.userid} 的人脸编码失败: {e}")
            continue

    if not known_encodings:
        return None, 0.0

    # 批量计算相似度
    logger.info("批量计算相似度")
    unknown_arr = np.asarray(unknown_encoding, dtype=np.float64).reshape(1, -1)
    known_matrix = np.array(known_encodings)
    logger.info("使用向量化计算")
    # 使用向量化计算
    distances = cdist(known_matrix, unknown_arr, metric='euclidean').flatten()
    similarities = 1 - distances
    logger.info("找到最佳匹配")

    # 找到最佳匹配
    best_idx = np.argmax(similarities)
    best_sim = similarities[best_idx]

    if best_sim >= tolerance:
        best_user = db.query(User).filter(User.userid == user_ids[best_idx]).first()
        logger.info(f"人脸匹配成功: 用户 {best_user.username}, 相似度: {best_sim:.3f}")
        return best_user, best_sim
    else:
        logger.info(f"未找到匹配用户，最佳相似度: {best_sim:.3f}")
        return None, best_sim
