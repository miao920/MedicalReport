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
            with st.spinner("正在从云端读取统计结果..."):
                # 1. 构建请求参数
                payload = {
                    "workflow_id": WORKFLOW_ID,
                    "version": "latest",
                    "parameters": {}
                }

                # 2. 调试信息
                st.write("### 🔍 调试信息")
                st.write("**发送的请求:**")
                st.json(payload)

                # 3. 调用 API
                res = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                res.raise_for_status()
                res_data = res.json()

                st.write("**API原始响应:**")
                st.json(res_data)

                # ========== 工具函数 ==========
                def try_json_load(x):
                    """如果是 JSON 字符串就解析，否则原样返回"""
                    if isinstance(x, str):
                        x = x.strip()
                        if not x:
                            return {}
                        try:
                            return json.loads(x)
                        except Exception:
                            return x
                    return x

                def normalize_obj(obj):
                    """递归解析可能嵌套的 JSON 字符串"""
                    obj = try_json_load(obj)

                    if isinstance(obj, dict):
                        return {k: normalize_obj(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [normalize_obj(v) for v in obj]
                    else:
                        return obj

                def pick_stats(obj):
                    """
                    从多种可能的返回结构里提取统计结果
                    兼容：
                    1) {"report_data": {...}}
                    2) {"total_answers": ..., "level0": ...}
                    3) {"output": {...}}
                    4) {"data": {...}}
                    """
                    if not isinstance(obj, dict):
                        return {}

                    # 优先 1：标准包装 report_data
                    if isinstance(obj.get("report_data"), dict):
                        return obj["report_data"]

                    # 优先 2：扁平统计字段直接在当前层
                    flat_keys = {"total_answers", "level0", "level1", "level2", "level3",
                                 "miss_adh", "miss_anp", "miss_raas",
                                 "total", "l0", "l1", "l2", "l3", "adh", "anp", "raas"}
                    if any(k in obj for k in flat_keys):
                        return obj

                    # 递归尝试 output / data / outputList[0]
                    for key in ["output", "data", "result"]:
                        if key in obj and isinstance(obj[key], dict):
                            found = pick_stats(obj[key])
                            if found:
                                return found

                    if isinstance(obj.get("outputList"), list) and len(obj["outputList"]) > 0:
                        first_item = obj["outputList"][0]
                        if isinstance(first_item, dict):
                            found = pick_stats(first_item)
                            if found:
                                return found

                    return {}

                def to_int(v, default=0):
                    try:
                        if v is None or v == "":
                            return default
                        return int(float(v))
                    except Exception:
                        return default

                # 4. 解析 data 字段
                raw_content = res_data.get("data", {})
                st.write("**data字段原始内容:**", raw_content)

                data_obj = normalize_obj(raw_content)

                st.write("**data字段解析后内容:**")
                st.json(data_obj)

                # 5. 提取统计结果
                s = pick_stats(data_obj)

                st.write("**提取到的统计结果对象:**")
                st.json(s)

                # 6. 同时兼容两套字段命名
                total = to_int(s.get("total", s.get("total_answers", 0)))
                l0 = to_int(s.get("l0", s.get("level0", 0)))
                l1 = to_int(s.get("l1", s.get("level1", 0)))
                l2 = to_int(s.get("l2", s.get("level2", 0)))
                l3 = to_int(s.get("l3", s.get("level3", 0)))

                adh = to_int(s.get("adh", s.get("miss_adh", 0)))
                anp = to_int(s.get("anp", s.get("miss_anp", 0)))
                raas = to_int(s.get("raas", s.get("miss_raas", 0)))

                st.write("**兼容解析后的关键指标:**")
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

                # 7. 显示看板
                if total > 0:
                    st.balloons()

                    # --- 第一行：核心指标卡 ---
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

                    # --- 第二行：可视化图表 ---
                    chart1, chart2 = st.columns(2)

                    with chart1:
                        fig_pie = px.pie(
                            names=["L0(不及格)", "L1(及格)", "L2(良好)", "L3(优秀)"],
                            values=[l0, l1, l2, l3],
                            title="🏆 成绩等级分布",
                            hole=0.4,
                            color_discrete_sequence=px.colors.sequential.RdBu
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                    with chart2:
                        fig_bar = px.bar(
                            x=["ADH缺失", "ANP缺失", "RAAS缺失"],
                            y=[adh, anp, raas],
                            title="🔍 关键知识点薄弱项统计",
                            labels={"x": "知识点", "y": "人数"},
                            color_discrete_sequence=["#F63366"]
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)

                    # --- 第三行：详细数据表格 ---
                    with st.expander("📋 查看详细统计数据"):
                        st.write("### 完整统计结果（原始提取对象）")
                        st.json(s)

                        st.write("### 标准化后的统计结果")
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

                else:
                    st.warning(
                        "⚠️ 当前统计人数为 0。\n\n"
                        "请重点查看上面的三段调试信息：\n"
                        "1. API原始响应\n"
                        "2. data字段原始内容\n"
                        "3. 提取到的统计结果对象\n"
                    )

        except requests.exceptions.RequestException as e:
            st.error(f"❌ API请求失败: {str(e)}")
            st.error("请检查：\n1. Coze Token是否有效\n2. Workflow ID是否正确\n3. 网络连接是否正常")

        except Exception as e:
            st.error(f"❌ 渲染看板失败: {str(e)}")
            st.error("请检查工作流返回结构是否为合法 JSON，或把上方调试信息发出来继续排查。")

# ================= 4. 诊断 TAB（已修复） =================
with tab_diag:
    st.header("🔬 后端数据链路测试")
    st.write("当教师端显示人数为0时，请点此按钮排查原因。")
    
    if st.button('🔍 执行深度诊断'):
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        with st.status("正在联系扣子工作流...", expanded=True) as status:
            try:
                # 修复1：添加参数
                payload = {
                    "workflow_id": WORKFLOW_ID,
                    "parameters": {"input_list": []}
                }
                
                # 步骤 1: 发送请求
                st.write("正在发送 API 请求至 Coze...")
                res = requests.post(API_URL, headers=headers, json=payload)
                res_json = res.json()
                
                # 步骤 2: 显示原始报文
                st.write("✅ 接口通讯成功，收到原始包裹：")
                st.code(json.dumps(res_json, indent=2, ensure_ascii=False))
                
                # 步骤 3: 解析内容
                raw_data = res_json.get("data", "{}")
                data_obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                
                # 修复2：使用 report_data
                report = data_obj.get("report_data", None)
                
                if report:
                    st.success(f"🎊 抓取成功！统计结果如下：")
                    st.write("报表详情：", report)
                    
                    # 添加智能诊断建议
                    if report.get("total", 0) == 0:
                        st.warning("🔍 **诊断建议**:\n"
                                  "1. 请检查工作流中的「SQL查询节点」是否返回了数据\n"
                                  "2. 登录Coze平台，打开下方的debug_url查看详细执行日志\n"
                                  f"3. Debug链接: {res_json.get('debug_url', '无')}")
                else:
                    st.warning("⚠️ 接口通了，但 report_data 字段是空的。")
                
                status.update(label="诊断完成", state="complete")
            except Exception as e:
                st.error(f"❌ 诊断过程崩溃: {str(e)}")
                status.update(label="诊断出错", state="error")

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
