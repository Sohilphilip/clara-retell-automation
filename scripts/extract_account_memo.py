import os
import json
import requests
from pathlib import Path
from utils import log
from validator import validate_json
import re
from normalize_transcript import normalize_transcript

def load_transcript(file_path):
    """
    Load transcript text from file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = normalize_transcript(f.read())
        log(f"Loaded transcript: {file_path}")
        return text
    except Exception as e:
        log(f"Error loading transcript {file_path}: {e}")
        raise


def derive_account_id(file_path):
    """
    Derive a safe account_id from filename.
    Works for most filename structures.
    """

    filename = Path(file_path).stem.lower()

    # remove common words
    filename = filename.replace("demo_", "")
    filename = filename.replace("onboarding_", "")
    filename = filename.replace(" demo", "")
    filename = filename.replace(" onboarding", "")

    # replace spaces with underscore
    filename = filename.replace(" ", "_")

    # remove non-alphanumeric characters
    filename = re.sub(r"[^a-z0-9_]", "", filename)

    # remove duplicate underscores
    filename = re.sub("_+", "_", filename)

    # trim underscores
    filename = filename.strip("_")

    return filename

def extract_json_from_text(text: str):
    """
    Extract the first JSON object from model output safely.
    Works even if the model adds extra text.
    """
    # quick path if it's already valid JSON
    try:
        return json.loads(text)
    except:
        pass

    # try to find the first {...} block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise ValueError("No valid JSON found in model output")


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
    Extract structured data using local LLM (Ollama).
    Falls back to rule-based extraction if needed.
    """

    prompt = f"""
You are a structured data extraction system.

Your job is to extract operational configuration details about a contractor's
business from a demo call transcript.

The transcript includes both:
1) Information about the contractor's business
2) A product demo of Clara AI

You MUST extract ONLY the contractor's business information.

IGNORE:
- Clara product explanation
- AI demo
- pricing discussion
- onboarding logistics
- meeting scheduling
- contract paperwork
- internal Clara team details

Only capture details about the contractor's business operations.

--------------------------------------------------

EXTRACTION RULES

1. ONLY extract information explicitly stated in the transcript.
2. DO NOT guess or infer missing information.
3. If a field cannot be determined, leave it empty and add a note in
   "questions_or_unknowns".
4. Prefer short factual entries over long explanations.

--------------------------------------------------

FIELD GUIDELINES

company_name:
Name of the contractor business.

business_hours:
Only fill if explicitly stated.

office_address:
Physical business location if mentioned.

services_supported:
Types of electrical work or services the contractor performs
(e.g. EV chargers, troubleshooting, panel changes, etc).

emergency_definition:
Situations considered urgent or emergency service requests.

emergency_routing_rules:
How emergency calls should be handled or routed.

non_emergency_routing_rules:
How regular service calls should be handled.

call_transfer_rules:
Rules about transferring calls to staff.

integration_constraints:
Software systems currently used by the business
(example: Jobber CRM).

after_hours_flow_summary:
Short description of how calls should be handled after hours.

office_hours_flow_summary:
Short description of how calls should be handled during business hours.

notes:
Any important operational details about the business.

--------------------------------------------------

OUTPUT REQUIREMENTS

Return ONLY a valid JSON object.

Do NOT include:
- explanations
- markdown
- comments
- text before or after the JSON

The response MUST start with {{ and end with }}.

--------------------------------------------------

OUTPUT SCHEMA

{{
  "account_id": "{account_id}",
  "company_name": "",
  "business_hours": {{
    "days": [],
    "start": "",
    "end": "",
    "timezone": ""
  }},
  "office_address": "",
  "services_supported": [],
  "emergency_definition": [],
  "emergency_routing_rules": [],
  "non_emergency_routing_rules": [],
  "call_transfer_rules": {{}},
  "integration_constraints": [],
  "after_hours_flow_summary": "",
  "office_hours_flow_summary": "",
  "questions_or_unknowns": [],
  "notes": ""
}}

--------------------------------------------------

TRANSCRIPT

{transcript_text}
"""

    try:

        response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False,
            "format": "json",           
            "options": {
            "temperature": 0,
            "num_predict": 800
            }
        },
        timeout=180
        )

        result = response.json()["response"]

        result_json = extract_json_from_text(result)

        # Start with safe default structure
        memo = create_empty_account_memo(account_id)

        # Merge only known schema fields
        for key in memo.keys():
            if key in result_json:
                memo[key] = result_json[key]

        # Normalize business_hours keys if LLM used different naming
        bh = memo.get("business_hours", {})

        if isinstance(bh, dict):

            # Map alternate names → schema names
            if "start_time" in bh and not bh.get("start"):
                bh["start"] = bh["start_time"]

            if "end_time" in bh and not bh.get("end"):
                bh["end"] = bh["end_time"]

            if "time_zone" in bh and not bh.get("timezone"):
                bh["timezone"] = bh["time_zone"]

        # Remove incorrect keys
        bh.pop("start_time", None)
        bh.pop("end_time", None)
        bh.pop("time_zone", None)

        memo["business_hours"] = bh

        # Ensure account_id is always correct
        memo["account_id"] = account_id

        log(f"{account_id} memo extracted using Ollama")

        return memo

    except Exception as e:

        log(f"Ollama extraction failed for {account_id}, using fallback rules. Error: {e}")

        return fallback_rule_extraction(transcript_text, account_id)


