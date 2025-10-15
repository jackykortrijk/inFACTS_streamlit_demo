import streamlit as st
import requests

st.title("Upload AML/XML for inFACTS Processing")

uploaded_file = st.file_uploader("Upload your file")
if uploaded_file:
    st.write(f"Uploading: {uploaded_file.name}")

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