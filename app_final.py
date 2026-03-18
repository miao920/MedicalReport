import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="课堂实时学情看板", layout="wide")

# =============================
# 飞书开放平台应用凭证
# =============================
FEISHU_APP_ID = "cli_a9302c7babf89cd4"
FEISHU_APP_SECRET = "15hzGFmO4NIai0j9dKIAodLhXzaoWLZm"

# =============================
# 多维表格信息
# =============================
APP_TOKEN = "J9qZba697aEirjsYiAQcodeUnue"
TABLE_ID = "tblryfcocA6mYGuL"

st.title("🏥 班级实时学情分析")


def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"获取 tenant_access_token 失败: {data}")

    return data["tenant_access_token"]


def search_all_records(tenant_access_token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/search"
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json"
    }

    all_items = []
    page_token = None

    while True:
        payload = {"page_size": 500}
        if page_token:
            payload["page_token"] = page_token

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise Exception(f"读取多维表格失败: {data}")

        items = data.get("data", {}).get("items", [])
        all_items.extend(items)

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")

        if not has_more:
            break

    return all_items


def normalize_cell_value(v):
    if v is None:
        return ""
    if isinstance(v, list):
        vals = []
        for item in v:
            if isinstance(item, dict):
                if "text" in item:
                    vals.append(str(item["text"]))
                elif "name" in item:
                    vals.append(str(item["name"]))
                else:
                    vals.append(json.dumps(item, ensure_ascii=False))
            else:
                vals.append(str(item))
        return ",".join(vals)
    if isinstance(v, dict):
        if "text" in v:
            return str(v["text"])
        if "name" in v:
            return str(v["name"])
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def parse_records_to_df(records):
    rows = []
    for item in records:
        fields = item.get("fields", {})
        row = {k: normalize_cell_value(v) for k, v in fields.items()}
        rows.append(row)
    return pd.DataFrame(rows)


def calc_report(df: pd.DataFrame):
    if df.empty:
        return {
            "total": 0,
            "l0": 0,
            "l1": 0,
            "l2": 0,
            "l3": 0,
            "adh": 0,
            "anp": 0,
            "raas": 0
        }

    score_series = (
        df["score_level"].fillna("").astype(str)
        if "score_level" in df.columns
        else pd.Series(dtype=str)
    )

    l0 = int((score_series == "Level0").sum())
    l1 = int((score_series == "Level1").sum())
    l2 = int((score_series == "Level2").sum())
    l3 = int((score_series == "Level3").sum())

    missing_series = (
        df["missing_points"].fillna("").astype(str)
        if "missing_points" in df.columns
        else pd.Series(dtype=str)
    )

    adh = int(missing_series.str.contains("ADH|adh", regex=True).sum())
    anp = int(missing_series.str.contains("ANP|anp", regex=True).sum())
    raas = int(missing_series.str.contains("RAAS|raas", regex=True).sum())

    return {
        "total": int(len(df)),
        "l0": l0,
        "l1": l1,
        "l2": l2,
        "l3": l3,
        "adh": adh,
        "anp": anp,
        "raas": raas
    }


if st.button("🔄 刷新统计看板", type="primary"):
    try:
        with st.spinner("正在从飞书读取真实数据..."):
            token = get_tenant_access_token()
            records = search_all_records(token)
            df = parse_records_to_df(records)
            s = calc_report(df)

        total = s["total"]
        l0 = s["l0"]
        l1 = s["l1"]
        l2 = s["l2"]
        l3 = s["l3"]
        adh = s["adh"]
        anp = s["anp"]
        raas = s["raas"]

        st.success("已读取飞书真实数据。")
        st.write("**当前统计结果：**")
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

        with st.expander("📋 查看原始表格数据"):
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 读取飞书失败：{str(e)}")

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
