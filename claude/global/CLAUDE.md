# Global Claude Context

## Project Session Management

This environment uses `dev` - a session manager for projects in `<projects-dir>/`.

**Key concepts:**
- Projects use git worktrees: `<projects-dir>/<repo>/<worktree>/` (e.g., `<projects-dir>/replay/main/`)
- Sessions use `_` separator internally but you type `/` (e.g., `dev replay/main/pi`)
- Sub-sessions like `pi`, `server`, `tests` keep long-running processes separate
- Use `/pi` for worktree agents (avoid `/claude` for worktree agent sessions)

**Common commands:**
```bash
dev                           # List active sessions
dev ls --full                 # Full project tree
dev <repo>/main/claude        # Orchestrator session (worktree-based repos)
dev <repo>                    # Orchestrator session (regular repos — starts Claude)

dev <repo>/<worktree>/pi      # Implementer session (starts Pi)
dev wt <repo> <branch>        # Add worktree + start pi in /pi sub-session (detached)
dev task new <repo> <slug>    # Create task artifacts under .cashew/tasks
dev task open <repo> <slug>   # Open default plan-owner-codex task session
dev task lock-plan <repo> <slug>   # Lock a reviewed plan
dev task start-impl <repo> <slug> [worktree]  # Start impl only after plan lock
dev cleanup <repo>/<worktree> # Remove worktree + branch + all sessions
dev kill <session>            # Kill a session
dev pi-status <session>       # Check agent status/last messages
dev queue-status <session> -m # Check pending queue
```

If you notice Cashew workflow friction, capture it locally with:
```text
/cashew-feedback
```
This writes a structured local feedback artifact into the Cashew repo for later triage.

**Rule:** Never nudge a worktree agent without reading its last message first:
```bash
dev pi-status <session> --messages 1
# optional queue check
dev queue-status <session> -m
```

**Messaging rule:** When you expect a response, use `dev send-pi <session> --await "message"` to send and wait in one step. Use plain `dev send-pi` only for fire-and-forget.

**Before merging or reviewing worktree output:**
```bash
dev review-loop
```
Run the loop manually. Always execute:
```bash
bash sleep 300
```
Run it in the foreground, then return to step 1 and repeat. Do **not** write scripts, nohup, or background loops.

Only review commits once the agent confirms it's done or asks for review.

## Serious Task Workflow

For non-trivial features, use task artifacts and persistent task-role sessions instead of a one-shot review workflow.

**Control model**
- The primary orchestrator agent remains in charge.
- Cashew task commands are orchestration primitives used by the orchestrator.
- Reviewer and implementer sessions do not advance task state on their own.
- The orchestrator decides when to ask for review, when to record signoff, when to validate, and when to move the task forward.
- Each project has its own dedicated orchestrator agent. Different projects have different orchestrators.
- A project orchestrator may manage multiple active tasks simultaneously.

**Task roles**
- `plan-owner-codex` — primary planner / plan maintainer
- `plan-review-codex` — persistent Codex reviewer for plan quality and implementation review
- `plan-critic-claude` — persistent architecture / risk critic
- `implementer-codex` — implementation session, opened only after plan lock
- `implementation-review-codex` — persistent Codex implementation reviewer on the worktree
- `implementation-critic-claude` — optional persistent implementation auditor

**Default serious-task flow**
1. Create task artifacts:
   ```bash
   dev task new <repo> <slug>
   ```
   Immediately declare commit slices. The planner must define them up front:
   ```bash
   dev task slice new <repo> <slug> slice-01
   # add more slices for larger work
   ```
2. Keep the planner/reviewer sessions persistent for the full task:
   ```bash
   dev task open <repo> <slug> plan-owner-codex
   dev task open <repo> <slug> plan-review-codex
   dev task open <repo> <slug> plan-critic-claude
   ```
3. As the orchestrator, iterate on `.cashew/tasks/<slug>/plan.md`, the declared slice definitions under `.cashew/tasks/<slug>/slices/`, `plan-review-codex.md`, `plan-review-claude.md`, and `plan-open-issues.md` until blockers are resolved.
   Validation infers approval state from the review docs. Use explicit signoff only if you need a manual override:
   ```bash
   dev task validate <repo> <slug> plan
   ```
4. Lock the plan:
   ```bash
   dev task lock-plan <repo> <slug>
   ```
5. Start implementation:
   ```bash
   dev task start-impl <repo> <slug> [worktree]
   ```
