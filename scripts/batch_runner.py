import os
from extract_account_memo import (
    load_transcript,
    derive_account_id,
    extract_account_memo,
    save_v1_account_memo
)
from generate_agent_spec import generate_agent_spec, save_agent_spec
from utils import log
from extract_account_memo import extract_onboarding_updates, load_existing_v1
from apply_onboarding_patch import apply_patch, save_v2_account_memo, save_changelog


DEMO_FOLDER = "./dataset/demo_calls"


def run_demo_batch():
    for filename in os.listdir(DEMO_FOLDER):
        if filename.endswith(".txt"):
            file_path = os.path.join(DEMO_FOLDER, filename)

            transcript = load_transcript(file_path)
            account_id = derive_account_id(file_path)

            memo = extract_account_memo(transcript, account_id)
            save_v1_account_memo(account_id, memo)

            agent_spec = generate_agent_spec(memo, version="v1")
            save_agent_spec(account_id, agent_spec, version="v1")

    log("Demo batch processing complete.")

ONBOARDING_FOLDER = "./dataset/onboarding_calls"

def run_onboarding_batch():
    for filename in os.listdir(ONBOARDING_FOLDER):
        if filename.endswith(".txt"):
            file_path = os.path.join(ONBOARDING_FOLDER, filename)

            transcript = load_transcript(file_path)
            account_id = derive_account_id(file_path).replace("onboarding_", "")

            updates = extract_onboarding_updates(transcript)
            v1_memo = load_existing_v1(account_id)

            v2_memo, changes = apply_patch(v1_memo, updates)

            save_v2_account_memo(account_id, v2_memo)
            save_changelog(account_id, changes)

    log("Onboarding batch processing complete.")

if __name__ == "__main__":
    run_demo_batch()
    run_onboarding_batch()