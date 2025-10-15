# inFACTS Streamlit Demo

## Backend (Windows)

1. Install Python 3.9+ and dependencies:
2. Run API server:
3. (Optional) Use ngrok for public testing:
Copy the HTTPS URL.

## Frontend (Streamlit Cloud)

1. Push `frontend/` folder to GitHub
2. In Streamlit Cloud, set secrets:
```toml
BACKEND_URL = "https://xxxx.ngrok.io"  # or your Windows server URL
API_KEY = "YOUR_SECRET_KEY"

---

# ✅ Usage Summary

1. **Backend** (Windows machine)
   - Runs inFACTS Studio
   - Exposes FastAPI endpoint
2. **Frontend** (Streamlit Cloud)
   - Uploads files to backend via HTTP
   - Displays results in browser
3. **Security**
   - API key stored in Streamlit secrets
   - No Windows-specific software on Streamlit
