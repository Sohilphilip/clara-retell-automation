import json
from pathlib import Path
from utils import log
from validator import validate_json


def generate_agent_spec(account_memo, version="v1"):
    """
    Generate Retell Agent Draft Spec.
    """

    system_prompt = f"""
You are an AI receptionist for {account_memo['company_name']}.

BUSINESS HOURS FLOW:
- Greet caller
- Ask purpose of call
- Collect name and phone number
- Route or transfer appropriately
- If transfer fails, apologize and confirm follow-up
- Ask if they need anything else
- Close call

AFTER HOURS FLOW:
- Greet caller
- Ask purpose
- Confirm if emergency
- If emergency: collect name, phone, address immediately
- Attempt transfer
- If transfer fails: apologize and assure follow-up
- If non-emergency: collect details and confirm follow-up during business hours
- Ask if anything else
- Close
"""

    agent_spec = {
        "agent_name": f"{account_memo['company_name']} AI Receptionist",
        "voice_style": "Professional, calm, efficient",
        "system_prompt": system_prompt.strip(),
        "variables": {
            "business_hours": account_memo["business_hours"],
            "emergency_definition": account_memo["emergency_definition"]
        },
        "call_transfer_protocol": {
            "timeout_seconds": 30,
            "retry_attempts": 2
        },
        "fallback_protocol": "If transfer fails, collect caller details and assure callback.",
        "version": version
    }

    return agent_spec

def save_agent_spec(account_id, agent_spec, version="v1"):
    # Validate before saving
    validate_json(
        agent_spec,
        "./schemas/agent_spec_schema.json",
        object_name=f"{account_id} {version} Agent Spec"
    )

    output_path = Path(f"./outputs/accounts/{account_id}/{version}")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "agent_spec.json"

    if file_path.exists():
        log(f"{version} agent spec already exists for {account_id}, skipping overwrite.")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(agent_spec, f, indent=2)

    log(f"Saved {version} agent spec for {account_id}")

