# Cashew

A dev-environment bootstrap and orchestration layer built around:
- a **Claude primary orchestrator**
- one dedicated project orchestrator per project
- persistent **Codex-backed Pi roles** for planning, review, and implementation
- a `dev` session/worktree/task manager
- Claude skills/commands for setup and orchestration
- a local-only `/cashew-feedback` command for capturing Cashew workflow friction

## Example prompts (human → Claude)

1. **Setup Cashew**
   - "Use /setup to set up my dev environment."

2. **Create a worktree to fix a README**
   - “Clone `git@github.com:user/repo.git` and make a `fix-readme` worktree.”

3. **Ask Claude to message a Pi worker**
   - “Tell the README agent how to improve the README.”

4. **Merge when done**
   - “Merge `fix-readme` into `main`.”

## Orientation (read this first)

**Observed**
- This repo contains: a `dev` CLI, Claude skills/commands, and a Pi extension.
- `dev` creates **tmux** sessions by default.
- Worktrees are stored at `~/Projects/<repo>/<worktree>`; bare repos live at `~/Projects/<repo>/.bare`.
- If you choose a different projects folder during setup, export it as `CASHEW_PROJECTS_DIR` so `dev` and agent instructions agree on the same path.
- Serious-task workflow uses `.cashew/tasks/<slug>/...` artifacts plus persistent task-role sessions.
- Cashew treats `.cashew/` and `.agent/` as local working state and adds both to the repo's local `.git/info/exclude` automatically when you create or initialize a project/task.

**Assumed (current defaults)**
- Claude is the **primary orchestrator** at the projects root and repo roots.
- Codex-backed Pi roles are used for persistent planner/reviewer/implementer sessions.
- Claude can still send messages to Pi workers running in worktrees.

**Desired (intended workflow)**
- One repo → many worktrees → many resumable agents.
- Claude remains the top-level controller.
- Serious work uses persistent task roles:
  - `plan-owner-codex`
  - `plan-review-codex`
  - `plan-critic-claude`
  - `implementer-codex`
  - `implementation-review-codex`
  - `implementation-critic-claude`
- Task progression is explicit: plan, review, lock, implement, verify, implementation review, merge.
- Commit slices are first-class checkpoints inside a task. Large plans should define multiple slices up front.

**Model defaults**
- Codex-backed Pi task roles are pinned through:
  - `CASHEW_CODEX_PROVIDER`
  - `CASHEW_CODEX_MODEL`
  - `CASHEW_CODEX_THINKING`
- Claude roles can be pinned with:
  - `CASHEW_CLAUDE_MODEL`

If these defaults are wrong for you, keep the tool and change the role env vars or startup commands.

## What Cashew Actually Does

Cashew ships Claude skills/commands that call `dev`. Answering the core question:

**What `dev` gives the orchestrator**
- **Persistent sessions** for long-running sub-agents (tmux sessions that survive disconnects).
- **Worktree-native isolation** so multiple agents can work without interfering (`dev new`, `dev wt`).
- **Predictable addressing** of agent contexts via `repo/worktree/sub` session names.
- **Task lifecycle primitives** via `dev task ...`.
- **Pinned serious-task roles** for Codex-backed Pi sessions and Claude critic sessions.
- **Queue hooks** for Pi messaging (`dev send-pi`, `dev pi-status`, `dev queue-status`).

Humans mostly use `dev` to reattach when they want to inspect or take over a long-running context.

What it does **not** do:
- It does **not** enforce Docker usage.
- It does **not** manage your credentials beyond the setup step.

Checksum: **`dev` is a session/worktree/task manager with an orchestrator-centric workflow; it is not an autonomous workflow engine.**

## Operational workflows (agent-first)

### 1) Multiple agents, one repo, zero interference

**Observed**
- Each worktree has its own session and agent.

**Workflow**
- Claude creates worktrees and assigns Pi to each worktree.
- Humans rarely touch `dev` unless they need to inspect a session.

Example (what Claude runs):
```bash
dev new myapp git@github.com:user/myapp    # from existing remote
dev init myapp                              # or create from scratch (no remote)
dev wt myapp feature-auth
```

### 2) Drop into any sub-agent’s context when needed

**Observed**
- Sessions are addressable by `repo/worktree/sub`.

