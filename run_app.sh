#!/bin/bash
# AI Stock Trader - 启动脚本
# 使用方法: ./run_app.sh

# 设置路径
export PATH="/Users/urwlee/Library/Python/3.9/bin:$PATH"

# 取消邮箱提示
export STREAMLIT_SERVER_HEADLESS=true

cd "$(dirname "$0")"

echo "🚀 启动 AI Stock Trader..."
echo ""
echo "📊 请在浏览器中打开:"
echo "   http://localhost:8501"
echo ""
echo "💡 提示: 如果页面无法打开，请确保端口8501未被占用"
echo ""

# 启动 Streamlit
streamlit run app.py --server.headless=true
