#!/bin/bash

# AI Crawler Assistant 启动脚本

set -e

echo "🚀 启动 AI Crawler Assistant..."

# 检查环境变量
# if [ -z "$OPENAI_API_KEY" ]; then
#     echo "❌ 错误: OPENAI_API_KEY 环境变量未设置"
#     echo "请设置您的 OpenAI API 密钥:"
#     echo "export OPENAI_API_KEY=your_api_key_here"
#     exit 1
# fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs exports screenshots uploads

# 检查.env文件
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cp env.example .env
    echo "⚠️  请编辑 .env 文件并设置您的配置"
    echo "特别注意设置 OPENAI_API_KEY"
fi

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查应用健康状态..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 应用健康检查通过"
else
    echo "❌ 应用健康检查失败"
    echo "查看日志:"
    docker-compose logs app
    exit 1
fi

echo ""
echo "🎉 AI Crawler Assistant 启动成功!"
echo ""
echo "📊 服务地址:"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/health"
echo "  - Flower监控: http://localhost:5555"
echo ""
echo "📝 常用命令:"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo "  - 重启服务: docker-compose restart"
echo ""
echo "✨ 开始使用 AI Crawler Assistant!"

