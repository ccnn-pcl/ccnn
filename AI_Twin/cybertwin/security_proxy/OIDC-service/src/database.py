import os
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from config import PRIMARY_DB_URI, SECONDARY_DB_URI

logger = logging.getLogger(__name__)

Base = declarative_base()


if not PRIMARY_DB_URI:
    raise ValueError("MYSQL_PRIMARY_URI is required")

engine = create_engine(PRIMARY_DB_URI, pool_pre_ping=True, pool_recycle=3600)
engine_secondary = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocalSecondary = None

def init_secondary_engine():
    """延迟初始化备用数据库引擎"""
    global engine_secondary, SessionLocalSecondary
    if SECONDARY_DB_URI and engine_secondary is None:
        try:
            engine_secondary = create_engine(SECONDARY_DB_URI, pool_pre_ping=True, pool_recycle=3600)
            SessionLocalSecondary = sessionmaker(autocommit=False, autoflush=False, bind=engine_secondary)
        except Exception as e:
            logger.error(f"备用数据库初始化失败: {e}")
            engine_secondary = None
            SessionLocalSecondary = None


def get_db_primary():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_read_with_fallback():
    """
    读操作：先尝试第一个数据库，失败才连接第二个数据库
    """
    db = None
    try:
        # 先尝试第一个数据库
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        yield db
        return
    except OperationalError:
        if db is not None:
            db.close()
        # 第一个数据库失败，尝试第二个数据库
        if not SECONDARY_DB_URI:
            raise Exception("主数据库连接失败，且未配置备用数据库")
        
        # 延迟初始化备用数据库引擎
        init_secondary_engine()
        
        if SessionLocalSecondary is None:
            raise Exception("备用数据库初始化失败")
        
        try:
            db = SessionLocalSecondary()
            db.execute(text("SELECT 1"))
            yield db
        except Exception as e:
            if db is not None:
                db.close()
            raise Exception(f"备用数据库连接失败: {e}")
    finally:
        if db is not None:
            db.close()