6. Keep plan-owner, plan-review, and critic sessions alive while implementation proceeds. Use the same task artifacts to review implementation against the locked plan.
   Operate on the task directly:
   ```bash
   dev task send <repo> <slug> implementer-codex "implement the locked plan"
   dev task poll <repo> <slug>
   dev task nudge <repo> <slug> implementer-codex "status update and next blocker?"
   dev task review <repo> <slug>
   ```
   For a repo-wide view across many active tasks:
   ```bash
   dev project tasks <repo>
   dev project review <repo>
   dev project poll <repo>
   dev project sessions <repo>
   ```
7. Run the slice loop for each commit slice. The slice is the commit checkpoint:
   ```bash
   dev task slice start <repo> <slug> <slice-id>
   dev task slice status <repo> <slug> <slice-id>
   dev task slice validate <repo> <slug> <slice-id>
   dev task slice approve-commit <repo> <slug> <slice-id>
   dev task slice committed <repo> <slug> <slice-id> <commit>
   ```
   The implementer must independently verify reviewer claims before applying them. Reviewer findings are advisory. The implementer records confirmed, rejected, or partially-applied findings in `implementer-response.md`.
   Slices progress sequentially. Only the current non-committed slice should be in active implementation/review.
8. Before merge, run implementation review explicitly:
   ```bash
   dev task verify <repo> <slug>
   dev task open <repo> <slug> implementation-review-codex
   dev task open <repo> <slug> implementation-critic-claude
   dev task validate <repo> <slug> implementation
   dev task ready-merge <repo> <slug>
   ```
   `ready-merge` requires every declared slice to already be committed and the worktree to be clean.
9. After the actual merge, close the task lifecycle explicitly:
   ```bash
   dev task merged <repo> <slug> [merge-ref]
   dev task close <repo> <slug> [--cleanup]
   ```

**Important:** The task workflow is additive. It does not replace the target repo's engineering guardrails.

## Target Repo Guardrails Are Authoritative

Cashew orchestrates work inside target repos. It does not weaken or replace repo-local standards.

When a target repo already has quality rails, those remain authoritative:
- `AGENTS.md`
- pre-commit / pre-push hooks
- CI workflows
- linting / formatting
- typechecking
- unit tests
- integration tests
- DB integration tests
- build / migration / release checks

When a repo lacks those rails, use Cashew guidance to add them. When they already exist, preserve them and make them part of task done-ness and mergeability.

## Update Cashew (recommended)

Periodically update Cashew so you have the latest skills/commands. Go to your Cashew repo and pull:

```bash
cd <cashew-root>
git pull
```

## Worktree Workflow

Worktree branches are local by default. You do **not** need to push them to remote to coordinate. Merge locally into `main` when ready.

**Your role depends on which worktree you're in:**

### If you're in `main` worktree → You're the orchestrator

**CRITICAL: Never implement features directly in main. Always delegate to worktree agents.**

Your job is planning, quality, delegation, and integration. Follow this sequence:

1. **Plan** — For non-trivial work, create a task and use the serious-task workflow above. Treat `.cashew/tasks/<slug>/plan.md` as the source of truth. If the repo has a remote, check `gh issue list` for open issues relevant to the current work.
2. **Quality gates** — For new projects, run `/repo-quality-rails-setup` before any delegation. For existing projects, preserve existing repo-local rails and make them part of the task verification contract.
3. **Delegate** — Create worktrees and send work to Pi agents:
   ```bash
   dev wt <repo> <feature>
   dev send-pi <repo>/<feature>/pi "instructions"
   ```
   Use `/prompting-worktree-agents` for non-trivial tasks to make agents reason before coding.

   **Every go-ahead message to a Pi agent MUST include:**
   > "When done: commit all changes using conventional commit format (type(scope): message) with a structured body. Include `Co-Authored-By: Codex <noreply@openai.com>` as the last line of every commit. If this work addresses a GitHub issue, reference it in the commit (e.g., `refs #42`). Run `codex review --base main`, fix any issues, commit the fixes, then report done with your commit hash."

4. **Monitor** — After delegating, **immediately enter an autonomous polling loop**. Do NOT wait for the user to ask for status. Poll every 2-3 minutes until all worktrees are merged:
   ```bash
   # Check each active worktree agent
   dev pi-status <repo>/<feature>/pi --messages 1
   ```
   On each poll:
   - If agent reports done → verify commit exists (`git log` in worktree), then proceed to step 5
   - If agent reports done but didn't commit → tell it to commit
   - If agent is stuck or idle for 10+ minutes → nudge with a status check
   - If agent asks a question → answer it
   Between polls, use `sleep 120` or `sleep 180`. **Never stop polling until all worktrees are merged and cleaned up.**

