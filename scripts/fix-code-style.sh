#!/bin/bash
# 自动修复常见代码风格问题
# 运行此脚本可以自动修复大部分 flake8 报告的问题

set -e

echo "🔧 自动修复代码风格问题..."
echo ""

# 进入 app 目录
cd "$(dirname "$0")/../app" || exit 1

# 1. 删除所有尾随空格
echo "📝 删除尾随空格..."
find . -type f -name "*.py" -exec sed -i '' 's/[[:space:]]*$//' {} +

# 2. 确保文件以换行符结尾
echo "📝 确保文件以换行符结尾..."
find . -type f -name "*.py" -exec bash -c 'tail -c1 "$1" | read -r _ || echo >> "$1"' _ {} \;

# 3. 删除多余的空行（超过2个连续空行）
echo "📝 删除多余的空行..."
find . -type f -name "*.py" -exec sed -i '' '/^$/N;/^\n$/N;/^\n\n$/d' {} +

echo ""
echo "✅ 代码风格修复完成！"
echo ""
echo "请运行 './scripts/check-code-quality.sh' 验证修复结果。"
