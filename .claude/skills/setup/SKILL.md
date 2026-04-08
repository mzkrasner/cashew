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
pull the latest, symlink everything into place, install Pi/Codex tooling, and
update the user's global Claude context so the orchestrator workflow matches the
current Cashew model.

## End State

| Component | Location | Purpose |
|-----------|----------|---------|
| dev script | `/usr/local/bin/dev` → `bin/dev` | Project session manager |
| cashew launcher | `/usr/local/bin/cashew` → `bin/cashew` | tmux + fzf TUI launcher |
| Global Claude config | `~/.claude/CLAUDE.md` | Cashew context block replaced in-place between markers |
| /setup command | `~/.claude/commands/setup.md` → `claude/commands/setup.md` | Entry point that invokes the authoritative setup skill |
| /dev command | `~/.claude/commands/dev.md` → `claude/commands/dev.md` | Session manager docs |
| /codex-review command | `~/.claude/commands/codex-review.md` → `claude/commands/codex-review.md` | Stateless final Codex review |
| /cashew-feedback command | `~/.claude/commands/cashew-feedback.md` → `claude/commands/cashew-feedback.md` | Local-only Cashew workflow feedback capture |
| /prompting-worktree-agents | `~/.claude/skills/prompting-worktree-agents/` → `claude/skills/prompting-worktree-agents/` | Socratic prompting for worktree agents |
| /repo-quality-rails-setup | `~/.claude/skills/repo-quality-rails-setup/` → `claude/skills/repo-quality-rails-setup/` | Optional quality rails setup |
| Pi extensions | `~/.pi/agent/extensions/` → `pi/extensions/` | message-queue, pi-subscribe, kw-role |
| Cashew role env defaults | `~/.zshrc` | Pins Codex-backed Pi roles and required Claude model override for task roles |
| Projects folder | `~/<user-choice>` | Where all projects live |

Everything is symlinked back to this repo. `git pull` updates the whole machine.
The chosen projects folder should also be exported via `CASHEW_PROJECTS_DIR` so
agents and `dev` agree on the same path.

## Step 1: Ask the User

Use the AskUserQuestion tool to ask:

1. **What should your projects folder be called?** (default: `~/projects`)
2. **Install the optional Repo Quality Rails skill?** (sets up quality gates for repos)
3. **What Claude model alias should Cashew use for Claude critic/orchestrator roles?** (required for serious-task workflow)

When rendering shell snippets below:
- replace `<projects-folder>` with the chosen folder name
- replace `<claude-model-env-line>` with:
  - `export CASHEW_CLAUDE_MODEL="<chosen-alias>"`

## Step 2: Pull Latest

```bash
git pull
```

## Step 3: Create Projects Directory

```bash
mkdir -p ~/<projects-folder>
```

Persist the projects directory and role defaults in your shell config so `dev`
and agents use the same path and model behavior:

```bash
python3 - <<'PY'
from pathlib import Path
zshrc = Path.home() / ".zshrc"
existing = zshrc.read_text() if zshrc.exists() else ""
begin = "# >>> CASHEW ENV >>>"
end = "# <<< CASHEW ENV <<<"
block = f"""{begin}
export CASHEW_PROJECTS_DIR="$HOME/<projects-folder>"
export CASHEW_CODEX_PROVIDER="${{CASHEW_CODEX_PROVIDER:-openai}}"
export CASHEW_CODEX_MODEL="${{CASHEW_CODEX_MODEL:-gpt-5.4}}"
export CASHEW_CODEX_THINKING="${{CASHEW_CODEX_THINKING:-high}}"
<claude-model-env-line>
{end}
"""
if begin in existing and end in existing:
    before = existing.split(begin, 1)[0]
    after = existing.split(end, 1)[1]
    zshrc.write_text(before + block + after.lstrip("\n"))
else:
    zshrc.write_text(existing.rstrip() + ("\n\n" if existing.rstrip() else "") + block + "\n")
PY
source ~/.zshrc >/dev/null 2>&1 || true
export CASHEW_PROJECTS_DIR="$HOME/<projects-folder>"
```

## Step 4: Symlink Binaries

```bash
CASHEW_ROOT="$(git rev-parse --show-toplevel)"
sudo ln -sf "$CASHEW_ROOT/bin/dev" /usr/local/bin/dev
sudo ln -sf "$CASHEW_ROOT/bin/cashew" /usr/local/bin/cashew
```

## Step 5: Install Claude Config and Skills

