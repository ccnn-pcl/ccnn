import base64
import uuid
import time

import jwt
from cryptography.hazmat.backends import default_backend
from flask import Blueprint, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from config import OIDC_CONFIG, JWKS_URI, CLIENTS, TRUST_SERVICE_URL, LOGIN_PAGE_URL
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('oidc', __name__, url_prefix='')

# 内存存储
auth_codes = {}
sso_sessions = {}
access_tokens = {}

# 持久化密钥

KEY_FILE = Path("op_private.pem")

def load_or_create_key():
    if KEY_FILE.exists():
        with KEY_FILE.open("rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    # 生成新密钥
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()

    )
    # 落盘 PEM（无加密）
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    KEY_FILE.write_bytes(pem)
    KEY_FILE.chmod(0o600)          # 只允许当前用户读写
    return private_key

private_key = load_or_create_key()
public_key  = private_key.public_key()
# KEY_FILE = Path("op_rsa_key.pem")
# if KEY_FILE.exists():
#     private_key = pickle.loads(KEY_FILE.read_bytes())
# else:
#     private_key = rsa.generate_private_key(
#         public_exponent=65537,
#         key_size=2048,
#         backend=default_backend()
#
#     )
#     KEY_FILE.write_bytes(pickle.dumps(private_key))
# public_key = private_key.public_key()

# ============== JWKS（OIDC 用） ==============
def b64url_encode(n: int) -> str:
    """把大整数转成 Base64URL（去掉=）"""
    byte_len = (n.bit_length() + 7) // 8
    data = n.to_bytes(byte_len, byteorder='big')
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')
# JWKS配置
jwks = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "kid": "1",
            "n": b64url_encode(public_key.public_numbers().n),
            "e": b64url_encode(public_key.public_numbers().e),
        }
    ]
}

# OIDC配置
# oidc_config = {
#     "issuer": "http://localhost:5000",
#     "authorization_endpoint": "http://localhost:5000/authorize",
#     "token_endpoint": "http://localhost:5000/token",
#     "userinfo_endpoint": "http://localhost:5000/userinfo",
#     "jwks_uri": "http://localhost:5000/.well-known/jwks.json",
#     "end_session_endpoint": "http://localhost:5000/endsession",
#     "scopes_supported": ["openid", "profile", "email"],
#     "response_types_supported": ["code"],
#     "subject_types_supported": ["public"],
#     "id_token_signing_alg_values_supported": ["RS256"]
# }
oidc_config = OIDC_CONFIG
clients = CLIENTS
# 注册的客户端应用
# clients = {
#     "user_agent": {
#         "secret": "user_agent-secret",
#         "redirect_uris": ["http://localhost:5001/callback"],
#         "post_logout_redirect_uris": ["http://localhost:5001"]
#     },
#     "app2": {
#         "secret": "app2-secret",
#         "redirect_uris": ["http://localhost:5002/callback"],
#         "post_logout_redirect_uris": ["http://localhost:5002"]
#     },
#     "agent_doctor": {
#         "secret": "agent_doctor-secret",
#         "redirect_uris": ["http://localhost:8000/oidc/callback"],
#         "post_logout_redirect_uris": ["http://localhost:8000"]
#     }
# }
#  discovery
@bp.get('/.well-known/openid-configuration')
def config():
    return jsonify(oidc_config)


@bp.route('/.well-known/jwks.json')
def jwks_endpoint():
    """JWKS端点"""
    return jsonify(jwks)
# 授权端点
@bp.get('/authorize')
def authorize():
    """OIDC授权端点"""
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    state = request.args.get('state')
    nonce = request.args.get('nonce')
    scope = request.args.get('scope', 'openid')
    logger.info(f"authorize获取request信息：{request}")
    logger.info(f"session：{session}")
    if not client_id or not redirect_uri or not state:
        return jsonify({"error": "invalid_request", "error_description": "Missing required parameters"}), 400

    # 验证客户端
    client = clients.get(client_id)
    if not client:
        return jsonify({"error": "unauthorized_client", "error_description": "Invalid client ID"}), 400

    # 验证重定向URI
    if redirect_uri not in client['redirect_uris']:
        return jsonify({"error": "invalid_request", "error_description": "Invalid redirect URI"}), 400

    # 检查用户是否已登录
    sso_session_id = session.get('sso_session_id')
    if not sso_session_id or sso_session_id not in sso_sessions:
        logger.info("用户未登录，重定向到登录页面")
        # 用户未登录，重定向到登录页面
        # session['auth_params'] = {
        #     'client_id': client_id,
        #     'redirect_uri': redirect_uri,
        #     'state': state,
        #     'nonce': nonce,
        #     'scope': scope
        # }
        session['auth_params'] = request.args.to_dict()
        return redirect(f'{LOGIN_PAGE_URL}?{request.query_string.decode()}')
        # return redirect(url_for('login_page'))

    # 用户已登录，生成授权码
    auth_code = str(uuid.uuid4())
    auth_codes[auth_code] = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'sso_session_id': sso_session_id,
        'state': state,
        'nonce': nonce,
        'scope': scope,
        'created_at': time.time(),
        'expires_at': time.time() + 300  # 5分钟过期
    }
    logger.info("用户已登录，重定向到客户端回调地址 " + f"{redirect_uri}?code={auth_code}&state={state}")
    # 重定向到客户端回调地址
    return redirect(f"{redirect_uri}?code={auth_code}&state={state}")

