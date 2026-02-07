#!/bin/bash
# 本地代码质量检查脚本
# 在推送到 GitHub 前运行此脚本，确保通过 CI 检查

set -e

echo "🔍 开始代码质量检查..."
echo ""

# 进入 app 目录
cd "$(dirname "$0")/../app" || exit 1

# 检查是否安装了 flake8
if ! command -v flake8 &> /dev/null; then
    echo "⚠️  flake8 未安装，正在安装..."
    pip install flake8
    echo ""
fi

# 运行 flake8 检查
echo "📋 运行 flake8 代码检查..."
if flake8 .; then
    echo "✅ flake8 检查通过！"
else
    echo ""
    echo "❌ flake8 检查失败！"
    echo "请修复上述问题后再推送代码。"
    exit 1
fi

echo ""
echo "🎉 所有检查通过！可以安全推送代码。"
