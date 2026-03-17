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

# ================= 3. 学生端：正确的Web SDK方式 =================
with tab2:
    st.title("📝 学生答题")
    
    # 使用Coze Web SDK的正确方式
    chat_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
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
                font-size: 16px;
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
                                host: 'https://api.coze.cn',  // 使用API地址
                            }},
                            componentProps: {{
                                title: '病生题库智能体',
                                layout: 'inline',  // 内联模式
                                hideTitleBar: false,
                                height: '100%',
                                width: '100%',
                                style: {{
                                    borderRadius: '8px',
                                }}
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
                                <h3>加载失败</h3>
                                <p>${{error.message}}</p>
                                <button onclick="location.reload()">刷新重试</button>
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
    components.html(chat_html, height=700)
    
    # 添加备用方案
    with st.expander("📱 如果无法加载，请使用手机扫码"):
        bot_url = f"https://www.coze.cn/store/bot/{BOT_ID}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={bot_url}"
        st.image(qr_url, width=200)
        st.markdown(f"或点击链接：[{bot_url}]({bot_url})")
