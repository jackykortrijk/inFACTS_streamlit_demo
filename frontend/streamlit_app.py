import streamlit as st
import requests

# 设置浏览器 Tab 的标题 和 图标
st.set_page_config(
    page_title="Simulate Now",   # ✅ 改成你想要的标题
    page_icon="⚙️",              # ✅ 可以是 emoji 或 .ico/.png 文件路径
    layout="wide"
)

# 隐藏 Streamlit 默认的菜单和页脚
hide_streamlit_elements = """
    <style>
        #MainMenu {visibility: hidden;}      /* 右上角的三条杠菜单 */
        header {visibility: hidden;}         /* 顶部 Streamlit 标志栏 */
        footer {visibility: hidden;}         /* 底部 “Made with Streamlit” */
        .stActionButton {visibility: hidden;}/* 右下角 Share 按钮 */
    </style>
"""
st.markdown(hide_streamlit_elements, unsafe_allow_html=True)

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

# -----------------------------
# 封装：当用户按 Run 按钮时执行上传并调用后端
# -----------------------------
def run_script_with_progress():
    uploaded_file = st.session_state.get("uploaded_file")
    if uploaded_file is None:
        st.error("没有可用的文件。请先上传一个 .aml 或 .xml 文件。")
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
            st.error("请求超时（timeout）。请稍后重试或检查后端服务是否可达。")
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
else:
    st.success(f"✅ Using file: {st.session_state.uploaded_file.name}")
    st.info("🔒 File is locked. Refresh the page to upload a new one.")

# -----------------------------
# STEP 2: Dynamic Tabs (Run 按钮会调用 run_script_with_progress)
# -----------------------------
if st.session_state.uploaded_file is None:
    st.info("Upload a file to unlock simulation options.")
else:
    ext = st.session_state.selected_extension

    if ext == "aml":
        tab_vc, = st.tabs(["⚙️ Visual Components"])
        with tab_vc:
            st.subheader("Run Visual Components")
            if st.button("Run Visual Components"):
                run_script_with_progress()

    elif ext == "xml":
        tab_inf, = st.tabs(["⚙️ inFACTS Studio"])
        with tab_inf:
            st.subheader("Run inFACTS Studio")
            if st.button("Run inFACTS Studio"):
                run_script_with_progress()

    else:
        st.warning(f"Uploaded file type '.{ext}' does not unlock any simulation tab.")