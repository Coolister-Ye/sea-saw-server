# 文件上传路径优化说明

## 问题背景

之前的文件上传配置存在**同名文件覆盖风险**：

```python
# ❌ 旧的实现 - 所有文件在同一文件夹
production_files = models.FileField(
    upload_to="production_files/",  # 如果两个用户上传 "invoice.pdf"，后者会覆盖前者
)
```

## 解决方案

### 1. 创建了通用的文件路径生成器 (`utils.py`)

```python
def get_upload_path(instance, filename, subfolder="files"):
    """
    生成唯一的上传路径，避免文件名冲突

    路径结构: {subfolder}/{YYYY}/{MM}/{DD}/{uuid}_{original_filename}

    示例:
        payment_attachments/2024/01/15/a3b5c7d9e1f2_invoice.pdf
    """
```

### 2. 路径特点

✅ **按日期分文件夹**：便于管理和归档
- `2024/01/15/` - 按年/月/日组织

✅ **添加 UUID 前缀**：确保唯一性
- `a3b5c7d9e1f2_invoice.pdf`

✅ **保留原始文件名**：便于识别
- 用户能看到 "invoice.pdf" 而不是乱码

✅ **保留文件扩展名**：确保文件类型正确
- `.pdf`, `.jpg`, `.xlsx` 等

### 3. 使用示例

#### 完整路径示例

```
# 支付附件
payment_attachments/2024/01/15/a3b5c7d9e1f2_bank_slip.pdf
payment_attachments/2024/01/15/b4c6d8e0f3a1_invoice.jpg

# 生产文件
production_files/2024/01/16/c5d7e9f1a4b2_production_plan.xlsx
production_files/2024/01/16/d6e8f0a2b5c3_material_list.pdf
```

#### 同名文件不会冲突

```python
# 用户 A 上传 invoice.pdf → payment_attachments/2024/01/15/a3b5c7d9e1f2_invoice.pdf
# 用户 B 上传 invoice.pdf → payment_attachments/2024/01/15/f9a2b3c4d5e6_invoice.pdf
# ✅ 两个文件都保存成功，不会互相覆盖
```

## 已更新的模型

### PaymentRecord
```python
attachment = models.FileField(
    upload_to=payment_attachment_path,  # ✅ 使用函数
    ...
)
```

### ProductionOrder
```python
production_files = models.FileField(
    upload_to=production_file_path,  # ✅ 使用函数
    ...
)
```

## 迁移说明

### 1. 已生成迁移文件

```bash
# 迁移文件已创建
sea_saw_crm/migrations/0004_update_file_upload_paths.py
```

### 2. 应用迁移

```bash
# 开发环境
python manage.py migrate

# 生产环境
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate
```

### 3. 对现有文件的影响

⚠️ **重要**：此更改**不会影响已上传的文件**
- 已存在的文件保持原路径不变
- 只有新上传的文件会使用新路径
- 旧文件仍然可以正常访问和下载

### 4. 如果需要迁移旧文件（可选）

```python
# 创建数据迁移脚本（如果需要）
python manage.py makemigrations --empty sea_saw_crm --name migrate_old_files

# 然后在迁移文件中添加自定义逻辑来移动文件
```

## 测试

### 运行测试

```bash
python manage.py test sea_saw_crm.tests_file_upload
```

### 测试覆盖

✅ 路径结构正确性
✅ 唯一性验证
✅ 文件扩展名保留
✅ 特殊字符处理
✅ 无扩展名文件处理

## 添加新的文件字段

如果将来需要添加新的文件上传字段：

### 1. 在 `utils.py` 中添加新函数

```python
def contract_file_path(instance, filename):
    """
    Upload path for contract files.
    """
    return get_upload_path(instance, filename, subfolder="contract_files")
```

### 2. 在模型中使用

```python
from ..utils import contract_file_path

class Contract(BaseModel):
    file = models.FileField(
        upload_to=contract_file_path,  # 使用函数而不是字符串
        ...
    )
```

### 3. 运行迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 优势总结

| 特性 | 旧方案 | 新方案 |
|------|--------|--------|
| 同名文件 | ❌ 覆盖 | ✅ 共存 |
| 文件组织 | ❌ 混乱 | ✅ 按日期分类 |
| 可追溯性 | ❌ 难以追踪 | ✅ 易于管理 |
| 原始文件名 | ❌ 不保留 | ✅ 保留 |
| 性能 | ❌ 大文件夹 | ✅ 小文件夹（更快） |

## 注意事项

1. **存储空间**：确保服务器有足够的存储空间
2. **备份策略**：建议定期备份 MEDIA_ROOT 目录
3. **文件清理**：如果删除数据库记录，考虑是否需要清理关联文件
4. **权限设置**：确保 Django 有权限写入 MEDIA_ROOT

## 相关配置

### settings.py

```python
# 媒体文件配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### nginx 配置（生产环境）

```nginx
location /media/ {
    alias /path/to/media/;
    expires 30d;
    access_log off;
}
```
