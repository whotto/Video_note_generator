#!/bin/bash

# 视频笔记生成器 - Web应用启动脚本

echo "🎬 视频笔记生成器 - Web应用启动"
echo "=================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装/更新依赖
echo "📦 检查依赖..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 配置文件"
    if [ -f ".env.example" ]; then
        echo "📋 从 .env.example 创建 .env 文件..."
        cp .env.example .env
        echo "✅ .env 文件已创建，请编辑并填入你的API密钥"
        echo ""
        echo "你需要配置以下内容："
        echo "  - OPENROUTER_API_KEY: OpenRouter API密钥"
        echo "  - UNSPLASH_ACCESS_KEY: Unsplash访问密钥（可选）"
        echo ""
        read -p "按 Enter 继续编辑配置文件，或 Ctrl+C 退出..."
        ${EDITOR:-nano} .env
    else
        echo "❌ 错误: 未找到 .env.example 文件"
        exit 1
    fi
fi

# 启动Web应用
echo ""
echo "🚀 启动 Web 应用..."
echo "=================================="
echo ""
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动uvicorn
python3 web_app.py
