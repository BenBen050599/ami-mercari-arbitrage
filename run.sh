#!/bin/bash
# 一键安装并运行套利分析
set -e

echo "📦 安装依赖..."
pip3 install -r requirements.txt
python3 -m playwright install chromium

echo ""
echo "🚀 开始运行..."
python3 -m src.main
