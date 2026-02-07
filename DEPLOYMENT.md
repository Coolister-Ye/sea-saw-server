# 生产环境部署说明

## 部署方式

Sea-Saw 后端使用 **Local 模式部署**：在生产服务器上从最新代码重新构建 Docker 镜像。

## 配置说明

### Docker Compose 配置

- **docker-compose.prod.yml** - 生产环境配置
  - 所有后端服务使用本地镜像：`sea-saw-backend:local`
  - 每次部署都会从 `./app` 目录重新构建镜像

### GitHub Actions 自动部署

推送到 `main` 分支会自动触发部署：

1. ✅ 运行测试
2. 📦 将代码 rsync 到服务器 `/home/sea-saw/sea-saw-server/`
3. 🔨 在服务器上从本地代码构建 Docker 镜像
4. 🚀 重启所有服务
5. 🗄️ 运行数据库迁移
6. 📦 收集静态文件
7. 🏥 健康检查

## 手动部署

### 初次部署或修复

在生产服务器上执行：

```bash
cd /home/sea-saw/sea-saw-server

# 1. 确保代码是最新的（如果遇到冲突，先清理）
git fetch origin
git reset --hard origin/main
git clean -fd

# 2. 停止所有服务
docker compose -f docker-compose.prod.yml down

# 3. 删除旧镜像
docker rmi sea-saw-backend:local -f 2>/dev/null || true

# 4. 从本地代码重新构建（不使用缓存）
docker compose -f docker-compose.prod.yml build --no-cache

# 5. 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 6. 等待服务启动
sleep 30

# 7. 运行数据库迁移
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 8. 收集静态文件
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 9. 验证部署
docker compose -f docker-compose.prod.yml ps
docker exec sea-saw-backend cat /home/app/web/sea_saw_crm/urls.py | grep "router.register"
```

### 快速重启服务

```bash
cd /home/sea-saw/sea-saw-server
docker compose -f docker-compose.prod.yml restart
```

### 查看日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker logs sea-saw-backend --tail 100 -f
docker logs sea-saw-celery-worker --tail 100 -f
```

## 验证部署

```bash
# 1. 检查所有容器状态
docker ps --filter "name=sea-saw"

# 2. 检查镜像
docker images | grep sea-saw-backend

# 3. 测试健康检查
curl http://localhost/health/

# 4. 测试 API 端点
curl http://localhost/api/sea-saw-crm/accounts/

# 5. 验证代码版本（应该看到 router.register(r"accounts", AccountViewSet)）
docker exec sea-saw-backend grep 'router.register(r"accounts"' /home/app/web/sea_saw_crm/urls.py
```

## 常见问题

### 1. Git pull 冲突

**问题**：`git pull` 提示本地文件会被覆盖。

**原因**：CI/CD 的 rsync 会复制代码到服务器，造成 Git 检测到本地修改。

**解决**：
```bash
cd /home/sea-saw/sea-saw-server

# 备份配置文件
cp -r .env .env.backup

# 强制重置到远程最新状态
git fetch origin
git reset --hard origin/main
git clean -fd

# 恢复配置文件
cp -r .env.backup/* .env/
rm -rf .env.backup
```

### 2. 容器内代码不是最新的

**问题**：部署后容器内代码还是旧的。

**原因**：Docker 镜像没有重新构建，或者使用了缓存。

**解决**：
```bash
# 删除旧镜像并重新构建
docker compose -f docker-compose.prod.yml down
docker rmi sea-saw-backend:local -f
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### 3. 端口被占用

**问题**：服务启动失败，提示端口被占用。

**解决**：
```bash
# 查找占用端口的进程
docker ps -a | grep sea-saw

# 停止所有相关容器
docker compose -f docker-compose.prod.yml down

# 清理孤立容器
docker ps -a --filter "status=exited" | grep sea-saw | awk '{print $1}' | xargs -r docker rm -f

# 重新启动
docker compose -f docker-compose.prod.yml up -d
```

## 服务架构

生产环境包含以下服务：

| 容器名 | 说明 | 端口 |
|--------|------|------|
| sea-saw-backend | Django API 服务器 | 内部 8000 |
| sea-saw-db | PostgreSQL 数据库 | 内部 5432 |
| sea-saw-redis | Redis 缓存/消息队列 | 内部 6379 |
| sea-saw-celery-worker | Celery 异步任务 | - |
| sea-saw-celery-beat | Celery 定时任务 | - |
| sea-saw-flower | Celery 监控面板 | 5555 |
| sea-saw-gateway | Nginx 反向代理 | 80 |
| sea-saw-frontend | React 前端 | 内部 80 |

所有服务通过 `sea-saw-network` Docker 网络通信。

## 配置文件

重要配置文件（不要提交到 Git）：
- `/home/sea-saw/sea-saw-server/.env/.prod` - Django 配置
- `/home/sea-saw/sea-saw-server/.env/.prod.db` - PostgreSQL 配置

## 数据备份

```bash
# 手动备份数据库
cd /home/sea-saw/sea-saw-server
./deploy.sh backup

# 备份文件位置
ls -lh backups/
```

## 回滚

如果部署失败，恢复到之前的版本：

```bash
cd /home/sea-saw/sea-saw-server

# 1. 停止服务
docker compose -f docker-compose.prod.yml down

# 2. 切换到之前的 commit
git log --oneline -10  # 查看最近的提交
git reset --hard <commit-hash>

# 3. 重新构建并启动
docker rmi sea-saw-backend:local -f
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```
