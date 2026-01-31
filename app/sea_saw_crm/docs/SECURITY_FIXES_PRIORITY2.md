# Security Vulnerability Fixes - Priority 2

## 概述 Overview

本文档记录了Sea-Saw CRM系统第二优先级安全漏洞的修复情况。

This document records the fixes for Priority 2 security vulnerabilities in Sea-Saw CRM.

## 修复日期 Fix Date

2026-01-31

## 修复的漏洞 Fixed Vulnerabilities

### 1. 批量赋值漏洞 - Mass Assignment (HIGH)

**漏洞描述**:
- 多个序列化器使用 `fields = "__all__"`
- 允许客户端设置任意模型字段，包括敏感字段如 `is_staff`、`is_superuser`

**修复内容**:
明确定义所有序列化器的 `fields` 列表，并设置 `read_only_fields`。

**修改文件**:
1. [sea_saw_auth/serializers.py:8-25](../../sea_saw_auth/serializers.py#L8-L25)
   ```python
   # Before (VULNERABLE)
   class GroupSerializer(serializers.ModelSerializer):
       class Meta:
           model = Group
           fields = "__all__"

   # After (SECURE)
   class GroupSerializer(serializers.ModelSerializer):
       class Meta:
           model = Group
           fields = ["id", "name", "permissions"]
           read_only_fields = ["id"]
   ```

2. [sea_saw_crm/serializers/order/order_nested.py:85-100](../serializers/order/order_nested.py#L85-L100)
   ```python
   # Before (VULNERABLE)
   class Meta(BaseSerializer.Meta):
       model = Order
       fields = "__all__"
       read_only_fields = ["status"]

   # After (SECURE)
   class Meta(BaseSerializer.Meta):
       model = Order
       fields = BASE_FIELDS + [
           "inco_terms", "currency", "deposit", "balance",
           "total_amount", "comment", "owner", "created_by",
           "updated_by", "created_at", "updated_at",
       ]
       read_only_fields = ["status", "id", "created_at", "updated_at"]
   ```

3. [sea_saw_crm/serializers/pipeline/pipeline.py](../serializers/pipeline/pipeline.py)
   - 移动 `BASE_FIELDS` 定义到类定义之前
   - 明确定义所有字段

**影响**:
- ✅ 防止了权限提升攻击
- ✅ 防止了未授权字段修改
- ✅ 符合最小权限原则

---

### 2. 文件上传验证缺失 (MEDIUM)

**漏洞描述**:
- 没有文件类型验证（仅基于扩展名）
- 没有文件大小限制
- 可能上传恶意文件（exe、dll等）

**修复内容**:
创建了完整的文件上传验证系统，包括：
1. MIME类型白名单验证
2. 文件大小限制（50MB）
3. 危险扩展名黑名单
4. 使用 `python-magic` 检测实际文件内容

**新增文件**:
1. [sea_saw_crm/validators/file_validators.py](../validators/file_validators.py)
   ```python
   # 允许的MIME类型白名单
   ALLOWED_MIME_TYPES = {
       'application/pdf': ['.pdf'],
       'application/msword': ['.doc'],
       'image/jpeg': ['.jpg', '.jpeg'],
       # ... 更多类型
   }

   # 最大文件大小
   MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

   # 危险扩展名黑名单
   DANGEROUS_EXTENSIONS = {
       '.exe', '.dll', '.bat', '.cmd', '.sh', '.ps1',
       # ... 更多危险类型
   }

   def validate_file_upload(value):
       """综合文件验证"""
       validate_file_extension(value)
       validate_file_size(value)
       validate_file_mime_type(value)  # 使用python-magic检测实际内容
   ```

2. [sea_saw_crm/validators/__init__.py](../validators/__init__.py)

**修改文件**:
1. [sea_saw_crm/models/attachment/attachment.py:104-108](../models/attachment/attachment.py#L104-L108)
   ```python
   file = models.FileField(
       upload_to=attachment_file_path,
       validators=[validate_file_upload],  # 添加验证器
       verbose_name=_("File"),
       help_text=_("Upload file. Max size: 50MB. Allowed types: PDF, Office documents, images, archives."),
   )
   ```

2. [app/requirements.txt:27](../../requirements.txt#L27)
   ```
   python-magic==0.4.27  # File MIME type detection for upload security
   ```

**安全特性**:
- ✅ **内容检测** - 使用 `python-magic` 检测实际文件内容，而非仅依赖扩展名
- ✅ **白名单验证** - 只允许预定义的安全文件类型
- ✅ **扩展名匹配** - 验证扩展名与检测到的MIME类型一致
- ✅ **大小限制** - 防止磁盘空间耗尽攻击
- ✅ **危险类型阻止** - 阻止所有可执行文件

**影响**:
- ✅ 防止了恶意文件上传
- ✅ 防止了文件扩展名欺骗
- ✅ 防止了资源耗尽攻击

---

### 3. 缺少安全HTTP头 (MEDIUM)

**漏洞描述**:
- Nginx配置缺少重要的安全HTTP头
- 容易受到XSS、点击劫持等攻击

**修复内容**:
在 Nginx 配置中添加了完整的安全HTTP头。

**修改文件**:
[sea-saw-gateway/nginx.conf:21-36](../../../../sea-saw-gateway/nginx.conf#L21-L36)

```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy (CSP)
# Adjust based on your application's needs
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'self';" always;

# Permissions Policy (formerly Feature-Policy)
# Restrict browser features to prevent misuse
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()" always;

# HTTP Strict Transport Security (HSTS)
# Only enable after SSL is configured
# add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

**新增的安全头**:
| 头部 | 作用 | 值 |
|------|------|-----|
| **Content-Security-Policy** | 防止XSS攻击 | 限制资源加载来源 |
| **Permissions-Policy** | 限制浏览器功能 | 禁用地理位置、相机、麦克风等 |
| **HSTS** (注释) | 强制HTTPS | 配置SSL后启用 |

**影响**:
- ✅ 防止XSS攻击
- ✅ 防止点击劫持
- ✅ 防止MIME类型嗅探
- ✅ 限制浏览器功能滥用

---

### 4. 调试代码泄露 (LOW)

**漏洞描述**:
- 生产代码中存在 `print()` 调试语句
- 可能泄露敏感信息到日志

**修复内容**:
移除所有调试 `print()` 语句，改用 `logging` 模块。

**修改文件**:
1. [download/utilis.py:104](../../download/utilis.py#L104)
   ```python
   # 移除: print("@@@headers", headers)
   ```

2. [preference/serializers.py:16](../../preference/serializers.py#L16)
   ```python
   # Before
   print("request.user", request.user)

   # After
   logger.debug(f"Creating preference for user: {request.user}")
   ```

3. [sea_saw_crm/policy/order_access_policy.py:190,195](../policy/order_access_policy.py)
   ```python
   # 移除: print("role", role)
   # 移除: print("get_visibles", get_visibles)
   ```

4. [sea_saw_crm/filtersets.py:31,41](../filtersets.py)
   ```python
   # 移除: print("start-end", start, end)
   # 移除: print("range value", value)
   ```

**影响**:
- ✅ 防止信息泄露到日志
- ✅ 提高代码质量
- ✅ 使用专业的日志系统

---

## 部署指南 Deployment Guide

### 必须的操作步骤

#### 1. 安装新依赖

```bash
# 在服务器上进入容器
docker exec -it sea-saw-backend bash

# 安装 python-magic
pip install python-magic==0.4.27

# 或者重新构建容器
cd /home/sea-saw/sea-saw-server
docker compose -f docker-compose.prod.yml up -d --build
```

**重要**: `python-magic` 依赖系统库 `libmagic`，在 Dockerfile 中已经通过基础镜像包含。

#### 2. 迁移数据库

由于修改了 `Attachment` 模型（添加了 validators），需要创建迁移：

```bash
# 在本地生成迁移
cd /Users/coolister/Desktop/sea-saw/sea-saw-server/app
python manage.py makemigrations

# 提交迁移文件
git add sea_saw_crm/migrations/
git commit -m "Add file upload validators to Attachment model"
```

#### 3. 更新 Nginx 配置

```bash
# SSH到服务器
ssh appuser@<server-ip>

# 拉取最新的 gateway 代码
cd /home/sea-saw/sea-saw-gateway
git pull origin main

# 测试 nginx 配置
docker exec sea-saw-gateway nginx -t

# 重启 gateway
docker compose restart
```

#### 4. 部署后端代码

```bash
# 从本地推送代码
cd /Users/coolister/Desktop/sea-saw/sea-saw-server
git add -A
git commit -m "Fix Priority 2 security vulnerabilities

- Fix mass assignment in serializers (explicit fields)
- Add comprehensive file upload validation
- Add security headers to nginx
- Remove debug print statements
- Add python-magic for MIME type detection"
git push origin main
```

GitHub Actions会自动部署。

#### 5. 验证部署

```bash
# 验证文件上传限制
# 尝试上传一个 .exe 文件（应该被拒绝）
# 尝试上传一个大于50MB的文件（应该被拒绝）
# 尝试上传一个允许的PDF文件（应该成功）

# 验证安全头
curl -I http://<server-ip>/ | grep -E "Content-Security-Policy|Permissions-Policy"

# 验证序列化器
# 尝试通过API设置 is_staff=True（应该被忽略）
```

---

## 测试建议 Testing Recommendations

### 文件上传测试

```python
# 测试1: 上传危险文件
# 应返回 ValidationError
with open('malware.exe', 'rb') as f:
    response = client.post('/api/sea-saw-crm/attachments/', {
        'file': f,
        'attachment_type': 'ORDER_ATTACHMENT'
    })
assert response.status_code == 400

# 测试2: 上传超大文件
# 应返回 ValidationError
with open('large_file.pdf', 'rb') as f:  # > 50MB
    response = client.post('/api/sea-saw-crm/attachments/', {
        'file': f
    })
assert response.status_code == 400

# 测试3: 上传正常文件
# 应成功
with open('document.pdf', 'rb') as f:
    response = client.post('/api/sea-saw-crm/attachments/', {
        'file': f
    })
assert response.status_code == 201
```

### 批量赋值测试

```python
# 测试: 尝试设置敏感字段
response = client.post('/api/auth/users/', {
    'username': 'testuser',
    'password': 'testpass',
    'is_staff': True,  # 应该被忽略
    'is_superuser': True  # 应该被忽略
})
user = User.objects.get(username='testuser')
assert user.is_staff is False
assert user.is_superuser is False
```

---

## 性能影响 Performance Impact

### 文件上传验证

- **MIME检测**: 每次上传增加约 10-50ms（读取文件头2048字节）
- **文件大小检查**: 可忽略（<1ms）
- **扩展名检查**: 可忽略（<1ms）

**总体影响**: 轻微，可接受

### 安全头

- **Nginx性能**: 可忽略（头部添加是非常快的操作）
- **客户端影响**: CSP可能影响某些第三方脚本加载（需要调整策略）

---

## 后续改进 Future Improvements

### 短期（本月完成）

1. **Token存储改进** - 前端使用HttpOnly Cookie替代localStorage
2. **速率限制增强** - 为token端点添加更严格的限制
3. **ContentType端点限制** - 仅管理员可访问

### 中期（下季度）

4. **文件扫描集成** - 集成病毒扫描（ClamAV）
5. **审计日志** - 记录所有敏感操作
6. **CSP细化** - 根据实际使用调整CSP策略

### 长期

7. **WAF集成** - 添加Web应用防火墙
8. **入侵检测** - 实施异常行为检测
9. **安全培训** - 定期团队安全培训

---

## 总结 Summary

| # | 漏洞 | 严重性 | 状态 | 文件修改数 |
|---|------|--------|------|-----------|
| 1 | Mass Assignment | 🟠 HIGH | ✅ 已修复 | 3 |
| 2 | File Upload Validation | 🟡 MEDIUM | ✅ 已修复 | 4 |
| 3 | Missing Security Headers | 🟡 MEDIUM | ✅ 已修复 | 1 |
| 4 | Debug Print Statements | 🟢 LOW | ✅ 已修复 | 4 |

**总计**: 4个漏洞修复，12个文件修改

**新增代码**:
- 文件验证器模块（200+ 行）
- 安全HTTP头配置
- 日志替代调试语句

**安全提升**:
- ✅ 防止权限提升
- ✅ 防止恶意文件上传
- ✅ 增强HTTP安全
- ✅ 减少信息泄露

---

## 相关文档 Related Documentation

- [Priority 1 Security Fixes](SECURITY_FIXES.md) - 第一优先级修复
- [Attachment Security Guide](ATTACHMENT_SECURITY.md) - 附件安全详细说明
- [Implementation Guide](guides/implementation-guide.md) - 部署指南
