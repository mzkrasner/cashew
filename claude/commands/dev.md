# Dev - Project Session Manager

Use the `dev` command to manage tmux-backed project sessions in `~/projects/`.

**Note:** Session names use `_` internally, but you always type `/` in commands.

**Auto-start:** New sessions start their auto-command (`pi` for worktrees, `claude` for regular repos) automatically.
**Detached by default:** Creating a new session always creates it detached and prints how to attach. Running `dev` against an existing session attaches to it. This means agents can safely create sessions without needing a terminal.
**Pi runs in sub-sessions:** Pi always runs in `/pi` sub-sessions (e.g., `dev repo/worktree/pi`), not the base session. This is consistent across `dev wt` and manual session creation.
**Important:** For implementation worktrees, use `/pi` sub-sessions (not `/claude`) so message tools target the correct agent session.
**Rule:** Never nudge a task-role or worktree agent without reading its last message first:
```bash
dev pi-status <session> --messages 1
# optionally check pending queue
dev queue-status <session> -m
# if you need to wait for completion
dev pi-subscribe <session>
```

**Orchestrator messaging rule:** Use `dev task send ...` for persistent task roles and `dev send-pi ...` for direct worktree sessions. Only use `dev send` for raw tmux key input when you explicitly need keystrokes (e.g., Enter/Ctrl-C).

**Anti-pattern (do NOT do this):**
```bash
# ❌ don't split send + subscribe
- dev send-pi <session> --no-await "message"
- dev pi-subscribe <session>

# ✅ do this instead
- dev send-pi <session> "message" &
```

**Issue assignment helper:** `dev pi-gh-assign <issue>` sends a standardized GH issue prompt to the current repo’s `/pi` session based on your cwd. Run it from inside `~/projects/<repo>/<worktree>/`. It auto-subscribes like `send-pi`, so if it times out you can recover with `dev pi-subscribe <session> --last` (or `--last-or-next`). If the agent replies with a plan, follow up with `dev send-pi <session> "feedback"` to continue.

**WARNING:** `pi-subscribe` blocks until the NEXT completion. If the agent is idle and no message is queued, it can hang indefinitely. Check `dev pi-status <session> --messages 1` and `dev queue-status <session> -m` first. If idle, use `--last` (or `--last-or-next`) instead.


## Quick Reference

```bash
dev                              # List active sessions
dev hub                          # Open hub session at ~/projects root
dev ls --full                    # Full project tree
dev hub/<sub>                    # Hub sub-session (e.g., hub/claude)
dev <repo>                       # Open main session for a repo
dev <repo>/<worktree>            # Open specific worktree (for worktree-based repos)
dev <repo>/<worktree>/<sub>      # Open sub-session (prefer /pi for worktrees)
dev new <repo> <git-url>         # Clone repo with worktree structure
dev init <repo>                  # Create new local repo with worktree structure (no remote)
dev wt <repo> <branch> [base]    # Add a new worktree for a branch
dev project tasks <repo>         # Project-level dashboard across active tasks
dev project review <repo>        # Project orchestrator queue summary
dev project poll <repo>          # Poll all task role lanes in a project
dev project sessions <repo>      # Show all task-role session mappings
dev task new <repo> <slug>       # Create task artifacts in .cashew/tasks/<slug>
dev task status <repo> <slug>    # Show task state + artifacts
dev task sessions <repo> <slug>  # Show task role session mappings
dev task open <repo> <slug> [role] # Open a persistent task role session
dev task open-current <repo> <slug> [role] # Open the most relevant role for this task
dev task open-slice <repo> <slug> <slice-id> [role] # Open a role for the current slice
dev task slice new <repo> <slug> <slice-id> # Declare a commit slice
dev task slice start <repo> <slug> <slice-id> # Start the current slice
dev task slice status <repo> <slug> <slice-id> # Show per-slice status
dev task slice validate <repo> <slug> <slice-id> # Validate one slice + run its checks
dev task slice request-revision <repo> <slug> <slice-id> # Send current slice back for more work
dev task slice reopen <repo> <slug> <slice-id> # Reopen current slice for implementation
dev task slice approve-commit <repo> <slug> <slice-id> # Authorize commit for one slice
dev task slice committed <repo> <slug> <slice-id> <commit> # Record committed slice
dev task lock-plan <repo> <slug> # Mark the plan locked
dev task validate <repo> <slug> [phase] # Validate task artifacts + approvals
dev task signoff <repo> <slug> <phase> <role> <decision> [note] # Record review signoff
dev task send <repo> <slug> <role> <message> # Send to a task role session
dev task poll <repo> <slug>     # Show last status across task roles
dev task nudge <repo> <slug> <role> <message> # Show status, then send a task-role message
dev task review <repo> <slug>   # Show task status plus role-session review
dev task verify <repo> <slug>   # Run verification-contract commands
dev task start-impl <repo> <slug> [worktree] # Start implementation after plan lock
dev task ready-merge <repo> <slug> # Mark task ready after implementation validation
dev task merged <repo> <slug> [merge-ref] # Record that merge actually happened
dev task close <repo> <slug> [--cleanup] # Close task lifecycle and optionally cleanup worktree
dev cleanup <repo>/<worktree>    # Remove worktree + branch + session (requires --force if unmerged)
dev kill <session>               # Kill a specific session
dev kw <repo> <name>             # Start a knowledge-worker session
dev kw-list [repo]               # List knowledge workers
dev kw-tags <repo>/<name> <tags> # Set knowledge-worker tags
dev kw-note <repo>/<name> <note> # Set knowledge-worker note
dev pi-status <session>          # Check agent status/last messages
dev review <session>             # Show completion status + git log/diff
dev queue-status <session> -m    # Check pending queue
dev pi-subscribe <session>       # Wait for the next completion entry (default)
dev pi-subscribe <session> --last # Show the last completion and exit
dev pi-subscribe <session> --last-or-next # Show last if present, else wait
dev pi-subscribe <session> --timeout 120  # Exit after N seconds if no completion
dev send <session> <keys>        # Send raw tmux keys (direct input)
dev send-pi <session> "message"   # Send + wait (default)
dev send-pi <session> --no-await "message" # Send without waiting
dev pi-gh-assign <issue>          # Send GH issue assignment to current repo pi session (auto-subscribes)
```

