#!/bin/bash

# AI 助手项目环境设置脚本
# 在 WSL 中运行此脚本

echo "🚀 开始设置 AI 助手项目环境..."

# 检查是否在 WSL 中
if [[ ! "$(uname -r)" =~ Microsoft|WSL ]]; then
    echo "⚠️  警告：似乎不在 WSL 环境中运行"
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查 Python 版本
echo "📦 检查 Python 版本..."
python3 --version

# 检查 pip
echo "📦 检查 pip..."
pip3 --version

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖
echo "📥 安装项目依赖..."
pip3 install -r requirements.txt

# 检查安装
echo "🔍 检查安装的包..."
pip3 list | grep -E "(streamlit|fastapi|uvicorn|openai|pydantic)"

echo ""
echo "✅ 环境设置完成！"
echo ""
echo "📋 可用命令："
echo "  前端运行: streamlit run main.py"
echo "  后端运行: python backend/main.py"
echo "  激活虚拟环境: source venv/bin/activate"
echo "  退出虚拟环境: deactivate"