import copy
from utils import log


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