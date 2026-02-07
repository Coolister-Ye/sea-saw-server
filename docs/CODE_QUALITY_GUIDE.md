# 代码质量检查指南

本指南说明如何在推送代码前进行本地代码质量检查，避免 GitHub Actions CI 失败。

## 快速开始

### 1. 检查代码质量

在推送代码前运行：

```bash
cd /Users/coolister/Desktop/sea-saw/sea-saw-server
./scripts/check-code-quality.sh
```

这会运行 flake8 检查所有 Python 代码，确保符合项目代码规范。

### 2. 自动修复常见问题

如果检查失败，可以先尝试自动修复：

```bash
./scripts/fix-code-style.sh
```

这会自动修复以下问题：
- 删除尾随空格
- 确保文件以换行符结尾
- 删除多余的空行

### 3. 重新检查

修复后重新运行检查：

```bash
./scripts/check-code-quality.sh
```

## 配置说明

项目使用 `.flake8` 配置文件进行代码检查，主要设置：

```ini
# 最大行长度
max-line-length = 120

# 排除检查的目录
exclude =
    */migrations/*,    # Django 迁移文件
    */settings.py,     # Django 设置文件
    __pycache__,       # Python 缓存
    venv,              # 虚拟环境
    ...

# 忽略的错误代码
ignore =
    E203,  # 切片中的空格
    W503,  # 二元运算符前的换行
    E402,  # module level import not at top
    F401,  # 导入但未使用
    F811,  # 重复定义
```

## 常见错误及修复

### E501: 行太长

**错误示例：**
```python
raise ValidationError({"error": "This is a very long error message that exceeds 120 characters limit"})
```

**修复方法：**
```python
raise ValidationError({
    "error": (
        "This is a very long error message that "
        "exceeds 120 characters limit"
    )
})
```

### W291: 尾随空格

**自动修复：**
```bash
./scripts/fix-code-style.sh
```

### F401: 导入但未使用

**解决方案：**
1. 删除未使用的导入
2. 或在 `.flake8` 中添加忽略规则

### E402: import 不在文件顶部

**常见于：**
```python
import sys
sys.path.append('..')
from mymodule import something  # E402
```

**修复：** 将所有 import 移到文件顶部，或在该行添加 `# noqa: E402`

## GitHub Actions 集成

推送到 `main` 分支会自动触发 CI 检查：

1. **代码检查 (flake8)** - 必须通过
2. **构建 Docker 镜像** - 通过后部署
3. **部署到生产服务器** - 自动更新服务

**查看 CI 状态：**
https://github.com/Coolister-Ye/sea-saw-server/actions

## 最佳实践

### 提交前检查流程

```bash
# 1. 查看改动
git status

# 2. 运行代码检查
./scripts/check-code-quality.sh

# 3. 如果失败，自动修复
./scripts/fix-code-style.sh

# 4. 重新检查
./scripts/check-code-quality.sh

# 5. 通过后提交
git add .
git commit -m "your commit message"
git push origin main
```

### Git Hooks（可选）

可以配置 git pre-commit hook 自动检查：

```bash
# 创建 .git/hooks/pre-commit
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
cd app
flake8 .
if [ $? -ne 0 ]; then
    echo "❌ flake8 检查失败，请修复后再提交"
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## 工具安装

### flake8

```bash
pip install flake8
```

### 可选工具

```bash
# Black - 代码格式化工具
pip install black

# isort - import 排序工具
pip install isort

# autopep8 - 自动修复 PEP8 问题
pip install autopep8
```

## 常见问题

### Q: 为什么我的代码在本地可以运行，但 CI 失败？

A: CI 环境更严格，会检查代码风格。使用 `./scripts/check-code-quality.sh` 可以复现 CI 的检查。

### Q: 可以完全禁用某些检查吗？

A: 可以在 `.flake8` 的 `ignore` 部分添加错误代码，但不建议过度禁用。

### Q: 如何忽略特定文件的检查？

A: 在 `.flake8` 的 `per-file-ignores` 部分添加：

```ini
per-file-ignores =
    specific_file.py:E501,F401
```

### Q: 行长度限制可以调整吗？

A: 可以在 `.flake8` 中修改 `max-line-length`，但建议保持在 120 以内。

## 参考资料

- [Flake8 文档](https://flake8.pycqa.org/)
- [PEP 8 风格指南](https://peps.python.org/pep-0008/)
- [Django 代码风格](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
