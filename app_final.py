import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ================= 1. 核心配置 =================
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
WORKFLOW_ID = "7617931269947506729"
BOT_ID = "7617094528700530742"
API_URL = "https://api.coze.cn/v1/workflow/run"

st.set_page_config(layout="wide", page_title="病生实时学情系统")

tab1, tab2 = st.tabs(["📊 教师大屏", "📝 学生答题"])

# --- 教师端逻辑保持不变 ---
with tab1:
    st.title("🏥 班级实时学情看板")
    if st.button('🔄 刷新数据', type="primary"):
        # ... (此处省略重复的统计代码，保持您原有的即可)
        st.write("数据已更新")

# ================= 2. 学生端：免登录 + 全屏适配版 =================
with tab2:
    # 这里的 HTML 我们给一个巨大的高度 1000，确保在手机上能撑开
    chat_html = f"""
    <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
    <div id="coze-chat-container" style="height: 90vh; width: 100%;"></div>
    <script>
        new CozeWebSDK.WebChatClient({{
            config: {{ bot_id: '{BOT_ID}' }},
            componentProps: {{ 
                title: '病生批改助手',
                layout: 'inline' 
            }},
            el: document.getElementById('coze-chat-container'),
            auth: {{
                type: 'token',
                token: '{PERSONAL_ACCESS_TOKEN}',
                onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
            }}
        }});
    </script>
    <style>
        /* 隐藏掉 Streamlit 自动生成的边距，让对话框更大 */
        iframe {{ min-height: 800px !important; }}
    </style>
    """
    components.html(chat_html, height=850)