5. **Review & merge** — Only after agent confirms completion, has committed, and codex review passed:
   ```bash
   # CRITICAL: verify the branch has NEW commits beyond main
   git log --oneline main..<feature>
   # If this output is EMPTY → the agent did NOT commit. Do NOT merge.
   # Tell the agent: "Your branch has no commits. Commit your changes."

   # Only if commits exist:
   git merge --quiet <feature>

   # After merge, verify HEAD actually moved:
   git log --oneline -1  # should show the feature's commit, not the old HEAD
   ```
6. **Cleanup** — After merge:
   ```bash
   COMPOSE_PROJECT_NAME=<repo>-<feature> docker compose down -v
   dev cleanup <repo>/<feature>
   ```
7. **End-of-session triage** (only if repo has a remote) — Spend 2-5 minutes on `gh issue list`. Close anything resolved by merged work. Label remaining issues. This is not a formal process — just a quick scan to keep the backlog honest.

**Small direct changes in main** — For trivial fixes (config tweaks, version bumps, typos) that don't warrant a worktree, the orchestrator may commit directly in main. The same quality bar applies:
1. Make the change
2. Run `codex review --base HEAD~1` to verify
3. Fix any issues flagged
4. Commit using conventional commit format with `Co-Authored-By: Claude <noreply@anthropic.com>`

### If you're in a feature worktree → You're the implementer
- Focus on implementing the feature
- Commit your work locally
- When done, tell the user it's ready for main Claude to merge
- Don't worry about worktree cleanup - main handles that

For full documentation, use the `/dev` skill.

## New Project Bootstrap

```bash
dev new <repo> <git-ssh-url>   # Clone existing remote with worktree structure
dev init <repo>                # Create new local repo with worktree structure (no remote)
```

Then start the orchestrator: `dev <repo>/main/claude`

To add a remote later: `cd <projects-dir>/<repo>/main && git remote add origin <git-ssh-url>`

**Entry point clarification:** For worktree-based repos, `dev <repo>` starts Pi (implementer), not Claude. The orchestrator session is always `dev <repo>/main/claude`.

**IMPORTANT: Always use `dev new` or `dev init` for repos you'll orchestrate.** Regular `git clone` creates a non-worktree repo where `dev wt` won't work. If a repo was cloned normally, re-create it:
```bash
rm -rf <projects-dir>/<repo>
dev new <repo> <git-ssh-url>
```

## Isolated Development Environments

**Run EVERYTHING in Docker** - app, services, tests, CI. The entire dev environment is containerized per worktree.

### What runs in Docker
- **App/services**: Web servers, APIs, workers
- **Databases**: Postgres, Redis, etc.
- **Tests/CI**: Run test suites inside containers
- **Build tools**: Compilers, bundlers, linters

The only things on the host are:
- Your code (mounted into containers)
- Docker itself
- Claude

### Naming convention
Use `COMPOSE_PROJECT_NAME=<repo>-<worktree>` to auto-prefix everything:
```bash
export COMPOSE_PROJECT_NAME="replay-main"
docker compose up -d      # All containers prefixed: replay-main-*
docker compose run test   # Tests in isolated container
docker compose down -v    # Clean teardown, only affects this worktree
```

### Port conflicts (host bindings)
`COMPOSE_PROJECT_NAME` only prefixes container names; it does **not** change host ports. Avoid hardcoded host bindings like `5432:5432` across worktrees.

**Recommended (env‑configurable ports):**
```yaml
services:
  db:
    ports:
      - "${DB_HOST_PORT:-5432}:5432"
  redis:
    ports:
      - "${REDIS_HOST_PORT:-6379}:6379"
```
Then set per worktree:
```bash
export DB_HOST_PORT=5433
export REDIS_HOST_PORT=6380
export DATABASE_URL="postgres://candles:candles@localhost:${DB_HOST_PORT}/candles"
```

**Alternative:** remove host port bindings entirely and run everything inside the Docker network (preferred for tests/CI).

**Optional scheme:** assign static port offsets per worktree (e.g., `main=5432/6379`, `feature-*=5433+N/6380+N`).

### Docker Compose structure
```yaml
name: ${COMPOSE_PROJECT_NAME:-myapp-main}

services:
  app:
    build: .
    volumes:
      - .:/app
    depends_on: [db, redis]

  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7

  test:
    build: .
    command: npm test
    depends_on: [db, redis]
    profiles: [ci]

volumes:
  pgdata:
```