## Project Structure

### Worktree-based repos (recommended)
```
~/projects/<repo>/
├── .bare/           # bare git repository
├── main/            # main branch worktree
├── feature-x/       # feature branch worktree
└── bugfix-y/        # another worktree
```

### Regular repos
```
~/projects/<repo>/
├── .git/
└── (files)
```

## Session Naming Convention

| You Type | Session Name | Use Case |
|----------|--------------|----------|
| `dev hub` | `hub` | Root session at ~/projects |
| `dev hub/claude` | `hub_claude` | Claude sub-session at root |
| `dev myapp` | `myapp` | Regular repo main session |
| `dev myapp/main` | `myapp_main` | Worktree main session |
| `dev myapp/main/pi` | `myapp_main_pi` | Preferred Pi sub-session (worktrees) |
| `dev myapp/main/claude` | `myapp_main_claude` | Claude sub-session |
| `dev myapp/main/kw-arch` | `myapp_main_kw-arch` | Knowledge-worker session |

Common sub-session names:
- `pi` - Preferred worktree agent session
- `claude` - Claude Code (avoid for worktree agents)
- `server` - Dev server
- `tests` - Running tests
- `build` - Build processes

## Workflow Examples

### Using the hub (projects root)
```bash
dev hub                      # session at ~/projects root
dev hub/claude               # claude session for managing projects
```

### Starting a new project
```bash
dev new myapp git@github.com:user/myapp    # from existing remote
dev init myapp                              # brand new, no remote
dev myapp                                   # opens main worktree
```

### Working on a feature branch
```bash
dev wt myapp feature-auth    # create worktree + start pi in /pi sub-session (detached)
dev myapp/feature-auth/pi    # attach to pi sub-session
```

### SSH reconnection
```bash
ssh myserver
dev                          # see what's running
dev myapp/main/pi            # attach to existing Pi session
```

## Task Workflow

Use `dev task ...` for non-trivial work that needs persistent planning and review memory.

The primary orchestrator agent remains the controller of the workflow. These commands are support primitives for the orchestrator. Persistent reviewers and implementers advise or execute, but they do not advance task state autonomously.

For a single project, assume one dedicated orchestrator agent may be managing multiple active tasks at once. Use the `dev project ...` commands to get the project-level view instead of reconstructing it task-by-task.

### Task artifacts

