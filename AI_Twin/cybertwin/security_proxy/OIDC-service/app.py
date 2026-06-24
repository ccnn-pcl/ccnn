import logging

from flask import Flask
from flask_cors import CORS
from src.database import engine, Base


def create_app():
    """应用工厂"""
    # 统一日志配置（仅首次调用生效）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    from oidc.views import bp as oidc_bp
    from user.views import bp as user_bp

    Base.metadata.create_all(bind=engine)  # 建表

    app = Flask(__name__)
    app.secret_key = 'sso-server-secret-key'
    CORS(app)
    app.register_blueprint(oidc_bp)
    app.register_blueprint(user_bp)
    return app