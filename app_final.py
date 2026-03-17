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

# ⚡ 暴力右移 CSS：针对左侧切边进行大幅度物理位移 ⚡
st.markdown("""
    <style>
    /* 1. 强制全局容器不准有任何负偏移 */
    .block-container {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin-left: 0.5rem !important; /* 给左侧加一个基础保底边距 */
        max-width: 95vw !important;
    }
    
    /* 2. 核心：将 iframe 物理向右推 25px，并同步缩小宽度防止右侧溢出 */
    iframe {
        position: relative !important;
        left: 25px !important;  /* 强行向右推 25 像素 */
        width: calc(100vw - 50px) !important; /* 总宽度减去偏移和安全距离 */
        height: 850px !important;
        border: none !important;
    }

    /* 隐藏所有干扰元素 */
    header, footer, [data-testid="stHeader"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

# --- 教师端逻辑 ---
with tab1:
    st.title("🏥 班级学情统计")
    if st.button('🔄 刷新数据', type="primary"):
        st.write("数据已尝试更新，请检查下方图表")

# ================= 2. 学生端：大幅度右移适配版 =================
with tab2:
    # 在内层 HTML 再次强制加 padding 保护左侧
    chat_sdk_code = f"""
    <div id="safe_wrapper" style="padding-left: 15px; width: 100%; height: 820px; box-sizing: border-box; overflow: hidden;">
        <div id="chat_box" style="width: 100%; height: 100%;"></div>
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
    
    # 高度给到 850，确保底部输入框完全可见
    components.html(chat_sdk_code, height=850)