`dev task new <repo> <slug>` creates:
- `.cashew/tasks/<slug>/task.json`
- `.cashew/tasks/<slug>/proposal.md`
- `.cashew/tasks/<slug>/plan.md`
- `.cashew/tasks/<slug>/plan-review-codex.md`
- `.cashew/tasks/<slug>/plan-review-claude.md`
- `.cashew/tasks/<slug>/plan-open-issues.md`
- `.cashew/tasks/<slug>/implementation-notes.md`
- `.cashew/tasks/<slug>/implementation-review-codex.md`
- `.cashew/tasks/<slug>/implementation-review-claude.md`
- `.cashew/tasks/<slug>/verification-contract.md`
- `.cashew/tasks/<slug>/slices/`

Persistent sessions help, but these files are the durable task record and the source of truth.

Cashew stores these artifacts under the target repo's `.cashew/` directory and automatically adds both `.cashew/` and `.agent/` to the repo's local `.git/info/exclude`, so orchestration and local analysis state stay local and are not accidentally committed.

### Commit slices are mandatory

For non-trivial work, the planner must define commit slices up front.

Cashew enforces this by making slices first-class:
- the plan is not lockable until at least one slice exists
- large tasks should have multiple slices
- each slice is its own review/feedback/re-review checkpoint
- a slice may only be committed after `dev task slice approve-commit ...`
- slices advance sequentially; only the current non-committed slice may move forward

Each slice lives under:
- `.cashew/tasks/<slug>/slices/<slice-id>/slice.md`
- `.cashew/tasks/<slug>/slices/<slice-id>/verification.md`
- `.cashew/tasks/<slug>/slices/<slice-id>/status.json`
- `.cashew/tasks/<slug>/slices/<slice-id>/rounds/round-01/review-codex.md`
- `.cashew/tasks/<slug>/slices/<slice-id>/rounds/round-01/review-claude.md`
- `.cashew/tasks/<slug>/slices/<slice-id>/rounds/round-01/implementer-response.md`
- `.cashew/tasks/<slug>/slices/<slice-id>/rounds/round-01/state.json`

Slice review rounds are append-only. When a slice is sent back for revision, Cashew advances to a new round directory and keeps prior rounds intact.

Declare slices explicitly:
```bash
dev task slice new <repo> <slug> slice-01
dev task slice new <repo> <slug> slice-02
```

### Task roles

Supported roles:
- `plan-owner-codex`
- `plan-review-codex`
- `plan-critic-claude`
- `implementer-codex`
- `implementation-review-codex`
- `implementation-critic-claude`

Default:
```bash
dev task open <repo> <slug>
```
opens `plan-owner-codex`.

Recommended serious-task setup:
```bash
dev task new <repo> <slug>
dev task slice new <repo> <slug> slice-01
dev task open <repo> <slug> plan-owner-codex
dev task open <repo> <slug> plan-review-codex
dev task open <repo> <slug> plan-critic-claude
dev task validate <repo> <slug> plan
```

### Plan lock gate

Implementation should not start until the plan is locked:
```bash
dev task lock-plan <repo> <slug>
dev task start-impl <repo> <slug> [worktree]
```

`dev task start-impl` refuses to proceed until `task.json` has `planLocked = true`.

Implementation review closes the loop:
```bash
dev task send <repo> <slug> implementer-codex "implement the locked plan"
dev task slice start <repo> <slug> slice-01
dev task review <repo> <slug>
dev task slice validate <repo> <slug> slice-01
dev task slice approve-commit <repo> <slug> slice-01
dev task slice committed <repo> <slug> slice-01 <commit>
dev task verify <repo> <slug>
dev task open <repo> <slug> implementation-review-codex
dev task open <repo> <slug> implementation-critic-claude
dev task validate <repo> <slug> implementation
dev task ready-merge <repo> <slug>
dev task merged <repo> <slug>
dev task close <repo> <slug> [--cleanup]
```

`dev task ready-merge` validates implementation artifacts and approvals before moving the task to `ready_to_merge`.
It also refuses to proceed until every declared slice is in `committed`.

`dev task signoff ...` is still available as a manual override, but the normal path is to let `dev task validate ...` read authoritative review state from the structured state files.

After the real merge occurs, record it explicitly with `dev task merged ...`, then close the lifecycle with `dev task close ...`.

### Model pinning

Task roles are pinned by role rather than left to ambient machine defaults.

Current defaults:
- Codex roles use Pi with:
  - `--provider ${CASHEW_CODEX_PROVIDER:-openai}`
  - `--model ${CASHEW_CODEX_MODEL:-gpt-5.4}`
  - `--thinking ${CASHEW_CODEX_THINKING:-high}`
  - `--session-dir <task role session dir>`
