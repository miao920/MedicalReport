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

# ================= 2. 页面初始化设置 =================
st.set_page_config(
    layout="wide", 
    page_title="病生实时学情反馈系统",
    page_icon="🏥"
)

# 强制注入 CSS：消除手机端白边，撑开聊天窗口高度
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-size: 18px; }
    /* 核心修改：强制让 iframe 容器在手机上足够高 */
    iframe { 
        height: 800px !important; 
        border-radius: 10px;
    }
    /* 减少页面顶部留白 */
    .block-container { padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计大屏", "📝 学生智能答题"])

# ================= 3. 教师端：学情统计 =================
with tab1:
    st.title("🏥 班级实时学情分析")
    if st.button('🔄 刷新全班最新数据', type="primary"):
        headers = {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}", "Content-Type": "application/json"}
        try:
            with st.spinner("数据提取中..."):
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                data_obj = json.loads(res.json().get("data", "{}"))
                report = data_obj.get("report_data", [])
                if report:
                    s = {k: (int(v) if (v and str(v).isdigit()) else 0) for k, v in report[0].items()}
                    m1, m2, m3 = st.columns(3)
                    m1.metric("已提交", f"{s.get('total_answers', 0)}人")
                    m2.metric("及格率", f"{(s.get('level1',0)+s.get('level2',0)+s.get('level3',0))/max(s.get('total_answers',1),1)*100:.1f}%")
                    m3.metric("薄弱环节", max({"ADH": s.get('miss_adh',0), "ANP": s.get('miss_anp',0), "RAAS": s.get('miss_raas',0)}, key=lambda x: 0))
                    
                    col_l, col_r = st.columns(2)
                    with col_l:
                        fig_pie = px.pie(names=["L0", "L1", "L2", "L3"], values=[s.get('level0',0), s.get('level1',0), s.get('level2',0), s.get('level3',0)], title="成绩分布")
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col_r:
                        fig_bar = px.bar(x=["ADH", "ANP", "RAAS"], y=[s.get('miss_adh',0), s.get('miss_anp',0), s.get('miss_raas',0)], title="知识点缺失")
                        st.plotly_chart(fig_bar, use_container_width=True)
        except: st.error("数据获取失败，请稍后再试")

# ================= 4. 学生端：【免登录 + 高度优化版】 =================
with tab2:
    st.markdown("### 📝 请开始你的分析")
    
    # 使用 SDK 方式嵌入，利用 TOKEN 实现免登录
    chat_sdk_code = f"""
    <div id="chat_container" style="height: 750px; width: 100%;"></div>
    <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
    <script>
      new CozeWebSDK.WebChatClient({{
        config: {{ bot_id: '{BOT_ID}' }},
        componentProps: {{ title: '病生批改助手', layout: 'inline' }},
        el: document.getElementById('chat_container'),
        auth: {{
          type: 'token',
          token: '{PERSONAL_ACCESS_TOKEN}',
          onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
        }}
      }});
    </script>
    """
    
    # 这里的 height=800 是解决“显示不全”的关键，它撑开了 Streamlit 的组件容器
    components.html(chat_sdk_code, height=800)
    
    st.info("👆 提示：如果看不到底部的输入框，请向上滑动一下页面。")
