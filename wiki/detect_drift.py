"""detect-drift: Log changed source files that correspond to wiki docs.

Called by the pre-commit hook (staged only). Safe to call manually.
"""

import subprocess

from .lib import (
    DRIFT_LOG,
    append_log, best_schema_match, get_repo_path,
    git_all_changed_files, git_head_hash, git_staged_files,
    load_drift_log, load_schema, now_ts, schema_paths, set_flag,
)


def run_detect_drift(staged_only: bool = False):
    repo = get_repo_path()
    schema = load_schema()
    s_paths = schema_paths(schema)

    files = git_staged_files(repo) if staged_only else git_all_changed_files(repo)
    if not files:
        return

    trigger = "pre-commit" if staged_only else "manual"
    commit = git_head_hash(repo)
    existing = {e["path"] for e in load_drift_log()}

    logged = 0
    for f in files:
        if f in existing:
            continue
        match = best_schema_match(f, s_paths)
        if match is None:
            continue

        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-status", "--cached" if staged_only else "HEAD"],
            capture_output=True, text=True,
        )
        event = "modified"
        for line in result.stdout.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] == f:
                status = parts[0][0]
                event = {"A": "added", "D": "deleted", "M": "modified"}.get(status, "modified")
                break

        wiki_doc = f"docs/{match}/CLAUDE.md" if match else "docs/CLAUDE.md"
        append_log(DRIFT_LOG, {
            "ts": now_ts(),
            "trigger": trigger,
            "event": event,
            "path": f,
            "wiki_doc": wiki_doc,
            "commit": commit,
        })
        logged += 1

    if logged:
        print(f"  [drift] Logged {logged} file(s) to {DRIFT_LOG.relative_to(DRIFT_LOG.parent.parent)}")
        set_flag("drift_detected")
