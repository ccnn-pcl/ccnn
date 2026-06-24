# AI Twin Frontend (CyberTwin)

人脸识别认证 + AI 聊天前端应用，基于 Vue 3，部署于 Kubernetes。

## 功能特性

- 🔐 **人脸识别认证** - 摄像头采集人脸 + 密码双因素认证
- 💬 **AI 实时聊天** - 基于 WebSocket 的 AI 对话，支持图片/文件上传
- 📱 **设备指纹** - 自动检测设备信息用于风控
- ⭐ **信任评分** - 实时轮询用户信任评分，低分自动登出
- 🩺 **医疗模块跳转** - AI 回复可携带 redirect 元数据跳转到医疗前端

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 路由 | Vue Router 4 |
| 状态管理 | Vue reactive (轻量) |
| 构建 | Vue CLI 5 + Babel |
| HTTP | Axios (统一拦截器) |
| WebSocket | 原生 WebSocket |
| 部署 | Docker + Nginx (K8s) |
| 认证 | Keycloak OIDC |
| 工具 | ua-parser-js, FontAwesome, markdown-it |

## 快速开始

### 环境要求

- Node.js >= 16
- npm

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
├── public/                    # 静态资源
├── src/
│   ├── api/                  # API 层
│   │   ├── request.js       # Axios 实例 + 拦截器
│   │   ├── auth.js          # 认证 API（登录/注册）
│   │   └── chat.js          # 聊天 API
│   ├── assets/               # 资源文件
│   ├── components/           # 组件
│   │   ├── chat/            # 聊天子组件
│   │   │   ├── ChatMessage.vue   # 消息气泡
│   │   │   ├── ChatInput.vue     # 输入框
│   │   │   ├── Sidebar.vue       # 侧边栏
│   │   │   └── HistoryPanel.vue  # 历史记录
│   │   ├── DeviceInfo.vue   # 设备信息
│   │   ├── FaceCamera.vue   # 人脸摄像头
│   │   └── TypeWriter.vue   # 打字机效果
│   ├── plugins/              # 插件
│   │   └── deviceDetect.js  # 设备检测
│   ├── router/
│   │   └── index.js         # 路由 + 导航守卫
│   ├── services/
│   │   └── socketService.js # WebSocket 单例
│   ├── store/
│   │   └── auth.js          # 认证状态管理
│   ├── views/
│   │   ├── chat.vue         # 聊天主页面
│   │   ├── home.vue         # 首页（自动跳转）
│   │   ├── Login.vue        # 登录页
│   │   └── Register.vue     # 注册页
│   ├── App.vue              # 根组件
│   └── main.js              # 入口
├── k8s/                     # Kubernetes 部署文件
│   ├── deployment.yaml     # Deployment（通用配置）
│   ├── service.yaml        # Service（ClusterIP）
│   └── configmap.yaml      # Nginx 配置
├── Dockerfile                # Docker 构建
├── nginx.conf                # Nginx 反向代理配置
├── vue.config.js             # Vue CLI 配置
└── package.json
```

## 部署

### Docker 构建

```bash
docker build -t CCNN/CCNN-frontend:latest .
```

### Kubernetes 部署

项目通过 Nginx 容器提供静态文件 + 反向代理，`nginx.conf` 中配置了：

| 路径 | 后端服务 |
|------|---------|
| `/api/v1/chat/ws` | user-agent:5050 (WebSocket) |
| `/api/v1/chat/send` | user-agent:5050 |
| `/api/me` | user-agent:5050 |
| `/api/register` | CCNN-backend:5000 |
| `/api/login` | CCNN-backend:5000 |
| `/api/auth/login` | CCNN-backend:5000 |
| `/api/keep-auth` | CCNN-backend:5000 |
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
