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

# 创建三个标签页
tab1, tab_diag, tab2 = st.tabs(["🏥 班级实时学情分析", "🔬 数据连接诊断", "📝 学生答题"])

# ================= 3.教师端：精准对接版 =================
with tab1:
    st.title("🏥 班级实时学情分析")
    if st.button('🔄 刷新统计图表', type="primary"):
        headers = {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}", "Content-Type": "application/json"}
        try:
            with st.spinner("正在从云端调取 12 条最新统计..."):
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                res_data = res.json()
                
                # 解析扣子返回的 JSON 字符串
                raw_content = res_data.get("data", "{}")
                data_obj = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
                report = data_obj.get("report_data", [])
                
                if report and len(report) > 0:
                    # 清洗函数：将 "" 或 null 转为 0
                    def clean(v):
                        if not v or str(v).strip() == "": return 0
                        return int(v) if str(v).isdigit() else 0

                    s = {k: clean(v) for k, v in report[0].items()}
                    total = s.get('total_answers', 0)
                    
                    if total > 0:
                        st.balloons() # 庆祝数据接通！
                        m1, m2, m3 = st.columns(3)
                        m1.metric("累计提交", f"{total} 人")
                        pass_n = s.get('level1',0) + s.get('level2',0) + s.get('level3',0)
                        m2.metric("及格以上人数", f"{pass_n} 人")
                        m3.metric("及格率", f"{(pass_n/total*100):.1f}%")
                        
                        st.markdown("---")
                        c1, c2 = st.columns(2)
                        with c1:
                            fig_pie = px.pie(names=["L0(极差)","L1(及格)","L2(良好)","L3(优秀)"], 
                                           values=[s.get('level0',0), s.get('level1',0), s.get('level2',0), s.get('level3',0)], 
                                           title="成绩等级分布", hole=0.3)
                            st.plotly_chart(fig_pie, use_container_width=True)
                        with c2:
                            fig_bar = px.bar(x=["ADH缺失", "ANP缺失", "RAAS缺失"], 
                                           y=[s.get('miss_adh',0), s.get('miss_anp',0), s.get('miss_raas',0)], 
                                           title="机制薄弱环节排查", color_discrete_sequence=['#F63366'])
                            st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.warning("⚠️ 接口已发布，但数据库反馈统计人数仍为 0，请检查 SQL 节点连接的表是否正确。")
                else:
                    st.error("❌ 没能从 report_data 中读到内容，请检查诊断页。")
        except Exception as e:
            st.error(f"渲染出错: {e}")

# ================= 4. 新增：数据连接诊断 TAB =================
with tab_diag:
    st.header("🔬 后端数据链路测试")
    st.write("当教师端不出图时，请点此按钮排查原因。")
    
    if st.button('🔍 执行深度诊断'):
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        with st.status("正在联系扣子工作流...", expanded=True) as status:
            try:
                # 步骤 1: 发送请求
                st.write("正在发送 API 请求至 Coze...")
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                res_json = res.json()
                
                # 步骤 2: 显示原始报文
                st.write("✅ 接口通讯成功，收到原始包裹：")
                st.code(json.dumps(res_json, indent=2, ensure_ascii=False))
                
                # 步骤 3: 解析内容
                raw_data = res_json.get("data", "{}")
                data_obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                report = data_obj.get("report_data", None)
                
                if report:
                    st.success(f"🎊 抓取成功！发现 {len(report)} 条报表记录。")
                    st.write("报表详情：", report)
                else:
                    st.warning("⚠️ 接口通了，但 report_data 字段是空的。请检查扣子工作流是否正确查询了数据库。")
                
                status.update(label="诊断完成", state="complete")
            except Exception as e:
                st.error(f"❌ 诊断过程崩溃: {str(e)}")
                status.update(label="诊断出错", state="error")

# ================= 5. 学生端：字体放大版 =================
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
