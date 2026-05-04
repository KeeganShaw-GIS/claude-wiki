# claude-wiki

A documentation management system for [Claude Code](https://claude.ai/code). Maintains `CLAUDE.md` files for a target git repo in a separate wiki repo and symlinks them in — so Claude Code loads the right docs at the right path depth automatically, without polluting the target's git history.

Requires the [Claude Code CLI](https://claude.ai/code) (`claude --version` to verify).

## Install

**macOS / Linux — standalone binary (no Python required):**

```bash
curl -fsSL https://raw.githubusercontent.com/KeeganShaw-GIS/claude-wiki/main/install.sh | bash
```

**Any platform — pip (requires Python 3.11+):**

```bash
# Latest
pipx install git+https://github.com/KeeganShaw-GIS/claude-wiki.git

# Specific version
pipx install git+https://github.com/KeeganShaw-GIS/claude-wiki.git@v0.1.0
```

---

## Quick start

```bash
# 1. Init — create config, absorb existing docs, install hooks
mkdir my-project-wiki && cd my-project-wiki
git init
claude-wiki init --repo-path /path/to/your/repo

# 2. Edit schema.yaml to promote paths to doc nodes (append +), then:
claude-wiki push    # create placeholder docs + symlinks

# 3. Done — symlinks are live, populate docs manually
```

Every command must be run from the wiki root (where `config.json` lives).

### Ejecting

`eject` copies each wiki doc back into the target repo as a real file, removes the symlinks, and stops the wiki from tracking those paths. After ejecting, the target repo owns its `CLAUDE.md` files again — the wiki no longer manages or updates them.

```bash
claude-wiki eject           # eject all managed paths
claude-wiki eject --scope frontend/survey  # eject a single path
```

---

## Config files

### `schema.yaml`

Defines which paths in the target repo have managed `CLAUDE.md` files. Generated automatically on `init` from the target repo's top-level directories — promote paths to doc nodes by appending `+`.

```yaml
# + = managed doc node (CLAUDE.md in docs/ + symlink in target)
# ~ = untracked (real file stays in target, wiki ignores it)
# (no suffix) = structural container only, no doc
root+:
  frontend+:
    admin+:
    survey+:
  server+:
  local-docs:
    as-built~:
```

### `config.json`

Set by `init`, gitignored. Stores the target repo path and options.

```json
{
  "repo_path": "/path/to/your/repo",
  "repo_name": "my-repo",
  "skip_worktree": true,
  "claude_path": "/optional/path/to/claude"
}
```

Set `claude_path` if `claude` is not on your `PATH`.

---

## Document generation

Wiki docs live in `docs/`, mirroring the target repo's path structure:

```
docs/
├── CLAUDE.md               ← target repo root
├── frontend/
│   ├── CLAUDE.md           ← target frontend/
│   └── survey/
│       └── CLAUDE.md       ← target frontend/survey/
└── server/
    └── CLAUDE.md
```

### Output → symlinks

For each `+` node in `schema.yaml`, `push` creates a symlink in the target repo pointing back to the wiki doc:

```
target/frontend/survey/CLAUDE.md  →  ../../../my-wiki/docs/frontend/survey/CLAUDE.md
```

Editing `docs/frontend/survey/CLAUDE.md` in the wiki is immediately reflected in the target. Symlinks are marked `skip-worktree` in the target repo so git never sees them as changes.

### `templates/instructions.md`

Created on `init`. House rules for writing CLAUDE.md content — edit it to control doc style and structure. Never overwritten after first creation.

### `templates/CLAUDE.template.md`

Placeholder written by `push` when a new doc is created. Contains a "not yet populated" banner. Populate docs manually after running `push`.

---

> **Key:** `D` Deterministic

## Commands

---

### `init` `D`

One-time setup. Run from an empty wiki directory. Fully deterministic — no LLM is invoked. After init, populate placeholder docs manually.

```bash
claude-wiki init --repo-path /path/to/repo

# Skip absorbing existing CLAUDE.md files from the target
claude-wiki init --repo-path /path/to/repo --no-detect-target-docs

# Skip installing git hooks
claude-wiki init --repo-path /path/to/repo --no-hooks
```

`init` runs these steps in order:
1. Saves `config.json` `D`
2. Generates `llm.md` and `templates/instructions.md` `D`
3. Generates `schema.yaml` from the target repo's top-level directories `D`
4. Absorbs any existing `CLAUDE.md` files from the target via `pull` (skip with `--no-detect-target-docs`) `D`
5. Runs `push` to create docs and symlinks `D`
6. Runs `hook-setup` to install git hooks (skip with `--no-hooks`) `D`
7. Prints any new-entry paths that need manual doc population

---

### `hook-setup` `D`

Installs git hooks and the `.claude-wiki/` wrapper in the target repo. Called automatically by `init`; run manually to re-install or adjust stages. Fully deterministic — no LLM.

Hooks locate the wiki automatically by resolving the `CLAUDE.md` symlink at the target repo root — no separate config file needed.

```bash
claude-wiki hook-setup

# Skip individual stages
claude-wiki hook-setup --no-pre-commit
claude-wiki hook-setup --no-post-checkout
claude-wiki hook-setup --no-skip-worktree
```

---

### `pull` `D`

Scans the target repo for unmanaged real `CLAUDE.md` files (not symlinks), absorbs their content into `docs/`, replaces them with symlinks, and adds them to `schema.yaml`. Logs each absorbed path to `logs/new-entry.jsonl`.

```bash
claude-wiki pull
```

Use this when cloning a target repo that already has `CLAUDE.md` files, or when someone added one manually without going through the wiki.

---

### `push` `D`

Reconciles `schema.yaml` ↔ `docs/` ↔ symlinks in the target. Run after editing `schema.yaml`. New docs are written as deterministic placeholders and logged to `logs/new-entry.jsonl` — no LLM.

```bash
# Sync schema with docs and symlinks
claude-wiki push

# Also absorb unmanaged CLAUDE.md files from the target
claude-wiki push --detect-target-docs

# Rebuild only broken or missing symlinks
claude-wiki push --verify
```

---

### `detect-drift` `D`

Computes drift by comparing each doc's `SourceCommitID` footer against `HEAD` in the target repo. For each doc with changes, logs a `drift.jsonl` entry containing the commit range and changed files — enough to run `git diff <from>..<to> -- <path>/` directly. Idempotent: re-running overwrites stale entries rather than appending.

Called automatically by the pre-commit hook (`--staged`). Safe to run manually at any time, including on repos that never had the hook installed.

```bash
claude-wiki detect-drift           # recompute all drift from SourceCommitIDs
claude-wiki detect-drift --staged  # narrow to staged files only
```

---

### `status` `D`

Shows pending drift statistics — which docs need attention and why. Reads `drift.jsonl` and `new-entry.jsonl`; no LLM involved.

```bash
# Show all pending docs from drift + new-entry logs
claude-wiki status

# Show docs affected by a specific path, ref, or diff
claude-wiki status --scope frontend/survey
claude-wiki status --scope diff
claude-wiki status --scope staged
```

---

### `eject` `D`

Copies each managed `CLAUDE.md` back into the target repo as a real file and removes the symlinks. The target repo owns its docs again — the wiki stops tracking and updating those paths. Wiki docs in `docs/` are preserved untouched. Run `push` to re-attach.

```bash
# Eject all managed paths
claude-wiki eject

# Eject a single path
claude-wiki eject --scope frontend/survey
```

---

### `add-agent` `D`

Creates a blank `.md` file in `.claude-wiki/agents/` of the target repo. Use this to add custom agent guidance docs that live alongside the standard `llm.md`, `WIKI_UPDATE.md`, and `WIKI_MERGE.md` symlinks.

```bash
claude-wiki add-agent --name researcher
# creates .claude-wiki/agents/researcher.md  (empty)
```

---

## Hooks

All hooks are **fully deterministic** — no LLM is ever invoked by a hook. The drift log they build up is visible via `claude-wiki status`.

| Hook | Trigger | What it runs | `D/🤖` |
|------|---------|-------------|--------|
| `pre-commit` | Before every commit | `detect-drift --staged` | `D` |
| `post-checkout` | After checkout / clone | `push` | `D` |

### `hook-setup` stages

Run automatically by `init` (or manually via `claude-wiki hook-setup`). Each hook stage can be skipped independently. The `.claude-wiki/` directory is always created — hooks depend on it.

Hooks call `.claude-wiki/wiki` in the target repo. The wrapper resolves the wiki root from `.claude-wiki/wiki-path` — no hardcoded paths, no separate config file needed.

| Stage | Flag to skip | `D/🤖` | What it does |
|-------|-------------|--------|-------------|
| `.claude-wiki/` | (always) | `D` | Creates `.claude-wiki/wiki` wrapper script, operational symlinks (flags.json, schema.yaml, CLAUDE.template.md, instructions.md), and the `agents/` subdirectory with llm.md, WIKI_UPDATE.md, WIKI_MERGE.md symlinks. Adds `.claude-wiki` to `.gitignore`. |
| `pre-commit` | `--no-pre-commit` | `D` | Installs `.git/hooks/pre-commit`. Before each commit, runs `detect-drift --staged` to recompute drift for staged files. Always exits 0 — never blocks a commit. |
| `post-checkout` | `--no-post-checkout` | `D` | Installs `.git/hooks/post-checkout`. After checkout or clone, runs `push` to create any missing docs and symlinks. New docs get a placeholder template and are logged to `new-entry.jsonl`. |
| `skip-worktree` | `--no-skip-worktree` | `D` | Marks every managed `CLAUDE.md` symlink `skip-worktree` so git never shows them as unstaged changes. Skip if you use sparse checkout or a tool that resets index flags. |

---

## Layout

### Wiki repo

```
my-project-wiki/
├── schema.yaml              # Source of truth for which paths are managed
├── config.json              # Target repo path — gitignored
├── llm.md                   # LLM reference for working in this wiki
├── docs/                    # All documentation; mirrors target repo structure
│   └── <path>/CLAUDE.md
├── templates/
│   ├── CLAUDE.template.md   # Placeholder written when push creates a new doc
│   ├── instructions.md      # House rules for writing CLAUDE.md content
│   ├── WIKI_UPDATE.md       # Step-by-step guide for updating docs (user-editable)
│   └── WIKI_MERGE.md        # Step-by-step guide for resolving conflicts (user-editable)
├── logs/
│   ├── drift.jsonl          # Per-doc drift entries with commit range + changed files
│   ├── new-entry.jsonl      # New schema entries pending documentation
│   └── sync.jsonl           # Permanent sync history
└── scripts/
    └── wiki.py              # Backward-compat shim for git hooks
```

### Target repo (after `hook-setup`)

```
my-target-repo/
├── CLAUDE.md                # Symlink → <wiki>/docs/CLAUDE.md
├── <path>/CLAUDE.md         # Symlinks for each managed path
└── .claude-wiki/            # Gitignored — created by hook-setup
    ├── wiki                 # Wrapper: runs claude-wiki from inside the target repo
    ├── wiki-path            # Path to the wiki root (read by wrapper)
    ├── flags.json           # Symlink → <wiki>/logs/flags.json
    ├── schema.yaml          # Symlink → <wiki>/schema.yaml
    ├── CLAUDE.template.md   # Symlink → <wiki>/templates/CLAUDE.template.md
    ├── instructions.md      # Symlink → <wiki>/templates/instructions.md
    └── agents/              # LLM guidance docs
        ├── llm.md           # Symlink → <wiki>/llm.md
        ├── WIKI_UPDATE.md   # Symlink → <wiki>/templates/WIKI_UPDATE.md
        ├── WIKI_MERGE.md    # Symlink → <wiki>/templates/WIKI_MERGE.md
        └── <name>.md        # User-added agent docs (via `add-agent --name <name>`)
```

Developers can run any wiki command directly from the target repo:

```bash
.claude-wiki/wiki push
.claude-wiki/wiki status
```

Claude Code agents working in the target repo can do the same — they see the `CLAUDE.md` outputs via symlinks and can run wiki commands through `.claude-wiki/wiki`.

### Doc metadata footer

Every managed `CLAUDE.md` gets a metadata block appended automatically:

```
<!-- claude-wiki-meta
Location: frontend/survey/CLAUDE.md
LastTouchedBy: claude-wiki push
ChangeDate: 2026-05-01
WikiCommitID: abc1234
SourceCommitID: def5678
-->
```

`SourceCommitID` is the target repo commit the doc was last reviewed against. `detect-drift` computes `git diff <SourceCommitID>..HEAD -- <path>/` to find what changed. `clear-flags --flag drift_detected` stamps it to the current HEAD. Stripped when you `eject`.
