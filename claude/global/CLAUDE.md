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
dev cleanup <repo>/<worktree> # Remove worktree + branch + all sessions
dev kill <session>            # Kill a session
dev pi-status <session>       # Check agent status/last messages
dev queue-status <session> -m # Check pending queue
```

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

1. **Plan** — Read the spec/issue, enter plan mode, design the worktree breakdown
2. **Quality gates** — For new projects, run `/repo-quality-rails-setup` before any delegation. Commit hooks to main so worktree agents inherit them.
3. **Delegate** — Create worktrees and send work to Pi agents:
   ```bash
   dev wt <repo> <feature>
   dev send-pi <repo>/<feature>/pi "instructions"
   ```
   Use `/prompting-worktree-agents` for non-trivial tasks to make agents reason before coding.

   **Every go-ahead message to a Pi agent MUST include:**
   > "Before reporting done, run `codex review --base main` and fix any issues it finds."

4. **Monitor** — Check progress, respond to agent questions:
   ```bash
   dev pi-status <repo>/<feature>/pi --messages 1
   dev queue-status <repo>/<feature>/pi -m
   ```
5. **Review & merge** — Only after agent confirms completion and codex review:
   ```bash
   dev pi-status <repo>/<feature>/pi --messages 1  # confirm done + codex review passed
   # If issues: dev send-pi <repo>/<feature>/pi "fix X"
   # If clean: merge
   cd <projects-dir>/<repo>/main
   git merge --quiet <feature>
   ```
6. **Cleanup** — After merge:
   ```bash
   COMPOSE_PROJECT_NAME=<repo>-<feature> docker compose down -v
   dev cleanup <repo>/<feature>
   ```

### If you're in a feature worktree → You're the implementer
- Focus on implementing the feature
- Commit your work locally
- When done, tell the user it's ready for main Claude to merge
- Don't worry about worktree cleanup - main handles that

For full documentation, use the `/dev` skill.

## New Project Bootstrap (no remote repo)

For brand new projects with no remote, create the worktree-based repo structure manually:

```bash
# 1. Create bare repo with initial commit
mkdir -p <projects-dir>/<repo>/tmp && cd <projects-dir>/<repo>/tmp
git init -b main && echo "# <repo>" > README.md && git add README.md && git commit --quiet -m "initial commit"

# 2. Clone as bare repo, clean up
cd <projects-dir>/<repo> && git clone --bare tmp/.git .bare && rm -rf tmp

# 3. Remove stale origin and create main worktree
cd .bare && git remote remove origin && git worktree add ../main main
```

Then start the orchestrator: `dev <repo>/main/claude`

**Entry point clarification:** For worktree-based repos, `dev <repo>` starts Pi (implementer), not Claude. The orchestrator session is always `dev <repo>/main/claude`.

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

When summarizing this conversation for context compaction, always preserve:
- **Orchestrator state**: which worktrees exist, their current status (implementing / awaiting review / fix requested / ready to merge / merged), and what action is next for each
- **Review pipeline**: codex review verdicts per worktree, what issues were found, what fixes were requested, what's still pending
- **Merge order**: the planned sequence and any blocking dependencies between worktrees
- **Agent messages**: the last meaningful status from each Pi agent (done, fixing, blocked, etc.)
- **Quality gates**: whether hooks/linting/CI are set up, and any failures encountered

## Git Preferences

- Never use HTTPS URLs which require interactive authentication
- ALWAYS run `git commit`, `git merge`, and `git push` with `--quiet` flag

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
