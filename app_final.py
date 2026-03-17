import streamlit as st
import streamlit.components.v1 as components

# ================= 1. 核心配置 =================
PERSONAL_ACCESS_TOKEN = st.secrets["COZE_TOKEN"]
BOT_ID = "7617094528700530742"

st.set_page_config(layout="wide", page_title="病生实时学情系统")

# ================= 2. 极简CSS =================
st.markdown("""
    <style>
    /* 重置基本边距 */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    /* 隐藏干扰元素 */
    header, footer, [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 移动端适配 */
    @media only screen and (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            padding: 10px 5px;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 16px;
            padding: 8px 12px;
        }
        
        h1 {
            font-size: 22px !important;
            padding: 10px 15px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 教师统计", "📝 学生答题"])

# --- 教师端 ---
with tab1:
    st.title("🏥 班级学情统计")
    if st.button('🔄 刷新数据', type="primary"):
        st.success("数据已刷新")

# ================= 3. 学生端：最简版本 =================
with tab2:
    st.title("📝 学生答题")
    
    # 使用最简单的iframe方式嵌入Coze官方组件
    coze_embed_code = f"""
    <iframe
        src="https://www.coze.cn/store/bot/{BOT_ID}?panel=1&bid={BOT_ID}"
        style="width: 100%; height: 700px; border: none; border-radius: 8px;"
        allow="microphone; clipboard-write"
        referrerpolicy="no-referrer"
    >
    </iframe>
    """
    
    # 添加一个简单的包装器
    st.markdown("### 病生题库智能体")
    st.caption("直接在下方对话窗口中输入你的答案")
    
    # 嵌入iframe
    components.html(
        coze_embed_code,
        height=720,
        scrolling=True
    )
    
    # 添加使用说明
    with st.expander("📖 使用说明"):
        st.markdown("""
        1. 在下方对话框中直接输入你的答案
        2. 智能体会自动批改并给出反馈
        3. 所有对话记录会自动保存
        """)
