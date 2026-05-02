# claude-wiki

A documentation management system for [Claude Code](https://claude.ai/code). Maintains `CLAUDE.md` files for a target git repo in a separate wiki repo and symlinks them in — so Claude Code loads the right docs at the right path depth automatically, without polluting the target's git history.

Requires Python 3.11+ and the [Claude Code CLI](https://claude.ai/code) (`claude --version` to verify).

## Quick start

```bash
# 1. Init — create config, absorb existing docs, install hooks
mkdir my-project-wiki && cd my-project-wiki
git init
claude-wiki init --repo-path /path/to/your/repo

# 2. Update schema — edit schema.yaml to promote paths to doc nodes (append +), then:
claude-wiki sync

# 3. Done — symlinks are live, docs are generated
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

Created on `init`. Injected into every `update` prompt as house rules — edit it to control how the LLM writes and structures docs. Never overwritten after first creation.

### `templates/CLAUDE.template.md`

Placeholder written by `push` when a new doc is created. Contains a "not yet populated" banner with instructions to run `update`. No LLM involved.

---

> **Key:** `D` Deterministic · `🤖` LLM · `D+🤖` Deterministic with optional LLM step

## Commands

---

### `init` `D`

One-time setup. Run from an empty wiki directory. Fully deterministic — no LLM is invoked. After init, run `update` when you're ready to generate doc content.

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
7. Prints any new-entry paths that need `update` to generate content

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

### `update` `🤖`

Uses the Claude CLI to read source files and update the relevant wiki doc. When run without `--scope`, picks up entries from both `drift.jsonl` (changed source files) and `new-entry.jsonl` (newly created docs), then clears both logs on completion. Injects `templates/instructions.md` as house rules into every prompt.

New docs (placeholder content) use a "generate from scratch" prompt; Claude scans all files under the path. Updated docs use a targeted "update sections that changed" prompt.

```bash
# Update from drift + new-entry logs (clears both after)
claude-wiki update

# Update a specific directory or file
claude-wiki update --scope frontend/survey
claude-wiki update --scope frontend/survey/App.tsx

# Update all files changed vs a git ref
claude-wiki update --scope main
claude-wiki update --scope diff       # all staged + unstaged
claude-wiki update --scope staged     # staged only

# Non-interactive — no questions, best-effort update (for CI)
claude-wiki update --no-prompt
```

Interactive mode (default) allows Claude to propose new schema paths, ask for clarification, and create new docs. `--no-prompt` restricts tools to `Read,Edit` — existing docs only, no new files.

---

### `sync` `D+🤖`

Full cycle: `push` → `update` → `push`. The standard command after a batch of changes. `update` clears drift and new-entry logs as part of its run.

```bash
claude-wiki sync

# Sync a specific area
claude-wiki sync --scope frontend/survey

# Structure only, no LLM
claude-wiki sync --no-llm
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

## Hooks

All hooks are **fully deterministic** — no LLM is ever invoked by a hook. The drift log they build up is consumed later by `update` or `sync`, which you run manually.

| Hook | Trigger | What it runs | `D/🤖` |
|------|---------|-------------|--------|
| `pre-commit` | Before every commit | `detect-drift --staged` | `D` |
| `post-checkout` | After checkout / clone | `push` | `D` |

### `hook-setup` stages

Run automatically by `init` (or manually via `claude-wiki hook-setup`). Each hook stage can be skipped independently. The `.claude-wiki/` directory is always created — hooks depend on it.

Hooks call `.claude-wiki/wiki` in the target repo. The wrapper resolves the wiki root from `.claude-wiki/wiki-path` — no hardcoded paths, no separate config file needed.

| Stage | Flag to skip | `D/🤖` | What it does |
|-------|-------------|--------|-------------|
| `.claude-wiki/` | (always) | `D` | Creates `.claude-wiki/wiki` wrapper script and `.claude-wiki/llm.md` symlink in the target repo. Adds `.claude-wiki` to `.gitignore`. This is the single entry point for all wiki commands run from the target repo. |
| `pre-commit` | `--no-pre-commit` | `D` | Installs `.git/hooks/pre-commit`. Before each commit, logs changed source files and their mapped wiki docs to `drift.jsonl`. Always exits 0 — never blocks a commit. |
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
│   └── instructions.md      # House rules injected into every update prompt
├── logs/
│   ├── drift.jsonl          # Changed source files (cleared by update no-scope)
│   ├── new-entry.jsonl      # New schema entries (cleared by update after processing)
│   └── sync.jsonl           # Permanent update history
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
    └── llm.md               # Symlink → <wiki>/llm.md
```

Developers can run any wiki command directly from the target repo:

```bash
.claude-wiki/wiki update --scope src/payments
.claude-wiki/wiki sync
.claude-wiki/wiki push
```

Claude Code agents working in the target repo can do the same — they see the `CLAUDE.md` outputs via symlinks and can trigger updates through `.claude-wiki/wiki`.

### Doc metadata footer

Every managed `CLAUDE.md` gets a metadata block appended automatically:

```
<!-- claude-wiki-meta
Location: frontend/survey/CLAUDE.md
LastTouchedBy: claude-wiki update
ChangeDate: 2026-05-01
WikiCommitID: abc1234
-->
```

This block is updated on every `update` or `push` run and stripped when you `eject`.
