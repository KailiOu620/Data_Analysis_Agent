"""Streamlit UI for uploading data and downloading an AI analysis report."""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("DATA_AGENT_API_URL", "http://127.0.0.1:8000").rstrip("/")
NONE_OPTION = "（不使用）"

st.set_page_config(page_title="企业经营数据分析 Agent", page_icon="📊", layout="wide")


def api_error(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail")
        return str(detail or response.text)
    except ValueError:
        return response.text or f"HTTP {response.status_code}"


def guess(columns: list[str], candidates: list[str], required: bool = False) -> int:
    lowered = [column.lower().replace("_", " ").strip() for column in columns]
    for candidate in candidates:
        candidate = candidate.lower()
        for index, column in enumerate(lowered):
            if candidate == column or candidate in column:
                return index + (0 if required else 1)
    return 0


def optional_select(label: str, columns: list[str], candidates: list[str]) -> str | None:
    options = [NONE_OPTION, *columns]
    value = st.selectbox(label, options, index=guess(columns, candidates))
    return None if value == NONE_OPTION else value


def inspect_uploaded_file(uploaded_file) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/files/inspect",
        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(api_error(response))
    return response.json()


with st.sidebar:
    st.header("运行状态")
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=3)
        st.success("FastAPI 已连接" if health.ok else "FastAPI 返回异常")
    except requests.RequestException:
        st.error("FastAPI 未启动")
    st.caption(f"后端地址：{API_BASE_URL}")
    st.markdown("先启动 `python run_api.py`，再启动本页面。阿里云 API Key 仅配置在后端环境变量中。")

st.title("企业经营数据分析 Agent")
st.write("上传 CSV 或 Excel，确认字段映射后，由统计工具完成计算、Qwen 生成解读，并输出可下载的 Word 报告。")

uploaded = st.file_uploader("上传经营数据文件", type=["csv", "xlsx", "xls"])
if uploaded is None:
    st.info("请先选择一个 CSV、XLSX 或 XLS 文件。")
    st.stop()

file_signature = f"{uploaded.name}:{uploaded.size}"
if st.session_state.get("file_signature") != file_signature:
    with st.spinner("正在读取并检查字段……"):
        try:
            st.session_state.upload_info = inspect_uploaded_file(uploaded)
            st.session_state.file_signature = file_signature
            st.session_state.pop("analysis_result", None)
        except (requests.RequestException, RuntimeError) as exc:
            st.error(f"上传失败：{exc}")
            st.stop()

info = st.session_state.upload_info
columns = info["columns"]
metric1, metric2, metric3 = st.columns(3)
metric1.metric("数据行数", info["row_count"])
metric2.metric("字段数量", info["column_count"])
metric3.metric("文件名", info["filename"])
with st.expander("数据预览与字段类型", expanded=True):
    st.dataframe(pd.DataFrame(info["preview"]), width="stretch")
    st.json(info["dtypes"])

st.subheader("字段映射")
left, right = st.columns(2)
with left:
    company_name = st.text_input("企业名称", "示例企业")
    sales_column = st.selectbox(
        "销售额字段（必选）",
        columns,
        index=guess(columns, ["sales", "revenue", "销售额", "销售"], required=True),
    )
    date_column = optional_select("日期字段", columns, ["order date", "date", "日期", "时间"])
    profit_column = optional_select("利润字段", columns, ["profit", "利润"])
    quantity_column = optional_select("数量字段", columns, ["quantity", "qty", "数量"])
with right:
    order_id_column = optional_select("订单编号字段", columns, ["order id", "订单id", "订单编号"])
    group_column = optional_select("分组字段（区域/品类）", columns, ["region", "category", "区域", "地区", "品类"])
    advertising_column = optional_select("广告投入字段", columns, ["advertising", "ad spend", "广告"])
    use_llm = st.checkbox("使用阿里云 Qwen 生成图表和统计解读", value=True)
    st.caption("关闭后仍会生成完整统计报告，但概要使用确定性统计结果。")

if st.button("开始 AI 分析并生成 Word", type="primary", width="stretch"):
    payload = {
        "upload_id": info["upload_id"],
        "company_name": company_name,
        "sales_column": sales_column,
        "date_column": date_column,
        "profit_column": profit_column,
        "quantity_column": quantity_column,
        "order_id_column": order_id_column,
        "group_column": group_column,
        "advertising_column": advertising_column,
        "use_llm_interpretation": use_llm,
    }
    with st.spinner("正在计算统计指标、生成图表并调用 Qwen，通常需要 1—3 分钟……"):
        try:
            response = requests.post(f"{API_BASE_URL}/api/v1/analysis", json=payload, timeout=600)
            if not response.ok:
                raise RuntimeError(api_error(response))
            st.session_state.analysis_result = response.json()
        except (requests.RequestException, RuntimeError) as exc:
            st.error(f"分析失败：{exc}")

result = st.session_state.get("analysis_result")
if result:
    st.divider()
    st.subheader(result.get("summary_title", "总结分析"))
    st.write(result["summary"])
    if result.get("warnings"):
        with st.expander("生成警告"):
            for warning in result["warnings"]:
                st.warning(warning)

    st.subheader(result.get("word_output_label", "Word文件输出如下"))
    st.write(result["report_filename"])
    try:
        download = requests.get(f"{API_BASE_URL}{result['download_url']}", timeout=120)
        if not download.ok:
            raise RuntimeError(api_error(download))
        st.download_button(
            "下载 Word 分析报告",
            data=download.content,
            file_name=result["report_filename"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
    except (requests.RequestException, RuntimeError) as exc:
        st.error(f"报告下载失败：{exc}")
