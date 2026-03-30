#!/bin/bash
set -e
echo "📦 安装依赖..."
pip3 install -r requirements.txt
echo ""
echo "🚀 开始运行..."
python3 -m src.main
