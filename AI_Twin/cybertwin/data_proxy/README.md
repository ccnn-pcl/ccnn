# Cybertwin-DataProxy

网络孪生数据代理服务，为 Cybertwin 平台提供医疗数据代理功能，支持 MCP (Model Context Protocol) 用于 AI 工具集成。

## 项目概述

Cybertwin-DataProxy 是一个基于 Go 语言开发的数据代理服务，主要用于管理和查询医疗数据存储信息。服务通过 MCP 协议提供标准化的 AI 工具接口，支持医疗数据的查询和访问。

### 核心功能

1. **医疗数据查询**：根据用户ID和科室查询医疗数据存储信息
2. **MCP 协议支持**：提供标准化的 AI 工具集成接口
3. **JWT 认证**：支持基于令牌的身份验证
4. **数据库管理**：MySQL 数据库连接和 ORM 操作
5. **配置管理**：支持 YAML 配置文件和环境变量

## 项目架构

### 目录结构

```
Cybertwin-DataProxy/
├── main.go                    # 程序入口，命令行参数解析和服务器启动
├── auth/                      # 认证模块
│   └── verifier.go           # JWT 令牌验证器
├── config/                    # 配置管理模块
│   ├── config.go             # 配置初始化
│   ├── version.go            # 版本信息管理
│   ├── server.go             # 服务器配置
│   ├── db.go                 # 数据库配置
│   └── log.go                # 日志配置
├── db/                        # 数据库模块
│   ├── db.go                 # 数据库连接和初始化
│   └── models.go             # 数据模型定义
├── handler/                   # 请求处理器
│   └── handler.go            # 数据处理器
├── query/                     # 数据查询模块
│   └── query.go              # 医疗数据查询
├── internal/tools/           # MCP 工具定义
│   ├── all_tools.go          # 工具注册器
│   └── query_hospital_medical_data.go  # 医院医疗数据查询工具
├── logger/                    # 日志模块
│   └── log.go                # 日志初始化
├── conf/                      # 配置文件目录
│   └── config.yaml           # 主配置文件
├── build/                     # 构建输出目录
├── logs/                      # 日志文件目录
├── deploy/                    # 部署相关文件
└── Dockerfile                # Docker 构建文件
```

### 核心模块说明

#### 1. 主程序 (`main.go`)
- 命令行参数解析（版本、帮助、配置、地址、日志级别）
- 配置初始化和管理
- 数据库初始化
- MCP 服务器创建和启动
- HTTP 服务器或 Stdio 传输支持

#### 2. 数据模型 (`db/models.go`)
```go
type MedicalDataStorage struct {
    ID                 int64     `gorm:"primaryKey;autoIncrement;column:id"`
    UserID             string    `gorm:"column:user_id;type:varchar(64);index:idx_user_id;not null"`
    Location           string    `json:"hospital_location"`
    HospitalName       string    `gorm:"column:hospital_name;type:varchar(255)"`
    Department         string    `gorm:"column:department;char(256)"`
    DataServiceAddress string    `gorm:"column:dataservice_address;type:varchar(500)"`
    DataTypes          string    `gorm:"column:data_types;type:varchar(1000)"`
    IsActive           bool      `gorm:"column:is_active;default:true"`
    LastSyncedAt       time.Time `gorm:"column:last_synced_at"`
    CreatedAt          time.Time `gorm:"column:created_at;autoCreateTime"`
    UpdatedAt          time.Time `gorm:"column:updated_at;autoUpdateTime"`
}
```

#### 3. 查询模块 (`query/query.go`)
- `GetUserMedicalData(userID string)` - 获取用户的所有医疗数据
- `GetMedicalDataByHospital(userID, department string)` - 根据医院和科室查询数据

#### 4. 处理器模块 (`handler/handler.go`)
- `GetHospitalMedicalData()` - 处理医院医疗数据查询请求
- 定义请求和响应数据结构

#### 5. MCP 工具 (`internal/tools/`)
- `query_hospital_medical_data` - MCP 工具：查询医院医疗数据
- 支持 JSON Schema 验证输入输出

#### 6. 认证模块 (`auth/verifier.go`)
- JWT 令牌验证
- 支持 Bearer Token 认证

## 快速开始

### 环境要求

- Go 1.23.0+
- MySQL 5.7+
- Docker (可选)

### 安装和运行

#### 方法一：使用 Makefile

```bash
# 安装依赖
make deps

# 构建项目
make build

# 运行项目
make run

# 或直接运行二进制文件
./build/server
```

#### 方法二：手动构建

```bash
# 下载依赖
go mod download

# 构建
go build -o server .

# 运行
./server
```

#### 方法三：Docker 运行

```bash
# 构建 Docker 镜像
make docker-build

# 运行 Docker 容器
make docker-run
```

### 配置说明

#### 配置文件位置
默认配置文件：`./conf/config.yaml`

#### 配置文件示例
```yaml
server:
  address: ":8080"

db:
  host: "localhost"
  port: 3306
  username: "root"
  password: "password"
  database: "cybertwin"
  max_idle_conns: 10
  max_open_conns: 100
  conn_max_lifetime: "1h"

log:
  file_path: "./logs/app.log"
  verbose: true
  debug: false
```

#### 环境变量
- `CYBERTWIN_CONFIG_PATH` - 配置文件路径
- `CYBERTWIN_SERVER_ADDRESS` - 服务器地址
- `CYBERTWIN_LOG_LEVEL` - 日志级别 (debug, info, warn, error)

### 命令行参数

