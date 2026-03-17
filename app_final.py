import streamlit as st
import streamlit.components.v1 as components
import requests  # 用于HTTP请求
import json      # 用于JSON解析
import pandas as pd  # 用于数据处理
import plotly.express as px  # 用于图表

# ================= 1. 核心配置 =================
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
WORKFLOW_ID = "7617931269947506729"
BOT_ID = "7617094528700530742"
API_URL = "https://api.coze.cn/v1/workflow/run"

st.set_page_config(layout="wide", page_title="病生实时学情系统")

# ================= 2. 基础CSS =================
st.markdown("""
    <style>
    .block-container {
        padding: 1rem 1rem !important;
        max-width: 100% !important;
    }
    
    /* 移动端优化 */
    @media only screen and (max-width: 768px) {
        .block-container {
            padding: 0.5rem !important;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h3 {
            font-size: 1.2rem !important;
        }
    }
    
    /* 隐藏干扰元素 */
    header, footer, [data-testid="stHeader"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

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
                            "生理机制": ["ADH缺失", "ANP缺失", "RAAS缺失"], 
                            "未掌握人数": [s.get('miss_adh',0), s.get('miss_anp',0), s.get('miss_raas',0)]
                        })
                        fig_bar = px.bar(df_bar, x='生理机制', y='未掌握人数', title="知识点薄弱项排查",
                                       color='未掌握人数', color_continuous_scale='Reds')
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.warning("📊 暂未发现有效数据。请确保：1. 数据库不为空；2. 统计工作流已发布且勾选API。")
        except Exception as e:
            st.error(f"连接扣子失败: {str(e)}")

# ================= 4. 学生端：字体放大版 =================
with tab2:
    st.title("📝 学生答题")
    
    # 使用Coze Web SDK的正确方式，并调大字体
    chat_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
        <style>
            body, html {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            
            #coze-container {{
                width: 100%;
                height: 100vh;
                min-height: 600px;
                border: none;
                background: white;
            }}
            
            /* 加载状态 */
            .loading {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                font-size: 18px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div id="coze-container">
            <div class="loading">正在加载智能体...</div>
        </div>

        <!-- 加载Coze SDK -->
        <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
        
        <script>
            (function() {{
                // 等待SDK加载完成
                function initCoze() {{
                    if (typeof CozeWebSDK === 'undefined') {{
                        setTimeout(initCoze, 100);
                        return;
                    }}
                    
                    try {{
                        // 创建聊天实例
                        const client = new CozeWebSDK.WebChatClient({{
                            config: {{
                                bot_id: '{BOT_ID}',
                                host: 'https://api.coze.cn',
                            }},
                            componentProps: {{
                                title: '病生题库智能体',
                                layout: 'inline',
                                hideTitleBar: false,
                                height: '100%',
                                width: '100%',
                                style: {{
                                    borderRadius: '8px',
                                }},
                                // 添加自定义CSS来调大字体
                                customCss: `
                                    /* 全局字体调大 */
                                    .markdown-body,
                                    .message-content,
                                    .chat-bubble,
                                    .rcw-message,
                                    div[class*="message"] {{
                                        font-size: 24px !important;
                                        line-height: 1.7 !important;
                                    }}
                                    
                                    /* 用户消息字体 */
                                    div[class*="message-user"],
                                    div[class*="client"] .markdown-body {{
                                        font-size: 24px !important;
                                    }}
                                    
                                    /* AI回复字体 */
                                    div[class*="message-bot"],
                                    div[class*="assistant"] .markdown-body {{
                                        font-size: 24px !important;
                                    }}
                                    
                                    /* 标题字体 */
                                    h1, h2, h3, h4 {{
                                        font-size: 24px !important;
                                        font-weight: 600 !important;
                                    }}
                                    
                                    /* 输入框字体 */
                                    input, textarea,
                                    div[class*="input"],
                                    div[class*="Input"],
                                    .rcw-new-message {{
                                        font-size: 24px !important;
                                        padding: 15px !important;
                                    }}
                                    
                                    /* 发送按钮 */
                                    button,
                                    div[class*="send"],
                                    .rcw-send {{
                                        font-size: 18px !important;
                                    }}
                                    
                                    /* 提示文字 */
                                    .rcw-timestamp,
                                    div[class*="timestamp"] {{
                                        font-size: 14px !important;
                                        color: #999 !important;
                                    }}
                                    
                                    /* AI点评区域特殊处理 */
                                    div[class*="ai-feedback"],
                                    div[class*="evaluation"] {{
                                        font-size: 24px !important;
                                        background-color: #f5f5f5 !important;
                                        padding: 15px !important;
                                        border-radius: 8px !important;
                                    }}
                                `,
                                // 桌面端字体更大
                                ...(window.innerWidth > 768 ? {{
                                    customCss: `
                                        .markdown-body,
                                        .message-content {{
                                            font-size: 20px !important;
                                            line-height: 1.7 !important;
                                        }}
                                        
                                        h1, h2, h3, h4 {{
                                            font-size: 24px !important;
                                        }}
                                        
                                        input, textarea {{
                                            font-size: 20px !important;
                                        }}
                                    `
                                }} : {{}})
                            }},
                            el: document.getElementById('coze-container'),
                            auth: {{
                                type: 'token',
                                token: '{PERSONAL_ACCESS_TOKEN}',
                                onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
                            }}
                        }});
                        
                        // 移除加载提示
                        document.querySelector('.loading')?.remove();
                        
                    }} catch (error) {{
                        console.error('Coze初始化失败:', error);
                        document.getElementById('coze-container').innerHTML = 
                            `<div style="padding:20px;color:red;">
                                <h3 style="font-size:20px;">加载失败</h3>
                                <p style="font-size:16px;">${{error.message}}</p>
                                <button onclick="location.reload()" style="font-size:16px;padding:10px 20px;">刷新重试</button>
                            </div>`;
                    }}
                }}
                
                initCoze();
            }})();
        </script>
    </body>
    </html>
    """
    
    # 显示聊天界面 - 调高了高度
    components.html(chat_html, height=750)