### Running CI locally
```bash
# Run full CI suite in Docker, isolated to this worktree
docker compose run --rm test
docker compose --profile ci up --abort-on-container-exit
```

### Why full Docker isolation
- Each worktree is a completely independent environment
- No port conflicts, no shared databases, no migration disasters
- `feature-x` can run destructive tests while `main` serves traffic
- Matches CI environment exactly - no "works on my machine"
- Clean teardown: `docker compose down -v` nukes everything for that worktree only

## Podman/Docker Machine Safety

**CRITICAL: Never disrupt shared infrastructure.**

- **NEVER restart or stop the Podman machine** (`podman machine stop/restart`) - other critical workloads may be running
- **NEVER stop or remove containers from other projects** - only manage containers in YOUR project's compose namespace
- **Only use `docker compose down`** for your own `COMPOSE_PROJECT_NAME` - never kill containers you didn't create
- If you encounter resource issues, ask the user before taking any action that affects the shared Podman machine

When in doubt, use `docker ps` to see what's running and confirm with the user before stopping anything outside your project scope.

## Replay Monorepo Infrastructure

The replay monorepo runs databases and services locally via Docker/Podman containers.

**CRITICAL: The Podman machine is shared across ALL projects. NEVER stop or restart it.**

### Starting Infrastructure

```bash
# Check if Podman machine is running
/opt/podman/bin/podman machine list

# If Podman machine is not running, start it (this is SAFE - it doesn't affect other containers)
/opt/podman/bin/podman machine start

# ❌ NEVER DO THIS - other projects depend on the running machine:
# /opt/podman/bin/podman machine stop
# /opt/podman/bin/podman machine rm

# Start databases from the repo root
cd <projects-dir>/replay/main
/opt/podman/bin/podman compose up -d postgres redis

# Verify databases are running
/opt/podman/bin/podman ps
pg_isready -h localhost -p 5432
```

### Required Services for Tests

| Service | Port | Required For |
|---------|------|--------------|
| PostgreSQL (TimescaleDB) | 5432 | Integration tests, schema drift checks |
| Redis | 6379 | Some integration tests, caching |

### Checking Service Health

```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Redis
redis-cli ping

# All containers
/opt/podman/bin/podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Common Issues

**Integration tests fail with ECONNREFUSED:5432**
- PostgreSQL isn't running
- Fix: `/opt/podman/bin/podman compose up -d postgres`

**Podman can't connect**
- Podman machine isn't running
- Fix: `/opt/podman/bin/podman machine start`

**Pre-push hook fails on integration tests**
- DATABASE_URL is set but database isn't running
- Fix: Start the database containers before pushing

## Trading Opportunities API

**NEVER submit opportunities to the API unless the user EXPLICITLY says "submit", "insert", "create it", or similar.**

When the user shares opportunity data or asks to "run it through" or "test it":
- Show a dry-run of the payload
- Validate the format
- Ask for explicit confirmation before submitting

```bash
# ❌ FORBIDDEN - Never auto-submit
curl -X POST .../opportunities -d '...'

# ✅ CORRECT - Show what WOULD be submitted, ask first
echo "This would submit:"
cat payload.json
echo "Submit this? (user must explicitly confirm)"
```

This applies to ANY write operation against trading/ops APIs.

## Compact Instructions

When summarizing this conversation for context compaction, preserve the following. Items marked VERBATIM must appear word-for-word in the summary.

**VERBATIM — Role identity:**
> If in `main`, you are the ORCHESTRATOR, not an implementer. Never make direct code changes in `main` except for clearly trivial edits (typos, docs-only wording, config-only tweaks, version bumps). All features, bug fixes, refactors, and any non-trivial changes must be delegated to worktree agents. If uncertain whether a change is trivial, delegate.

**VERBATIM — Polling rule:**
> After delegating, immediately enter an autonomous polling loop. Never stop polling until all worktrees are merged and cleaned up. Never nudge a worktree agent without reading its last message first.

**Preserve in summary form:**
- **Issue tracking**: If the repo has a remote, create GitHub issues for deferred/cross-cutting bugs. The orchestrator owns issue creation, not agents.
- **Orchestrator state**: which worktrees exist, their current status (implementing / awaiting review / fix requested / ready to merge / merged), and what action is next for each
- **Review pipeline**: codex review verdicts per worktree, what issues were found, what fixes were requested, what's still pending
- **Merge order**: the planned sequence and any blocking dependencies between worktrees
- **Agent messages**: the last meaningful status from each Pi agent (done, fixing, blocked, etc.)
- **Quality gates**: whether hooks/linting/CI are set up, and any failures encountered

## Issue Tracking (optional — requires remote repo)

**All issue tracking is conditional on the repo having a GitHub remote.** Check with `git remote get-url origin` before any `gh` command. If there is no remote, skip all issue tracking silently — never fail, never warn, never create a remote.

### When to create an issue

| Situation | Action |
|-----------|--------|
| Bug/task discovered and fixed immediately in the same session (small, local) | No issue needed |
| Bug/task discovered but deferred, cross-cutting, scope-expanding, unclear owner, or recurring | Create issue: `gh issue create --title "..." --label bug` |
| User explicitly reports something | Always create issue |

**The rule:** issue required for anything that might be forgotten, debated, deferred, or handed off. If it's fixed right now and the fix is obvious, skip the issue.

### Issue references in commits

When work addresses an existing issue, reference it:
- Commit subject: `fix(grading): truncate feedback to 3 sentences refs #42`
- PR body: `Closes #42` or `Refs #42`
- Branch naming (optional): `fix/42-grading-validation`

