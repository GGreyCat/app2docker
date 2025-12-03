#!/bin/bash

echo "🚀 启动 App2Docker 开发环境"
echo "================================"

# 检查后端虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ 准备就绪！"
echo ""
echo "📍 后端服务: http://localhost:8000"
echo "📍 前端服务: http://localhost:3000"
echo ""
echo "请在两个终端分别运行："
echo "  终端1: python backend/app.py"
echo "  终端2: cd frontend && npm run dev"
echo ""
echo "或使用 tmux/screen 同时运行两个服务"

