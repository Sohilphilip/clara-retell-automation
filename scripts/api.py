from fastapi import FastAPI
import subprocess
import datetime

app = FastAPI()

@app.get("/")
def health():
    return {"status": "API running"}

@app.post("/run-batch")
def run_batch():

    start_time = datetime.datetime.now()

    result = subprocess.run(
        ["python", "scripts/batch_runner.py"],
        capture_output=True,
        text=True
    )

    end_time = datetime.datetime.now()

    return {
        "status": "completed" if result.returncode == 0 else "failed",
        "started_at": str(start_time),
        "ended_at": str(end_time),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }