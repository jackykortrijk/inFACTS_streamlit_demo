import streamlit as st
import pandas as pd
import requests
import random
import string
import json
import os

# 设置浏览器 Tab 的标题 和 图标
st.set_page_config(
    page_title="Simulate Now",   # ✅ 改成你想要的标题
    page_icon="⚙️",              # ✅ 可以是 emoji 或 .ico/.png 文件路径
    layout="centered" # "centered" 或 "wide"
)

# 隐藏 Streamlit 默认的菜单和页脚
hide_streamlit_default = """
    <style>
        /* 隐藏顶部菜单、默认页眉和底部 footer */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_default, unsafe_allow_html=True)

BACKEND_URL = st.secrets["BACKEND_URL"]
API_KEY = st.secrets["API_KEY"]

st.title("Simulate Now")
st.subheader("Import Configuration File")

# Initialize session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.selected_extension = None
    st.session_state.config_path = None
    st.session_state.process_response = None  # optional: store last response


def generate_random_operations():
    num_ops = random.randint(2, 5)
    operations = []
    # Add Source at the beginning with a random interval (speed)
    interval = random.choice([x for x in range(30, 101, 5)])  # seconds, step 5
    operations.append({
        "name": "Source",
        "mean (s)": "-",
        "sigma (s)": "-",
        "MTTR (%)": "-",
        "Interval (s)": interval
    })
    for i in range(num_ops):
        # Add Buffer before each operation except the first
        if i > 0:
            max_capacity = random.choice([x for x in range(10, 51, 5)])
            operations.append({
                "name": f"Buffer_{i}",
                "mean (s)": "-",
                "sigma (s)": "-",
                "MTTR (%)": "-",
                "Max Capacity": max_capacity
            })
        name = "Op" + ''.join(random.choices(string.ascii_uppercase, k=3))
        mean = random.randint(100, 600)
        sigma = random.randint(10, 50)
        mttr_percent = random.randint(10, 30)  # MTTR as percentage
        operations.append({
            "name": name,
            "mean (unit: s)": mean,
            "sigma (unit: s)": sigma,
            "MTTR (%)": f"{mttr_percent}%"
        })
    return operations

# -----------------------------
# 封装：当用户按 Run 按钮时执行上传并调用后端
# -----------------------------
def run_script_with_progress():
    uploaded_file = st.session_state.get("uploaded_file")
    if uploaded_file is None:
        st.error("No files available. Please upload a .aml or .xml file first.")
        return

    files = {"file": (uploaded_file.name, uploaded_file)}
    headers = {"x-api-key": API_KEY}

    # 这里用 spinner 显示进度
    with st.spinner("Processing..."):
        try:
            response = requests.post(f"{BACKEND_URL}/process_file/", files=files, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            st.success("Processing complete!")
            st.json(result)
            # 可选：保存到 session_state 以便页面其他地方访问
            st.session_state.process_response = result
        except requests.exceptions.Timeout:
            st.error("The request timed out. Please try again later or check whether the backend service is reachable.")
        except requests.exceptions.HTTPError as he:
            # 如果后端返回了错误码并且带有 json 内容，尝试显示
            try:
                st.error(f"HTTP error: {response.status_code}")
                st.json(response.json())
            except Exception:
                st.error(f"HTTP error: {he}")
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# 文件上传 UI（只在没有已上传文件时显示）
# -----------------------------
if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader(
        "Choose a configuration file",
        type=["aml", "xml"]
    )
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.selected_extension = uploaded_file.name.split(".")[-1].lower()
        st.session_state.config_path = f"configs/{uploaded_file.name}"
        st.write(f"Uploaded: {uploaded_file.name}")
        st.success(f"✅ Configuration file uploaded: {uploaded_file.name}")

        # Generate and persist operations and simulation parameters
        st.session_state.operations = generate_random_operations()
        st.session_state.replications = random.randint(2, 5)
        st.session_state.warmup_days = random.randint(1, 2)
        st.session_state.horizon_days = random.randint(30, 60)
else:
    st.success(f"✅ Using file: {st.session_state.uploaded_file.name}")
    st.info("🔒 File is locked. Refresh the page to upload a new one.")

# Always show operations and simulation parameters if a file is uploaded
if st.session_state.uploaded_file is not None:
    if "operations" in st.session_state:

        # Separate source, buffers, and operations
        ops = st.session_state.operations
        source = [op for op in ops if op["name"].lower() == "source"]
        buffers = [op for op in ops if op["name"].lower().startswith("buffer")]
        # Remove unwanted keys from operations
        operations = []
        for op in ops:
            if op["name"].lower().startswith("op"):
                op_clean = {k: v for k, v in op.items() if k not in ["Max Capacity", "Interval (s)"]}
                operations.append(op_clean)

        # --- Three.js Visualization Integration (move before tables) ---
        import streamlit.components.v1 as components
        html_path = os.path.join(os.path.dirname(__file__), "operations_flow.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_template = f.read()
            # Clean operations for visualization: remove Max Capacity and Interval (s) from non-buffer/source
            vis_ops = []
            for op in ops:
                if op["name"].lower() == "source":
                    vis_ops.append(op)
                elif op["name"].lower().startswith("buffer"):
                    vis_ops.append(op)
                elif op["name"].lower().startswith("op"):
                    op_clean = {k: v for k, v in op.items() if k not in ["Max Capacity", "Interval (s)"]}
                    vis_ops.append(op_clean)
            ops_json = json.dumps(vis_ops)
            html_code = html_template.replace(
                '/*__OPERATIONS_PLACEHOLDER__*/',
                f'const operations = {ops_json};'
            )
            components.html(html_code, height=400)
        else:
            st.warning("Three.js visualization file not found.")

        # Show Source table
        if source:
            st.write("✅ Source:")
            df_source = pd.DataFrame(source)[["name", "Interval (s)"]]
            st.table(df_source)

        # Show Buffers table
        if buffers:
            st.write("✅ Buffers:")
            df_buffers = pd.DataFrame(buffers)[["name", "Max Capacity"]]
            st.table(df_buffers)

        # Show Operations table
        if operations:
            st.write("✅ Operations:")
            df_ops = pd.DataFrame(operations)[["name", "mean (unit: s)", "sigma (unit: s)", "MTTR (%)"]]
            st.table(df_ops)

        st.write(f"**Replications:** {st.session_state.replications}")
        st.write(f"**Warmup:** {st.session_state.warmup_days} days")
        st.write(f"**Horizon:** {st.session_state.horizon_days} days")

# -----------------------------
# STEP 2: Dynamic Tabs (Run 按钮会调用 run_script_with_progress)
# -----------------------------
if st.session_state.uploaded_file is None:
    st.info("Upload a file to unlock simulation options.")
else:
    ext = st.session_state.selected_extension

    if ext == "aml":
        tab_vc, tab_nx = st.tabs(["⚙️ Visual Components", "⚙️ Siemens NX-MCD"])
        with tab_vc:
            st.subheader("Run Visual Components")
            if st.button("Run Visual Components"):
                run_script_with_progress()
        with tab_nx:
            st.subheader("Run Siemens NX-MCD")
            if st.button("Run Siemens NX-MCD"):
                run_script_with_progress()       


    elif ext == "xml":
        tab_inf, tab_flexsim = st.tabs(["⚙️ inFACTS Studio", "⚙️ FlexSim"])
        with tab_inf:
            st.subheader("Run inFACTS Studio")
            if st.button("Run inFACTS Studio"):
                run_script_with_progress()  # ✅ Call backend first
                if st.session_state.get("process_response"):
                    # Generate and store random chart data
                    ops = st.session_state.operations
                    op_names = [op["name"] for op in ops if op["name"].lower().startswith("op")]
                    import numpy as np
                    utilizations = np.random.uniform(0.5, 0.99, size=len(op_names))
                    st.session_state["infacts_utilizations"] = utilizations.tolist()
                    st.session_state["infacts_op_names"] = op_names
                    buffer_names = [op["name"] for op in ops if op["name"].lower().startswith("buffer")]
                    st.session_state["infacts_buffer_names"] = buffer_names
                    if buffer_names:
                        import pandas as pd
                        time_points = list(range(1, 11))
                        wip_data = {name: np.random.randint(0, 10, size=len(time_points)) for name in buffer_names}
                        st.session_state["infacts_time_points"] = time_points
                        st.session_state["infacts_wip_data"] = wip_data
            # Show charts if data is present
            if st.session_state.get("infacts_utilizations") and st.session_state.get("infacts_op_names"):
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                utilizations = st.session_state["infacts_utilizations"]
                op_names = st.session_state["infacts_op_names"]
                ax.bar(op_names, utilizations, color="#0077ff")
                ax.set_ylabel("Utilization")
                ax.set_ylim(0, 1)
                ax.set_title("Operation Utilization")
                for i, v in enumerate(utilizations):
                    ax.text(i, v + 0.02, f"{v:.2f}", ha='center', va='bottom')
                st.pyplot(fig)
            if st.session_state.get("infacts_buffer_names") and st.session_state.get("infacts_wip_data"):
                import pandas as pd
                buffer_names = st.session_state["infacts_buffer_names"]
                time_points = st.session_state["infacts_time_points"]
                wip_data = st.session_state["infacts_wip_data"]
                df_wip = pd.DataFrame(wip_data, index=time_points)
                fig2, ax2 = plt.subplots()
                for name in buffer_names:
                    ax2.plot(time_points, df_wip[name], marker='o', label=name)
                ax2.set_xlabel("Time")
                ax2.set_ylabel("WIP")
                ax2.set_title("Buffers WIP Over Time")
                ax2.legend()
                st.pyplot(fig2)
            if not st.session_state.get("process_response"):
                st.warning("Backend did not return a valid response.")
        with tab_flexsim:
            st.subheader("Run FlexSim")
            if st.button("Run FlexSim"):
                run_script_with_progress()

                # ✅ Only generate plots if backend response is valid
                if st.session_state.get("process_response"):

                    # --- Utilization Bar Chart ---
                    ops = st.session_state.operations
                    op_names = [op["name"] for op in ops if op["name"].lower().startswith("op")]

                    import numpy as np
                    utilizations = np.random.uniform(0.5, 0.99, size=len(op_names))
                    import matplotlib.pyplot as plt
                    fig, ax = plt.subplots()
                    ax.bar(op_names, utilizations, color="#0077ff")
                    ax.set_ylabel("Utilization")
                    ax.set_ylim(0, 1)
                    ax.set_title("Operation Utilization")
                    for i, v in enumerate(utilizations):
                        ax.text(i, v + 0.02, f"{v:.2f}", ha='center', va='bottom')
                    st.pyplot(fig)

                    # --- Buffers WIP Line Chart ---
                    buffer_names = [op["name"] for op in ops if op["name"].lower().startswith("buffer")]
                    if buffer_names:
                        import pandas as pd
                        time_points = list(range(1, 11))
                        wip_data = {name: np.random.randint(0, 10, size=len(time_points)) for name in buffer_names}
                        df_wip = pd.DataFrame(wip_data, index=time_points)
                        fig2, ax2 = plt.subplots()
                        for name in buffer_names:
                            ax2.plot(time_points, df_wip[name], marker='o', label=name)
                        ax2.set_xlabel("Time")
                        ax2.set_ylabel("WIP")
                        ax2.set_title("Buffers WIP Over Time")
                        ax2.legend()
                        st.pyplot(fig2)

                with tab_flexsim:
                    st.subheader("Run FlexSim")
                    run_flexsim_clicked = st.session_state.get("run_flexsim_clicked", False)
                    if st.button("Run FlexSim"):
                        st.session_state["run_flexsim_clicked"] = True
                        run_flexsim_clicked = True
                        run_script_with_progress()
                        # Generate and store random chart data
                        ops = st.session_state.operations
                        op_names = [op["name"] for op in ops if op["name"].lower().startswith("op")]
                        import numpy as np
                        utilizations = np.random.uniform(0.5, 0.99, size=len(op_names))
                        st.session_state["flexsim_utilizations"] = utilizations.tolist()
                        st.session_state["flexsim_op_names"] = op_names
                        buffer_names = [op["name"] for op in ops if op["name"].lower().startswith("buffer")]
                        st.session_state["flexsim_buffer_names"] = buffer_names
                        if buffer_names:
                            import pandas as pd
                            time_points = list(range(1, 11))
                            wip_data = {name: np.random.randint(0, 10, size=len(time_points)) for name in buffer_names}
                            st.session_state["flexsim_time_points"] = time_points
                            st.session_state["flexsim_wip_data"] = wip_data

                    # Show charts if data is present
                    if st.session_state.get("flexsim_utilizations") and st.session_state.get("flexsim_op_names"):
                        import matplotlib.pyplot as plt
                        fig, ax = plt.subplots()
                        utilizations = st.session_state["flexsim_utilizations"]
                        op_names = st.session_state["flexsim_op_names"]
                        ax.bar(op_names, utilizations, color="#0077ff")
                        ax.set_ylabel("Utilization")
                        ax.set_ylim(0, 1)
                        ax.set_title("Operation Utilization")
                        for i, v in enumerate(utilizations):
                            ax.text(i, v + 0.02, f"{v:.2f}", ha='center', va='bottom')
                        st.pyplot(fig)
                    if st.session_state.get("flexsim_buffer_names") and st.session_state.get("flexsim_wip_data"):
                        import pandas as pd
                        buffer_names = st.session_state["flexsim_buffer_names"]
                        time_points = st.session_state["flexsim_time_points"]
                        wip_data = st.session_state["flexsim_wip_data"]
                        df_wip = pd.DataFrame(wip_data, index=time_points)
                        fig2, ax2 = plt.subplots()
                        for name in buffer_names:
                            ax2.plot(time_points, df_wip[name], marker='o', label=name)
                        ax2.set_xlabel("Time")
                        ax2.set_ylabel("WIP")
                        ax2.set_title("Buffers WIP Over Time")
                        ax2.legend()
                        st.pyplot(fig2)
                    if run_flexsim_clicked and not st.session_state.get("process_response"):
                        st.warning("Backend did not return a valid response.")