**Workflow**
- Use `dev` only when you need to interrupt, inspect, or manually assist.

Examples (human reattach):
```bash
dev myapp/feature-auth            # Reattach to Pi in that worktree
dev myapp/feature-auth/pi          # Explicit Pi sub-session (preferred)
dev myapp/feature-auth/claude      # Claude helper (avoid for worktree agents)
dev myapp/feature-auth/tests       # Reattach to long-running tests
```

### 3) Remote persistence (resume at any time)

**Observed**
- Sessions persist across SSH disconnects.

**Workflow**
- SSH in, list sessions, reattach to any agent context.

```bash
ssh myserver
dev                              # List running contexts
dev myapp/feature-auth            # Resume Pi agent
```

### Worktree → agent mapping (default, not enforced)

- `dev <repo>/<worktree>` → **Pi auto-starts** (implementation agent)
- `dev <repo>/<worktree>/pi` → **Preferred** explicit Pi session (use this for agent sessions)
- `dev <repo>` (non-worktree repo) → **Claude auto-starts** (orchestrator)
- `dev hub/claude` → **Claude** for cross-repo coordination

## How Sessions Map to Names

**Observed**
- Session names use `_` internally; you type `/` in commands.

Example mapping:
- `dev myapp/feature-auth/pi` → session name `myapp_feature-auth_pi`
- `dev myapp/feature-auth/claude` → session name `myapp_feature-auth_claude`

This is a constraint of session naming, not a feature. If it breaks for you, change `SEP` in `bin/dev`.

## Setup (by Claude skill)

1. **Install Claude Code**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Ask Claude to configure the machine**:
   ```bash
   claude --dangerously-skip-permissions
   ```
   Then say: "Use /setup to set up my dev environment."

   Claude will:
   - Ask for your projects folder name
   - Install Docker, Git, GitHub CLI, `jq`, and tmux
   - Configure SSH keys for GitHub
   - Install the `dev` command
   - Install Claude skills/commands

3. **Optional: install Pi + queue/subscribe/knowledge-worker extensions**:
   ```bash
   CASHEW_ROOT="$(git rev-parse --show-toplevel)"
   npm install -g @mariozechner/pi-coding-agent
   mkdir -p ~/.pi/agent/extensions
   ln -sf "$CASHEW_ROOT/pi/extensions/message-queue.ts" ~/.pi/agent/extensions/message-queue.ts
   ln -sf "$CASHEW_ROOT/pi/extensions/pi-subscribe.ts" ~/.pi/agent/extensions/pi-subscribe.ts
   ln -sf "$CASHEW_ROOT/pi/extensions/kw-role.ts" ~/.pi/agent/extensions/kw-role.ts
   ```
   This enables: `dev send`, `dev send-pi`, `dev pi-status`, `dev pi-subscribe`, `dev queue-status`, `dev kw`.

4. **Cashew role defaults**
   Setup now writes role defaults into your shell config so serious-task roles are pinned consistently:
   ```bash
   export CASHEW_PROJECTS_DIR=...
   export CASHEW_CODEX_PROVIDER=openai
   export CASHEW_CODEX_MODEL=gpt-5.4
   export CASHEW_CODEX_THINKING=high
   export CASHEW_CLAUDE_MODEL=<your-claude-alias>
   ```
   The core serious-task path uses Pi-backed Codex roles, so no separate global Codex config file is required for that path.

## Serious Task Workflow

For non-trivial work, use persistent task roles and task artifacts:

```bash
dev project tasks <repo>
dev project review <repo>
dev project poll <repo>
dev project sessions <repo>
dev task new <repo> <slug>
dev task slice new <repo> <slug> slice-01
dev task slice new <repo> <slug> slice-02   # for larger work
dev task open <repo> <slug> plan-owner-codex
dev task open <repo> <slug> plan-review-codex
dev task open <repo> <slug> plan-critic-claude
dev task validate <repo> <slug> plan
dev task lock-plan <repo> <slug>
dev task start-impl <repo> <slug> [worktree]
dev task send <repo> <slug> implementer-codex "implement the locked plan"
dev task slice start <repo> <slug> slice-01
dev task slice validate <repo> <slug> slice-01
dev task slice approve-commit <repo> <slug> slice-01
dev task slice committed <repo> <slug> slice-01 <commit>
dev task verify <repo> <slug>
dev task validate <repo> <slug> implementation
dev task ready-merge <repo> <slug>
```

