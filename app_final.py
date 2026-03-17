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

# ================= 3. 教师端：学情统计逻辑 =================
with tab1:
    st.title("🏥 班级实时学情分析")
    
    if st.button('🔄 刷新全班最新数据', type="primary"):
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            with st.spinner("正在同步数据库最新记录..."):
                res = requests.post(API_URL, headers=headers, json={"workflow_id": WORKFLOW_ID})
                res_json = res.json()
                
                # 1. 深度解析：处理可能存在的字符串嵌套
                raw_data = res_json.get("data", "{}")
                data_obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                report = data_obj.get("report_data", [])
                
                if report and len(report) > 0:
                    # 获取第一条报表数据
                    raw_s = report[0]
                    
                    # 💡 核心修复：模糊匹配逻辑 (不分大小写，自动找关键词)
                    def get_val(keywords, default=0):
                        for k, v in raw_s.items():
                            if any(word.lower() in k.lower() for word in keywords):
                                return int(v) if str(v).isdigit() else 0
                        return default

                    # 重新提取数据（即便工作流改了名也能识别）
                    s = {
                        "total": get_val(["total", "sum", "count"]),
                        "l0": get_val(["level0", "l0"]),
                        "l1": get_val(["level1", "l1"]),
                        "l2": get_val(["level2", "l2"]),
                        "l3": get_val(["level3", "l3"]),
                        "adh": get_val(["adh", "miss_adh"]),
                        "anp": get_val(["anp", "miss_anp"]),
                        "raas": get_val(["raas", "miss_raas"])
                    }

                    # 2. 渲染核心指标
                    m1, m2, m3 = st.columns(3)
                    m1.metric("已提交人数", f"{s['total']} 人")
                    
                    pass_total = s['l1'] + s['l2'] + s['l3']
                    rate = (pass_total / s['total'] * 100) if s['total'] > 0 else 0
                    m2.metric("综合及格率", f"{rate:.1f}%")
                    
                    miss_list = {"ADH": s['adh'], "ANP": s['anp'], "RAAS": s['raas']}
                    weak = max(miss_list, key=miss_list.get) if s['total'] > 0 else "无"
                    m3.metric("最薄弱环节", weak)

                    # 3. 渲染可视化图表
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        fig_pie = px.pie(
                            names=["极差(L0)", "及格(L1)", "良好(L2)", "优秀(L3)"],
                            values=[s['l0'], s['l1'], s['l2'], s['l3']],
                            title="成绩分布状况",
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with c2:
                        fig_bar = px.bar(
                            x=["ADH缺失", "ANP缺失", "RAAS缺失"],
                            y=[s['adh'], s['anp'], s['raas']],
                            title="机制薄弱项排查",
                            labels={'x':'病生机制', 'y':'人数'},
                            color_discrete_sequence=['#FF4B4B']
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.warning("📊 连接成功，但后端数据库反馈目前提交记录为 0。请确认学生是否已成功点击“提交”。")
                    
        except Exception as e:
            st.error(f"❌ 数据解析失败: {str(e)}")

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
