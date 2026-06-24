import uuid
import time
import threading

import requests
from flask import Blueprint, request, jsonify, session, redirect, url_for
from oidc.views import sso_sessions
from src.database import get_db_primary, get_db_read_with_fallback
from src.models import User, find_user_by_face_optimized
from src.utils import base64_to_image, extract_face_encoding, compare_faces, resolve_client_ip, call_trust_service
from config import TRUST_SERVICE_URL, OPENXG_ADDR
import logging
import json

logger = logging.getLogger(__name__)
bp = Blueprint('user', __name__, url_prefix='')

FIXED_USERID = 10000000


@bp.post('/api/register')
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    image_data = data.get('image')
    email = data.get('email')
    if not all([username, password, image_data, email]):
        return {"success": False, "message": "缺少参数"}, 400

    db = next(get_db_primary())
    if db.query(User).filter_by(username=username).first():
        return {"success": False, "message": "用户名已存在"}, 400

    img = base64_to_image(image_data)
    enc = extract_face_encoding(img)
    if enc is None:
        return {"success": False, "message": "未检测到人脸"}, 400

    for u in db.query(User).all():
        known = u.get_face_encoding()
        if known is not None:
            match, sim = compare_faces(known, enc, tolerance=0.5)
            if match and sim > 0.8:
                return {"success": False, "message": f"与用户 {u.username} 相似度过高"}, 409

    new_id = User.generate_id()
    if db.query(User).filter_by(userid=new_id).first():
        new_id = User.generate_id()

    new = User(userid=new_id, username=username, email=email)
    new.set_password(password)
    new.set_face_encoding(enc)
    db.add(new)
    db.commit()
    return {"success": True, "message": "注册成功"}


@bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    浏览器 POST 到 /login（仍在 OP 域）
    只收 username（人脸已验证通过）
    发 OIDC Cookie -> 302 回 authorize
    """
    username = request.form.get('username')
    trustscore = request.form.get('trustscore')
    if not username:
        return "缺少用户名", 400

    db = next(get_db_read_with_fallback())
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return "用户名不存在", 401

    sso_session_id = str(uuid.uuid4())
    sso_sessions[sso_session_id] = {
        'user_id': str(user.userid),
        'name': user.username,
        'email': user.email,
        'trustscore': trustscore,
        'created_at': time.time(),
        'expires_at': time.time() + 3600
    }

    session['sso_session_id'] = sso_session_id
    logger.info("sso_session_id生成")
    session.permanent = True

    if 'auth_params' in session:
        def send_background_requests():
            try:
                requests_data = [
                    {"mac": "70:C9:4E:E2:FF:1B", "imsi": "466920000000001", "limit": 1000},
                    {"mac": "48:7E:25:07:12:EA", "imsi": "466920000000002", "limit": 1000},
                    {"mac": "94:B6:09:21:49:9A", "imsi": "466920000000003", "limit": 1000}
                ]
                for data in requests_data:
                    try:
                        response = requests.post(
                            OPENXG_ADDR,
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps(data),
                            timeout=5
                        )
                        logger.info(f"后台请求发送成功: {data['mac']}, 状态码: {response.status_code}")
                    except Exception as e:
                        logger.error(f"后台请求发送失败 {data['mac']}: {str(e)}")
            except Exception as e:
                logger.error(f"后台任务异常: {str(e)}")

        thread = threading.Thread(target=send_background_requests)
        thread.daemon = True
        thread.start()

        logger.info("auth_params: %s", session.get('auth_params'))
        auth_params = session.pop('auth_params')
        return redirect(url_for('oidc.authorize', **auth_params))

    return "Login successful"


@bp.post('/api/login')
def login_with_face():
    try:
        ipv4 = resolve_client_ip(request)
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_data = data.get('image')
        device_info = data.get('deviceInfo', {})

        logger.info(f"登录请求: 用户名={username}")
        logger.info(f"登录请求: 设备信息={device_info}")
        has_pwd = bool(username and password)
        has_face = bool(image_data)
        logger.info("has_face=%s, has_pwd=%s", has_face, has_pwd)

        if not any([has_pwd, has_face]):
            logger.warning("登录失败: 缺少必要参数")
            return jsonify({'success': False, 'message': '缺少必要参数'})

        db = next(get_db_read_with_fallback())

        if has_face:
            img = base64_to_image(image_data)
            if img is None:
                return jsonify(success=False, message='无法处理图像数据')

            unknown_encoding = extract_face_encoding(img)
            if unknown_encoding is None:
                return jsonify(success=False, message='未检测到人脸')

            best_user, best_sim = find_user_by_face_optimized(unknown_encoding, db)
            if best_user is None or best_sim < 0.70:
                logger.warning(f"人脸登录未找到匹配用户，最高相似度: {best_sim:.2f}")
                return jsonify(success=False, message='未识别到已注册用户')

            trust = call_trust_service(ipv4, device_info, best_sim, 0.0)
            logger.info(f"用户 {best_user.username} 人脸登录成功，相似度: {best_sim:.2f}，信任分: {trust}")
            return jsonify(
                success=True,
                message=f'登录成功，欢迎 {best_user.username}！',
                username=best_user.username,
                similarity=round(best_sim, 2),
                trustscore=trust
            )
        else:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"用户 {username} 不存在")
                return jsonify({'success': False, 'message': '用户不存在'})

            if not user.check_password(password):
                logger.warning(f"用户 {username} 密码错误")
                return jsonify({'success': False, 'message': '密码错误'})

            trust = call_trust_service(ipv4, device_info, 0.0, 1.0)
            return jsonify(
                success=True,
                message=f'登录成功，欢迎 {username}！',
                username=user.username,
                trustscore=trust
            )

    except Exception as e:
        logger.exception(f"登录错误: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@bp.route('/api/keep-auth', methods=['POST'])
def keep_auth():
    try:
        ipv4 = resolve_client_ip(request)
        data = request.get_json()
        device_info = data.get('deviceInfo', {})

        trust = call_trust_service(ipv4, device_info, 0.0, 0.0)
        return jsonify(success=True, trustscore=trust)

    except Exception as e:
        logger.exception(f"持续认证错误: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500
