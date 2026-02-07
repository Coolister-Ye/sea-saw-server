# 部署配置修复说明

## 修改内容

### 1. docker-compose.prod.yml
所有后端服务镜像现在使用环境变量 `BACKEND_IMAGE`：
- web
- celery_worker
- celery_beat
- flower

默认值：`hkccr.ccs.tencentyun.com/sea-saw/backend:latest`

### 2. .github/workflows/deploy-production.yml
部署脚本现在根据 `BUILD_MODE` 设置正确的环境变量：
- **Registry 模式**: `BACKEND_IMAGE=hkccr.ccs.tencentyun.com/sea-saw/backend:latest`
- **Local 模式**: `BACKEND_IMAGE=sea-saw-backend:local`

## 立即修复生产环境

在生产服务器上执行以下命令：

```bash
cd /home/sea-saw/sea-saw-server

# 1. 停止所有服务
docker compose -f docker-compose.prod.yml down

# 2. 删除旧镜像
docker rmi hkccr.ccs.tencentyun.com/sea-saw/backend:latest -f 2>/dev/null || true
docker rmi sea-saw-backend:local -f 2>/dev/null || true

# 3. 设置环境变量为 local 模式
export BACKEND_IMAGE=sea-saw-backend:local

# 4. 从本地代码重新构建（无缓存）
docker compose -f docker-compose.prod.yml build --no-cache

# 5. 启动服务
docker compose -f docker-compose.prod.yml up -d

# 6. 等待服务启动
sleep 30

# 7. 验证容器内代码已更新
echo "验证容器内代码版本..."
docker exec sea-saw-backend grep 'router.register(r"accounts"' /home/app/web/sea_saw_crm/urls.py

# 8. 测试 API 端点
echo "测试 API 端点..."
curl http://localhost/api/sea-saw-crm/accounts/

# 9. 查看服务状态
docker compose -f docker-compose.prod.yml ps
```

## 部署新配置

在本地开发机器上：

```bash
cd /Users/coolister/Desktop/sea-saw/sea-saw-server

# 1. 查看修改
git diff docker-compose.prod.yml
git diff .github/workflows/deploy-production.yml

# 2. 提交修改
git add docker-compose.prod.yml .github/workflows/deploy-production.yml
git commit -m "feat: add BACKEND_IMAGE env var to support local/registry build modes"

# 3. 推送到远程（触发自动部署）
git push origin main
```

## 使用说明

### 自动部署（通过 GitHub Actions）

**默认行为（push 到 main）**: Local 模式
- 在服务器上从本地代码构建
- 镜像名：`sea-saw-backend:local`

**手动触发 Registry 模式**:
1. 访问 GitHub Actions 页面
2. 选择 "Deploy to Tencent Cloud Production" workflow
3. 点击 "Run workflow"
4. 选择 `build_mode: registry`
5. 运行

### 手动部署

**Local 模式**:
```bash
cd /home/sea-saw/sea-saw-server
export BACKEND_IMAGE=sea-saw-backend:local
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

**Registry 模式**:
```bash
cd /home/sea-saw/sea-saw-server
export BACKEND_IMAGE=hkccr.ccs.tencentyun.com/sea-saw/backend:latest
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## 验证部署

```bash
# 检查镜像
docker images | grep backend

# 检查容器
docker ps --filter "name=sea-saw"

# 验证代码版本
docker exec sea-saw-backend cat /home/app/web/sea_saw_crm/urls.py | grep "router.register"

# 测试 API
curl http://localhost/api/sea-saw-crm/accounts/
curl http://localhost/health/
```

## 优势

✅ **灵活性**: 可以根据需要选择 local 或 registry 模式
✅ **明确性**: 通过环境变量清晰地控制镜像来源
✅ **可靠性**: Local 模式不会意外拉取远程旧镜像
✅ **向后兼容**: 默认值保持不变，不影响现有流程
