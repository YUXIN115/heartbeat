import streamlit as st
import time
import datetime
import pandas as pd
import plotly.express as px
from threading import Thread

# -------------------------- 全局状态初始化（Streamlit会话状态，避免刷新丢失） --------------------------
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []  # 存储所有心跳包数据：[序号, 时间, 状态, 时间戳, 时间差]
if "seq" not in st.session_state:
    st.session_state.seq = 0  # 心跳序号，从1开始递增
if "last_heartbeat_time" not in st.session_state:
    st.session_state.last_heartbeat_time = time.time()  # 最后一次收到心跳的时间戳
if "is_running" not in st.session_state:
    st.session_state.is_running = False  # 模拟运行开关
if "timeout_count" not in st.session_state:
    st.session_state.timeout_count = 0  # 超时掉线次数统计

# -------------------------- 心跳包模拟线程（后台持续运行，不阻塞界面） --------------------------
def heartbeat_sender():
    """
    无人机心跳包发送线程：
    1. 每秒生成1个心跳包（含序号+时间戳）
    2. 检测3秒超时掉线
    3. 存储数据用于可视化
    """
    while st.session_state.is_running:
        # 1. 生成心跳包（无人机端发送）
        st.session_state.seq += 1
        current_timestamp = time.time()
        current_time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒
        
        # 2. 地面站掉线检测（核心逻辑：3秒阈值）
        time_since_last = current_timestamp - st.session_state.last_heartbeat_time
        if time_since_last > 3:
            status = "超时掉线"
            st.session_state.timeout_count += 1  # 超时次数+1
        else:
            status = "正常"
        
        # 3. 存储心跳数据（用于可视化）
        st.session_state.heartbeat_data.append({
            "序号": st.session_state.seq,
            "时间": current_time_str,
            "状态": status,
            "时间戳": current_timestamp,
            "时间差(秒)": round(time_since_last, 2)
        })
        
        # 4. 更新最后一次心跳时间
        st.session_state.last_heartbeat_time = current_timestamp
        
        # 5. 每秒发送一次（严格符合作业要求）
        time.sleep(1)

# -------------------------- Streamlit 页面布局与交互 --------------------------
# 页面配置
st.set_page_config(
    page_title="无人机心跳监测可视化",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🚁 无人机通信'心跳'监测可视化系统")
st.subheader("《无人机智能化应用2451》分组作业2")

# 控制按钮区（启动/停止/重置）
col1, col2, col3 = st.columns(3)
with col1:
    start_btn = st.button("▶️ 启动心跳模拟", disabled=st.session_state.is_running, use_container_width=True)
with col2:
    stop_btn = st.button("⏸️ 停止模拟", disabled=not st.session_state.is_running, use_container_width=True)
with col3:
    reset_btn = st.button("🔄 重置数据", use_container_width=True)

# 按钮逻辑
if start_btn:
    st.session_state.is_running = True
    # 启动守护线程（页面关闭自动终止，不残留进程）
    thread = Thread(target=heartbeat_sender, daemon=True)
    thread.start()
    st.rerun()  # 刷新页面，实时更新状态

if stop_btn:
    st.session_state.is_running = False
    st.rerun()

if reset_btn:
    # 重置所有状态，清空数据
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_heartbeat_time = time.time()
    st.session_state.is_running = False
    st.session_state.timeout_count = 0
    st.rerun()

# 实时状态面板
st.subheader("📊 实时监测状态")
status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    st.metric(label="当前心跳序号", value=st.session_state.seq)
with status_col2:
    st.metric(label="超时掉线次数", value=st.session_state.timeout_count)
with status_col3:
    system_status = "运行中" if st.session_state.is_running else "已停止"
    st.metric(label="系统状态", value=system_status)

# 数据可视化区（折线图）
st.subheader("📈 心跳包序号-时间变化曲线")
if st.session_state.heartbeat_data:
    df = pd.DataFrame(st.session_state.heartbeat_data)
    # 用不同颜色区分正常/超时状态，直观展示掉线
    fig = px.line(
        df,
        x="时间",
        y="序号",
        color="状态",
        title="无人机心跳包监测曲线（红色=超时掉线）",
        color_discrete_map={"正常": "#2ECC71", "超时掉线": "#E74C3C"},
        markers=True  # 显示数据点，更清晰
    )
    fig.update_layout(xaxis_title="时间", yaxis_title="心跳序号")
    st.plotly_chart(fig, use_container_width=True)

    # 原始数据表格（可筛选、排序）
    st.subheader("📋 完整心跳包数据")
    st.dataframe(
        df[["序号", "时间", "状态", "时间差(秒)"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("请点击【启动心跳模拟】开始生成心跳数据")

# 原理说明（作业加分项）
with st.expander("ℹ️ 系统原理与作业要求说明"):
    st.markdown("""
    ### 一、无人机心跳包机制原理
    1. **心跳包作用**：无人机每秒向地面站发送1次心跳包，用于证明通信链路正常，相当于无人机给地面站「报平安」
    2. **包结构**：每个心跳包包含**序号（seq）**和**时间戳（time）**，用于识别数据包顺序和发送时间
    3. **掉线检测规则**：地面站连续3秒未收到新的心跳包，判定为通信超时掉线，触发报警并统计掉线次数
    
    ### 二、作业要求对应
    | 作业任务 | 本项目实现 |
    |----------|------------|
    | 模拟心跳包 | 每秒发送1次，含序号+时间戳 |
    | 掉线检测 | 3秒未收到心跳自动报警，统计掉线次数 |
    | 数据可视化 | Streamlit网页+折线图+数据表格 |
    | 部署提交 | 支持GitHub+Streamlit Cloud部署 |
    """)

# 侧边栏（项目信息）
with st.sidebar:
    st.subheader("项目信息")
    st.markdown("**课程**：无人机智能化应用2451")
    st.markdown("**作业**：分组作业2 - 无人机心跳监测可视化")
    st.markdown("**技术栈**：Python + Streamlit + Pandas + Plotly")
    st.markdown("**部署**：GitHub + Streamlit Cloud")