# 令牌端点
@bp.post('/token')
def token():
    """令牌端点"""
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    redirect_uri = request.form.get('redirect_uri')

    if grant_type != 'authorization_code':
        return jsonify({"error": "unsupported_grant_type"}), 400

    if not code or not client_id or not client_secret or not redirect_uri:
        return jsonify({"error": "invalid_request"}), 400

    # 验证客户端
    client = clients.get(client_id)
    if not client or client['secret'] != client_secret:
        return jsonify({"error": "invalid_client"}), 401

    # 验证授权码
    auth_code_data = auth_codes.get(code)
    if not auth_code_data:
        return jsonify({"error": "invalid_grant"}), 400

    if (time.time() > auth_code_data['expires_at'] or
            auth_code_data['client_id'] != client_id or
            auth_code_data['redirect_uri'] != redirect_uri):
        del auth_codes[code]  # 删除无效的授权码
        return jsonify({"error": "invalid_grant"}), 400

    # 获取SSO会话信息
    sso_session_id = auth_code_data['sso_session_id']
    sso_session = sso_sessions.get(sso_session_id)
    if not sso_session or time.time() > sso_session['expires_at']:
        del auth_codes[code]
        return jsonify({"error": "invalid_grant"}), 400
    print("================",sso_session)
    # 生成ID令牌
    id_token_payload = {
        'iss': oidc_config['issuer'],
        'sub': sso_session['user_id'],
        'aud': client_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'auth_time': int(time.time()),
        'nonce': auth_code_data.get('nonce'),
        'name': sso_session['name'],
        'email': sso_session['email'],
        # 'roles': sso_session['roles']
    }

    id_token = jwt.encode(
        id_token_payload,
        private_key,
        algorithm='RS256',
        headers={'kid': '1'}
    )
    # 生成访问令牌
    access_token = str(uuid.uuid4())
    access_tokens[access_token] = {
        'sso_session_id': sso_session_id,
        'expires_at': time.time() + 3600  # 1 小时
    }
    # 删除已使用的授权码
    del auth_codes[code]

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": id_token
    })

# userinfo
@bp.get('/userinfo')
def userinfo():
    token = request.headers.get('Authorization', '').split()[-1]
    rec = access_tokens.get(token)
    if not rec or time.time() > rec['expires_at']:
        return {"error": "invalid_token"}, 401
    sso = sso_sessions.get(rec['sso_session_id'])
    if not sso:
        return {"error": "invalid_token"}, 401
    return jsonify(sub=sso['user_id'], name=sso['name'], email=sso['email'],trustscore=sso['trustscore'])

# 退出
@bp.get('/endsession')
def end_session():
    """结束会话端点"""
    id_token_hint = request.args.get('id_token_hint')
    post_logout_redirect_uri = request.args.get('post_logout_redirect_uri')
    state = request.args.get('state')

    # 1. 统一清全局会话（无论验证是否成功）
    sso_session_id = session.get('sso_session_id')
    if sso_session_id and sso_session_id in sso_sessions:
        del sso_sessions[sso_session_id]
    session.clear()  # 清浏览器 cookie

    # 2. 如果带了 id_token_hint，尝试解出客户端并校验回跳地址
    client_id = None
    if id_token_hint:
        try:
            payload = jwt.decode(
                id_token_hint,
                public_key,
                algorithms=['RS256'],
                options={"verify_signature": True, "verify_aud": False}
            )
            client_id = payload.get('aud')
        except jwt.InvalidTokenError:
            pass

    # 3. 回跳地址合法 → 重定向；不合法 → 直接返回文本
    if client_id and post_logout_redirect_uri:
        client = clients.get(client_id)
        logger.info(f"回跳地址合法: {post_logout_redirect_uri}, {client['post_logout_redirect_uris']}")
        if client and post_logout_redirect_uri in client['post_logout_redirect_uris']:
            if state:
                return redirect(f"{post_logout_redirect_uri}?state={state}")
            return redirect(post_logout_redirect_uri)

    # 4. 默认提示
    # return "You have been logged out", 200
    return redirect(post_logout_redirect_uri)#5.19修改
# ------------------- 对外 JWT 服务 -------------------

@bp.post("/jwt/generate")
def jwt_generate():
    """
    生成 JWT
    POST JSON
    {
        "payload": {
            "name": "u123",
        },
        "expires_in": 3600    # 可选，秒，默认 3600
    }
    返回
    {
        "token": "<JWT>"
    }
    """
    from datetime import timezone
    data = request.get_json(force=True, silent=True) or {}
    payload = data.get("payload")
    if not isinstance(payload, dict):
        return jsonify({"error": "missing or invalid 'payload'"}), 400

    expires_in = int(data.get("expires_in", 3600))
    now = datetime.now(timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": oidc_config["issuer"]
    })
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "1"})
    return jsonify({"token": jwt_token})


@bp.post("/jwt/verify")
def jwt_verify():
    """
    验证 JWT
    POST JSON
    {
        "token": "<JWT>"
    }
    返回
    {
        "valid": true,
        "payload": { ... }
    }
    or
    {
        "valid": false,
        "error": "expired"
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    token = data.get("token")
    if not token or not isinstance(token, str):
        return jsonify({"valid": False, "error": "missing or invalid 'token'"}), 400

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return jsonify({"valid": True, "payload": payload})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "token expired"}), 200
    except jwt.InvalidTokenError as e:
        return jsonify({"valid": False, "error": str(e)}), 200