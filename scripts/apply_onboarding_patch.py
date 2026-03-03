import copy
from utils import log
import json
from pathlib import Path

def apply_patch(v1_memo, onboarding_updates):
    """
    Apply onboarding updates without destroying unrelated fields.
    Returns updated memo and list of changes.
    """

    v2_memo = copy.deepcopy(v1_memo)
    changes = []

    for key, new_value in onboarding_updates.items():
        old_value = v2_memo.get(key)

        if old_value != new_value:
            v2_memo[key] = new_value
            changes.append({
                "field": key,
                "old": old_value,
                "new": new_value
            })

    return v2_memo, changes


def save_v2_account_memo(account_id, memo_json):
    output_path = Path(f"./outputs/accounts/{account_id}/v2")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "account_memo.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memo_json, f, indent=2)

    log(f"Saved v2 memo for {account_id}")