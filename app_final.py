import streamlit as st
import streamlit.components.v1 as components

# ================= 1. 核心配置 =================
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
BOT_ID = "7617094528700530742"

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

# --- 教师端 ---
with tab1:
    st.title("🏥 班级学情统计")
    if st.button('🔄 刷新数据', type="primary"):
        st.success("数据已刷新")

# ================= 3. 学生端：字体放大版 =================
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
                                        font-size: 16px !important;
                                        line-height: 1.6 !important;
                                    }}
                                    
                                    /* 用户消息字体 */
                                    div[class*="message-user"],
                                    div[class*="client"] .markdown-body {{
                                        font-size: 16px !important;
                                    }}
                                    
                                    /* AI回复字体 */
                                    div[class*="message-bot"],
                                    div[class*="assistant"] .markdown-body {{
                                        font-size: 16px !important;
                                    }}
                                    
                                    /* 标题字体 */
                                    h1, h2, h3, h4 {{
                                        font-size: 20px !important;
                                        font-weight: 600 !important;
                                    }}
                                    
                                    /* 输入框字体 */
                                    input, textarea,
                                    div[class*="input"],
                                    div[class*="Input"],
                                    .rcw-new-message {{
                                        font-size: 16px !important;
                                        padding: 12px !important;
                                    }}
                                    
                                    /* 发送按钮 */
                                    button,
                                    div[class*="send"],
                                    .rcw-send {{
                                        font-size: 16px !important;
                                    }}
                                    
                                    /* 小标题强调 */
                                    strong, b {{
                                        font-weight: 700 !important;
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
                                        font-size: 16px !important;
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
                                            font-size: 18px !important;
                                            line-height: 1.7 !important;
                                        }}
                                        
                                        h1, h2, h3, h4 {{
                                            font-size: 22px !important;
                                        }}
                                        
                                        input, textarea {{
                                            font-size: 18px !important;
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
