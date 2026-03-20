#!/bin/bash
# Video Generator API 启动脚本

# 激活虚拟环境
source venv/bin/activate

# 启动服务
echo "Starting Video Generator API on port 15321..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 15321 --reload