This is soft discipline — don't block work on minting an issue number. But if an issue exists, reference it.

### Labels (minimal set)

Set up once per repo. Only these:
- **Type:** `bug`, `task`, `debt`
- **Status:** `triage`, `ready`, `blocked`
- **Optional:** `agent-found` (discovered by an agent mid-session, not human-reported)

No priority matrices, no severity levels, no story points. If you stop maintaining labels, you have too many.

### Mid-session issue discovery

When the orchestrator or an agent discovers a bug/task during active work:
1. If it can be fixed right now as part of the current worktree — just fix it, no issue
2. If it's out of scope for the current worktree — create an issue immediately so it isn't lost
3. Never ask an agent to create issues — the orchestrator owns issue creation

## Git Preferences

- Never use HTTPS URLs which require interactive authentication
- ALWAYS run `git commit`, `git merge`, and `git push` with `--quiet` flag

### Commit Style (Conventional Commits)

All commits must use conventional commit format: `type(scope): message`

- **Types:** `feat`, `fix`, `chore`, `test`, `perf`, `docs`, `refactor`, `ci`, `build`, `style`
- **Scope:** the package, module, or area affected (e.g., `scanner`, `execution`, `sum-to-one`)
- **Message:** imperative mood, lowercase, no trailing period, descriptive of the actual change
- Keep the subject line under 72 characters
- For non-trivial changes, include a structured body:

```
type(scope): subject line

## Summary
1-3 sentences explaining what changed and why at a high level.

## Changes
- bullet list of specific changes made

## Why
Motivation — what problem, incident, or goal drove this change.
Omit if obvious from the summary.

## Testing
How the change was verified (test commands, test counts, manual checks).
```

- For small changes (one-liners, config tweaks, version bumps), the subject line alone is fine
- Always include `## Summary` at minimum for multi-file changes

### Agent Attribution

Every AI-assisted commit must include a `Co-Authored-By` trailer as the last line of the commit body identifying the agent that wrote the code:

- **Claude Code (orchestrator):** `Co-Authored-By: Claude <noreply@anthropic.com>`
- **Codex / Pi (implementer):** `Co-Authored-By: Codex <noreply@openai.com>`

This is non-optional. If a commit was written by an AI agent and has no co-author line, it is missing attribution. The orchestrator must ensure its go-ahead messages to implementer agents include this requirement, and repos should include commit attribution rules in their `AGENTS.md` so Codex picks them up directly.

```bash
# ❌ Bad
git commit -m "Fixed the bug"
git commit -m "Add feature"
git commit -m "WIP"
git commit -m "Update code"
```

### CRITICAL: Never Bypass Git Hooks

**NEVER use `--no-verify` on commit or push. No exceptions. No rationalizations.**

```bash
# ❌ FORBIDDEN - These commands are NEVER acceptable
git commit --no-verify
git push --no-verify
git commit -n  # -n is shorthand for --no-verify

# ✅ CORRECT - Fix what the hooks are telling you
# If pre-commit fails: fix lint/format/type errors
# If pre-push fails: fix failing tests
```

**Why this matters:**
- Hooks exist to catch problems BEFORE they reach the repository
- A failing hook is telling you something is broken that YOU need to fix
- Bypassing hooks creates broken commits that waste everyone's time
- "It works on my machine" is not an excuse - fix the tests

**When hooks fail:**
1. Read the error output carefully
2. Fix the underlying issue (lint, types, tests, etc.)
3. Re-run the commit/push
4. If tests require infrastructure (database, Redis), ensure it's running
5. If you're stuck, ask for help - but NEVER bypass