```bash
# 显示版本信息
./server -v

# 显示帮助信息
./server -h

# 指定配置文件
./server -c /path/to/config.yaml

# 指定服务器地址
./server -a :9090

# 指定日志级别
./server -l debug

# 组合使用
./server -c config.yaml -a :8080 -l info
```

## 接口定义

### MCP 工具接口

#### 查询医院医疗数据
- **工具名称**: `query_hospital_medical_data`
- **描述**: 获取查询医疗数据服务信息

**请求参数**:
```json
{
  "user_id": "string",
  "department": "string"
}
```

**响应结构**:
```json
{
  "datas": [
    {
      "hospital_location": "string",
      "hospital_name": "string",
      "department": "string",
      "data_service_address": "string",
      "data_types": "string"
    }
  ]
}
```

### HTTP 接口

服务支持两种运行模式：
1. **HTTP 模式**: 通过 `-a` 参数指定地址，提供 HTTP 接口
2. **Stdio 模式**: 不指定地址时，使用标准输入输出作为 MCP 传输

#### 认证
HTTP 模式需要 Bearer Token 认证：
```
Authorization: Bearer <token>
```

## 数据库设置

### 创建数据库表

服务启动时会自动创建以下表：

```sql
CREATE TABLE medical_data_storage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    hospital_name VARCHAR(255),
    department CHAR(256),
    dataservice_address VARCHAR(500),
    data_types VARCHAR(1000),
    is_active BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);
```

### 数据示例

### 初始化脚本

项目提供了数据库初始化脚本 `deploy/data.sql`：

```sql
INSERT INTO medical_data_storage (id, user_id, hospital_name, department, dataservice_address, data_labels, is_active, last_synced_at, created_at, updated_at, location, data_types)
VALUES (20250001, '70133600', '北京协和', '内分泌科', 'mcp://192.168.208.66:30211', '病史数据 用药记录 化验报告 影像数据 手术记录', 1, '2025-11-22 18:00:00', '2025-11-22 18:00:00','2025-11-22 18:00:00','北京','病史数据 用药记录 化验报告 影像数据 手术记录');
```

使用方式：
```bash
# 导入示例数据
mysql -u username -p cybertwin < deploy/data.sql
```

```sql
INSERT INTO medical_data_storage 
(user_id, hospital_name, department, dataservice_address, data_types, is_active)
VALUES 
('user123', '北京协和医院', '心血管内科', 'http://api.hospital.com/data', '心电图,血压,血脂', 1);
```

## 开发指南

### 代码结构规范

1. **包组织**：按功能模块划分目录
2. **错误处理**：统一使用 logger 记录错误
3. **配置管理**：通过 config 包统一管理
4. **数据库操作**：使用 GORM ORM

### 添加新的 MCP 工具

1. 在 `internal/tools/` 目录下创建新文件
2. 定义工具的结构和处理器
3. 在 `init()` 函数中注册工具
4. 工具会自动注册到 MCP 服务器

### 测试

```bash
# 运行测试
make test

# 运行测试并生成覆盖率报告
make test-coverage
```

## 部署指南

### 生产环境部署

#### 使用 Systemd

```bash
# 创建服务文件 /etc/systemd/system/cybertwin-dataproxy.service
[Unit]
Description=Cybertwin DataProxy Service
After=network.target

[Service]
Type=simple
User=cybertwin
Group=cybertwin
Environment=CYBERTWIN_CONFIG_PATH=/etc/cybertwin/config.yaml
Environment=CYBERTWIN_LOG_LEVEL=info
ExecStart=/usr/local/bin/cybertwin-dataproxy
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 使用 Docker

```bash
# 构建生产镜像
BUILD_VERSION=1.0.0 make docker-build

# 运行容器
docker run -d \
  -p 8080:8080 \
  -v /etc/cybertwin:/app/conf \
  -v /var/log/cybertwin:/app/logs \
  cybertwin-dataproxy-service:1.0.0
```

### 监控和日志

- 日志文件：`./logs/app.log`（可配置）
- 日志级别：支持 debug, info, warn, error
- 访问日志：HTTP 请求日志
- 错误日志：详细错误信息

## 版本管理

### 版本信息

版本信息通过编译时注入：
- 版本号：`BUILD_VERSION`
- Git 提交哈希：`GIT_COMMIT`
- Git 分支：`GIT_BRANCH`
- 构建时间：`BUILD_TIME`

### 查看版本

```bash
# 命令行查看
./server -v

# 输出示例
Cybertwin DataProxy Service
Version: 0.1.5
Commit: a1b2c3d
Branch: main
Build Time: 2024-02-28T20:13:00Z
```

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 检查配置文件路径和格式
   - 检查数据库连接配置

2. **数据库连接失败**
   - 确认 MySQL 服务正在运行
   - 检查用户名和密码
   - 验证网络连接

3. **认证失败**
   - 检查 JWT 令牌格式
   - 验证令牌有效期

4. **MCP 工具调用失败**
   - 检查输入参数格式
   - 查看服务日志获取详细信息

### 日志查看

```bash
# 查看服务日志
tail -f logs/app.log

# 调试模式运行
./server -l debug

# Docker 容器日志
docker logs <container_id>
```

## 许可证

版权所有 © 2024 Cybertwin DataProxy Service

## 相关文档

- [USAGE.md](./USAGE.md) - 详细使用指南
- [README-MAKEFILE.md](./README-MAKEFILE.md) - Makefile 说明
- [VERSIONING_SUMMARY.md](./VERSIONING_SUMMARY.md) - 版本管理总结
