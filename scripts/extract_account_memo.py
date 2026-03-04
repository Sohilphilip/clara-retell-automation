import os
import json
import requests
from pathlib import Path
from utils import log
from validator import validate_json
import re
from docx import Document
from normalize_transcript import normalize_transcript
from PyPDF2 import PdfReader


def load_transcript(file_path):
    """
    Load transcript text from .txt, .docx, or .pdf files.
    """

    try:
        path = Path(file_path)

        if path.suffix.lower() == ".txt":

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

        elif path.suffix.lower() == ".docx":

            doc = Document(path)
            text = "\n".join([para.text for para in doc.paragraphs])

        elif path.suffix.lower() == ".pdf":

            reader = PdfReader(path)
            pages = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)

            text = "\n".join(pages)

        else:
            raise ValueError(f"Unsupported transcript format: {path.suffix}")

        text = normalize_transcript(text)

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

    transcript_text = transcript_text[:6000]

    prompt = f"""
You are extracting structured business information from a sales demo call transcript.

The conversation contains BOTH:
1) Clara AI demo discussion
2) Information about the contractor's business

Only extract the contractor's business information.

Ignore:
- Clara product explanations
- AI capabilities
- pricing discussion
- sales pitch
- onboarding steps

--------------------------------------

Extraction rules:

- Only extract information explicitly stated in the conversation.
- Do NOT guess missing information.
- If something is not mentioned, leave it empty.
- Do NOT write explanations like "not mentioned".

--------------------------------------

Extract the following fields if mentioned:

company_name:
Name of the contractor business.

services_supported:
List ALL electrical services mentioned.

Examples:
- service calls
- troubleshooting
- EV charger installation
- hot tub wiring
- panel upgrades
- renovations
- tenant improvements
- residential electrical work
- commercial electrical work

integration_constraints:
Software systems used by the company.
Example: Jobber CRM.

emergency_definition:
Only include if emergencies are clearly defined.

after_hours_flow_summary:
How after-hours calls are handled.

notes:
Operational details such as:
- years of experience
- number of vans
- subcontractors
- hiring plans
- business growth plans

--------------------------------------

Return ONLY valid JSON using this schema:

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

--------------------------------------

Transcript:
{transcript_text}
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 2000
                }
            },
            timeout=180
        )

        result = response.json()["response"]

        print("\n----- MODEL RESPONSE -----\n")
        print(result)
        print("\n--------------------------\n")

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

            if "start_time" in bh and not bh.get("start"):
                bh["start"] = bh["start_time"]

            if "end_time" in bh and not bh.get("end"):
                bh["end"] = bh["end_time"]

            if "time_zone" in bh and not bh.get("timezone"):
                bh["timezone"] = bh["time_zone"]

        bh.pop("start_time", None)
        bh.pop("end_time", None)
        bh.pop("time_zone", None)

        memo["business_hours"] = bh

        # Remove duplicates from list fields
        for field in [
            "services_supported",
            "integration_constraints",
            "emergency_definition"
        ]:
            if isinstance(memo.get(field), list):
                memo[field] = list(set(memo[field]))

        # Clean emergency_definition placeholders
        memo["emergency_definition"] = [
            x for x in memo["emergency_definition"]
            if "not mentioned" not in x.lower()
            and "not explicitly defined" not in x.lower()
        ]

        # Ensure account_id is correct
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