- Claude roles use:
  - `claude --dangerously-skip-permissions --model ${CASHEW_CLAUDE_MODEL}`

For serious task roles:
- do not launch bare `pi`
- `CASHEW_CLAUDE_MODEL` must be set for Claude task roles

### Guardrails in target repos

The task workflow is additive. It does not replace target-repo engineering rails.

Existing repo-local standards remain authoritative:
- `AGENTS.md`
- hooks
- CI workflows
- lint / format
- typecheck
- unit tests
- integration tests
- DB integration tests
- build / migration checks

Use `verification-contract.md` to record the concrete checks that apply to the target repo before implementation starts.

For execution, put the actual commands inside fenced `bash` or `sh` blocks. `dev task verify` executes those commands from the worktree when one exists, otherwise from the repo base directory.

### Slice review loop

The slice is the commit checkpoint. The orchestrator should run this loop until the slice is satisfactory:

1. implementer produces uncommitted slice work
2. reviewers inspect the uncommitted state
3. implementer independently verifies reviewer claims
4. implementer revises or rejects findings with rationale
5. orchestrator re-runs `dev task slice validate ...`
6. only when clean, authorize commit with `dev task slice approve-commit ...`
7. after the real commit exists in git, record it with `dev task slice committed ...`

Important:
- reviewer findings are advisory, not automatically true
- each slice round has authoritative structured state in `rounds/<round>/state.json`
- reviewer markdown files are explanatory; state transitions come from structured fields in `state.json`
- the implementer must respond to each finding ID in `implementerResponses`
- `dev task slice committed ...` verifies the commit exists, is on the current worktree HEAD path, is new relative to `main` when available, and only touches files declared in the slice scope
- implementation validation also requires a clean worktree before merge readiness

### Project-level orchestration

For a project orchestrator managing several active tasks:

```bash
dev project tasks <repo>
dev project review <repo>
dev project poll <repo>
dev project sessions <repo>
```

These commands surface:
- current slice per task
- per-task queue/priority bucket
- role-session mappings
- cross-task warnings:
  - shared worktree
  - overlapping declared slice scopes
  - overlapping changed files across active tasks

## Structured Review State

Review markdown is narrative only. Authoritative machine state now lives in JSON files.
Cashew validates these files against versioned JSON Schema first, then applies workflow-specific semantic checks.

Task-level reviews:
- `.cashew/tasks/<slug>/plan-review-codex.state.json`
- `.cashew/tasks/<slug>/plan-review-claude.state.json`
- `.cashew/tasks/<slug>/implementation-review-codex.state.json`
- `.cashew/tasks/<slug>/implementation-review-claude.state.json`

Slice-level reviews:
- `.cashew/tasks/<slug>/slices/<slice-id>/rounds/<round>/state.json`

Required task-level state shape:
```json
{
  "schemaVersion": 1,
  "decision": "pending",
  "blockingFindings": [],
  "nonBlockingFindings": [],
  "summary": "",
  "updatedAt": null
}
```

Required slice round state shape:
```json
{
  "schemaVersion": 1,
  "round": 1,
  "reviewerStates": {
    "codex": {
      "decision": "pending",
      "blockingFindings": [],
      "nonBlockingFindings": [],
      "summary": "",
      "updatedAt": null
    },
    "claude": {
      "decision": "pending",
      "blockingFindings": [],
      "nonBlockingFindings": [],
      "summary": "",
      "updatedAt": null
    }
  },
  "implementerResponses": [],
  "verification": {
    "lastRun": {
      "at": null,
      "commands": [],
      "failures": [],
      "success": false
    }
  }
}
```

Each finding must have:
- `id`
- `title`
- `claim`
- `evidence`

Each implementer response must include:
- `findingId`
- `status` as `confirmed`, `rejected`, or `partially_applied`
- `verificationMethod`
- `evidence`
- `resolutionSummary`

## Worktree Workflow

Worktree branches are local by default. You do **not** need to push them to a remote just to coordinate. Merge by switching to `main` and merging locally after the task reaches `ready_to_merge`.

**Main session = orchestrator**, feature worktrees = isolated implementation environments.

### Starting implementation for a task
1. In the main Claude session, create or choose the feature worktree:
   ```bash
   dev wt <repo> <feature-branch>
   ```
2. Use the task workflow to bind implementation to the approved plan:
   ```bash
   dev task start-impl <repo> <slug> <feature-branch>
   dev task send <repo> <slug> implementer-codex "implement the approved current slice"
   ```
