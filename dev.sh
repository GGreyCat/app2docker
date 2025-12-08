#!/bin/bash

echo "🚀 启动 App2Docker 开发环境"
echo "================================"

# 检查后端虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败，请确保已安装 Python3"
        exit 1
    fi
    source .venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 安装依赖失败"
        exit 1
    fi
else
    source .venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "❌ 激活虚拟环境失败"
        exit 1
    fi
    # 检查关键依赖是否已安装
    python3 -c "import uvicorn" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  检测到缺少依赖，正在安装..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "❌ 安装依赖失败"
            exit 1
        fi
    fi
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 初始化环境（创建目录和配置文件）
echo ""
echo "🔧 初始化环境..."
if python3 -c "from backend.utils import ensure_dirs; from backend.config import ensure_config_exists; ensure_dirs(); ensure_config_exists(); print('✅ 环境初始化完成')" 2>/dev/null; then
    echo "   ✓ 目录结构已创建"
    echo "   ✓ 配置文件已初始化"
else
    echo "⚠️  环境初始化失败，将在应用启动时自动初始化"
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

