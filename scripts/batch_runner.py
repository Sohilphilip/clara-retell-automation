import os
from pathlib import Path

from extract_account_memo import (
    load_transcript,
    derive_account_id,
    extract_account_memo,
    save_v1_account_memo,
    extract_onboarding_updates,
    load_existing_v1
)

from generate_agent_spec import generate_agent_spec, save_agent_spec
from apply_onboarding_patch import apply_patch, save_v2_account_memo, save_changelog
from utils import log


DEMO_FOLDER = "./dataset/demo_calls"
ONBOARDING_FOLDER = "./dataset/onboarding_calls"


def run_demo_batch():

    log("Starting demo batch processing...")

    for filename in os.listdir(DEMO_FOLDER):

        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(DEMO_FOLDER, filename)

        account_id = derive_account_id(file_path)

        # ✅ Idempotency check (skip if v1 already exists)
        v1_path = Path(f"./outputs/accounts/{account_id}/v1/account_memo.json")

        if v1_path.exists():
            log(f"Skipping {account_id} — v1 memo already exists.")
            continue

        try:

            transcript = load_transcript(file_path)

            memo = extract_account_memo(transcript, account_id)

            save_v1_account_memo(account_id, memo)

            agent_spec = generate_agent_spec(memo, version="v1")

            save_agent_spec(account_id, agent_spec, version="v1")

            log(f"Demo pipeline complete for {account_id}")

        except Exception as e:

            log(f"Demo pipeline failed for {account_id}: {e}")

    log("Demo batch processing complete.")


def run_onboarding_batch():

    log("Starting onboarding batch processing...")

    for filename in os.listdir(ONBOARDING_FOLDER):

        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(ONBOARDING_FOLDER, filename)

        account_id = derive_account_id(file_path)

        try:

            transcript = load_transcript(file_path)

            updates = extract_onboarding_updates(transcript)

            #  Ensure v1 exists before applying onboarding updates
            v1_path = Path(f"./outputs/accounts/{account_id}/v1/account_memo.json")

            if not v1_path.exists():
                log(f"Skipping onboarding for {account_id} — v1 memo not found.")
                continue

            v1_memo = load_existing_v1(account_id)

            v2_memo, changes = apply_patch(v1_memo, updates)

            if changes:

                file_written = save_v2_account_memo(account_id, v2_memo)

                if file_written:

                    # Save changelog
                    save_changelog(account_id, changes)

                    # Generate v2 agent spec
                    agent_spec = generate_agent_spec(v2_memo, version="v2")

                    save_agent_spec(account_id, agent_spec, version="v2")

                    log(f"Onboarding pipeline complete for {account_id}")

                else:
                    log(f"No file update required for {account_id}, skipping changelog and agent spec.")

            else:
                log(f"No updates required for {account_id}, skipping v2 generation.")

        except Exception as e:

            log(f"Onboarding pipeline failed for {account_id}: {e}")

    log("Onboarding batch processing complete.")


if __name__ == "__main__":

    run_demo_batch()

    run_onboarding_batch()