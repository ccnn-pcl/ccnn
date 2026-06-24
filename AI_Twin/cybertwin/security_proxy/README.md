# 项目结构
```
CYBERTWIN-SECURITY-ALL/
├── auth-service/                 # 授权服务模块，负责权限管理
│   ├── K8s/                      # Kubernetes 部署配置文件
│   │   ├── configmap.yaml        # 配置映射，存储服务运行所需配置信息
│   │   ├── deployment.yaml       # 部署配置，定义服务的Pod模板、副本数及更新策略
│   │   ├── rbac.yaml             # 角色权限控制配置，定义服务的访问权限与角色绑定
│   │   └── service.yaml          # 服务暴露配置，定义服务的网络访问方式与端口映射
│   └── main-folder/              # 认证服务核心业务代码目录
│       ├── Dockerfile            # 构建认证服务容器镜像的脚本
│       ├── main.py               # 认证服务主程序入口，处理认证请求与权限校验
│       └── requirements.txt      # 认证服务Python依赖包列表
├── datamodel/                    # 数据敏感度分级模型推理服务模块
│   ├── K8s/                      # Kubernetes 部署配置文件
│   │   └── deployment.yaml       # 部署配置，定义数据模型服务的Pod模板与副本数
│   ├── models/                   # 模型参数
│   ├── Dockerfile                # 构建模型服务容器镜像的脚本
│   ├── main.py                   # 模型推理服务主程序入口，处理数据敏感度评级请求
│   └── requirements.txt          # 数据敏感度分级模型服务Python依赖包列表
├── matchmodel/                   # 匹配模型推理服务模块
│   ├── K8s/                      # Kubernetes 部署配置文件
│   │   └── deployment.yaml       # 部署配置，定义匹配模型服务的Pod模板与副本数
│   ├── models/                   # 匹配模型定义与实现文件目录
│   ├── Dockerfile                # 构建匹配模型服务容器镜像的脚本
│   ├── main.py                   # 匹配模型服务主程序入口，处理匹配请求，进行动态授权决策
│   └── requirements.txt          # 匹配模型服务Python依赖包列表
├── usermodel/                    # 用户信任评估模块，负责用户属性管理与信任值计算
│   ├── __pycache__/              # Python 缓存文件目录
│   │   ├── app.cpython-38.pyc    # 编译后的应用缓存文件
│   │   └── trust_eval.cpython-38.pyc # 编译后的信任评估缓存文件
│   ├── K8s/                      # Kubernetes 部署配置文件
│   │   └── deployment.yaml       # 部署配置，定义用户信任评估服务的Pod模板与副本数
│   ├── static/                   # 静态资源目录
│   │   └── index.html            # 前端静态页面入口
│   ├── Tables/                   # 数据表定义或存储目录
│   │   ├── location_time_active.json # 位置与时间活跃度数据表
│   │   └── time_active.json      # 时间活跃度数据表
│   ├── build/                    # 构建相关配置目录
│   │   └── docker-compose.x86.yml # x86架构下的Docker Compose部署配置
│   ├── app.py                    # 用户信任评估服务的Web应用入口
│   ├── Dockerfile                # 构建用户信任评估服务容器镜像的脚本
│   ├── README.md                 # 用户信任评估模块说明文档
│   ├── requirements.txt          # 用户信任评估服务Python依赖包列表
│   ├── test_api.py               # API接口测试脚本
│   ├── trust_eval.py             # 信任评估核心逻辑实现
│   ├── TrustEval.log             # 信任评估运行日志文件
│   ├── user_attributes.json      # 用户属性配置文件，存储用户属性数据
│   ├── UserTrustEval.py          # 用户信任评估主类实现
│   └── UserTrustEval.pth         # 用户信任评估模型权重文件
└── README.md                     # 项目总览说明文档
```
---
# 模块职责说明（更新）

- **auth-service**: 作为系统的授权中枢，提供ABAC、RBAC、动态评估等能力，支持容器化部署与独立运行。

- **datamodel**: 数据敏感度分级模型负责数据敏感度智能分级，根据本访问资源元数据管理与数据预处理，支持容器化部署与独立运行。

- **matchmodel**: 实现数据敏感度与用户信任分智能匹配，基于数据敏感度分级模型输出与用户信任评估模型输出进行动态授权决策，支持容器化部署与独立运行。

