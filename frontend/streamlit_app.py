import streamlit as st
import requests

st.title("Simulate Now")
st.subheader("Import Configuration File")

# Initialize session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.selected_extension = None
    st.session_state.config_path = None

# Show uploader only if no file uploaded
if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader(
        "Choose a configuration file",
        type=["aml", "xml"]
    )
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.selected_extension = uploaded_file.name.split(".")[-1].lower()
        st.session_state.config_path = f"configs/{uploaded_file.name}"
        st.write(f"Uploading: {uploaded_file.name}")
        st.success(f"✅ Configuration file uploaded: {uploaded_file.name}")
else:
    st.success(f"✅ Using file: {st.session_state.uploaded_file.name}")
    st.info("🔒 File is locked. Refresh the page to upload a new one.")


def run_script_with_progress():
    # Get backend URL & API key from Streamlit secrets
        BACKEND_URL = st.secrets["BACKEND_URL"]
        API_KEY = st.secrets["API_KEY"]

        files = {"file": (uploaded_file.name, uploaded_file)}
        headers = {"x-api-key": API_KEY}

        with st.spinner("Processing..."):
            try:
                response = requests.post(f"{BACKEND_URL}/process_file/", files=files, headers=headers)
                response.raise_for_status()
                st.success("Processing complete!")
                st.json(response.json())
            except Exception as e:
                st.error(f"Error: {e}")

# -----------------------------
# STEP 2: Dynamic Tabs
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