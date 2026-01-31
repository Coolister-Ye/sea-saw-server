# Attachment Security Guide

## 概述 Overview

本文档说明Sea-Saw CRM系统的附件权限管理方案。

This document explains the attachment permission management system for Sea-Saw CRM.

## 安全问题 Security Issue

**之前的实现** (Old Implementation):
- 使用 `static(settings.MEDIA_URL)` 直接暴露 `/media/` 目录
- 任何知道文件路径的人都可以访问附件
- 没有权限检查

**安全风险**:
- 未授权访问敏感文件（合同、订单附件等）
- 信息泄露风险

## 新的安全方案 New Security Solution

### 架构 Architecture

```
User Request
    ↓
Frontend: GET /api/sea-saw-crm/attachments/{id}/download/
    ↓
Django: SecureAttachmentDownloadView
    ↓
Permission Check:
  - User authenticated?
  - User has access to related entity?
    ↓
  ✅ Authorized → X-Accel-Redirect → Nginx → File
  ❌ Unauthorized → 403 Forbidden
```

### 核心组件 Core Components

#### 1. 受保护的下载视图 (Protected Download View)

**文件**: `sea_saw_crm/views/attachment_view.py`

```python
class SecureAttachmentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id):
        # 1. 验证用户已登录
        # 2. 检查附件是否存在
        # 3. 检查用户是否有权限访问关联实体
        # 4. 使用 X-Accel-Redirect (Nginx) 高效传输文件
```

**权限检查逻辑**:
- ✅ 用户必须已登录
- ✅ 附件必须存在
- ✅ 用户必须有权限访问附件关联的实体（Order、ProductionOrder等）
- ✅ 防止目录遍历攻击（directory traversal）

#### 2. 安全的URL生成 (Secure URL Generation)

**文件**: `sea_saw_crm/serializers/shared/base_attachment.py`

```python
def get_file_url(self, obj):
    # 生成受保护的下载URL而非直接的media URL
    download_path = reverse(
        "sea-saw-crm:attachment-download",
        kwargs={"attachment_id": obj.pk}
    )
    # 返回: /api/sea-saw-crm/attachments/123/download/
```

**Before** (不安全):
```
/media/attachments/order/2024/01/15/abc123_document.pdf
```

**After** (安全):
```
/api/sea-saw-crm/attachments/123/download/
```

#### 3. Nginx配置 (Nginx Configuration)

**文件**: `sea-saw-gateway/nginx.conf`

```nginx
# 内部保护路由 - 仅供X-Accel-Redirect使用
location /protected-media/ {
    internal;  # 外部无法直接访问
    alias /home/app/web/mediafiles/;
    autoindex off;
    expires 7d;
    add_header Cache-Control "private";
}

# 移除了直接的 /media/ 访问
# location /media/ { ... }  ← REMOVED
```

**X-Accel-Redirect** 工作流程:
1. Django视图检查权限
2. 如果授权，返回 `X-Accel-Redirect: /protected-media/...` 头
3. Nginx接收到头后，内部重定向到文件
4. 文件直接由Nginx传输（高效，不占用Django进程）

#### 4. URL配置更新 (URL Configuration)

**主URL配置** (`sea_saw_server/urls.py`):
```python
# Only serve media files directly in development
# In production, use secure download view with permission checks
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**CRM URL配置** (`sea_saw_crm/urls.py`):
```python
path(
    "attachments/<int:attachment_id>/download/",
    SecureAttachmentDownloadView.as_view(),
    name="attachment-download",
)
```

## 部署步骤 Deployment Steps

### 1. 修复生产环境权限问题

在部署新代码之前，先修复现有的mediafiles权限:

```bash
ssh appuser@<server-ip>
docker exec -u root sea-saw-backend chown -R app:app /home/app/web/mediafiles
```

### 2. 部署后端更新

```bash
cd /Users/coolister/Desktop/sea-saw/sea-saw-server
git add -A
git commit -m "Add attachment permission management

- Add SecureAttachmentDownloadView with permission checks
- Update attachment serializer to use protected URLs
- Remove direct /media/ exposure in production
- Add X-Accel-Redirect support for efficient file serving"
git push origin main
```

GitHub Actions会自动部署。

### 3. 部署Gateway更新

```bash
cd /Users/coolister/Desktop/sea-saw/sea-saw-gateway
git add nginx.conf
git commit -m "Add protected media access via X-Accel-Redirect

- Add /protected-media/ internal location
- Remove direct /media/ access
- Improve attachment security"
git push origin main
```

### 4. 验证部署

```bash
# SSH到服务器
ssh appuser@<server-ip>

# 检查容器状态
docker ps --filter "name=sea-saw"

# 检查backend日志
docker logs sea-saw-backend --tail 50

