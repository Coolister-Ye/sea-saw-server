# Sea-Saw 服务器

<img src="https://img.shields.io/badge/Python-3.8+-brightgreen">
<img src="https://img.shields.io/badge/Django-3.2+-brightgreen">
<img src="https://img.shields.io/badge/PostgreSQL-15-brightgreen">
<img src="https://img.shields.io/badge/Redis-latest-brightgreen">

<br>
<img src="./assests/images/sea-saw-logo.png" style="width: 20%">

Sea-Saw CRM 应用的服务器端，基于 Django 构建。有关前端应用的更多信息，请访问 [此仓库](https://github.com/Coolister-Ye/sea-saw-app)。

👉 [English Version](./README.md) | [中文版](./README_zh.md)

## 目录

- [项目概述](#项目概述)
- [项目架构](#项目架构)
- [依赖项](#依赖项)
- [安装指南](#安装指南)
- [API 端点](#api-端点)
- [开发指南](#开发指南)
- [测试](#测试)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [参考资料](#参考资料)
- [许可证](#许可证)

## 项目概述

Sea-Saw CRM 系统是一款高效、可扩展的 CRM 解决方案。我们致力于打造一个可以快速扩展、方便定制的系统，用户只需遵循一定的后端开发规范，即可让前端应用迅速适配并投入使用。系统架构注重灵活性和可扩展性，后端基于 Django 构建，结合 Celery 高效调度任务，Redis 负责缓存和任务管理，PostgreSQL 提供安全可靠的数据存储，为企业提供稳定高效的管理平台。

## 项目架构

### Django 应用模块

- **sea_saw_crm**: CRM 核心模块，包含公司、联系人、订单、合同、产品、支付等模型
- **sea_saw_auth**: 用户认证与权限管理（JWT 认证）
- **preference**: 用户偏好设置和列可见性配置
- **download**: 异步下载任务管理（基于 Celery）

### 技术栈

- **Django REST Framework**: RESTful API 开发，支持 ViewSet 模式
- **JWT 认证**: 基于 Token 的身份验证，支持 Token 刷新
- **Celery + Celery Beat**: 异步任务队列和定时任务调度
- **Flower**: Celery 任务实时监控
- **Redis**: 消息代理、缓存和任务管理
- **PostgreSQL**: 生产环境数据库
- **SQLite**: 开发环境数据库
- **Docker + Docker Compose**: 容器化部署

### 容器服务

开发环境包含以下 Docker 服务：
- `web`: Django 应用服务器（端口 8001）
- `db`: PostgreSQL 数据库
- `redis`: Redis 服务器（端口 6380）
- `celery_worker`: Celery 任务执行器
- `celery_beat`: Celery 定时任务调度器
- `flower`: Celery 监控面板（端口 5558）

生产环境额外包含：
- `nginx`: 反向代理和静态文件服务

## 依赖项

- **Python**: 3.8+
- **Django**: 3.2+ - 后端 Web 框架
- **Django REST Framework**: API 开发框架
- **Celery**: 分布式任务队列系统
- **Celery Beat**: 周期性任务调度器
- **Flower**: Celery 任务的实时监控工具
- **Redis**: 消息代理和缓存
- **PostgreSQL**: 关系型数据库管理系统（生产环境）
- **Docker**: 用于开发和生产环境的容器化工具
- **Docker Compose**: 定义和运行多容器 Docker 应用的工具

## 安装指南

### 1. 克隆仓库

```bash
git clone <repository-url>
cd sea-saw-server
```

### 2. 配置环境变量

编辑 `.env/.dev` 或 `.env/.prod` 文件，配置服务器地址和 CORS 设置：

```shell
# Django 配置
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
FRONTEND_HOST=http://localhost:8001

# 数据库配置（参考 .env/.dev.db 或 .env/.prod.db）
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=sea_saw_db
```

### 3. 安装 Docker 和 Docker Compose

确保您的计算机上已安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。

### 4. 启动开发环境

构建并启动本地开发环境的 Docker 容器：

```bash
docker compose -p sea_saw_dev up --build
```

**注意**：首次启动可能需要几分钟来下载镜像和构建容器。

### 5. 运行数据库迁移

在新的终端窗口中，执行数据库迁移：

```bash
# 进入 web 容器
docker exec -it sea_saw_dev_web_1 bash

# 运行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 退出容器
exit
```

或者直接在容器外执行：

```bash
docker exec -it sea_saw_dev_web_1 python manage.py migrate
docker exec -it sea_saw_dev_web_1 python manage.py createsuperuser
```

### 6. 配置翻译（可选）

如果项目支持多语言，使用以下命令管理翻译：

```bash
cd app
django-admin makemessages -l zh_Hans  # 生成简体中文翻译
django-admin compilemessages           # 编译翻译文件
```

### 7. 访问应用

服务启动后，可以通过以下地址访问：

- **Django 应用**: [http://localhost:8001](http://localhost:8001)
- **管理后台**: [http://localhost:8001/admin](http://localhost:8001/admin)
- **API 根路径**: [http://localhost:8001/api](http://localhost:8001/api)
- **Flower 监控**: [http://localhost:5558](http://localhost:5558)

### 8. 测试服务连接

测试 Redis 是否正常运行：

```bash
docker exec -it sea_saw_dev_redis_1 redis-cli ping
# 应该返回: PONG
```

查看 Celery Worker 日志：

```bash
docker logs -f sea_saw_dev_celery_worker_1
```

### 9. 配置生产环境

部署应用到生产环境：

```bash
docker compose -f docker-compose.prod.yml -p sea_saw_prod up --build -d
```

生产环境使用 PostgreSQL 数据库，确保正确配置 `.env/.prod` 和 `.env/.prod.db` 文件。

### 10. 停止服务

停止开发环境：

```bash
docker compose -p sea_saw_dev down
```

停止生产环境：

```bash
docker compose -f docker-compose.prod.yml -p sea_saw_prod down
```

## API 端点

### 认证端点

- `POST /api/sea-saw-auth/login/` - 用户登录
- `POST /api/sea-saw-auth/logout/` - 用户登出
- `POST /api/sea-saw-auth/token/refresh/` - 刷新 JWT Token
- `POST /api/sea-saw-auth/token/verify/` - 验证 JWT Token

### CRM 端点

所有 CRM 端点遵循 Django REST Framework ViewSet 模式：

- `GET /api/sea-saw-crm/{resource}/` - 列表视图
- `POST /api/sea-saw-crm/{resource}/` - 创建资源
- `GET /api/sea-saw-crm/{resource}/{id}/` - 详情视图
- `PUT /api/sea-saw-crm/{resource}/{id}/` - 完整更新
- `PATCH /api/sea-saw-crm/{resource}/{id}/` - 部分更新
- `DELETE /api/sea-saw-crm/{resource}/{id}/` - 删除资源
- `OPTIONS /api/sea-saw-crm/{resource}/` - 获取字段元数据

支持的资源包括：`companies`, `contacts`, `orders`, `contracts`, `products`, `payments` 等。

### 下载任务端点

- `GET /api/download/tasks/` - 获取下载任务列表
- `POST /api/download/tasks/` - 创建下载任务
- `GET /api/download/tasks/{id}/` - 获取任务状态
- `GET /api/download/tasks/{id}/download/` - 下载文件

## 开发指南

### 创建新的 Django 应用

```bash
cd app
python manage.py startapp <app_name>
```

然后将新应用添加到 `sea_saw_server/settings.py` 的 `INSTALLED_APPS` 中。

### 数据库操作

```bash
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移历史
python manage.py showmigrations

# 创建超级用户
python manage.py createsuperuser
```

### 运行 Celery（本地开发，不使用 Docker）

如果需要在本地（非 Docker）环境中运行 Celery：

```bash
# 启动 Celery Worker
celery -A sea_saw_server worker --loglevel=info

# 启动 Celery Beat
celery -A sea_saw_server beat --loglevel=info

# 启动 Flower 监控
celery -A sea_saw_server flower --port=5555
```

### 收集静态文件

```bash
python manage.py collectstatic --noinput
```

## 测试

我们使用 Django 的内置测试框架。请确保为您的代码编写测试，新功能应具有完整的测试覆盖。

### 运行所有测试

```bash
# 在本地环境
python manage.py test

# 在 Docker 容器中
docker exec -it sea_saw_dev_web_1 python manage.py test
```

### 运行特定应用的测试

```bash
python manage.py test sea_saw_crm
python manage.py test sea_saw_auth
```

### 查看测试覆盖率

```bash
# 安装 coverage
pip install coverage

# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成 HTML 报告
```

## 代码风格

请遵循 [PEP8](https://www.python.org/dev/peps/pep-0008/) 代码风格指南。我们强烈建议使用以下工具：

```bash
# 安装 black 和 flake8
pip install black flake8

# 格式化代码
black .

# 检查代码风格
flake8 .
```

## 故障排除

### Docker 相关问题

**问题**: Docker 容器无法启动
```bash
# 检查 Docker 是否运行
docker ps

# 查看容器日志
docker logs sea_saw_dev_web_1

# 重新构建容器
docker compose -p sea_saw_dev up --build --force-recreate
```

**问题**: 端口冲突
```bash
# 检查端口占用
lsof -i :8001
lsof -i :6380
lsof -i :5558

# 在 docker-compose.yml 中修改端口映射
```

### Redis 相关问题

**问题**: Redis 连接失败

```bash
# 确认 Redis 容器正在运行
docker ps | grep redis

# 检查 Redis 日志
docker logs sea_saw_dev_redis_1

# 测试 Redis 连接
docker exec -it sea_saw_dev_redis_1 redis-cli ping
```

### Celery 相关问题

**问题**: Celery Worker 未启动或任务未执行

```bash
# 查看 Worker 日志
docker logs -f sea_saw_dev_celery_worker_1

# 查看 Beat 日志
docker logs -f sea_saw_dev_celery_beat_1

# 确保 Redis 已启动
docker ps | grep redis

# 重启 Celery 服务
docker compose -p sea_saw_dev restart celery_worker
docker compose -p sea_saw_dev restart celery_beat
```

### 数据库相关问题

**问题**: 数据库迁移失败

```bash
# 检查数据库连接
docker exec -it sea_saw_dev_db_1 psql -U <username> -d <database>

# 回滚迁移
python manage.py migrate <app_name> <migration_number>

# 清除数据库（开发环境）
docker compose -p sea_saw_dev down -v  # 删除数据卷
```

**问题**: 无法登录管理后台

- 确认超级用户的凭据正确
- 检查服务器是否正在运行
- 清除浏览器缓存和 Cookie
- 检查 Django 日志中的错误信息

### 内存和性能问题

**问题**: 容器内存不足

编辑 `docker-compose.prod.yml` 调整资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## 贡献指南

我们欢迎对 Sea-Saw CRM 系统的贡献。

### 贡献流程

1. Fork 本仓库
2. 创建新分支：`git checkout -b feature/your-feature`
3. 进行更改并提交：`git commit -m "Add: your feature description"`
4. 推送到远程分支：`git push origin feature/your-feature`
5. 创建 Pull Request，详细描述您的更改

### 提交信息规范

使用清晰的提交信息：

- `Add: 新增功能`
- `Fix: 修复 Bug`
- `Update: 更新功能`
- `Refactor: 代码重构`
- `Docs: 文档更新`
- `Test: 测试相关`

### 代码审查

所有 PR 需要经过代码审查才能合并。请确保：

- 代码遵循 PEP8 规范
- 包含必要的测试
- 更新相关文档
- 通过所有 CI 检查

## 参考资料

- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery 文档](https://docs.celeryproject.org/)
- [Docker 文档](https://docs.docker.com/)
- [django-celery-docker 教程](https://testdriven.io/courses/django-celery/docker/)
- [Django Docker 部署指南](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/)

## 许可证

本项目遵循 MIT 许可证 - 详情请参阅 [LICENSE](./LICENSE) 文件。

---

**开发团队**: Sea-Saw CRM Team
**联系方式**: [GitHub Issues](https://github.com/Coolister-Ye/sea-saw-server/issues)
