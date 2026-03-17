---
name: setup
description: >
  Bootstrap the Cashew dev environment on this machine. Use this skill whenever
  the user says "set up cashew", "bootstrap my environment", or anything about
  initial setup. If the user is in this repo and asking for setup, they have
  everything they need — just run the steps.
---

# Setup - Bootstrap Dev Environment

You are running from inside the cashew repo. This IS cashew. Setup means:
pull the latest, symlink everything into place, and install Pi extensions.

## End State

| Component | Location | Purpose |
|-----------|----------|---------|
| dev script | `/usr/local/bin/dev` → `bin/dev` | Project session manager |
| cashew launcher | `/usr/local/bin/cashew` → `bin/cashew` | tmux + fzf TUI launcher |
| Global Claude config | `~/.claude/CLAUDE.md` | Cashew context block appended |
| /dev command | `~/.claude/commands/dev.md` → `claude/commands/dev.md` | Session manager docs |
| /codex-review command | `~/.claude/commands/codex-review.md` → `claude/commands/codex-review.md` | Codex CLI code review |
| /prompting-worktree-agents | `~/.claude/skills/prompting-worktree-agents/` → `claude/skills/prompting-worktree-agents/` | Socratic prompting for worktree agents |
| /repo-quality-rails-setup | `~/.claude/skills/repo-quality-rails-setup/` → `claude/skills/repo-quality-rails-setup/` | Optional quality rails setup |
| Pi extensions | `~/.pi/agent/extensions/` → `pi/extensions/` | message-queue, pi-subscribe, kw-role |
| Projects folder | `~/<user-choice>` | Where all projects live |

Everything is symlinked back to this repo. `git pull` updates the whole machine.
The chosen projects folder should also be exported via `CASHEW_PROJECTS_DIR` so
agents and `dev` agree on the same path.

## Step 1: Ask the User

Use the AskUserQuestion tool to ask:

1. **What should your projects folder be called?** (default: `~/projects`)
2. **Install the optional Repo Quality Rails skill?** (sets up quality gates for repos)

## Step 2: Pull Latest

```bash
git pull
```

## Step 3: Create Projects Directory

```bash
mkdir -p ~/<projects-folder>
```

Persist the projects directory in your shell config so `dev` and agents use the
same path:

```bash
grep -q 'CASHEW_PROJECTS_DIR=' ~/.zshrc 2>/dev/null || \
  echo 'export CASHEW_PROJECTS_DIR="$HOME/<projects-folder>"' >> ~/.zshrc
export CASHEW_PROJECTS_DIR="$HOME/<projects-folder>"
```

## Step 4: Symlink Binaries

```bash
CASHEW_ROOT="$(git rev-parse --show-toplevel)"
sudo ln -sf "$CASHEW_ROOT/bin/dev" /usr/local/bin/dev
sudo ln -sf "$CASHEW_ROOT/bin/cashew" /usr/local/bin/cashew
```

## Step 5: Install Claude Config and Skills

Append the Cashew context block to `~/.claude/CLAUDE.md` if it's not already
there. Idempotent — running it twice won't duplicate the block.

The setup skill itself is NOT symlinked. It lives in `.claude/skills/` and is
only available when Claude is in this repo.

```bash
CASHEW_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p ~/.claude/commands ~/.claude/skills
TARGET=~/.claude/CLAUDE.md

if ! grep -q "BEGIN CASHEW GLOBAL CONTEXT" "$TARGET" 2>/dev/null; then
  {
    echo ""
    echo "<!-- BEGIN CASHEW GLOBAL CONTEXT -->"
    sed -e "s|<cashew-root>|$CASHEW_ROOT|g" \
        -e "s|<projects-dir>|$CASHEW_PROJECTS_DIR|g" \
        "$CASHEW_ROOT/claude/global/CLAUDE.md"
    echo "<!-- END CASHEW GLOBAL CONTEXT -->"
  } >> "$TARGET"
fi

# Global commands
ln -sf "$CASHEW_ROOT/claude/commands/dev.md" ~/.claude/commands/dev.md
ln -sf "$CASHEW_ROOT/claude/commands/codex-review.md" ~/.claude/commands/codex-review.md

# Global skills
ln -sf "$CASHEW_ROOT/claude/skills/prompting-worktree-agents" ~/.claude/skills/prompting-worktree-agents

# Optional: Repo Quality Rails (only if user opted in during Step 1)
ln -sf "$CASHEW_ROOT/claude/skills/repo-quality-rails-setup" ~/.claude/skills/repo-quality-rails-setup
```