Important:
- Claude remains the primary orchestrator.
- each project has its own dedicated orchestrator agent
- Task-role sessions are persistent support lanes used by the orchestrator.
- Validation reads authoritative approval state from structured `.state.json` files. Review markdown remains explanatory.
- Structured state files are validated against versioned JSON Schema before Cashew applies workflow-specific semantic checks.
- `verification-contract.md` should contain fenced runnable `bash`/`sh` checks for the target repo.
- The plan is not lockable until at least one commit slice exists.
- Each slice must pass its own review loop before commit authorization.
- Slices are sequential. Only the current non-committed slice should move through implementation/review.
- Reviewer findings are advisory; the implementer must independently verify them and record that verification in the current slice round's `state.json`. `implementer-response.md` remains the narrative explanation.
- Recording a slice commit is not just bookkeeping; Cashew verifies the commit exists in git and stays within the declared slice scope.
- project-level commands surface active-task queues, session mappings, and cross-task warnings for shared worktrees, overlapping scopes, and overlapping changed files.

## Capturing Cashew Feedback

When you notice Cashew friction or something feels wrong, capture it locally with:

```text
/cashew-feedback
```

This command:
- writes a structured local feedback artifact into the local Cashew repo
- captures expected vs actual behavior, repro steps, and context
- does not create a GitHub issue

Use it from the orchestrator when you want a problem preserved for later Cashew improvement work without interrupting the current project flow.

## Cashew TUI (optional)

Launch the tmux + fzf TUI:
```bash
cashew
```

- Left pane: project/worktree/session tree (type to filter)
- Right pane: status for the highlighted entry; Enter attaches the session in the right pane
- Uses tmux panes (no embedded terminal), so the left navigator stays visible

Requirements: `tmux`, `fzf`.

## Docker Isolation (recommended, not enforced)

**Observed**
- `dev` does not create containers or set `COMPOSE_PROJECT_NAME`.

**Assumed best practice**
- Use one Docker project per worktree to avoid cross-branch contamination.

Example:
```bash
export COMPOSE_PROJECT_NAME="myapp-feature-auth"
docker compose up -d      # Containers: myapp-feature-auth-db, etc.
docker compose down -v    # Teardown only this worktree
```

**Port conflicts:** `COMPOSE_PROJECT_NAME` does not change host ports. Prefer env‑configurable ports in `docker-compose.yml`:
```yaml
ports:
  - "${DB_HOST_PORT:-5432}:5432"
```
Then per worktree:
```bash
export DB_HOST_PORT=5433
export DATABASE_URL="postgres://candles:candles@localhost:${DB_HOST_PORT}/candles"
```

If you do not use Docker, remove this from your workflow. Nothing in `dev` depends on it.

## Screenshots (optional)

**Unknown**
- We don’t ship screenshots yet. If you want them, define which views matter:
  - `dev` list output
  - a Pi session attached to a worktree
  - a Claude hub session at `~/Projects`

If you want me to add screenshots, tell me which host and which terminal theme to capture.

## Repo Contents

```
cashew/
├── bin/
│   └── dev                      # Project session manager CLI
├── .claude/
│   └── skills/
│       └── setup/
│           └── SKILL.md         # /setup skill for bootstrapping
├── claude/
│   ├── global/
│   │   └── CLAUDE.md            # Global context for all Claude sessions
│   ├── commands/
│   │   ├── dev.md               # /dev command
│   │   └── codex-review.md      # Stateless final Codex review
│   └── skills/
│       ├── prompting-worktree-agents/
│       │   └── SKILL.md         # Socratic prompting loop for worktree agents
│       └── repo-quality-rails-setup/
│           └── SKILL.md         # Optional quality rails setup skill
└── pi/
    └── extensions/
        ├── message-queue.ts     # Queue integration for Pi
        ├── pi-subscribe.ts      # Completion subscription
        └── kw-role.ts           # Knowledge-worker role support
```

## Requirements

- **Node.js** (for Claude Code)
- **macOS or Linux** (setup skill handles dependencies)

## License

MIT
