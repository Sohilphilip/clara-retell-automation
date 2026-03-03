import json
from pathlib import Path
from utils import log
from validator import validate_json

def generate_agent_spec(account_memo, version="v1"):
    """
    Generate dynamic Retell Agent Draft Spec.
    Injects operational rules directly into prompt.
    """

    company_name = account_memo["company_name"] or "the company"

    business_hours = account_memo["business_hours"]
    emergency_definitions = account_memo["emergency_definition"]
    integration_constraints = account_memo["integration_constraints"]
    transfer_rules = account_memo.get("call_transfer_rules", {})

    # Build dynamic sections safely
    emergency_text = (
        ", ".join(emergency_definitions)
        if emergency_definitions
        else "Emergency definition not explicitly provided"
    )

    business_hours_text = (
        f"Days: {', '.join(business_hours['days'])}\n"
        f"Hours: {business_hours['start']} - {business_hours['end']}\n"
        f"Timezone: {business_hours['timezone']}"
        if business_hours["days"]
        else "Business hours not fully specified."
    )

    transfer_timeout = transfer_rules.get("timeout_seconds", 30)
    retry_attempts = transfer_rules.get("retry_attempts", 2)

    integration_text = (
        "\n".join(f"- {rule}" for rule in integration_constraints)
        if integration_constraints
        else "No integration constraints explicitly defined."
    )

    system_prompt = f"""
You are an AI receptionist for {company_name}.

You must follow structured operational behavior exactly.

========================
BUSINESS INFORMATION
========================

Business Hours:
{business_hours_text}

Emergency Definition:
{emergency_text}

Integration Constraints:
{integration_text}

Transfer Protocol:
- Timeout: {transfer_timeout} seconds
- Retry Attempts: {retry_attempts}

========================
BUSINESS HOURS FLOW
========================

1. Greet the caller professionally.
2. Ask the purpose of the call.
3. Collect caller name and phone number.
4. Determine if the call matches emergency definition.
5. Route or transfer accordingly.
6. If transfer fails after {transfer_timeout} seconds:
   - Apologize
   - Collect caller details
   - Assure quick follow-up
7. Ask if they need anything else.
8. Close the call professionally.

========================
AFTER HOURS FLOW
========================

1. Greet caller.
2. Ask purpose.
3. Confirm if situation matches emergency definition.
4. If emergency:
   - Immediately collect name, phone, and address.
   - Attempt transfer using defined protocol.
   - If transfer fails:
       • Apologize
       • Assure rapid follow-up
5. If non-emergency:
   - Collect details
   - Confirm follow-up during business hours
6. Ask if anything else.
7. Close call.

========================
IMPORTANT RULES
========================

- Do NOT invent information not explicitly defined.
- Do NOT mention system functions or internal tools.
- Collect only information necessary for routing and dispatch.
- Follow integration constraints strictly.
"""

    agent_spec = {
        "agent_name": f"{company_name} AI Receptionist",
        "voice_style": "Professional, calm, efficient",
        "system_prompt": system_prompt.strip(),
        "variables": {
            "business_hours": business_hours,
            "emergency_definition": emergency_definitions
        },
        "call_transfer_protocol": {
            "timeout_seconds": transfer_timeout,
            "retry_attempts": retry_attempts
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

