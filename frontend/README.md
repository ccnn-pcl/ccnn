# AI Twin Frontend (CyberTwin)

人脸识别认证 + AI 聊天前端应用，基于 Vue 3，部署于 Kubernetes。

## 功能特性

- 🔐 **人脸识别认证** - 摄像头采集人脸 + 密码双因素认证
- 💬 **AI 实时聊天** - 基于 WebSocket 的 AI 对话，支持图片/文件上传
- 📱 **设备指纹** - 自动检测设备信息用于风控
- 📍 **GPS 定位采集** - `navigator.geolocation` + 高德 API 解码到区级（需 HTTPS）
- ⭐ **信任评分** - 实时轮询用户信任评分，低分自动登出
- 🩺 **医疗模块跳转** - AI 回复可携带 redirect 元数据跳转到医疗前端

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 路由 | Vue Router 4 |
| 状态管理 | Pinia |
| 构建 | Vite 6 |
| HTTP | Axios (统一拦截器) |
| WebSocket | 原生 WebSocket |
| 定位 | navigator.geolocation + 高德 Web API |
| 部署 | Docker + Nginx (K8s) |
| 认证 | Keycloak OIDC |
| 工具 | ua-parser-js, FontAwesome, markdown-it |

## 快速开始

### 环境要求

- Node.js >= 18
- npm

### 环境变量

创建 `.env` 文件（本地开发）和 `.env.production`（生产构建），变量以 `VITE_` 开头：

```bash
VITE_AMAP_KEY=your_amap_key          # 高德地图 API Key
VITE_MEDICAL_FRONTEND=http://...     # 医疗前端地址
```

### 安装与运行

```bash
# 安装依赖
npm install

# 开发环境运行
npm run serve

# 生产构建
npm run build
```

构建产物在 `dist/` 目录。

## 项目结构

```
face_frontend/
├── index.html                   # Vite 入口（根目录）
├── public/
│   └── config.js              # 运行时配置（K8s ConfigMap 注入）
├── src/
│   ├── api/                  # API 层
│   │   ├── request.js       # Axios 实例 + 拦截器
│   │   ├── auth.js          # 认证 API（登录/注册）
│   │   └── chat.js          # 聊天 API
│   ├── assets/               # 资源文件
│   ├── components/           # 组件
│   │   ├── chat/            # 聊天子组件
│   │   │   ├── ChatMessage.vue
│   │   │   ├── ChatInput.vue
│   │   │   ├── Sidebar.vue
│   │   │   └── HistoryPanel.vue
│   │   ├── DeviceInfo.vue
│   │   ├── FaceCamera.vue
│   │   └── TypeWriter.vue
│   ├── composables/          # 组合式函数
│   │   └── useGeolocation.js # GPS 定位 + 高德解码
│   ├── plugins/
│   │   └── deviceDetect.js
│   ├── router/
│   │   └── index.js
│   ├── services/
│   │   └── socketService.js
│   ├── store/
│   │   └── auth.js
│   ├── views/
│   │   ├── chat.vue
│   │   ├── home.vue
│   │   ├── Login.vue
│   │   └── Register.vue
│   ├── App.vue
│   └── main.js
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml        # Nginx + config.js（含高德 Key）
├── .env                       # 本地环境变量（gitignore）
├── .env.production            # 生产环境变量
├── Dockerfile
├── nginx.conf
├── vite.config.js
└── package.json
```

## 部署

### Docker 构建

```bash
docker build -t face-frontend .
```

### Kubernetes 部署

项目通过 Nginx 容器提供静态文件 + 反向代理，`nginx.conf` 中配置了：

| 路径 | 后端服务 |
|------|---------|
| `/api/v1/chat/ws` | user-agent:5050 (WebSocket) |
| `/api/v1/chat/send` | user-agent:5050 |
| `/api/me` | user-agent:5050 |
| `/api/register` | cybertwin-OIDC-service:31111 |
| `/api/login` | cybertwin-OIDC-service:31111 |
| `/api/auth/login` | cybertwin-OIDC-service:31111 |
| `/api/keep-auth` | cybertwin-OIDC-service:31111 |
| `/login`, `/logout` | user-agent:5050 |
| `/medical_frontend/` | medical-frontend:80 |

### 部署到 Kubernetes

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | home | 自动跳转到 `/ctlogin` |
| `/ctlogin` | Login | 登录页 |
| `/register` | Register | 注册页 |
| `/chat` | Chat | AI 聊天主界面 |
