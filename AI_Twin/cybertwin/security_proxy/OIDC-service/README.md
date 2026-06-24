# cybertwin-OIDC-service

基于 Flask 的 OIDC (OpenID Connect) 单点登录服务端，支持人脸识别登录与信任评分。

## 项目架构

```
┌──────────────────────────────────────────────────┐
│                  run.py (入口)                   │
│                      │                           │
│              app.py (应用工厂)                    │
│                   /        \                     │
│          oidc/views.py   user/views.py           │
│          (OIDC OP 蓝图)   (用户管理蓝图)          │
│               │                │                 │
│         ┌─────┴──────┐   ┌────┴─────┐            │
│         │ JWT / 令牌  │   │ 注册/登录 │           │
│         │ 授权码/会话 │   │ 人脸识别  │           │
│         │ 用户信息    │   │ 信任评分  │           │
│         └────────────┘   └──────────┘            │
│               │                │                 │
│         ┌─────┴────────────────┴─────┐           │
│         │       src/ 公共模块         │           │
│         │  database  models  utils   │           │
│         └────────────────────────────┘           │
└──────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env` 文件并修改配置：

```bash
# OIDC 配置（单行 JSON）
OIDC_CONFIG={"issuer":"http://your-ip:5000","authorization_endpoint":"...",...}

# 客户端注册信息（JSON 格式）
CLIENTS={"app_id":{"secret":"...","redirect_uris":["..."],"post_logout_redirect_uris":["..."]}}

# 数据库（MySQL 主备）
MYSQL_DB1_URL=mysql+pymysql://user:password@host1:3306/CCNN_db1?charset=utf8mb4
MYSQL_DB2_URL=mysql+pymysql://user:password@host2:3306/CCNN_db2?charset=utf8mb4

# 信任评分服务
TRUST_SERVICE_URL=http://CCNN-trust-service/evaluate/user-trust

# 外部登录页面 URL
LOGIN_PAGE_URL=http://CCNN-frontend/login
```

### 启动服务

```bash
# 启动 OIDC OP（端口 5000）
python run.py
```

## 项目结构

```
cybertwin-OIDC-service/
├── app.py                  # Flask 应用工厂
├── run.py                  # 启动入口
├── config.py               # 配置加载（从 .env 读取）
├── .env                    # 环境变量配置
├── .gitignore              # Git 忽略规则
├── .dockerignore           # Docker 构建忽略规则
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 构建文件
│
├── oidc/                   # OIDC OP 蓝图
│   ├── __init__.py
│   └── views.py            # 授权/令牌/用户信息/注销/JWT 端点
│
├── user/                   # 用户管理蓝图
│   ├── __init__.py
│   └── views.py            # 注册/登录/持续认证
│
├── src/                    # 公共模块
│   ├── __init__.py
│   ├── database.py         # 数据库引擎（主备故障转移）
│   ├── models.py           # User 模型（密码哈希/人脸编码/ID 生成）
│   └── utils.py            # 图像处理/IP 解析/信任评分调用
│
└── k8s/                    # Kubernetes 部署配置
    ├── configmap.yaml      # 环境变量配置
    ├── deployment.yaml     # Deployment + 健康检查
    └── service.yaml        # Service（ClusterIP）
```

## API 端点

### OIDC 协议端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/.well-known/openid-configuration` | GET | OIDC 发现配置 |
| `/.well-known/jwks.json` | GET | JWKS 公钥 |
| `/authorize` | GET | 授权码端点 |
| `/token` | POST | 令牌交换（授权码 → access_token + id_token） |
| `/userinfo` | GET | 用户信息（需 Bearer token） |
| `/endsession` | GET | 会话注销 |

### 用户管理端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/register` | POST | 用户注册（用户名+密码+人脸+邮箱） |
| `/api/login` | POST | 登录（人脸或账密），返回信任分 |
| `/api/auth/login` | POST | OIDC 流程登录，创建 SSO 会话 |
| `/api/keep-auth` | POST | 持续认证，刷新信任分 |

### JWT 服务端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/jwt/generate` | POST | 生成 JWT（RS256 签名） |
| `/jwt/verify` | POST | 验证 JWT |

## 技术栈

| 组件 | 技术 |
|------|------|
| 框架 | Flask 3.1 |
| 数据库 | SQLAlchemy 2.0 + MySQL（支持主备故障转移） |
| 认证 | OIDC (OpenID Connect) + JWT (RS256) |
| 人脸识别 | face_recognition + dlib + OpenCV |
| 密码哈希 | bcrypt |
| 密钥 | RSA 2048-bit |

## 开发说明

### 代码规范

- 使用 Flask Blueprint 组织路由，禁止独立 Flask 应用
- 公共工具函数统一放在 `src/utils.py`
- 日志使用 `logging.getLogger(__name__)`，`print()` 仅限临时调试
- 配置从 `.env` 加载，不硬编码密钥和 URL

### 架构原则

1. **应用工厂模式**：`app.py` 提供 `create_app()` 工厂函数，`run.py` 仅做启动
2. **蓝图分离**：OIDC 协议逻辑与用户管理逻辑分离到不同蓝图
3. **主备数据库**：读操作自动故障转移，写操作仅用主库
4. **无状态令牌**：JWT 用于无状态验证，access_token 当前使用服务端存储

## Docker 部署

```bash
# 构建镜像
docker build -t CCNN/cybertwin-OIDC-service:latest .

# 运行容器
docker run -d \
  --name cybertwin-OIDC-service \
  -p 5000:5000 \
  --env-file .env \
  cybertwin-OIDC-service
```

## Kubernetes 部署

```bash
# 1. 先修改 k8s/configmap.yaml 中的占位符
#   将 <OP_SERVICE_HOST> 等替换为实际地址

# 2. 部署到 K8s 集群
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 配置文件说明

| 文件 | 说明 |
|------|------|
| `k8s/configmap.yaml` | 环境变量配置，部署前需替换 `<PLACEHOLDER>` |
| `k8s/deployment.yaml` | Deployment，含健康检查、资源限制、滚动更新 |
| `k8s/service.yaml` | ClusterIP 服务，端口 31111 → 5000 |

### ConfigMap 占位符

| 占位符 | 说明 |
|--------|------|
| `<OP_SERVICE_HOST>` | OP 服务 K8s Node IP |
| `<USER_AGENT_HOST>` | User Agent 客户端 K8s Node IP |
| `<mysql-host1>` / `<mysql-host2>` | MySQL 主/备库地址 |
| `<user>` / `<password>` | MySQL 账号密码 |
| `<FRONTEND_HOST>` | 前端页面地址 |
| `<OPENXG_HOST>` | 接入端服务地址 |
| `<YOUR_DOMAIN>` | Session cookie 域名 |
| `<YOUR_REGISTRY>` / `<VERSION>` | 镜像仓库地址和版本号 |