def fallback_rule_extraction(transcript_text, account_id):

    memo = create_empty_account_memo(account_id)

    text = transcript_text.lower()

    # detect CRM tools
    if "jobber" in text:
        memo["integration_constraints"].append("Uses Jobber CRM")

    if "servicetrade" in text:
        memo["integration_constraints"].append("Uses ServiceTrade")

    # detect emergency keywords
    if "emergency" in text:
        memo["emergency_definition"].append("Emergency service request")

    # generic service detection
    service_keywords = [
        "repair",
        "installation",
        "inspection",
        "maintenance",
        "service call"
    ]

    for keyword in service_keywords:
        if keyword in text:
            memo["services_supported"].append(keyword)

    if not memo["services_supported"]:
        memo["questions_or_unknowns"].append(
            "Services not clearly specified"
        )

    memo["questions_or_unknowns"].append(
        "Business hours not specified"
    )

    log(f"Fallback rule extraction applied for {account_id}")

    return memo

def save_v1_account_memo(account_id, memo_json):

    validate_json(
        memo_json,
        "./schemas/account_memo_schema.json",
        object_name=f"{account_id} v1 Account Memo"
    )

    output_path = Path(f"./outputs/accounts/{account_id}/v1")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "account_memo.json"

    if file_path.exists():
        log(f"v1 memo already exists for {account_id}, skipping overwrite.")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memo_json, f, indent=2)

    log(f"Saved v1 memo for {account_id}")

def extract_onboarding_updates(transcript_text):

    updates = {}
    text = transcript_text.lower()

    # business hours
    if "monday" in text and "friday" in text:
        updates["business_hours"] = {
            "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"]
        }

    # transfer timeout detection
    if "transfer fails" in text or "no answer" in text:
        updates.setdefault("call_transfer_rules", {})["timeout_seconds"] = 60

    # integration constraints
    if "never create" in text and "servicetrade" in text:
        updates.setdefault("integration_constraints", []).append(
            "Never create jobs in ServiceTrade"
        )

    if "jobber" in text:
        updates.setdefault("integration_constraints", []).append(
            "Uses Jobber CRM"
        )

    return updates

def load_existing_v1(account_id):
    """
    Load existing v1 memo for patching.
    """

    path = Path(f"./outputs/accounts/{account_id}/v1/account_memo.json")

    if not path.exists():
        raise FileNotFoundError(f"v1 memo not found for {account_id}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    transcript_file = "./dataset/demo_calls/bens_demo_clean.txt"

    transcript_text = load_transcript(transcript_file)

    account_id = derive_account_id(transcript_file)

    memo = extract_account_memo(transcript_text, account_id)

    save_v1_account_memo(account_id, memo)


if __name__ == "__main__":
    main()