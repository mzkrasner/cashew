---
name: codex-review
description: Run a stateless final-pass review with OpenAI Codex CLI after the persistent task review workflow has already happened
argument-hint: [commit|--uncommitted|--base main|file-path]
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Codex Final Review

Use OpenAI Codex CLI as a **stateless final-pass reviewer**.

This command is **not** the primary serious-task review mechanism.

For non-trivial work, the normal path is:
1. persistent task planning/review via `dev task ...`
2. implementation review through persistent task roles
3. `dev task verify ...`
4. optional final stateless Codex CLI review via `/codex-review`

Use `/codex-review` for:
- final sanity checks before merge
- small direct changes
- one extra detached Codex verdict after the main review loop is complete

## Arguments

$ARGUMENTS

- If blank and in a feature worktree: review all commits since branching from main (`--base main`)
- If blank and on main: review the last commit (`--commit HEAD`)
- If `HEAD` or a commit SHA: review that specific commit
- If `--uncommitted`: review staged + unstaged + untracked changes
- If a file path: review that specific file interactively

## Step 0: Check prerequisites

First verify Codex CLI is installed:

```bash
command -v codex || echo "CODEX_NOT_FOUND"
```

If `CODEX_NOT_FOUND`, stop and tell the user:
> Codex CLI is not installed. Install it with `npm install -g @openai/codex` and set `OPENAI_API_KEY` in your environment.

## Step 1: Determine review scope and run Codex

Figure out what to review based on arguments and git context.

**Worktree review (final pass before merge):**
```bash
codex review --base main
```

**Specific commit:**
```bash
codex review --commit HEAD
```

**Uncommitted changes:**
```bash
codex review --uncommitted
```

**Specific file (interactive):**
```bash
codex --full-auto "Review this file for bugs, security issues, and edge cases. File: FILE_PATH" < FILE_PATH
```

If no arguments are provided, detect context:
- If current branch is not `main` → use `--base main`
- If on `main` → use `--commit HEAD`

## Step 2: Wait for results

`codex review` runs non-interactively and outputs findings directly. For large reviews this may take 1-3 minutes.

## Step 3: Present findings

Present Codex's findings in a structured format:

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| Critical/High/Medium/Low | Description | file:line | How to fix |

If Codex found no issues, say so clearly.

## Step 4: Verdict

Based on the findings, give a clear verdict:

- **MERGE** — No issues or only minor style nits
- **FIX FIRST** — Issues that should be fixed before merging. List them.
- **RETHINK** — Architectural or design problems that need the agent to redo work

If the verdict is FIX FIRST and you're the orchestrator, send feedback to the relevant implementer session or reopen the task review flow as needed:
```bash
dev send-pi <repo>/<worktree>/pi "Codex review found issues: <summary>. Fix these before marking done."
```

## Review Focus Areas

1. **Bugs & Logic Errors** — Off-by-one, null checks, race conditions, unwrap/panic in Rust
2. **Security Issues** — Injection, auth bypass, data exposure, unsafe blocks
3. **Edge Cases** — Empty inputs, boundaries, error paths, malformed data
4. **Performance** — N+1 queries, memory leaks, inefficient loops, unnecessary clones
5. **Type Safety** — Missing checks, unsafe casts, stringly-typed APIs
6. **Interface Compatibility** — Does this worktree's output match what other worktrees expect?
