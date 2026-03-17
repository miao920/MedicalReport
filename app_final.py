import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ================= 1. 核心配置（已补全） =================
# 这一行告诉程序：去 Streamlit 系统的“保险柜”里找名为 COZE_TOKEN 的钥匙
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
WORKFLOW_ID = "7617931269947506729"
BOT_ID = "7617094528700530742"  # 根据您之前提供的 SDK 信息补全
API_URL = "https://api.coze.cn/v1/workflow/run"

# ================= 2. 页面初始化设置 =================
st.set_page_config(
    layout="wide", 
    page_title="病生课堂实时学情反馈系统",
    page_icon="🏥"
)

# 自定义样式：让标签页更醒目
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

# 创建两个主功能区
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
                # 运行统计工作流
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                res_json = res.json()
                
                # 解析数据字段
                raw_data = res_json.get("data", "{}")
                # 兼容处理：如果 data 是字符串则解析为对象
                data_obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                report = data_obj.get("report_data", [])
                
                if report and len(report) > 0:
                    # 数据清洗：处理空字符串并转为整数
                    s = {k: (int(v) if (v and str(v).isdigit()) else 0) for k, v in report[0].items()}
                    
                    # --- A. 核心指标行 ---
                    m1, m2, m3, m4 = st.columns(4)
                    total = s.get('total_answers', 0)
                    m1.metric("已提交人数", f"{total} 人")
                    
                    # 计算及格率 (L1+L2+L3)
                    pass_total = s.get('level1',0) + s.get('level2',0) + s.get('level3',0)
                    rate = (pass_total / total * 100) if total > 0 else 0
                    m2.metric("综合及格率", f"{rate:.1f}%")
                    
                    m3.metric("需关注人数(L0)", f"{s.get('level0', 0)} 人")
                    
                    # 识别最薄弱环节
                    miss_dict = {"ADH": s.get('miss_adh',0), "ANP": s.get('miss_anp',0), "RAAS": s.get('miss_raas',0)}
                    weak_point = max(miss_dict, key=miss_dict.get) if total > 0 else "暂无"
                    m4.metric("最薄弱机制", weak_point)

                    st.markdown("---")

                    # --- B. 可视化图表行 ---
                    col_l, col_r = st.columns(2)
                    
                    with col_l:
                        # 饼图：成绩分布
                        df_pie = pd.DataFrame({
                            "评价等级": ["极差(L0)", "及格(L1)", "良好(L2)", "优秀(L3)"], 
                            "人数": [s.get('level0',0), s.get('level1',0), s.get('level2',0), s.get('level3',0)]
                        })
                        fig_pie = px.pie(df_pie, values='人数', names='评价等级', title="全班成绩等级分布",
                                       hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_pie, use_container_width=True)
                        
                    with col_r:
                        # 柱状图：知识点缺失统计
                        df_bar = pd.DataFrame({
                            "病生机制": ["ADH缺失", "ANP缺失", "RAAS缺失"], 
                            "未掌握人数": [s.get('miss_adh',0), s.get('miss_anp',0), s.get('miss_raas',0)]
                        })
                        fig_bar = px.bar(df_bar, x='病生机制', y='未掌握人数', title="知识点薄弱项排查",
                                       color='未掌握人数', color_continuous_scale='Reds')
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.warning("📊 暂未发现有效数据。请确保：1. 数据库不为空；2. 统计工作流已发布且勾选API。")
        except Exception as e:
            st.error(f"连接扣子失败: {str(e)}")

# ================= 4. 学生端：优化后的布局 =================
with tab2:
    st.header("📝 病理生理学练习批改")
    st.write("请在下方窗口中输入答案（若显示不全，请尝试上下滑动窗口内部）。")
    
    # 修改点：将 width 设为 100%，height 设为更适合手机的 80vh（视口高度）
    # 增加了一个容器样式确保在手机上能撑开
    chat_sdk_html = f"""
    <style>
        /* 强制让对话框撑满手机屏幕，不留白边 */
        #coze-chat-window {{
            width: 100%;
            height: 75vh !important; 
            border: 1px solid #f0f2f6;
            border-radius: 12px;
            overflow: hidden;
        }}
    </style>
    <div id="coze-chat-window"></div>
    <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
    <script>
      const client = new CozeWebSDK.WebChatClient({{
        config: {{
          bot_id: '{BOT_ID}',
        }},
        componentProps: {{
          title: '医学批改助手',
          layout: 'inline', // 保持内嵌模式
        }},
        el: document.getElementById('coze-chat-window'),
        auth: {{
          type: 'token',
          token: '{PERSONAL_ACCESS_TOKEN}',
          onRefreshToken: function () {{
            return '{PERSONAL_ACCESS_TOKEN}'
          }}
        }}
      }});
    </script>
    """
    
    # 修改点：将 components.html 的 height 设得比内部 div 高一点，防止出现两个滚动条
    components.html(chat_sdk_html, height=800)
    
    # 将 HTML 注入页面
    components.html(chat_sdk_html, height=720)
