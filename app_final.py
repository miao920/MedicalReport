import streamlit as st
import streamlit.components.v1 as components
import requests  # 用于HTTP请求
import json      # 用于JSON解析
import pandas as pd  # 用于数据处理
import plotly.express as px  # 用于图表

# ================= 1. 核心配置 =================
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
WORKFLOW_ID = "7618540807894073354"
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

st.write("当前 WORKFLOW_ID:", WORKFLOW_ID)

# 创建三个标签页
tab1, tab_diag, tab2 = st.tabs(["🏥 班级实时学情分析", "🔬 数据连接诊断", "📝 学生答题"])

# ================= 教师端：学情看板（稳健兼容版） =================
with tab1:
    st.title("🏥 班级实时学情分析")

    if st.button("🔄 刷新统计看板", type="primary"):
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            with st.spinner("正在读取统计结果..."):
                payload = {
                    "workflow_id": "7618540807894073354",
                    "version": "latest",
                    "parameters": {}
                }

                res = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                res_data = res.json()

                st.write("### 🔍 调试信息")
                st.write("**API原始响应:**")
                st.json(res_data)

                if res_data.get("interrupt_data"):
                    st.error("统计工作流通过 API 调用时触发了飞书鉴权，暂时无法直接取回 report_data。")
                    st.info("先按固定统计结果展示，确认前端看板正常。")

                    demo_data = {
                        "total": 3,
                        "l0": 0,
                        "l1": 2,
                        "l2": 1,
                        "l3": 0,
                        "adh": 1,
                        "anp": 1,
                        "raas": 3
                    }
                    s = demo_data
                else:
                    raw = res_data.get("data", "{}")
                    outer = json.loads(raw) if isinstance(raw, str) else raw
                    inner = outer.get("data", {})
                    inner = json.loads(inner) if isinstance(inner, str) else inner
                    s = inner.get("report_data", {})

                def to_int(v, default=0):
                    try:
                        if v is None or v == "":
                            return default
                        return int(float(v))
                    except Exception:
                        return default

                total = to_int(s.get("total", 0))
                l0 = to_int(s.get("l0", 0))
                l1 = to_int(s.get("l1", 0))
                l2 = to_int(s.get("l2", 0))
                l3 = to_int(s.get("l3", 0))
                adh = to_int(s.get("adh", 0))
                anp = to_int(s.get("anp", 0))
                raas = to_int(s.get("raas", 0))

                st.write("**当前用于展示的统计结果：**")
                st.json(s)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("累计提交人数", f"{total} 人")

                with col2:
                    pass_n = l1 + l2 + l3
                    st.metric("及格人数", f"{pass_n} 人")

                with col3:
                    pass_rate = (pass_n / total * 100) if total > 0 else 0
                    st.metric("及格率", f"{pass_rate:.1f}%")

                st.markdown("---")

                chart1, chart2 = st.columns(2)

                with chart1:
                    fig_pie = px.pie(
                        names=["L0(不及格)", "L1(及格)", "L2(良好)", "L3(优秀)"],
                        values=[l0, l1, l2, l3],
                        title="🏆 成绩等级分布",
                        hole=0.4
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                with chart2:
                    fig_bar = px.bar(
                        x=["ADH缺失", "ANP缺失", "RAAS缺失"],
                        y=[adh, anp, raas],
                        title="🔍 关键知识点薄弱项统计",
                        labels={"x": "知识点", "y": "人数"}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                with st.expander("📋 查看详细统计数据"):
                    st.json({
                        "total": total,
                        "l0": l0,
                        "l1": l1,
                        "l2": l2,
                        "l3": l3,
                        "adh": adh,
                        "anp": anp,
                        "raas": raas
                    })

        except Exception as e:
            st.error(f"❌ 教师端渲染失败: {str(e)}")
# ================= 5. 学生端（保持不变） =================
with tab2:
    st.title("📝 学生答题")
    
    # 使用Coze Web SDK，调大字体
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
    
    # 显示聊天界面
    components.html(chat_html, height=750)
