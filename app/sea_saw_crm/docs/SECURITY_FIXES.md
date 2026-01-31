# Security Vulnerability Fixes - Priority 1

## 概述 Overview

本文档记录了Sea-Saw CRM系统第一优先级安全漏洞的修复情况。

This document records the fixes for Priority 1 security vulnerabilities in Sea-Saw CRM.

## 修复日期 Fix Date

2026-01-31

## 修复的漏洞 Fixed Vulnerabilities

### 1. 硬编码的 SECRET_KEY (CRITICAL)

**漏洞描述**:
- Django SECRET_KEY 有硬编码的默认值作为fallback
- 如果环境变量未设置，会使用暴露在代码中的密钥

**修复内容**:
- 移除了默认fallback值
- 如果SECRET_KEY环境变量未设置，应用启动时会抛出 `ValueError`
- 更新了环境变量示例文件，添加了生成安全密钥的说明

**修改文件**:
- [settings.py:23-30](../sea_saw_server/settings.py#L23-L30)
- [.env/.dev.example](../../.env/.dev.example)
- [.env/.prod.example](../../.env/.prod.example)

**修复代码**:
```python
# Before (VULNERABLE)
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-!46^gn^&egu^@5%k9l(_b$wv^f3a=3n4i*u909dzm-@*jdmp*d"
)

# After (SECURE)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is not set. "
        "Generate a secure key with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )
```

**影响**:
- ✅ 防止了使用默认密钥导致的Session劫持
- ✅ 防止了JWT token伪造
- ⚠️ **部署前必须操作**: 生成并设置新的SECRET_KEY到生产环境

---

### 2. 硬编码的数据库凭证 (CRITICAL)

**漏洞描述**:
- 数据库用户名和密码有默认值 (`user`/`password`)
- 如果环境变量未设置，会使用这些弱凭证

**修复内容**:
- 添加了针对PostgreSQL的凭证验证
- 如果使用PostgreSQL但未提供凭证，启动时抛出 `ValueError`
- SQLite仍允许默认值（仅用于开发环境）
- 更新了环境变量示例文件，添加了强密码要求说明

**修改文件**:
- [settings.py:122-151](../sea_saw_server/settings.py#L122-L151)
- [.env/.prod.example](../../.env/.prod.example)

**修复代码**:
```python
# Before (VULNERABLE)
"USER": os.environ.get("SQL_USER", "user"),
"PASSWORD": os.environ.get("SQL_PASSWORD", "password"),

# After (SECURE)
DB_USER = os.environ.get("SQL_USER")
DB_PASSWORD = os.environ.get("SQL_PASSWORD")

# Security: require credentials for PostgreSQL (production)
if "postgresql" in DB_ENGINE:
    if not DB_USER or not DB_PASSWORD:
        raise ValueError(
            "SQL_USER and SQL_PASSWORD environment variables must be set for PostgreSQL. "
            "Never use default credentials in production."
        )
```

**影响**:
- ✅ 防止了使用默认凭证导致的数据库未授权访问
- ✅ 强制生产环境设置强密码
- ⚠️ **部署前必须操作**: 生成并设置强数据库密码到生产环境

---

### 3. 附件权限检查不足 (HIGH)

**漏洞描述**:
- 附件下载视图仅检查用户是否已登录
- 任何登录用户可以下载任何附件，无论是否有权限访问关联实体

**修复内容**:
- 实现了实体级别的权限检查
- 支持基于owner、created_by、updated_by的访问控制
- 支持基于角色层级的访问控制

**修改文件**:
- [attachment_view.py:87-157](views/attachment_view.py#L87-L157)

**修复逻辑**:
```python
def _has_permission(self, user, attachment):
    """
    权限检查逻辑（多层级安全）:
    1. 超级用户和管理员可以访问所有附件
    2. 用户可以访问附件，如果他们:
       - 拥有关联实体 (owner字段)
       - 创建了关联实体 (created_by字段)
       - 更新了关联实体 (updated_by字段)
       - 基于角色层级有权限查看实体owner
    """
    # 实现了完整的权限检查逻辑
    # 详见attachment_view.py
```

**权限层级**:
1. ✅ **超级用户/管理员** - 完全访问
2. ✅ **实体所有者** - owner字段匹配
3. ✅ **实体创建者** - created_by字段匹配
4. ✅ **实体更新者** - updated_by字段匹配
5. ✅ **角色可见性** - 基于User.get_all_visible_users()
6. ❌ **其他用户** - 拒绝访问

**影响**:
- ✅ 防止了未授权访问机密文件
- ✅ 实现了基于角色的访问控制
- ✅ 支持企业级的权限分级

---

### 4. 动态导入代码注入风险 (HIGH)

**漏洞描述**:
- `dynamic_import_model()` 和 `dynamic_import_serializer()` 函数使用用户输入进行动态导入
- 没有白名单验证，理论上可以导入任意模块

**修复内容**:
- 添加了 `ALLOWED_MODELS` 和 `ALLOWED_SERIALIZERS` 白名单字典
- 在导入前验证app_name和model_name/serializer_name
- 如果不在白名单中，抛出 `ValueError`

**修改文件**:
- [download/utilis.py:112-219](../../download/utilis.py#L112-L219)

**修复代码**:
```python
# 定义白名单
ALLOWED_MODELS = {
    'sea_saw_crm': [
        'Order', 'Contract', 'Company', 'Contact', 'Pipeline',
        'Payment', 'ProductionOrder', 'PurchaseOrder', 'OutboundOrder',
        'Supplier', 'Product', 'Attachment'
    ],
    'sea_saw_auth': ['User', 'Role'],
    'download': ['DownloadTask'],
}

ALLOWED_SERIALIZERS = {
    'sea_saw_crm': [
        'OrderSerializer', 'OrderSerializer4Prod', 'ContractSerializer',
        # ... 其他序列化器
    ],
    # ... 其他app
}

def dynamic_import_model(app_name, model_name):
    # 白名单验证
    if app_name not in ALLOWED_MODELS:
        raise ValueError(f"Security Error: App '{app_name}' is not in the allowed apps list.")

    if model_name not in ALLOWED_MODELS[app_name]:
        raise ValueError(f"Security Error: Model '{model_name}' is not allowed for app '{app_name}'.")

    # 只有通过验证才执行导入
    # ...
```

**影响**:
- ✅ 防止了通过动态导入的代码注入攻击
- ✅ 限制了可导入的模块范围
- ⚠️ **维护注意**: 添加新model/serializer时需更新白名单

---

## 部署指南 Deployment Guide

### 必须的环境变量 Required Environment Variables

在部署修复后的代码前，**必须**设置以下环境变量：

#### 1. 生成 SECRET_KEY

```bash
# 在服务器上执行
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 将输出添加到 .env/.prod 文件
echo "SECRET_KEY=<生成的密钥>" >> /home/sea-saw/sea-saw-server/.env/.prod
```

#### 2. 设置数据库密码

```bash
# 生成强密码
openssl rand -base64 32

# 添加到 .env/.prod 和 .env/.prod.db 文件
# .env/.prod
SQL_USER=sea_saw_prod_user
SQL_PASSWORD=<生成的强密码>

# .env/.prod.db (PostgreSQL容器使用)
POSTGRES_USER=sea_saw_prod_user
POSTGRES_PASSWORD=<相同的强密码>
```

### 部署步骤 Deployment Steps

#### 1. 备份现有配置

```bash
ssh appuser@<server-ip>
cd /home/sea-saw/sea-saw-server
cp -r .env .env.backup.$(date +%Y%m%d)
```

#### 2. 更新环境变量

编辑 `/home/sea-saw/sea-saw-server/.env/.prod`:
```bash
# 添加SECRET_KEY（必需）
SECRET_KEY=<你生成的密钥>

# 确认数据库凭证已设置
SQL_USER=sea_saw_prod_user
SQL_PASSWORD=<你的强密码>
```

#### 3. 部署代码

```bash
# 从本地推送代码
cd /Users/coolister/Desktop/sea-saw/sea-saw-server
git add -A
git commit -m "Fix Priority 1 security vulnerabilities

- Remove hardcoded SECRET_KEY with required env var
- Remove hardcoded database credentials
- Implement entity-level attachment permission checks
- Add whitelist validation for dynamic imports

BREAKING CHANGE: SECRET_KEY and SQL_USER/SQL_PASSWORD must now be set via
environment variables. See SECURITY_FIXES.md for deployment guide."
git push origin main
```

GitHub Actions会自动部署。

#### 4. 验证部署

```bash
# SSH到服务器
ssh appuser@<server-ip>

# 检查容器启动状态
docker logs sea-saw-backend --tail 50

# 如果看到错误 "SECRET_KEY environment variable is not set"
# 说明环境变量未正确配置，检查 .env/.prod 文件

# 测试应用启动
curl http://localhost/api/health/
# 应返回: {"status": "ok"}
```

#### 5. 安全验证

```bash
# 测试1: 验证附件权限（未登录）
curl -I http://<server-ip>/api/sea-saw-crm/attachments/1/download/
# 应返回: 401 Unauthorized

# 测试2: 验证动态导入白名单
# 在Django shell中测试
docker exec -it sea-saw-backend python manage.py shell
>>> from download.utilis import dynamic_import_model
>>> dynamic_import_model('os', 'system')  # 应抛出ValueError
>>> dynamic_import_model('sea_saw_crm', 'Order')  # 应成功
```

---

## 回滚方案 Rollback Plan

如果部署后出现问题，可以按以下步骤回滚：

```bash
# 1. 恢复旧版本代码
cd /home/sea-saw/sea-saw-server
git checkout <上一个commit-id>

# 2. 重新部署
docker compose -f docker-compose.prod.yml up -d --build

# 3. 如果仍有问题，恢复环境变量
cp .env.backup.<date>/.prod .env/.prod
docker compose -f docker-compose.prod.yml restart
```

**重要**: 回滚后系统仍然存在安全漏洞，需尽快重新部署修复版本。

---

## 后续安全改进计划 Future Security Improvements

### 第二优先级（建议本周完成）

1. **修复批量赋值漏洞** - 明确定义所有序列化器的fields
2. **改进Token存储** - 前端使用HttpOnly Cookie替代localStorage
3. **文件上传验证** - 添加MIME类型验证和文件大小限制

### 第三优先级（建议本月完成）

4. **添加Nginx安全头** - CSP, Permissions-Policy等
5. **Token端点速率限制** - 防止暴力破解
6. **移除调试代码** - 清理print语句，使用logging

### 长期改进

7. **定期安全审计** - 每季度进行一次全面安全扫描
8. **密钥轮换** - 建立SECRET_KEY和数据库密码定期轮换机制
9. **访问日志审计** - 记录所有敏感操作（附件下载、用户登录等）

---

## 相关文档 Related Documentation

- [附件安全指南](ATTACHMENT_SECURITY.md) - 附件权限管理详细说明
- [实施指南](guides/implementation-guide.md) - 完整部署流程
- [Django安全最佳实践](https://docs.djangoproject.com/en/5.1/topics/security/)

---

## 联系方式 Contact

如有安全问题或发现新漏洞，请联系：
- GitHub Issues: https://github.com/your-org/sea-saw/issues
- 安全邮件: security@your-domain.com

**请勿公开披露安全漏洞，请通过私密渠道报告。**
