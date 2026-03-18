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
    return pd.DataFrame(rows) if rows else pd.DataFrame()


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

    missing_series = (
        df["missing_points"].fillna("").astype(str)
        if "missing_points" in df.columns
        else pd.Series(dtype=str)
    )

    return {
        "total": int(len(df[df.notna().any(axis=1)])),
        "l0": int((score_series == "Level0").sum()),
        "l1": int((score_series == "Level1").sum()),
        "l2": int((score_series == "Level2").sum()),
        "l3": int((score_series == "Level3").sum()),
        "adh": int(missing_series.str.contains("ADH|抗利尿激素", regex=True).sum()),
        "anp": int(missing_series.str.contains("ANP|心房利钠肽", regex=True).sum()),
        "raas": int(missing_series.str.contains("RAAS|醛固酮|肾素|血管紧张素", regex=True).sum())
    }


if st.button("🔄 刷新统计看板", type="primary"):
    try:
        with st.spinner("正在从飞书读取真实数据..."):
            access_token = get_tenant_access_token()
            records = search_all_records(access_token)
            df = parse_records_to_df(records)
            df_valid = df[df.notna().any(axis=1)].copy() if not df.empty else df
            s = calc_report(df_valid)

        st.success("已读取飞书真实数据。")
        st.write("**当前统计结果：**")
        st.json(s)

        total = s["total"]
        l0 = s["l0"]
        l1 = s["l1"]
        l2 = s["l2"]
        l3 = s["l3"]
        adh = s["adh"]
        anp = s["anp"]
        raas = s["raas"]

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
            st.dataframe(df_valid, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 读取飞书失败：{str(e)}")
