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

# ⚡ 核心修复：强制删除左右白边，确保手机端满屏显示 ⚡
st.markdown("""
    <style>
    /* 1. 彻底清空左右边距 */
    .block-container {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    /* 2. 隐藏 Streamlit 自带的 Padding */
    .main .block-container { padding-top: 1rem !important; }
    /* 3. 强制 iframe 宽度 100% 且不溢出 */
    iframe {
        width: 100% !important;
        min-width: 100% !important;
        height: 800px !important;
    }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师端", "📝 学生端"])

# --- 教师端略 (保持原样即可) ---
with tab1:
    st.title("🏥 班级学情统计")
    st.write("点击刷新查看结果")

# ================= 2. 学生端：全屏且不切边版 =================
with tab2:
    # 使用 container 控制宽度，确保内部 SDK 不会横向溢出
    chat_sdk_code = f"""
    <div id="chat_box" style="width: 100vw; height: 750px; overflow-x: hidden;"></div>
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
        /* 强制隐藏 SDK 可能产生的横向滚动条 */
        body {{ margin: 0; overflow-x: hidden; }}
    </style>
    """
    
    # 将组件宽度设为真正意义上的满屏
    components.html(chat_sdk_code, height=800, scrolling=False)

    st.warning("💡 提示：若字迹过小，可双指放大。答题后请告知老师刷新大屏。")
