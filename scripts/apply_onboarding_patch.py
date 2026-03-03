import copy
from utils import log
import json
from pathlib import Path

def apply_patch(v1_memo, onboarding_updates):
    """
    Apply onboarding updates safely.
    - Merge arrays
    - Merge nested dictionaries
    - Preserve unrelated fields
    - Track granular changes
    """

    import copy
    v2_memo = copy.deepcopy(v1_memo)
    changes = []

    for key, new_value in onboarding_updates.items():
        old_value = v2_memo.get(key)

        # CASE 1: If value is a list → merge unique values
        if isinstance(new_value, list):
            merged = list(set(old_value + new_value)) if old_value else new_value
            if merged != old_value:
                v2_memo[key] = merged
                changes.append({
                    "field": key,
                    "old": old_value,
                    "new": merged
                })

        # CASE 2: If value is dict → update nested keys only
        elif isinstance(new_value, dict):
            updated_dict = old_value.copy() if old_value else {}
            nested_changes = False

            for sub_key, sub_value in new_value.items():
                if updated_dict.get(sub_key) != sub_value:
                    updated_dict[sub_key] = sub_value
                    nested_changes = True

            if nested_changes:
                v2_memo[key] = updated_dict
                changes.append({
                    "field": key,
                    "old": old_value,
                    "new": updated_dict
                })

        # CASE 3: Primitive replacement
        else:
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

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if existing == memo_json:
            log(f"No changes detected for {account_id}, skipping v2 overwrite.")
            return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memo_json, f, indent=2)

    log(f"Saved v2 memo for {account_id}")
    return True

def save_changelog(account_id, changes):
    output_path = Path(f"./outputs/accounts/{account_id}")
    file_path = output_path / "changes.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# Changes v1 → v2\n\n")
        for change in changes:
            f.write(f"## {change['field']}\n")
            f.write(f"- Old: {change['old']}\n")
            f.write(f"- New: {change['new']}\n\n")

    log(f"Saved changelog for {account_id}")