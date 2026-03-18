import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="课堂实时学情看板", layout="wide")

# =============================
# 飞书开放平台自建应用凭证
# =============================
FEISHU_APP_ID = "cli_a9302c7babf89cd4".strip()
FEISHU_APP_SECRET = "15hzGFmO4NIai0j9dKIAodLhXzaoWLZm".strip()

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
    data = resp.json()

    if resp.status_code != 200 or data.get("code") != 0:
        raise Exception(f"获取 tenant_access_token 失败：{data}")

    token = data.get("tenant_access_token")
    if not token:
        raise Exception(f"tenant_access_token 为空：{data}")

    return token


def search_all_records(access_token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    all_items = []
    page_token = None

    while True:
        payload = {"page_size": 500}
        if page_token:
            payload["page_token"] = page_token

        resp = requests.post(url, headers=headers, json=payload, timeout=30)

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        if resp.status_code != 200:
            raise Exception(f"查询记录 HTTP 失败：{data}")

        if data.get("code") != 0:
            raise Exception(f"查询记录接口失败：{data}")

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
        return "；".join(vals)

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
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def calc_report(df: pd.DataFrame):
    if df.empty:
        return {
            "total": 0,
            "l0": 0,
            "l1": 0,
            "l2": 0,
            "l3": 0,
            "kp1": 0,
            "kp2": 0,
            "kp3": 0,
            "kp4": 0,
            "kp5": 0,
            "kp6": 0,
            "kp7": 0,
            "kp8": 0,
            "kp1_rate": 0,
            "kp2_rate": 0,
            "kp3_rate": 0,
            "kp4_rate": 0,
            "kp5_rate": 0,
            "kp6_rate": 0,
            "kp7_rate": 0,
            "kp8_rate": 0,
            "excellent_rate": 0,
            "top_missing_points": [],
            "best_examples": [],
            "mid_examples": [],
            "weak_examples": []
        }

    score_series = (
        df["score_level"].fillna("").astype(str)
        if "score_level" in df.columns
        else pd.Series(dtype=str)
    )

    total = int(len(df[df.notna().any(axis=1)]))

    l0 = int((score_series == "Level0").sum())
    l1 = int((score_series == "Level1").sum())
    l2 = int((score_series == "Level2").sum())
    l3 = int((score_series == "Level3").sum())

    def contains_any(series, keywords):
        pattern = "|".join(keywords)
        return int(series.fillna("").astype(str).str.contains(pattern, regex=True).sum())

    hit_series = (
        (
            df.get("knowledge_hit", pd.Series(dtype=str)).fillna("").astype(str)
            + " "
            + df.get("user_answer", pd.Series(dtype=str)).fillna("").astype(str)
        )
        if not df.empty else pd.Series(dtype=str)
    )

    missing_series = (
        df["missing_points"].fillna("").astype(str)
        if "missing_points" in df.columns
        else pd.Series(dtype=str)
    )

    kp1 = contains_any(hit_series, ["肾小球滤过膜通透性增高", "滤过膜通透性增高", "肾小球通透性增高", "滤过膜损伤"])
    kp2 = contains_any(hit_series, ["大量蛋白尿", "蛋白尿", "尿蛋白"])
    kp3 = contains_any(hit_series, ["低白蛋白血症", "低蛋白血症", "白蛋白降低", "血浆白蛋白降低"])
    kp4 = contains_any(hit_series, ["血浆胶体渗透压下降", "胶体渗透压下降", "血浆胶体渗透压降低", "胶体渗透压降低"])
    kp5 = contains_any(hit_series, ["有效循环血量减少", "有效血容量减少", "循环血量减少", "血容量减少"])
    kp6 = contains_any(hit_series, ["RAAS", "raas", "RAAS系统激活", "肾素-血管紧张素-醛固酮系统", "肾素血管紧张素醛固酮系统"])
    kp7 = contains_any(hit_series, ["肾血管收缩", "肾小球滤过率降低", "滤过率降低", "GFR降低", "gfr降低"])
    kp8 = contains_any(hit_series, ["醛固酮", "抗利尿激素", "ADH", "adh", "肾小管钠水重吸收增加", "钠水重吸收增加", "钠水潴留", "水钠潴留"])

    # 常见失分点 Top3
    missing_counter = {}
    if "missing_points" in df.columns:
        for raw in df["missing_points"].fillna("").astype(str):
            if not raw.strip():
                continue
            parts = (
                raw.replace("；", "，")
                .replace(";", "，")
                .replace("|", "，")
                .split("，")
            )
            for p in parts:
                point = p.strip()
                if point:
                    missing_counter[point] = missing_counter.get(point, 0) + 1

    top_missing_points = sorted(
        missing_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    top_missing_points = [{"point": k, "count": v} for k, v in top_missing_points]

    # 代表性答案
    view_cols = []
    for col in ["student_id", "score_level", "user_answer", "knowledge_hit", "missing_points", "timestamp"]:
        if col in df.columns:
            view_cols.append(col)

    df_view = df[view_cols].copy() if view_cols else df.copy()

    def pick_examples(level_name, max_n=2):
        if "score_level" not in df_view.columns:
            return []

        sub = df_view[df_view["score_level"].astype(str) == level_name].copy()
        if sub.empty:
            return []

        if "user_answer" in sub.columns:
            sub["answer_len"] = sub["user_answer"].fillna("").astype(str).apply(len)
            sub = sub.sort_values("answer_len", ascending=False)

        examples = []
        for _, row in sub.head(max_n).iterrows():
            examples.append({
                "student_id": str(row["student_id"]) if "student_id" in row and pd.notna(row["student_id"]) else "未提供",
                "score_level": str(row["score_level"]) if "score_level" in row and pd.notna(row["score_level"]) else "",
                "user_answer": str(row["user_answer"]) if "user_answer" in row and pd.notna(row["user_answer"]) else "",
                "knowledge_hit": str(row["knowledge_hit"]) if "knowledge_hit" in row and pd.notna(row["knowledge_hit"]) else "",
                "missing_points": str(row["missing_points"]) if "missing_points" in row and pd.notna(row["missing_points"]) else "",
                "timestamp": str(row["timestamp"]) if "timestamp" in row and pd.notna(row["timestamp"]) else ""
            })
        return examples

    best_examples = (pick_examples("Level3", 2) + pick_examples("Level2", 1))[:2]
    mid_examples = (pick_examples("Level2", 1) + pick_examples("Level1", 2))[:2]
    weak_examples = (pick_examples("Level0", 2) + pick_examples("Level1", 1))[:2]

    return {
        "total": total,
        "l0": l0,
        "l1": l1,
        "l2": l2,
        "l3": l3,
        "kp1": kp1,
        "kp2": kp2,
        "kp3": kp3,
        "kp4": kp4,
        "kp5": kp5,
        "kp6": kp6,
        "kp7": kp7,
        "kp8": kp8,
        "kp1_rate": round(kp1 / total * 100, 1) if total > 0 else 0,
        "kp2_rate": round(kp2 / total * 100, 1) if total > 0 else 0,
        "kp3_rate": round(kp3 / total * 100, 1) if total > 0 else 0,
        "kp4_rate": round(kp4 / total * 100, 1) if total > 0 else 0,
        "kp5_rate": round(kp5 / total * 100, 1) if total > 0 else 0,
        "kp6_rate": round(kp6 / total * 100, 1) if total > 0 else 0,
        "kp7_rate": round(kp7 / total * 100, 1) if total > 0 else 0,
        "kp8_rate": round(kp8 / total * 100, 1) if total > 0 else 0,
        "excellent_rate": round((l2 + l3) / total * 100, 1) if total > 0 else 0,
        "top_missing_points": top_missing_points,
        "best_examples": best_examples,
        "mid_examples": mid_examples,
        "weak_examples": weak_examples
    }


st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 18px;
    border-radius: 16px;
}
div[data-testid="metric-container"] label {
    font-size: 22px !important;
    font-weight: 700 !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 34px !important;
    font-weight: 800 !important;
}
.big-title {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 10px;
}
.case-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 14px;
}
.case-title {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 8px;
}
.case-meta {
    font-size: 16px;
    color: #374151;
    margin-bottom: 8px;
}
.case-answer {
    font-size: 17px;
    line-height: 1.7;
    color: #111827;
    margin-bottom: 8px;
}
.case-tag {
    font-size: 15px;
    color: #4b5563;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


if st.button("🔄 刷新统计看板", type="primary"):
    try:
        with st.spinner("正在从飞书读取真实数据..."):
            access_token = get_tenant_access_token()
            records = search_all_records(access_token)
            df = parse_records_to_df(records)
            df_valid = df[df.notna().any(axis=1)].copy() if not df.empty else df
            s = calc_report(df_valid)

        st.success("已读取飞书真实数据。")

        total = s["total"]
        l0 = s["l0"]
        l1 = s["l1"]
        l2 = s["l2"]
        l3 = s["l3"]

        kp1 = s["kp1"]
        kp2 = s["kp2"]
        kp3 = s["kp3"]
        kp4 = s["kp4"]
        kp5 = s["kp5"]
        kp6 = s["kp6"]
        kp7 = s["kp7"]
        kp8 = s["kp8"]

        kp1_rate = s["kp1_rate"]
        kp2_rate = s["kp2_rate"]
        kp3_rate = s["kp3_rate"]
        kp4_rate = s["kp4_rate"]
        kp5_rate = s["kp5_rate"]
        kp6_rate = s["kp6_rate"]
        kp7_rate = s["kp7_rate"]
        kp8_rate = s["kp8_rate"]

        excellent_rate = s["excellent_rate"]
        top_missing_points = s["top_missing_points"]
        best_examples = s["best_examples"]
        mid_examples = s["mid_examples"]
        weak_examples = s["weak_examples"]

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("累计提交人数", f"{total} 人")
        with col2:
            st.metric("Level0", f"{l0} 人")
        with col3:
            st.metric("Level1", f"{l1} 人")
        with col4:
            st.metric("Level2", f"{l2} 人")
        with col5:
            st.metric("Level3", f"{l3} 人")

        st.markdown("---")

        col6, col7, col8, col9 = st.columns(4)
        with col6:
            st.metric("KP1命中率", f"{kp1_rate}%")
        with col7:
            st.metric("KP2命中率", f"{kp2_rate}%")
        with col8:
            st.metric("KP3命中率", f"{kp3_rate}%")
        with col9:
            st.metric("优良率（L2+L3）", f"{excellent_rate}%")

        st.markdown("---")

        chart1, chart2 = st.columns(2)

        with chart1:
            level_df = pd.DataFrame({
                "等级": ["Level0", "Level1", "Level2", "Level3"],
                "人数": [l0, l1, l2, l3]
            })
            fig_pie = px.pie(
                level_df,
                names="等级",
                values="人数",
                title="🏆 作答等级分布",
                hole=0.45
            )
            fig_pie.update_layout(height=520, title_font_size=24, font=dict(size=18))
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart2:
            hit_rate_df = pd.DataFrame({
                "知识点": ["KP1", "KP2", "KP3", "KP4", "KP5", "KP6", "KP7", "KP8"],
                "命中率": [kp1_rate, kp2_rate, kp3_rate, kp4_rate, kp5_rate, kp6_rate, kp7_rate, kp8_rate]
            })
            fig_hit = px.bar(
                hit_rate_df,
                x="知识点",
                y="命中率",
                text="命中率",
                title="🎯 八个知识点命中率"
            )
            fig_hit.update_traces(texttemplate="%{y}%", textposition="outside")
            fig_hit.update_layout(
                height=520,
                title_font_size=24,
                font=dict(size=18),
                yaxis_title="命中率（%）",
                xaxis_title="知识点"
            )
            st.plotly_chart(fig_hit, use_container_width=True)

        st.markdown("---")

        chart3, chart4 = st.columns(2)

        with chart3:
            hit_count_df = pd.DataFrame({
                "知识点": ["KP1", "KP2", "KP3", "KP4", "KP5", "KP6", "KP7", "KP8"],
                "命中人数": [kp1, kp2, kp3, kp4, kp5, kp6, kp7, kp8]
            })
            fig_count = px.bar(
                hit_count_df,
                x="知识点",
                y="命中人数",
                text="命中人数",
                title="✅ 八个知识点命中人数"
            )
            fig_count.update_traces(textposition="outside")
            fig_count.update_layout(height=500, title_font_size=24, font=dict(size=18))
            st.plotly_chart(fig_count, use_container_width=True)

        with chart4:
            if top_missing_points:
                top_df = pd.DataFrame(top_missing_points)
                top_df.columns = ["失分点", "出现次数"]
                fig_top = px.bar(
                    top_df,
                    x="失分点",
                    y="出现次数",
                    text="出现次数",
                    title="📌 常见失分点 Top3"
                )
                fig_top.update_traces(textposition="outside")
                fig_top.update_layout(
                    height=500,
                    title_font_size=24,
                    font=dict(size=18),
                    xaxis_title="失分点",
                    yaxis_title="出现次数"
                )
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("暂无可展示的失分点 Top3。")

        st.markdown("---")
        st.markdown('<div class="big-title">📝 代表性答案展示</div>', unsafe_allow_html=True)

        ex1, ex2, ex3 = st.columns(3)

        def render_examples(title, examples):
            st.markdown(f'<div class="case-title">{title}</div>', unsafe_allow_html=True)
            if not examples:
                st.info("暂无对应答案。")
                return

            for ex in examples:
                st.markdown(f"""
                <div class="case-card">
                    <div class="case-meta">学号：{ex["student_id"]} ｜ 等级：{ex["score_level"]} ｜ 时间：{ex["timestamp"]}</div>
                    <div class="case-answer">{ex["user_answer"]}</div>
                    <div class="case-tag"><b>命中知识点：</b>{ex["knowledge_hit"]}</div>
                    <div class="case-tag"><b>缺失点：</b>{ex["missing_points"]}</div>
                </div>
                """, unsafe_allow_html=True)

        with ex1:
            render_examples("🌟 优秀答案示例", best_examples)
        with ex2:
            render_examples("🟡 中等答案示例", mid_examples)
        with ex3:
            render_examples("🔍 典型薄弱答案", weak_examples)

        with st.expander("📋 查看原始表格数据"):
            st.dataframe(df_valid, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 读取飞书失败：{str(e)}")
