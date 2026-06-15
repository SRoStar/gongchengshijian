#!/bin/bash

# 获取脚本所在目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DBTABLE_DIR="$PROJECT_DIR/backend/dbtable"

echo "=== 启动材料可视化项目 ==="
echo "项目目录: $PROJECT_DIR"

# 检测 dbtable 文件夹是否存在且不为空
if [ ! -d "$DBTABLE_DIR" ] || [ -z "$(ls -A "$DBTABLE_DIR" 2>/dev/null)" ]; then
    echo "[1/3] dbtable 不存在或为空，初始化数据库..."
    cd "$PROJECT_DIR/backend" && uv run database/initial_db.py
    if [ $? -ne 0 ]; then
        echo "数据库初始化失败，请检查错误信息"
        exit 1
    fi
    echo "数据库初始化完成"
else
    echo "[1/3] dbtable 已存在且不为空，跳过初始化"
fi

# 启动后端（后台运行）
echo "[2/3] 启动后端服务 (uv run main.py)..."
cd "$PROJECT_DIR/backend"
uv run main.py &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 2

# 启动前端
echo "[3/3] 启动前端服务 (npm run serve)..."
cd "$PROJECT_DIR/frontend"
npm run serve

# 前端退出时，结束后端
echo "正在关闭后端服务..."
kill $BACKEND_PID 2>/dev/null

echo "项目已停止"
