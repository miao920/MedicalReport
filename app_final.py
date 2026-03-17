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

# ================= 2. 基础CSS =================
st.markdown("""
    <style>
    /* 重置所有 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    /* 隐藏干扰元素 */
    header, footer, [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 教师端按钮优化 */
    .stButton button {
        width: calc(100% - 30px);
        margin: 10px 15px;
    }
    
    /* 移动端适配 */
    @media only screen and (max-width: 768px) {
        h1 {
            font-size: 22px !important;
            padding: 10px 15px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

# --- 教师端逻辑 ---
with tab1:
    st.title("🏥 班级学情统计")
    if st.button('🔄 刷新数据', type="primary"):
        st.write("数据已尝试更新，请检查下方图表")

# ================= 3. 学生端：强制重置版 =================
with tab2:
    chat_sdk_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            /* 彻底重置所有可能的限制 */
            * {{
                margin: 0 !important;
                padding: 0 !important;
                box-sizing: border-box !important;
                max-width: 100vw !important;
            }}
            
            html, body {{
                width: 100vw !important;
                height: 100vh !important;
                overflow-x: hidden !important;
                overflow-y: hidden !important;
                background: white;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
            }}
            
            /* 主容器 - 完全占满 */
            #main-container {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                width: 100% !important;
                height: 100% !important;
                overflow: hidden !important;
                background: white;
            }}
            
            /* 聊天容器 */
            #chat-container {{
                width: 100% !important;
                height: 100% !important;
                position: relative !important;
                overflow: hidden !important;
            }}
            
            /* 强制覆盖Coze内部样式 */
            .chat-wrapper,
            .chat-container,
            .coze-chat,
            .rcw-conversation-container,
            .rcw-widget-container,
            [class*="chat"],
            [class*="Chat"],
            [class*="coze"],
            [class*="Coze"] {{
                width: 100% !important;
                height: 100% !important;
                max-width: 100% !important;
                max-height: 100% !important;
                min-width: 0 !important;
                min-height: 0 !important;
                position: relative !important;
                left: 0 !important;
                right: 0 !important;
                top: 0 !important;
                bottom: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                transform: none !important;
            }}
            
            /* 消息区域 */
            [class*="message"],
            [class*="Message"],
            .rcw-messages-container,
            .messages-container {{
                width: 100% !important;
                max-width: 100% !important;
                padding: 10px !important;
                overflow-y: auto !important;
                -webkit-overflow-scrolling: touch !important;
            }}
            
            /* 消息气泡 */
            [class*="bubble"],
            [class*="Bubble"],
            .rcw-message {{
                max-width: 85% !important;
                word-wrap: break-word !important;
                white-space: pre-wrap !important;
            }}
            
            /* 输入区域 */
            [class*="input"],
            [class*="Input"],
            .rcw-sender,
            .sender-container {{
                width: 100% !important;
                max-width: 100% !important;
                padding: 8px !important;
                background: white !important;
                border-top: 1px solid #eee !important;
                position: absolute !important;
                bottom: 0 !important;
                left: 0 !important;
                right: 0 !important;
            }}
            
            /* 输入框 */
            [class*="text-input"],
            [class*="TextInput"],
            .rcw-new-message {{
                width: 100% !important;
                max-width: 100% !important;
                font-size: 16px !important;
                padding: 12px !important;
                border: 1px solid #ddd !important;
                border-radius: 8px !important;
            }}
            
            /* 发送按钮 */
            [class*="send"],
            [class*="Send"],
            .rcw-send {{
                width: auto !important;
                padding: 8px 16px !important;
            }}
            
            /* 确保所有文字可见 */
            p, span, div, h1, h2, h3 {{
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                white-space: normal !important;
                max-width: 100% !important;
            }}
        </style>
    </head>
    <body>
        <div id="main-container">
            <div id="chat-container"></div>
        </div>
        
        <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
        <script>
            (function() {{
                // 立即执行函数，确保在DOM加载前就设置好
                function overrideCozeStyles() {{
                    // 动态创建样式表覆盖
                    const style = document.createElement('style');
                    style.innerHTML = `
                        /* 暴力覆盖所有可能的Coze内部类 */
                        div[class*="chat"], div[class*="Chat"],
                        div[class*="message"], div[class*="Message"],
                        div[class*="container"], div[class*="Container"],
                        div[class*="wrapper"], div[class*="Wrapper"],
                        div[class*="widget"], div[class*="Widget"],
                        div[class*="conversation"], div[class*="Conversation"] {{
                            width: 100% !important;
                            max-width: 100% !important;
                            left: 0 !important;
                            right: 0 !important;
                            margin: 0 !important;
                            padding: 0 !important;
                            position: relative !important;
                        }}
                        
                        /* 确保文字区域不被裁剪 */
                        .rcw-messages-container,
                        div[class*="messages"] {{
                            height: calc(100% - 80px) !important;
                            overflow-y: auto !important;
                            padding: 16px !important;
                        }}
                        
                        /* 修复左侧文字 */
                        .rcw-message,
                        div[class*="message-client"],
                        div[class*="message-bot"] {{
                            margin: 8px 0 !important;
                            padding: 8px 12px !important;
                            max-width: 90% !important;
                        }}
                        
                        /* 输入区域固定在底部 */
                        div[class*="sender"],
                        div[class*="input-container"] {{
                            position: absolute !important;
                            bottom: 0 !important;
                            left: 0 !important;
                            right: 0 !important;
                            width: 100% !important;
                            background: white !important;
                            border-top: 1px solid #e0e0e0 !important;
                            padding: 8px !important;
                        }}
                    `;
                    document.head.appendChild(style);
                }}
                
                // 先覆盖样式
                overrideCozeStyles();
                
                // 检测是否为移动设备
                const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                
                // 配置选项
                const config = {{
                    bot_id: '{BOT_ID}',
                    host: 'https://www.coze.cn',
                    // 关键：使用inline模式
                    layout: 'inline'
                }};
                
                // 等待DOM加载完成
                setTimeout(function() {{
                    try {{
                        // 初始化聊天
                        const client = new CozeWebSDK.WebChatClient({{
                            config: config,
                            componentProps: {{ 
                                title: '病生题库智能体',
                                layout: 'inline',
                                hideTitleBar: false,
                                hideHistory: true,
                                // 自定义样式
                                customCss: `
                                    .chat-container {{ width: 100% !important; }}
                                    .message-container {{ padding: 10px !important; }}
                                `
                            }},
                            el: document.getElementById('chat-container'),
                            auth: {{
                                type: 'token',
                                token: '{PERSONAL_ACCESS_TOKEN}',
                                onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
                            }}
                        }});
                        
                        // 初始化后再强制覆盖一次样式
                        setTimeout(function() {{
                            overrideCozeStyles();
                            
                            // 查找所有可能包含文字的元素，确保它们可见
                            const allElements = document.querySelectorAll('*');
                            allElements.forEach(el => {{
                                if (el.children.length === 0 || el.textContent.trim()) {{
                                    // 这是叶子节点或包含文字的元素
                                    el.style.maxWidth = '100%';
                                    el.style.overflow = 'visible';
                                    el.style.whiteSpace = 'normal';
                                    el.style.wordWrap = 'break-word';
                                }}
                            }});
                        }}, 500);
                        
                    }} catch (e) {{
                        console.error('初始化失败:', e);
                        document.getElementById('chat-container').innerHTML = 
                            '<div style="padding:20px;color:red;">加载失败，请刷新页面</div>';
                    }}
                }}, 100);
            }})();
        </script>
    </body>
    </html>
    """
    
    # 使用固定的高度，但通过内部CSS控制
    components.html(
        chat_sdk_code, 
        height=800,
        scrolling=False
    )
