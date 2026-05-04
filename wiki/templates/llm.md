# claude-wiki — LLM Reference

This directory is a **claude-wiki** wiki root. It holds CLAUDE.md documentation for a target
git repo and symlinks them in so Claude Code loads them automatically at the correct path depth.

## Directory layout

```
<wiki-root>/
├── schema.yaml          # Which paths in the target repo are documented
├── config.json          # Target repo path — gitignored, set by `init`
├── docs/                # All documentation; mirrors target repo structure
│   └── <path>/CLAUDE.md
├── templates/
│   ├── CLAUDE.template.md   # Structure every CLAUDE.md must follow
│   ├── instructions.md      # House rules for writing CLAUDE.md content
│   ├── WIKI_UPDATE.md       # Step-by-step guide for updating docs manually
│   └── WIKI_MERGE.md        # Step-by-step guide for resolving doc conflicts
├── logs/
│   ├── drift.jsonl      # Source files changed since last doc sync
│   ├── new-entry.jsonl  # New schema paths pending documentation
│   ├── conflict.jsonl   # Paths with both a wiki doc and an unmanaged repo file
│   ├── flags.json       # Current wiki status flags (see below)
│   └── sync.jsonl       # Permanent sync history
└── llm.md               # This file

<target-repo>/
├── CLAUDE.md            # Symlink → <wiki>/docs/CLAUDE.md
├── <path>/CLAUDE.md     # Symlinks for each managed path
└── .claude-wiki/        # Gitignored — created by `hook-setup`
    ├── wiki             # Wrapper script: runs claude-wiki from within the target repo
    ├── wiki-path        # Path to this wiki root (read by wrapper)
    ├── flags.json       # Symlink → <wiki>/logs/flags.json
    ├── schema.yaml      # Symlink → <wiki>/schema.yaml
    ├── CLAUDE.template.md  # Symlink → <wiki>/templates/CLAUDE.template.md
    ├── instructions.md     # Symlink → <wiki>/templates/instructions.md
    └── agents/             # LLM guidance docs (symlinks + user-added blank docs)
        ├── llm.md          # Symlink → <wiki>/llm.md  (this file)
        ├── WIKI_UPDATE.md  # Symlink → <wiki>/templates/WIKI_UPDATE.md
        ├── WIKI_MERGE.md   # Symlink → <wiki>/templates/WIKI_MERGE.md
        └── <name>.md       # User-added agent docs (via `add-agent --name <name>`)
```

## ⚠ Symlink mechanic — read before editing

**Files in `.claude-wiki/` and `.claude-wiki/agents/` are symlinks back to the wiki.** Editing `.claude-wiki/schema.yaml`
edits the canonical `schema.yaml` in the wiki root. The same applies to `CLAUDE.template.md` and the files in `agents/`.

**Do not copy these files.** Do not duplicate content from them into CLAUDE.md files.
Instead, reference them by path and use the CLI to act on them:

- To add a new documented path → edit `.claude-wiki/schema.yaml`, then run `.claude-wiki/wiki push`
- To absorb an unmanaged doc → run `.claude-wiki/wiki pull`
- To repair broken symlinks → run `.claude-wiki/wiki push --verify`
- To check what needs attention → run `.claude-wiki/wiki status`

## Checking flags before any doc work

Always read `.claude-wiki/flags.json` before starting any task that touches documentation.
Flags signal pending work. A missing key means no action needed for that concern.

| Flag | Meaning | How to resolve |
|------|---------|----------------|
| `new_entry` | New schema paths were added; placeholder docs exist | Read `new-entry.jsonl` for the paths. Populate each doc manually. Run `clear-flags --flag new_entry` when done. |
| `drift_detected` | Source files changed since docs were last reviewed | Read `drift.jsonl` — each entry has `from_commit`, `to_commit`, and `changed_files`. Run `git diff <from_commit>..<to_commit> -- <path>/` to see what changed. Update affected docs following `.claude-wiki/agents/WIKI_UPDATE.md`. Run `clear-flags --flag drift_detected` when done — this stamps `SourceCommitID=HEAD` on each drifted doc. |
| `multiple_versions` | Both a wiki doc and an unmanaged repo file exist at the same path | Read `conflict.jsonl` for the paths. Resolve each by running `pull --strategy wiki` or `pull --strategy repo`. Run `clear-flags` when done — it auto-clears if the conflict log is empty. |
| `docs_out_of_sync` | Broken/missing symlinks were found and repaired | Run `.claude-wiki/wiki push --verify` to ensure all symlinks are intact. Check if any repaired docs have placeholder content and populate them manually. |

