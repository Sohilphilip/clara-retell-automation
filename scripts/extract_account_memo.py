import os
import json
from pathlib import Path
from utils import log


def load_transcript(file_path):
    """
    Load transcript text from file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        log(f"Loaded transcript: {file_path}")
        return text
    except Exception as e:
        log(f"Error loading transcript {file_path}: {e}")
        raise

def derive_account_id(file_path):
    """
    Extract account_id from filename.
    demo_acme.txt -> acme
    """
    filename = Path(file_path).stem
    if filename.startswith("demo_"):
        return filename.replace("demo_", "")
    return filename

def create_empty_account_memo(account_id):
    """
    Create structured memo with safe defaults.
    """
    return {
        "account_id": account_id,
        "company_name": "",
        "business_hours": {
            "days": [],
            "start": "",
            "end": "",
            "timezone": ""
        },
        "office_address": "",
        "services_supported": [],
        "emergency_definition": [],
        "emergency_routing_rules": [],
        "non_emergency_routing_rules": [],
        "call_transfer_rules": {},
        "integration_constraints": [],
        "after_hours_flow_summary": "",
        "office_hours_flow_summary": "",
        "questions_or_unknowns": [],
        "notes": ""
    }

def extract_account_memo(transcript_text, account_id):
    """
    Extract structured data from demo transcript.
    Only extract explicitly mentioned information.
    """
    memo = create_empty_account_memo(account_id)

    text_lower = transcript_text.lower()

    # Company name (very simple heuristic)
    if "company name is" in text_lower:
        memo["company_name"] = transcript_text.split("company name is")[-1].split("\n")[0].strip()

    else:
        memo["questions_or_unknowns"].append("Company name not explicitly stated")

    # Emergency keywords
    if "sprinkler leak" in text_lower:
        memo["emergency_definition"].append("Sprinkler leak")

    if "fire alarm" in text_lower:
        memo["emergency_definition"].append("Fire alarm triggered")

    if not memo["emergency_definition"]:
        memo["questions_or_unknowns"].append("Emergency definition unclear")

    # Business hours
    if "monday" in text_lower and "friday" in text_lower:
        memo["business_hours"]["days"] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    if not memo["business_hours"]["days"]:
        memo["questions_or_unknowns"].append("Business days not specified")

    log(f"Extracted memo for account: {account_id}")
    return memo

def save_v1_account_memo(account_id, memo_json):
    """
    Save v1 memo safely without overwriting.
    """
    output_path = Path(f"./outputs/accounts/{account_id}/v1")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "account_memo.json"

    if file_path.exists():
        log(f"v1 memo already exists for {account_id}, skipping overwrite.")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memo_json, f, indent=2)

    log(f"Saved v1 memo for {account_id}")