Replace the Cashew context block inside `~/.claude/CLAUDE.md` if present,
otherwise append it. This must be update-in-place so existing users receive new
workflow guidance.

The setup skill remains in `.claude/skills/` in this repo. The global
`/setup` command is now just a stable entrypoint that points Claude at this
skill.

```bash
CASHEW_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p ~/.claude/commands ~/.claude/skills

python3 - <<'PY'
from pathlib import Path
import os

target = Path.home() / ".claude" / "CLAUDE.md"
cashew_root = Path(os.popen("git rev-parse --show-toplevel").read().strip())
projects_dir = os.environ.get("CASHEW_PROJECTS_DIR", "$HOME/<projects-folder>")
template = (cashew_root / "claude" / "global" / "CLAUDE.md").read_text()
template = template.replace("<cashew-root>", str(cashew_root))
template = template.replace("<projects-dir>", projects_dir)
begin = "<!-- BEGIN CASHEW GLOBAL CONTEXT -->"
end = "<!-- END CASHEW GLOBAL CONTEXT -->"
block = f"\n{begin}\n{template}{end}\n"

existing = target.read_text() if target.exists() else ""
if begin in existing and end in existing:
    before = existing.split(begin, 1)[0]
    after = existing.split(end, 1)[1]
    target.write_text(before + block + after.lstrip("\n"))
else:
    target.write_text(existing.rstrip() + block + ("\n" if not existing.endswith("\n") else ""))
PY

# Global commands
ln -sf "$CASHEW_ROOT/claude/commands/setup.md" ~/.claude/commands/setup.md
ln -sf "$CASHEW_ROOT/claude/commands/dev.md" ~/.claude/commands/dev.md
ln -sf "$CASHEW_ROOT/claude/commands/codex-review.md" ~/.claude/commands/codex-review.md
ln -sf "$CASHEW_ROOT/claude/commands/cashew-feedback.md" ~/.claude/commands/cashew-feedback.md

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

Codex CLI is used for stateless final review and other direct Codex workflows.
The serious-task flow primarily uses Pi with pinned Codex-backed role sessions,
so there is no separate required global Codex config file for the core workflow.
If `codex` isn't on the PATH, install it.

```bash
# Install Codex CLI if missing
command -v codex || npm install -g @openai/codex
```

Codex requires an `OPENAI_API_KEY` in the environment. If the user doesn't
have one, note that direct `codex` CLI flows will be unavailable until they set
it up. Pi-backed Codex roles still depend on the user's Pi/OpenAI configuration.

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
dev task
pi --version
codex --version || echo "Codex CLI not installed — /codex-review will be unavailable"
ls -l ~/.pi/agent/extensions/
ls -l ~/.claude/commands/dev.md
ls -l ~/.claude/commands/setup.md
ls -l ~/.claude/commands/codex-review.md
ls -l ~/.claude/commands/cashew-feedback.md
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
   to use `dev` to set up a repo. Claude remains the primary orchestrator. It
   will clone, configure worktrees, and create sessions:
   ```bash
   claude
   # "Use dev to set up git@github.com:user/myapp"
   ```

4. **Talk to a project's PM** — each project has a Claude session on `main`
   that acts as the orchestrator:
   ```bash
   dev <project>/main/claude
   ```

5. **Tell the PM what to build** — the PM uses the `/dev` command and `dev task`
   workflow to create persistent Codex reviewer/implementer roles, define commit
   slices up front, manage per-slice review loops, run verification, and monitor
   worktree agents.

6. **Drop in anytime** — use `dev` to rejoin any session. Attach to a worktree
   agent to interact directly, check on a knowledge worker, or rejoin the PM
   to continue planning:
   ```bash
   dev                              # see everything running
   dev <project>/main/claude        # rejoin PM
   dev <project>/<feature>/pi       # drop into a worktree agent
   dev <project>/main/kw-<name>     # check on a knowledge worker
   ```

7. **For serious work, use the task workflow through the PM**:
   ```bash
   dev task new <project> <slug>
   dev task slice new <project> <slug> slice-01
   # add more slices up front for larger work; Cashew enforces sequential slice progression
   dev task open <project> <slug> plan-owner-codex
   dev task open <project> <slug> plan-review-codex
   dev task open <project> <slug> plan-critic-claude
   dev task validate <project> <slug> plan
   dev task lock-plan <project> <slug>
   dev task start-impl <project> <slug> [worktree]
   ```
