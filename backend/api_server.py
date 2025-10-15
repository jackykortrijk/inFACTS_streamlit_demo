from fastapi import FastAPI, UploadFile, File, Header, HTTPException
import subprocess
import shutil
import os

app = FastAPI()

# Create folder for temporary files
os.makedirs("temp", exist_ok=True)

# API key (change to a strong secret)
API_KEY = "YOUR_SECRET_KEY"

@app.post("/process_file/")
async def process_file(file: UploadFile = File(...), x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Save uploaded file temporarily
    temp_path = os.path.join("temp", file.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run inFACTS Studio (adjust path if needed)
    try:
        result = subprocess.run(
            [r"C:\Program Files\Evoma AB\inFACTS Studio 140\inFACTS Studio.exe", temp_path],
            capture_output=True, text=True
        )
    except Exception as e:
        return {"error": str(e)}

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "filename": file.filename
    }
