# Sea-Saw 服务器

Sea-Saw CRM 应用的服务器端，基于 Django 构建。有关前端应用的更多信息，请访问 [此仓库](https://github.com/Coolister-Ye/sea-saw-app)。

👉 [English Version](./README.md) | [中文版](./README_zh.md)

## 项目概述

Sea-Saw CRM 系统是一款高效、可扩展的 CRM 解决方案。我们致力于打造一个可以快速扩展、方便定制的系统，用户只需遵循一定的后端开发规范，即可让前端应用迅速适配并投入使用。系统架构注重灵活性和可扩展性，后端基于 Django 构建，结合 Celery 高效调度任务，Redis 负责缓存和任务管理，PostgreSQL 提供安全可靠的数据存储，为企业提供稳定高效的管理平台。

## 依赖项

- **Django**：后端 Web 框架。
- **Celery**：分布式任务队列系统。
- **Celery Beat**：周期性任务调度器。
- **Flower**：Celery 任务的实时监控工具。
- **Redis**：消息代理和缓存。
- **PostgreSQL**：关系型数据库管理系统。
- **Docker**：用于开发和生产环境的容器化工具。
- **Docker Compose**：定义和运行多容器 Docker 应用的工具。

## 安装指南

### 1. 配置服务器地址

编辑 `.env/.dev` 或 `.env/.prod` 文件，允许前端连接指定的主机地址：

```shell
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
FRONTEND_HOST=http://localhost:8001
```

### 2. 设置环境

确保您的计算机上已安装 Docker 和 Docker Compose。您将使用 Docker 来设置服务器及其依赖项。

### 3. 配置翻译

如果项目支持多语言，请使用以下命令管理翻译：

```shell
django-admin makemessages -l zh_Hans  # 生成简体中文翻译
django-admin compilemessages  # 编译翻译文件
```

### 4. 启动开发环境

构建并启动本地开发环境的 Docker 容器：

```shell
docker-compose -p sea_saw_dev up --build
```

### 7. 测试 Redis 连接

运行以下命令测试 Redis 是否正常运行：

```shell
docker exec -it sea_saw_dev_redis_1 redis-cli ping
```

### 8. 运行 Celery Worker 和 Flower

启动 Celery Worker 和 Flower 任务监控工具：

```shell
celery -A django_celery_example worker --loglevel=info
celery -A django_celery_example flower --port=5555
```

### 9. 配置生产环境

部署应用到生产环境：

```shell
docker-compose -f docker-compose.prod.yml -p sea_saw_prod up --build
```

### 10. 创建超级用户

创建管理员账户以访问 Django 管理后台：

```shell
python manage.py createsuperuser
```

### 11. 访问应用

端口号已在 `docker-compose.yml` 和 `docker-compose.prod.yml` 中配置。

- **管理后台**：[http://localhost:8000/admin](http://localhost:8000/admin)

## 贡献指南

我们欢迎对 Sea-Saw CRM 系统的贡献。

- Fork 本仓库。
- 创建新分支：`git checkout -b feature/your-feature`。
- 进行更改并提交：`git commit -m "Add new feature"`。
- 推送到远程分支：`git push origin feature/your-feature`。
- 创建 Pull Request，详细描述您的更改。

## 代码风格

请遵循 PEP8 代码风格指南。我们建议使用 `black` 自动格式化 Python 代码。

## 测试

请确保为您的代码编写测试。我们使用 Django 的测试框架，并希望新功能具有完整的测试覆盖。

运行测试：

```shell
python manage.py test
```

## 故障排除

- **Docker 问题**：如果 Docker 无法正常工作，请确保其正在运行，并检查系统资源（内存和 CPU）是否充足。
- **Redis 连接问题**：如果 Redis 无响应，请检查 Redis 容器是否正在运行：
  ```shell
  docker ps
  docker logs <container_name>
  ```
- **Celery Worker 运行失败**：检查 Celery 配置，并确保 Redis 已启动。
- **无法登录管理后台**：请确认超级用户的凭据正确，并检查服务器是否正在运行。

## 参考资料

- [django-celery-docker](https://testdriven.io/courses/django-celery/docker/)
- [django-docker](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/)

## 许可证

本项目遵循 MIT 许可证 - 详情请参阅 LICENSE 文件。

