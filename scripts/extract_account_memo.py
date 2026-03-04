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

SERVICE_KEYWORDS = [
    "service call",
    "repair",
    "installation",
    "maintenance",
    "replacement",
    "upgrade",
    "inspection",
    "renovation",
    "project"
]

SERVICE_NORMALIZATION = {
    "service call": "service calls",
    "repair": "repair services",
    "installation": "installation services",
    "maintenance": "maintenance services",
    "inspection": "inspection services"
}

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

def chunk_text(text, size=2000):
    """
    Split transcript into smaller chunks for better LLM processing.
    """
    return [text[i:i + size] for i in range(0, len(text), size)]

def call_ollama(prompt):

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.9,
                "num_predict": 1200
            }
        },
        timeout=180
    )

    result = response.json()["response"]

    return extract_json_from_text(result)


def summarize_transcript(transcript_text):

    prompt = f"""
Summarize the contractor's business information from this transcript.

Focus only on:
- services offered
- business hours
- emergency rules
- routing rules
- software tools used
- company details

Ignore:
- product demo discussion
- sales conversation
- unrelated chatter

Return a short structured summary.

Transcript:
{transcript_text}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 800
            }
        },
        timeout=180
    )

    return response.json()["response"]

def extract_company_info(transcript_text, account_id):

    prompt = f"""
You are extracting structured information from a contractor demo call transcript.

IMPORTANT RULES:
1. Only extract information explicitly stated in the transcript.
2. If information is missing return empty values ("", []).
3. NEVER write phrases like:
   - "Not specified"
   - "Not mentioned"
   - "Unknown"

Return JSON only.

Schema:

{{
 "company_name": "",
 "business_hours": {{
    "days": [],
    "start": "",
    "end": "",
    "timezone": ""
 }},
 "office_address": "",
 "integration_constraints": [],
 "notes": ""
}}

Extract:

company_name:
Name of the contractor business.

business_hours:
If mentioned.

office_address:
City or business location.

integration_constraints:
Software tools used by the business such as:
- Jobber
- ServiceTitan
- Housecall Pro
- QuickBooks

notes:
Important business facts such as:
- years of experience
- team size
- vans
- subcontractors
- hiring plans

Transcript:
{transcript_text}
"""

    return call_ollama(prompt)



def extract_services(transcript_text):

    prompt = f"""
Extract electrical services offered by the contractor.

Example:

Transcript:
"We do EV charger installs and panel upgrades."

Output:
{{
 "services_supported": [
   "EV charger installation",
   "panel upgrades"
 ]
}}

Return JSON only.

Schema:
{{
 "services_supported": []
}}

Rules:
- Extract only services mentioned
- Do not invent services
- If none found return []

Transcript:
{transcript_text}
"""

    return call_ollama(prompt)


def extract_emergency_rules(transcript_text):

    prompt = f"""
Extract emergency situations and emergency call routing rules.

IMPORTANT RULES:
1. Only extract explicit emergency conditions.
2. If none mentioned return empty lists.
3. Do NOT write explanations.

Return JSON only.

Schema:

{{
 "emergency_definition": [],
 "emergency_routing_rules": []
}}

Transcript:
{transcript_text}
"""

    return call_ollama(prompt)



def extract_routing_rules(transcript_text):

    prompt = f"""
Extract call handling rules for the business.

IMPORTANT RULES:
1. Only extract rules explicitly stated.
2. If missing return empty values.
3. Do NOT write explanations.

Return JSON only.

Schema:

{{
 "non_emergency_routing_rules": [],
 "call_transfer_rules": {{}},
 "after_hours_flow_summary": "",
 "office_hours_flow_summary": ""
}}

Transcript:
{transcript_text}
"""

    return call_ollama(prompt)


def extract_account_memo(transcript_text, account_id):

    transcript_text = transcript_text.replace("\n", " ")

    memo = create_empty_account_memo(account_id)

    try:

        summary = summarize_transcript(transcript_text)

        chunks = chunk_text(summary)

        all_services = []

        # keyword detection first
        for keyword in SERVICE_KEYWORDS:
            if keyword in transcript_text.lower():
                all_services.append(keyword)

        # run LLM extraction per chunk
        for chunk in chunks:

            company = extract_company_info(chunk, account_id)
            services = extract_services(chunk)
            emergency = extract_emergency_rules(chunk)
            routing = extract_routing_rules(chunk)

            sections = [company, services, emergency, routing]

            for section in sections:
                if isinstance(section, dict):
                    for key, value in section.items():
                        if key in memo and value:

                            if isinstance(value, list):
                                memo[key].extend(value)
                            else:
                                memo[key] = value

            # collect services
            if isinstance(services, dict):
                all_services.extend(services.get("services_supported", []))

        # merge services
        memo["services_supported"].extend(all_services)

        # normalize services
        normalized = []

        for service in memo["services_supported"]:

            s = service.lower()

            for key, value in SERVICE_NORMALIZATION.items():
                if key in s:
                    s = value

            normalized.append(s)

        memo["services_supported"] = list(set(normalized))

        memo["account_id"] = account_id

        log(f"{account_id} memo extracted using chunked multi-step extraction")

        return memo

    except Exception as e:

        log(f"Ollama extraction failed for {account_id}: {e}")

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