3. Review and commit one slice at a time through:
   ```bash
   dev task slice start <repo> <slug> <slice-id>
   dev task slice validate <repo> <slug> <slice-id>
   dev task slice approve-commit <repo> <slug> <slice-id>
   dev task slice committed <repo> <slug> <slice-id> <commit>
   ```

### Completing a task-backed feature
1. Finish all slices and task-level validation:
   ```bash
   dev task verify <repo> <slug>
   dev task validate <repo> <slug> implementation
   dev task ready-merge <repo> <slug>
   ```
2. Merge locally from `main`, then record closure:
   ```bash
   git merge <feature-branch>
   dev task merged <repo> <slug> [merge-ref]
   dev task close <repo> <slug> [--cleanup]
   ```

## Knowledge Workers (long-running domain agents)

Knowledge workers are persistent Pi sessions anchored on `main` for design, review, risk analysis, and planning. They are advisors, not implementers. Requires the `kw-role` extension.

**Commands:**
```bash
dev kw <repo> <name> --tags "arch,api"                    # Start a KW
dev kw <repo> <name> --tags "arch,api" --bootstrap "..."   # Start with custom bootstrap
dev kw-list <repo>                                         # List all KWs
dev kw-tags <repo>/<name> "arch,api"                       # Update tags (from shell)
dev kw-note <repo>/<name> "Owns auth contracts"            # Update note (from shell)
```

Inside a KW session, `/kw-tags` and `/kw-note` update metadata automatically.

**Messaging (send-pi now awaits by default):**
```bash
dev send-pi <repo>/main/kw-<name> "message"                # Send + wait for response
dev send-pi <repo>/main/kw-<name> --no-await "message"      # Send without waiting

dev pi-subscribe <repo>/main/kw-<name>                     # Wait for next completion
dev pi-subscribe <repo>/main/kw-<name> --last              # Show last completion

dev pi-subscribe <repo>/main/kw-<name> --last-or-next      # Show last if present, else wait
```

**WARNING:** `pi-subscribe` blocks until the NEXT completion. If the agent is idle and no message is queued, it can hang indefinitely. Check `dev pi-status <session> --messages 1` and `dev queue-status <session> -m` first. If idle, use `--last` (or `--last-or-next`) instead.

**How to use them:** Ask KWs focused questions — "where are the architecture risks in this plan?", "review this change for data-timeliness issues." They respond with constraints, edge cases, and guidance. Use their output to shape plans and slices before handing work to implementer sessions.

**Role boundaries:** KWs advise — they don't create worktrees, merge branches, or run destructive commands. If asked to implement, they respond with a plan instead.

## Killing sessions (use sparingly)

**Do NOT kill agent sessions (PM or worktree) just because they errored or hit `context_length_exceeded`.** A crash is not completion. Unstaged changes and in-progress edits remain on disk in the worktree.

**Do this instead:**
1. Start a new session: `dev <repo>/<worktree>/pi`
2. Send a consolidated prompt summarizing what they were doing and warn about unstaged changes to preserve.

**Only kill sessions when:**
- The worktree is merged/complete and no further work is needed, or
- You are abandoning the work entirely, or
- The session is broken beyond recovery.

## Reviewing implementation before merging

Use the task and slice workflow rather than an ad hoc review loop:

1. Read the relevant role/session status before nudging:
   ```bash
   dev task review <repo> <slug>
   dev task poll <repo> <slug>
   ```
2. Validate the current slice and require implementer verification of reviewer findings:
   ```bash
   dev task slice validate <repo> <slug> <slice-id>
   ```
3. Only authorize commit for that slice when validation passes:
   ```bash
   dev task slice approve-commit <repo> <slug> <slice-id>
   ```
4. Before merge, require task-level verification and implementation validation:
   ```bash
   dev task verify <repo> <slug>
   dev task validate <repo> <slug> implementation
   dev task ready-merge <repo> <slug>
   ```

## Tips

1. Always use sub-sessions for long-running processes (Claude, servers)
2. Use `dev task send ...` for persistent task roles and `dev send-pi <session> <message>` for direct worktree sessions. Use `dev send` only for raw keystrokes.
3. `dev cleanup` now blocks if the branch has commits not in main; re-run with `--force` only after deciding it's safe to discard.
4. The session persists even if you close SSH or terminal (until reboot)
5. Use `dev` with no args to see all projects and active sessions
6. Worktree repos let you work on multiple branches simultaneously
7. Main Claude is the project orchestrator. Use it to manage tasks, slices, and merges.
