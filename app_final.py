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

# ⚡ 核心修复：强制左侧对齐，消除位移 ⚡
st.markdown("""
    <style>
    /* 1. 彻底清空 Streamlit 所有容器的间距 */
    .block-container {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin-left: 0rem !important;
        margin-right: 0rem !important;
        max-width: 100% !important;
    }
    /* 2. 修正 iframe 的定位，确保它从屏幕最左侧 (0) 开始渲染 */
    iframe {
        position: relative;
        left: 0 !important;
        width: 100vw !important;
        height: 850px !important;
        border: none;
    }
    /* 3. 隐藏顶部不必要的元素 */
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

# --- 教师端略 ---
with tab1:
    st.title("🏥 班级学情统计")
    st.info("请在学生答题后刷新")

# ================= 2. 学生端：左侧对齐修正版 =================
with tab2:
    # 核心修改：在最外层 div 增加 margin-left 补偿，确保内容不被切掉
    chat_sdk_code = f"""
    <div id="wrapper" style="width: 100vw; height: 800px; margin-left: 0px; padding-left: 2px; overflow: hidden;">
        <div id="chat_box" style="width: 98%; height: 100%;"></div>
    </div>
    <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
    <script>
      new CozeWebSDK.WebChatClient({{
        config: {{ bot_id: '{BOT_ID}' }},
        componentProps: {{ 
            title: '病生批改助手', 
            layout: 'inline'
        }},
        el: document.getElementById('chat_box'),
        auth: {{
          type: 'token',
          token: '{PERSONAL_ACCESS_TOKEN}',
          onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
        }}
      }});
    </script>
    <style>
        /* 强制 body 从 0 开始，不留任何边距 */
        body {{ margin: 0 !important; padding: 0 !important; overflow: hidden; }}
    </style>
    """
    
    # 将高度设为 850 确保底部可见
    components.html(chat_sdk_code, height=850)

    st.caption("提示：若左侧仍有遮挡，请尝试横屏或刷新。")
