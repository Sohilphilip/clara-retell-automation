from flask import Flask, render_template, request, redirect, url_for
import os
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path("../dataset")
DEMO_DIR = BASE_DIR / "demo_calls"
ONBOARDING_DIR = BASE_DIR / "onboarding_calls"
TEMP_DIR = BASE_DIR / "temp_uploads"

DEMO_DIR.mkdir(parents=True, exist_ok=True)
ONBOARDING_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


# STEP 1: Upload files to temp folder
@app.route("/upload", methods=["POST"])
def upload_file():

    files = request.files.getlist("transcripts")

    if not files:
        return "No files uploaded", 400

    filenames = []

    for transcript in files:

        filename = transcript.filename

        if not filename:
            continue

        save_path = TEMP_DIR / filename
        transcript.save(save_path)

        filenames.append(filename)

    return render_template("select_types.html", filenames=filenames)


# STEP 2: Move files to correct dataset folders
@app.route("/process_uploads", methods=["POST"])
def process_uploads():

    for filename in os.listdir(TEMP_DIR):

        filetype = request.form.get(filename)

        src = TEMP_DIR / filename

        if filetype == "demo":
            dst = DEMO_DIR / filename
        else:
            dst = ONBOARDING_DIR / filename

        src.rename(dst)

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():

    accounts = []
    processing_files = []

    outputs_path = Path("../outputs/accounts")

    # Detect currently processing transcripts
    demo_files = list(DEMO_DIR.glob("*.txt"))
    onboarding_files = list(ONBOARDING_DIR.glob("*.txt"))

    for f in demo_files + onboarding_files:
        processing_files.append(f.name)

    if outputs_path.exists():
        for acc in os.listdir(outputs_path):

            acc_path = outputs_path / acc

            v1 = acc_path / "v1"
            v2 = acc_path / "v2"

            v1_memo = (v1 / "account_memo.json").exists()
            v1_agent = (v1 / "agent_spec.json").exists()
            v2_memo = (v2 / "account_memo.json").exists()
            v2_agent = (v2 / "agent_spec.json").exists()
            changes = (acc_path / "changes.md").exists()

            if v2_memo:
                status = "Completed"
            elif v1_memo:
                status = "Demo Processed"
            else:
                status = "Processing"

            accounts.append({
                "account": acc,
                "status": status,
                "v1_memo": v1_memo,
                "v1_agent": v1_agent,
                "v2_memo": v2_memo,
                "v2_agent": v2_agent,
                "changes": changes
            })

    return render_template(
        "dashboard.html",
        accounts=accounts,
        processing_files=processing_files
    )


@app.route("/view/<account>/<version>/<filetype>")
def view_file(account, version, filetype):

    base = Path("../outputs/accounts") / account

    if filetype == "memo":
        path = base / version / "account_memo.json"

    elif filetype == "agent":
        path = base / version / "agent_spec.json"

    elif filetype == "changes":
        path = base / "changes.md"

    else:
        return "Invalid file type"

    if not path.exists():
        return "File not found"

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return f"<pre>{content}</pre>"


@app.route("/logs")
def view_logs():

    log_dir = Path("../logs")

    if not log_dir.exists():
        return "No logs yet"

    log_files = sorted(log_dir.glob("*.txt"), reverse=True)

    if not log_files:
        return "No logs yet"

    latest_log = log_files[0]

    with open(latest_log, "r", encoding="utf-8") as f:
        content = f.read()

    return f"<pre>{content}</pre>"


if __name__ == "__main__":
    app.run(debug=True, port=5000)