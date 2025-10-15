from fastapi import FastAPI, UploadFile, File, Header, HTTPException, BackgroundTasks
import shutil
import pathlib
import subprocess
import threading

app = FastAPI()

# Base folder for temp files (absolute path)
BASE_DIR = pathlib.Path(__file__).parent.resolve()
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# Path to inFACTS executable
EXE_PATH = pathlib.Path(r"C:\Program Files\Evoma AB\inFACTS Studio 140\inFACTS Studio.exe")
if not EXE_PATH.exists():
    raise FileNotFoundError(f"inFACTS executable not found at {EXE_PATH}")

# API key
API_KEY = "YOUR_SECRET_KEY"

# Dictionary to track background jobs
jobs_status = {}  # key: filename, value: "running" or "finished"

# Background function to run inFACTS and save logs
def run_infacts(file_path: pathlib.Path):
    jobs_status[file_path.name] = "running"
    log_file = file_path.with_suffix(file_path.suffix + ".log")
    with open(log_file, "w", encoding="utf-8") as f:
        subprocess.run(
            [str(EXE_PATH), str(file_path)],
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
    jobs_status[file_path.name] = "finished"

@app.post("/process_file/")
async def process_file(
    file: UploadFile = File(...),
    x_api_key: str = Header(...),
    background_tasks: BackgroundTasks = None
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    temp_path = TEMP_DIR / file.filename
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(run_infacts, temp_path)

    return {
        "status": "Processing started in background",
        "filename": file.filename,
        "temp_path": str(temp_path),
        "log_file": str(temp_path.with_suffix(temp_path.suffix + ".log"))
    }

@app.get("/status/{filename}")
async def check_status(filename: str, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    log_file = TEMP_DIR / f"{filename}.log"
    if filename not in jobs_status:
        raise HTTPException(status_code=404, detail="File not found")

    status = jobs_status[filename]
    log_content = ""
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()

    return {
        "filename": filename,
        "status": status,
        "log": log_content
    }
