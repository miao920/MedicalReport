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
    page_title="病生课堂实时学情反馈系统",
    page_icon="🏥"
)

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 50px; }
    .stTabs [data-baseweb="tab"] { 
        height: 60px; 
        font-size: 20px; 
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师端：全班统计大屏", "📝 学生端：智能批改练习"])

# ================= 3. 教师端：学情统计逻辑 =================
with tab1:
    st.title("🏥 班级实时学情分析看板")
    st.info("💡 操作指南：当学生完成提交后，点击下方按钮即可刷新最新的统计图表。")
    
    if st.button('🔄 刷新全班最新数据', type="primary"):
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            with st.spinner("正在连接扣子提取数据..."):
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                res_json = res.json()
                raw_data = res_json.get("data", "{}")
                data_obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                report = data_obj.get("report_data", [])
                
                if report and len(report) > 0:
                    s = {k: (int(v) if (v and str(v).isdigit()) else 0) for k, v in report[0].items()}
                    m1, m2, m3, m4 = st.columns(4)
                    total = s.get('total_answers', 0)
                    m1.metric("已提交人数", f"{total} 人")
                    pass_total = s.get('level1',0) + s.get('level2',0) + s.get('level3',0)
                    rate = (pass_total / total * 100) if total > 0 else 0
                    m2.metric("综合及格率", f"{rate:.1f}%")
                    m3.metric("需关注人数(L0)", f"{s.get('level0', 0)} 人")
                    miss_dict = {"ADH": s.get('miss_adh',0), "ANP": s.get('miss_anp',0), "RAAS": s.get('miss_raas',0)}
                    weak_point = max(miss_dict, key=miss_dict.get) if total > 0 else "暂无"
                    m4.metric("最薄弱机制", weak_point)
                    st.markdown("---")
                    col_l, col_r = st.columns(2)
                    with col_l:
                        df_pie = pd.DataFrame({
                            "评价等级": ["极差(L0)", "及格(L1)", "良好(L2)", "优秀(L3)"], 
                            "人数": [s.get('level0',0), s.get('level1',0), s.get('level2',0), s.get('level3',0)]
                        })
                        fig_pie = px.pie(df_pie, values='人数', names='评价等级', title="全班成绩等级分布",
                                       hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col_r:
                        df_bar = pd.DataFrame({
                            "病生机制": ["ADH缺失", "ANP缺失", "RAAS缺失"], 
                            "未掌握人数": [s.get('miss_adh',0), s.get('miss_anp',0), s.get('miss_raas',0)]
                        })
                        fig_bar = px.bar(df_bar, x='病生机制', y='未掌握人数', title="知识点薄弱项排查",
                                       color='未掌握人数', color_continuous_scale='Reds')
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.warning("📊 暂未发现有效数据。请检查数据库或工作流配置。")
        except Exception as e:
            st.error(f"连接失败: {str(e)}")

# ================= 4. 学生端：终极跳转版 =================
with tab2:
    st.header("📝 病理生理学练习批改")
    st.info("💡 提示：点击下方按钮将进入全屏答题模式，体验更佳。")
    
    # 采用扣子商店链接，确保手机全屏且输入法兼容
    coze_url = "https://www.coze.cn/store/bot/7617094528700530742"

    st.link_button("🚀 点击进入 AI 批改教室", coze_url, use_container_width=True, type="primary")
    st.write("")
    st.warning("⚠️ 答题须知：请输入学号后开始。完成后，老师在大屏点刷新即可看到结果。")
