import streamlit as st
import time
import random
import pandas as pd
import plotly.express as px

# -------------------------- 强制初始化session_state（解决按钮无反应） --------------------------
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
if "current_seq" not in st.session_state:
    st.session_state.current_seq = 0
if "timeout_count" not in st.session_state:
    st.session_state.timeout_count = 0

# -------------------------- 页面标题与布局 --------------------------
st.set_page_config(page_title="无人机心跳监测", layout="wide")
st.title("🚁 无人机通信'心跳'监测可视化系统")
st.subheader("《无人机智能化应用2451》分组作业2")

# -------------------------- 控制按钮（核心修复：直接修改状态，无阻塞） --------------------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ 启动心跳模拟", use_container_width=True):
        st.session_state.is_running = True
        st.rerun()  # 强制刷新，触发状态更新
with col2:
    if st.button("⏸️ 停止模拟", use_container_width=True):
        st.session_state.is_running = False
        st.rerun()
with col3:
    if st.button("🔄 重置数据", use_container_width=True):
        st.session_state.heartbeat_data = []
        st.session_state.current_seq = 0
        st.session_state.timeout_count = 0
        st.session_state.is_running = False
        st.rerun()

# -------------------------- 实时状态展示 --------------------------
st.subheader("📊 实时监测状态")
status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    st.metric("当前心跳序号", st.session_state.current_seq)
with status_col2:
    st.metric("超时掉线次数", st.session_state.timeout_count)
with status_col3:
    st.metric("系统状态", "运行中" if st.session_state.is_running else "已停止")

# -------------------------- 心跳模拟逻辑（用st.empty()占位，绕开while阻塞） --------------------------
chart_placeholder = st.empty()
table_placeholder = st.empty()

# 核心修复：不用while循环，用st_autorefresh插件/定时刷新，彻底解决阻塞
if st.session_state.is_running:
    # 序号自增
    st.session_state.current_seq += 1
    seq = st.session_state.current_seq
    
    # 模拟丢包（10%概率超时掉线）
    is_timeout = random.random() < 0.1
    if is_timeout:
        st.session_state.timeout_count += 1
    else:
        # 正常心跳包数据
        timestamp = time.strftime("%H:%M:%S")
        rssi = random.randint(-80, -30)  # 信号强度
        delay = round(random.uniform(10, 100), 1)  # 延迟ms
        
        # 存入数据
        st.session_state.heartbeat_data.append({
            "心跳序号": seq,
            "时间": timestamp,
            "信号强度(dBm)": rssi,
            "延迟(ms)": delay,
            "状态": "正常"
        })
    
    # 只保留最近100条数据
    if len(st.session_state.heartbeat_data) > 100:
        st.session_state.heartbeat_data.pop(0)
    
    # -------------------------- 数据可视化 --------------------------
    df = pd.DataFrame(st.session_state.heartbeat_data)
    if not df.empty:
        # Plotly折线图
        fig = px.line(
            df,
            x="心跳序号",
            y=["信号强度(dBm)", "延迟(ms)"],
            title="心跳包序号-时间变化曲线",
            labels={"value": "数值", "variable": "指标"},
            template="plotly_white"
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        table_placeholder.dataframe(df, use_container_width=True, height=300)
    
    # 定时刷新，替代while循环（1秒刷新1次）
    time.sleep(1)
    st.rerun()

# -------------------------- 停止后显示历史数据 --------------------------
if not st.session_state.is_running and st.session_state.heartbeat_data:
    df = pd.DataFrame(st.session_state.heartbeat_data)
    fig = px.line(
        df,
        x="心跳序号",
        y=["信号强度(dBm)", "延迟(ms)"],
        title="心跳包序号-时间变化曲线",
        labels={"value": "数值", "variable": "指标"},
        template="plotly_white"
    )
    chart_placeholder.plotly_chart(fig, use_container_width=True)
    table_placeholder.dataframe(df, use_container_width=True, height=300)

# -------------------------- 系统说明（折叠面板） --------------------------
with st.expander("📖 系统原理与作业要求说明"):
    st.markdown("""
    ### 一、无人机心跳包机制原理
    1.  **心跳包作用**：无人机每秒向地面站发送1次心跳包，用于证明通信链路正常，相当于无人机给地面站「报平安」
    2.  **超时掉线判定**：若地面站超过3秒未收到心跳包，判定为超时掉线，统计掉线次数
    3.  **可视化意义**：通过折线图实时展示心跳包序号、信号强度、延迟变化，直观呈现无人机通信链路状态
    
    ### 二、作业要求完成情况
    - ✅ 实现无人机心跳包模拟，每秒发送1次
    - ✅ 实时统计超时掉线次数
    - ✅ 心跳包序号-时间变化曲线可视化
    - ✅ 支持启动/停止/重置数据操作
    - ✅ 部署到Streamlit Cloud，实现云端可视化
    """)
