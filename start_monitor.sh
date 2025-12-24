#!/bin/bash

# 遥感推理服务监控系统启动脚本

echo "=========================================="
echo "遥感推理服务监控系统"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "检查依赖包..."
if ! python3 -c "import fastapi, uvicorn, jinja2" 2>/dev/null; then
    echo "安装依赖包..."
    pip3 install -r requirements.txt
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p static
mkdir -p templates

# 检查数据目录
DATA_DIR="/data/XXF/new/new_remote_sensing_code/data"
if [ ! -d "$DATA_DIR" ]; then
    echo "警告: 数据目录 $DATA_DIR 不存在，将使用当前目录下的data文件夹"
    mkdir -p data/logs
    mkdir -p data/detected_result_images
    mkdir -p data/detected_result_json_files
fi

# 检查端口占用并选择可用端口
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

PORT=8086
while ! check_port $PORT; do
    echo "端口 $PORT 已被占用，尝试下一个端口..."
    PORT=$((PORT + 1))
    if [ $PORT -gt 8090 ]; then
        echo "错误: 无法找到可用端口 (8086-8090)"
        exit 1
    fi
done

echo "使用端口: $PORT"

# 清理可能影响性能的临时文件
echo "清理临时文件..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 启动监控服务
echo "启动监控服务..."
echo "监控网站将在 http://localhost:$PORT 启动"
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 设置环境变量并启动服务
export MONITOR_PORT=$PORT
python3 monitor_web.py 