Example flags.json:
```json
{
  "new_entry": true,
  "drift_detected": true,
  "multiple_versions": true,
  "last_updated": "2026-05-03T10:00:00Z"
}
```

## schema.yaml

Controls which paths have managed CLAUDE.md files. Edit via `.claude-wiki/schema.yaml`.

| Suffix | Meaning |
|--------|---------|
| `+`    | Managed — has a doc in `docs/` and a symlink in the target |
| `~`    | Untracked — real file stays in target, wiki ignores it |
| (none) | Structural — nesting container only, no doc |

`root+` is the sentinel for the repo root (maps to `docs/CLAUDE.md`).

## Adding a new documented path

1. Edit `.claude-wiki/schema.yaml` — add the path with `+` (e.g. `frontend/payments+:`)
2. Run `.claude-wiki/wiki push` — creates placeholder doc + symlink, logs to `new-entry.jsonl`,
   sets `new_entry` flag
3. Populate the new doc manually
4. Run `.claude-wiki/wiki clear-flags --flag new_entry` when done

## Commands

| Command | What it does |
|---------|-------------|
| `init --repo-path <path>` | One-time setup: save config, absorb existing docs, create symlinks, install hooks |
| `hook-setup` | (Re)create `.claude-wiki/` and install git hooks in the target repo |
| `push` | Reconcile schema ↔ docs ↔ symlinks; log new entries |
| `push --verify` | Rebuild any broken or missing symlinks |
| `pull` | Scan target for unmanaged CLAUDE.md files and absorb them |
| `pull --strategy wiki/repo` | Resolve conflicts during pull instead of flagging them |
| `detect-drift [--staged]` | Recompute drift by comparing each doc's `SourceCommitID` to HEAD; logs per-doc entries with commit range and changed files |
| `status [--scope X]` | Show pending drift statistics — docs that need attention |
| `eject [--scope X]` | Copy docs back as real files, detaching them from the wiki |
| `clear-flags [--flag X]` | Clear one or all flags; auto-clears flags whose log is empty |
| `add-agent --name <name>` | Create a blank `.md` doc in `.claude-wiki/agents/` (no template) |

## hook-setup stages

| Stage | Flag to skip | What it does |
|-------|-------------|--------------|
| `.claude-wiki/` | (always) | Creates wrapper script, symlinks for flags.json, schema.yaml, CLAUDE.template.md, instructions.md; creates `agents/` with llm.md, WIKI_UPDATE.md, WIKI_MERGE.md symlinks. Adds to .gitignore. |
| pre-commit | `--no-pre-commit` | Logs changed source files to drift.jsonl before each commit. Non-blocking. |
| post-checkout | `--no-post-checkout` | Runs `push` after checkout to create missing docs and symlinks. |
| skip-worktree | `--no-skip-worktree` | Marks CLAUDE.md symlinks so git never shows them as changes. |

## Key invariants

- Always run `claude-wiki` from the wiki root directory (`config.json` must be present).
- CLAUDE.md symlinks in the target repo are pointers — `docs/<path>/CLAUDE.md` in the wiki is the source of truth.
- `schema.yaml` is the source of truth for which paths are managed.
- Files in `.claude-wiki/` and `.claude-wiki/agents/` are symlinks — editing them edits the wiki directly. Never copy them.
- `instructions.md`, `WIKI_UPDATE.md`, and `WIKI_MERGE.md` are user-owned — they are never overwritten after first creation.
- Files added via `add-agent` are plain files in the target repo, not symlinks — they are not managed by the wiki.