# 检查gateway日志
docker logs sea-saw-gateway --tail 50

# 测试nginx配置
docker exec sea-saw-gateway nginx -t

# 重启gateway（如果nginx -t成功）
cd /home/sea-saw/sea-saw-gateway
docker compose restart
```

### 5. 功能测试

**测试1: 未登录用户无法访问**
```bash
# 应返回 401 Unauthorized
curl -I http://<server-ip>/api/sea-saw-crm/attachments/1/download/
```

**测试2: 登录用户可以访问**
```bash
# 1. 获取token
TOKEN=$(curl -X POST http://<server-ip>/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}' \
  | jq -r '.access')

# 2. 下载附件
curl -H "Authorization: Bearer $TOKEN" \
  http://<server-ip>/api/sea-saw-crm/attachments/1/download/ \
  -o downloaded_file.pdf

# 应成功下载文件
```

**测试3: 直接访问/media/被拒绝**
```bash
# 应返回 404 Not Found（nginx没有该路由）
curl -I http://<server-ip>/media/attachments/order/2024/01/15/test.pdf
```

## 权限扩展 Permission Extension

当前实现中，所有已登录用户都可以访问附件。如需更细粒度的权限控制，可以扩展 `_has_permission` 方法：

```python
def _has_permission(self, user, attachment):
    """自定义权限逻辑"""
    related_object = attachment.related_object

    # 示例1: 检查用户角色
    if user.role == 'sales_manager':
        return True

    # 示例2: 检查实体归属
    if hasattr(related_object, 'owner') and related_object.owner == user:
        return True

    # 示例3: 检查部门权限
    if hasattr(related_object, 'department'):
        return user.department == related_object.department

    return False
```

## 性能优化 Performance Optimization

### X-Accel-Redirect优势

- ✅ Django只负责权限检查，不传输文件
- ✅ Nginx直接传输文件（更高效）
- ✅ 支持断点续传（Range requests）
- ✅ 减少Django进程占用

### 缓存策略

```nginx
location /protected-media/ {
    internal;
    alias /home/app/web/mediafiles/;
    expires 7d;
    add_header Cache-Control "private";  # 仅客户端缓存，不缓存在CDN
}
```

## 故障排查 Troubleshooting

### 问题1: 403 Forbidden

**原因**: 用户没有权限或未登录

**解决**:
- 确认用户已登录
- 检查 `_has_permission` 逻辑
- 查看backend日志

### 问题2: 404 Not Found

**原因**: 附件不存在或文件路径错误

**解决**:
```bash
# 检查附件记录
docker exec sea-saw-backend python manage.py shell
>>> from sea_saw_crm.models import Attachment
>>> att = Attachment.objects.get(pk=1)
>>> print(att.file.path)
>>> import os; print(os.path.exists(att.file.path))
```

### 问题3: 500 Internal Server Error

**原因**: Nginx无法访问mediafiles目录

**解决**:
```bash
# 检查volume挂载
docker inspect sea-saw-backend | jq '.[0].Mounts'
docker inspect sea-saw-gateway | jq '.[0].Mounts'

# 确认gateway可以访问media volume
docker exec sea-saw-gateway ls -la /home/app/web/mediafiles/
```

### 问题4: X-Accel-Redirect不工作

**检查**:
```bash
# 测试内部location（应失败）
curl -I http://<server-ip>/protected-media/test.pdf  # 应返回404

# 检查nginx配置
docker exec sea-saw-gateway nginx -t

# 查看gateway日志
docker logs sea-saw-gateway --tail 100 | grep protected-media
```

## 相关文件 Related Files

### Backend (sea-saw-server)
- `app/sea_saw_crm/views/attachment_view.py` - 下载视图
- `app/sea_saw_crm/serializers/shared/base_attachment.py` - 序列化器
- `app/sea_saw_crm/urls.py` - URL路由
- `app/sea_saw_server/urls.py` - 主URL配置
- `app/sea_saw_crm/models/attachment/attachment.py` - 附件模型

### Gateway (sea-saw-gateway)
- `nginx.conf` - Nginx配置

### Infrastructure
- `sea-saw-server/docker-compose.prod.yml` - 后端Docker配置（media volume）
- `sea-saw-gateway/docker-compose.yml` - Gateway Docker配置

## 总结 Summary

新的安全方案:
- ✅ 所有附件访问都需要身份验证
- ✅ 权限检查在Django层面完成
- ✅ 使用X-Accel-Redirect保证性能
- ✅ 防止未授权访问
- ✅ 支持未来扩展更细粒度的权限控制

**重要提醒**: 部署后，所有现有的直接`/media/`链接将失效。前端应使用API返回的`file_url`字段，该字段现在指向受保护的下载端点。
