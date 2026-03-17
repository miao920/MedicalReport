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

# ================= 2. 响应式CSS（移动端优先）=================
st.markdown("""
    <style>
    /* 重置所有默认边距 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* 主容器适配移动端 */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* 隐藏干扰元素 */
    header, footer, [data-testid="stHeader"], 
    [data-testid="stToolbar"], [data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* 确保主内容区域占满 */
    .main > div {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
    }
    
    /* Tab样式优化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 10px 0;
        background: white;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 8px 16px;
        background: #f0f2f6;
        border-radius: 20px;
    }
    
    /* 移动端特定优化 */
    @media only screen and (max-width: 768px) {
        /* 标题优化 */
        h1 {
            font-size: 24px !important;
            padding: 10px 15px !important;
            margin: 0 !important;
        }
        
        /* 按钮优化 */
        .stButton button {
            width: 100%;
            margin: 10px 0;
            border-radius: 8px;
            font-size: 16px;
            padding: 12px !important;
        }
        
        /* 刷新数据按钮特殊处理 */
        [data-testid="baseButton-primary"] {
            width: calc(100% - 30px) !important;
            margin: 10px 15px !important;
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

# ================= 3. 学生端：移动端完全适配版 =================
with tab2:
    # 使用媒体查询动态适配不同屏幕尺寸
    chat_sdk_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes, viewport-fit=cover">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            html, body {{
                width: 100%;
                height: 100%;
                overflow-x: hidden;
                background: transparent;
            }}
            
            /* 主容器 */
            #safe_wrapper {{
                width: 100%;
                height: 100vh;
                min-height: 700px;
                padding: 0;
                margin: 0;
                overflow: hidden;
                background: white;
            }}
            
            /* 对话容器 */
            #chat_box {{
                width: 100%;
                height: 100%;
                border: none;
                background: white;
            }}
            
            /* Coze SDK 内部样式覆盖 */
            .chat-wrapper {{
                width: 100% !important;
                height: 100% !important;
                border: none !important;
            }}
            
            /* 移动端适配 */
            @media screen and (max-width: 768px) {{
                #safe_wrapper {{
                    height: calc(100vh - 50px); /* 减去tab高度 */
                    min-height: 600px;
                    padding: 0;
                }}
                
                /* 强制让聊天界面占满 */
                .chat-container,
                .chat-messages,
                .chat-input-area {{
                    width: 100% !important;
                    max-width: 100% !important;
                    left: 0 !important;
                    right: 0 !important;
                }}
                
                /* 确保文字不被裁剪 */
                .message-content,
                .chat-bubble {{
                    word-wrap: break-word !important;
                    white-space: pre-wrap !important;
                    max-width: 100% !important;
                    padding: 12px !important;
                }}
            }}
            
            /* 横屏优化 */
            @media screen and (orientation: landscape) and (max-height: 600px) {{
                #safe_wrapper {{
                    height: 500px;
                }}
            }}
        </style>
    </head>
    <body>
        <div id="safe_wrapper">
            <div id="chat_box"></div>
        </div>
        
        <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js"></script>
        <script>
            // 检测是否为移动设备
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            
            // 配置基础选项
            const config = {{
                bot_id: '{BOT_ID}',
                host: 'https://www.coze.cn',
                // 移动端特定配置
                ...(isMobile ? {{
                    width: '100%',
                    height: '100%',
                    containerStyle: {{
                        padding: '0',
                        margin: '0'
                    }}
                }} : {{}})
            }};
            
            // 创建聊天实例
            const client = new CozeWebSDK.WebChatClient({{
                config: config,
                componentProps: {{ 
                    title: '病生批改助手',
                    layout: 'inline', // 使用内联布局
                    hideTitleBar: false,
                    hideHistory: true,
                    customStyle: {{
                        // 自定义样式覆盖
                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                        borderRadius: '0',
                        boxShadow: 'none',
                        // 移动端样式
                        ...(isMobile ? {{
                            messageFontSize: '16px',
                            inputFontSize: '16px', // 防止iOS自动缩放
                            buttonSize: '44px' // 增大点击区域
                        }} : {{}})
                    }}
                }},
                el: document.getElementById('chat_box'),
                auth: {{
                    type: 'token',
                    token: '{PERSONAL_ACCESS_TOKEN}',
                    onRefreshToken: () => '{PERSONAL_ACCESS_TOKEN}'
                }}
            }});
            
            // 动态调整高度
            function adjustHeight() {{
                const wrapper = document.getElementById('safe_wrapper');
                if (wrapper) {{
                    if (window.innerWidth <= 768) {{
                        // 移动端：减去标签栏高度和URL栏高度
                        wrapper.style.height = (window.innerHeight - 50) + 'px';
                    }} else {{
                        wrapper.style.height = '850px';
                    }}
                }}
            }}
            
            // 监听窗口大小变化
            window.addEventListener('resize', adjustHeight);
            window.addEventListener('orientationchange', function() {{
                setTimeout(adjustHeight, 100); // 旋转后延迟调整
            }});
            
            // 初始调整
            adjustHeight();
        </script>
    </body>
    </html>
    """
    
    # 使用更灵活的容器高度
    components.html(
        chat_sdk_code, 
        height=850,
        scrolling=False  # 禁用iframe滚动
    )
