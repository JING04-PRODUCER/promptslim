"""AgentOrchestrator — Streamlit 管理控制台"""

import streamlit as st
import requests
import os

API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")

st.set_page_config(page_title="AgentOrchestrator", page_icon="🤖", layout="wide")
st.title("AgentOrchestrator — 管理控制台")

# Health check
try:
    resp = requests.get(f"{API_URL}/health", timeout=5)
    health = resp.json()
    st.sidebar.success(f"✅ Agent Core 在线 — {health.get('tools', 0)} 个工具可用")
except Exception:
    st.sidebar.error("❌ Agent Core 离线")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["执行任务", "Agent 管理", "工具列表"])

with tab1:
    st.subheader("运行 Agent")
    task = st.text_area("任务描述", "请帮我分析这段代码的性能问题")
    model = st.selectbox("模型", ["gpt-4o", "gpt-4o-mini", "deepseek-chat", "claude-sonnet-4-6"])

    if st.button("执行", type="primary"):
        try:
            with st.spinner("Agent 执行中..."):
                resp = requests.post(
                    f"{API_URL}/agents/default/run",
                    json={"task": task},
                    timeout=120,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("执行完成")
                    st.markdown("### 响应")
                    st.write(data.get("response", ""))
                    usage = data.get("usage", {})
                    if usage:
                        st.caption(f"Token: {usage.get('total_tokens', 0)}")
                else:
                    st.error(f"错误: {resp.text}")
        except Exception as e:
            st.error(f"请求失败: {e}")

with tab2:
    st.subheader("创建 Agent")
    agent_name = st.text_input("Agent 名称", "default")
    system_prompt = st.text_area("System Prompt", "你是一个有用的 AI 助手。")
    tools = st.multiselect(
        "工具", ["read_file", "execute_sql", "web_search"], default=["web_search"]
    )

    if st.button("创建 Agent"):
        try:
            resp = requests.post(
                f"{API_URL}/agents",
                json={
                    "name": agent_name,
                    "model": "gpt-4o",
                    "system_prompt": system_prompt,
                    "tools": tools,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                st.success(f"Agent '{agent_name}' 创建成功")
            else:
                st.error(resp.text)
        except Exception as e:
            st.error(f"请求失败: {e}")

with tab3:
    st.subheader("可用工具")
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        data = resp.json()
        st.json({"tools_count": data.get("tools", 0)})
    except Exception as e:
        st.error(f"请求失败: {e}")