- **usermodel**: 用户信任评估模型专注于用户信任评估，通过用户行为数据计算信任值，支持容器化部署与独立运行。

# 部署与运行


一、各模块Docker镜像构建（实操代码）

所有模块均在自身根目录执行构建命令，镜像命名遵循「模块名:v1.0」规范（可自行修改版本号），构建完成后可推送至私有镜像仓库，方便K8s集群拉取。

0. 基础py312镜像构建
```
# 构建基础镜像
docker build -t py312-base:3.12-slim -f Dockerfile.py312-base .
```
1. auth-service 镜像构建
```
# 进入auth-service核心代码目录
cd auth-service/main-folder
# 构建镜像（指定Dockerfile路径，当前目录即为Dockerfile所在目录）
docker build -t auth-service:v1.0 .
# 可选：推送镜像至仓库（示例，需替换仓库地址）
# docker tag auth-service:v1.0 仓库地址/auth-service:v1.0
# docker push 仓库地址/auth-service:v1.0
```

2. datamodel 镜像构建
```
# 进入datamodel模块根目录
cd datamodel
# 构建镜像
docker build -t datamodel:v1.0 .
# 可选：推送镜像至仓库
# docker tag datamodel:v1.0 仓库地址/datamodel:v1.0
# docker push 仓库地址/datamodel:v1.0
```

3. matchmodel 镜像构建
```
# 进入matchmodel模块根目录
cd matchmodel
# 构建镜像
docker build -t matchmodel:v1.0 .
# 可选：推送镜像至仓库
# docker tag matchmodel:v1.0 仓库地址/matchmodel:v1.0
# docker push 仓库地址/matchmodel:v1.0
```
4. usermodel 镜像构建（主服务+子模块）

```
# 1. 进入usermodel模块根目录（核心步骤，确保路径正确）
cd usermodel

# 2. 构建usermodel镜像（Dockerfile位于该目录下）
docker build -t usermodel:v1.0 .

# 3. 可选：推送镜像至私有仓库（需替换为你的仓库地址）
# docker tag usermodel:v1.0 你的仓库地址/usermodel:v1.0
# docker push 你的仓库地址/usermodel:v1.0

# 补充：若需使用build目录下的docker-compose.x86.yml部署（非K8s方式）
# cd build
# docker-compose -f docker-compose.x86.yml up -d
```

二、各模块K8s部署步骤详解（实操版）

前提条件：K8s集群已正常运行（单节点/多节点均可），本地已配置kubectl命令行工具（可连接集群），所有模块Docker镜像已推送至集群可访问的镜像仓库（或本地镜像已同步至集群所有节点）。

部署顺序：优先部署datamodel、matchmodel、usermodel（子业务模块），再部署auth-service（授权中枢），确保依赖正常。



**datamodel 部署步骤**

1. 进入K8s配置文件目录：cd datamodel/K8s

2. 应用部署配置：kubectl apply -f deployment.yaml，查看部署状态：kubectl get deployment datamodel。




**matchmodel 部署步骤**

1. 进入K8s配置文件目录：cd matchmodel/K8s

2. 应用部署配置：kubectl apply -f deployment.yaml，查看部署状态：kubectl get deployment matchmodel。


**usermodel 部署步骤**

1. 进入K8s配置文件目录：cd usermodel/K8s

2. 部署主服务：kubectl apply -f deployment.yaml，查看部署状态：kubectl get deployment usermodel。


**auth-service 部署步骤（含4个配置文件）**

1. 进入K8s配置文件目录：cd auth-service/K8s

2. 应用配置映射（configmap）：kubectl apply -f configmap.yaml，执行完成后可通过kubectl get configmap查看是否创建成功。

3. 应用角色权限控制（rbac）：kubectl apply -f rbac.yaml，确保服务拥有足够的集群访问权限，查看命令：kubectl get roles、kubectl get rolebindings。

4. 应用部署配置（deployment）：kubectl apply -f deployment.yaml，部署服务Pod，查看部署状态：kubectl get deployment auth-service（需替换为deployment.yaml中定义的服务名）。

5. 应用服务暴露配置（service）：kubectl apply -f service.yaml，暴露服务供其他模块访问，查看服务状态：kubectl get svc auth-service，记录服务IP/端口，供后续模块关联。

---
