"""sync: Full update cycle — push, update, clear drift log."""

from .lib import SYNC_LOG, append_log, load_drift_log, now_ts
from .check_paths import run_push_docs
from .validate import run_update_docs


def run_sync_docs(scope=None, no_llm: bool = False):
    drift = load_drift_log()
    if not drift and scope is None:
        print("Drift log is empty and no --scope provided. Nothing to sync.")
        print("Run detect-drift first, or pass --scope to target specific files.")
        return

    print("=== push ===")
    run_push_docs()

    if no_llm:
        print("\n--no-llm: skipping update step.")
    else:
        print("\n=== update ===")
        run_update_docs(scope=scope, no_prompt=True)

        print("\n=== push (post-update) ===")
        run_push_docs()

    append_log(SYNC_LOG, {
        "ts": now_ts(),
        "status": "finished",
        "scope": scope or "drift-log",
        "drift_entries_cleared": len(drift),
    })
    print("\nSync complete.")
