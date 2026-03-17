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

# ⚡ 极致位移 CSS：强制整体向右偏移，防止左侧切边 ⚡
st.markdown("""
    <style>
    /* 1. 消除全局边距 */
    .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100vw !important;
    }
    /* 2. 关键：强制 iframe 整体向右平移 10 像素，并收缩宽度防止右侧溢出 */
    iframe {
        position: relative !important;
        transform: translateX(10px) !important; /* 向右物理位移 */
        width: calc(100vw - 20px) !important;  /* 宽度减去位移空间，防止右边又被切 */
        height: 850px !important;
        border: none !important;
    }
    /* 隐藏不必要的 Streamlit 元素 */
    header, footer, #MainMenu {visibility: hidden; display: none !important;}
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

# --- 教师端保持原样 ---
with tab1:
    st.title("🏥 班级学情统计")
    st.info("请在学生答题后刷新")

# ================= 2. 学生端：物理位移修正版 =================
with tab2:
    # 在 HTML 层面也进行安全加固
    chat_sdk_code = f"""
    <div id="wrapper" style="width: 100%; height: 800px; overflow: hidden; padding-left: 5px;">
        <div id="chat_box" style="width: 95%; height: 100%;"></div>
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
    """
    
    # 容器高度设为 850，确保输入框露出来
    components.html(chat_sdk_code, height=850)
