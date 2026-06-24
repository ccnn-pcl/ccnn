# SQLite到PostgreSQL迁移指南

## 概述

本指南将帮助您将项目从SQLite数据库迁移到PostgreSQL数据库，为后续的微服务化改造做准备。

## 前置条件

1. **Docker和Docker Compose**: 用于运行PostgreSQL服务
2. **Python 3.8+**: 运行迁移脚本
3. **现有SQLite数据**: 确保data目录下有SQLite数据库文件

## 迁移步骤

### 第一步：安装依赖

```bash
# 安装Python依赖
python scripts/install_dependencies.py

# 或者手动安装
pip install asyncpg psycopg2-binary python-dotenv
```

### 第二步：启动PostgreSQL服务

```bash
# 启动PostgreSQL容器
docker-compose up -d postgresql

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs postgresql
```

### 第三步：初始化PostgreSQL数据库

```bash
# 等待PostgreSQL启动完成（约30秒）
sleep 30

# 连接到PostgreSQL并创建数据库结构
docker exec -i private_doctor_postgres psql -U doctor_user -d private_doctor_db < scripts/init_postgresql.sql
```

### 第四步：执行数据迁移

```bash
# 运行数据迁移脚本
python scripts/migrate_sqlite_to_postgresql.py
```

### 第五步：验证迁移结果

```bash
# 运行验证脚本
python scripts/validate_migration.py
```

### 第六步：测试PostgreSQL数据库管理器

```bash
# 测试新的数据库管理器
python scripts/test_postgresql_manager.py
```

## 验证迁移成功

迁移成功后，您应该看到：

1. **迁移日志**: 显示各表迁移的记录数量
2. **验证通过**: 所有数据验证都显示"✅ 成功"
3. **测试通过**: 数据库管理器测试全部通过

## 故障排除

### 常见问题

1. **PostgreSQL连接失败**
   ```bash
   # 检查容器状态
   docker-compose ps
   
   # 重启PostgreSQL
   docker-compose restart postgresql
   ```

2. **权限问题**
   ```bash
   # 检查数据库权限
   docker exec -it private_doctor_postgres psql -U doctor_user -d private_doctor_db -c "\du"
   ```

3. **数据迁移失败**
   ```bash
   # 查看详细日志
   cat migration.log
   
   # 重新运行迁移
   python scripts/migrate_sqlite_to_postgresql.py
   ```

### 回滚方案

如果需要回滚到SQLite：

1. 停止PostgreSQL服务：`docker-compose down`
2. 修改环境变量：`DATABASE_TYPE=sqlite`
3. 重启应用服务

## 下一步

迁移完成后，您可以：

1. **更新应用配置**: 将`DATABASE_TYPE`设置为`postgresql`
2. **测试应用功能**: 确保所有功能正常工作
3. **性能测试**: 对比SQLite和PostgreSQL的性能
4. **准备微服务化**: 为后续的微服务拆分做准备

## 文件说明

- `scripts/init_postgresql.sql`: PostgreSQL数据库初始化脚本
- `scripts/migrate_sqlite_to_postgresql.py`: 数据迁移脚本
- `scripts/validate_migration.py`: 迁移验证脚本
- `scripts/test_postgresql_manager.py`: 数据库管理器测试脚本
- `shared/postgresql_database_manager.py`: PostgreSQL数据库管理器
- `config/database_config.py`: 数据库配置文件
- `docker-compose.yml`: Docker服务配置

## 注意事项

1. **数据备份**: 迁移前请备份所有SQLite数据
2. **磁盘空间**: 确保有足够空间存储PostgreSQL数据
3. **网络连接**: 确保Docker可以正常访问网络
4. **权限设置**: 确保脚本有读写data目录的权限
