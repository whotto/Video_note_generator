#!/bin/bash
# 启动Streamlit Web应用

# 激活虚拟环境
source venv/bin/activate

# 启动Streamlit
streamlit run streamlit_app.py \
    --server.port=8501 \
    --server.address=localhost \
    --theme.primaryColor="#667eea" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f0f2f6" \
    --theme.textColor="#262730" \
    --theme.font="sans serif"