## Step 6: Install Pi Extensions

Pi must be installed (`npm install -g @mariozechner/pi-coding-agent`). If `pi`
isn't on the PATH, install it first.

These extensions enable `dev send-pi` messaging, pub/sub coordination, and
knowledge worker roles. Symlinked so `git pull` updates them. Do NOT remove
other extensions in `~/.pi/agent/extensions`—users may install their own
plugins there.

```bash
CASHEW_ROOT="$(git rev-parse --show-toplevel)"

# Install Pi if missing
command -v pi || npm install -g @mariozechner/pi-coding-agent

mkdir -p ~/.pi/agent/extensions
# Only add Cashew symlinks; leave any existing extensions intact.
ln -sf "$CASHEW_ROOT/pi/extensions/message-queue.ts" ~/.pi/agent/extensions/message-queue.ts
ln -sf "$CASHEW_ROOT/pi/extensions/pi-subscribe.ts" ~/.pi/agent/extensions/pi-subscribe.ts
ln -sf "$CASHEW_ROOT/pi/extensions/kw-role.ts" ~/.pi/agent/extensions/kw-role.ts
```

## Step 7: Install Codex CLI

Codex CLI is used by `/codex-review` for AI-powered second-pass code review.
If `codex` isn't on the PATH, install it.

```bash
# Install Codex CLI if missing
command -v codex || npm install -g @openai/codex
```

Codex requires an `OPENAI_API_KEY` in the environment. If the user doesn't
have one, note that `/codex-review` will be unavailable until they set it up,
but everything else works fine without it.

## Optional: Web Search for Pi

Consider installing [pi-web-access](https://github.com/nicobailon/pi-web-access/blob/main/README.md) for web search in Pi:

```bash
pi install npm:pi-web-access
cat > ~/.pi/web-search.json <<'EOF'
{
  "provider": "perplexity"
}
EOF
# pi-web-access reads PERPLEXITY_API_KEY from the environment, or you can put
# "perplexityApiKey" directly in ~/.pi/web-search.json
```

## Step 8: Verify

Report what passed/failed — don't run silently.

```bash
dev --help
pi --version
codex --version || echo "Codex CLI not installed — /codex-review will be unavailable"
ls -l ~/.pi/agent/extensions/
ls -l ~/.claude/commands/dev.md
ls -l ~/.claude/commands/codex-review.md
ls -l ~/.claude/skills/prompting-worktree-agents
```

## Step 9: Tell the User What to Do Next

After verification, walk the user through how to start using Cashew:

1. **Go to your projects folder:**
   ```bash
   cd ~/<projects-folder>
   ```

2. **Bootstrap initial sessions** (creates hub and baseline sessions):
   ```bash
   dev reboot
   ```

3. **Or start a new project** — run Claude from the projects folder and ask it
   to use `dev` to set up a repo. It will clone, configure worktrees, and
   create sessions:
   ```bash
   claude
   # "Use dev to set up git@github.com:user/myapp"
   ```

4. **Talk to a project's PM** — each project has a Claude session on `main`
   that acts as the orchestrator:
   ```bash
   dev <project>/main/claude
   ```

5. **Tell the PM what to build** — the PM uses the `/dev` command to create
   worktrees, task and monitor worktree agents, and bootstrap knowledge workers.

6. **Drop in anytime** — use `dev` to rejoin any session. Attach to a worktree
   agent to interact directly, check on a knowledge worker, or rejoin the PM
   to continue planning:
   ```bash
   dev                              # see everything running
   dev <project>/main/claude        # rejoin PM
   dev <project>/<feature>/pi       # drop into a worktree agent
   dev <project>/main/kw-<name>     # check on a knowledge worker
   ```
