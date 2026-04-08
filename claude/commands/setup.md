# Setup - Bootstrap Cashew

Use the `setup` skill to install or refresh Cashew on this machine.

## When to Use

Use `/setup` when the user asks to:
- set up Cashew
- bootstrap the dev environment
- refresh or reinstall the local Cashew install

## What `/setup` should do

Run the Cashew setup skill from this repo and follow its current instructions.

The authoritative setup logic lives in:
- `.claude/skills/setup/SKILL.md`

That setup flow is responsible for:
- pulling the latest Cashew repo state
- symlinking commands, skills, Pi extensions, and launchers
- updating the Cashew block in `~/.claude/CLAUDE.md`
- updating Cashew shell env defaults
- installing or verifying Pi / Codex tooling

## Important

- Do not use stale downloaded setup instructions.
- Do not fetch raw command files from GitHub for installation when the user is already in this repo.
- Prefer symlinks back to this repo so future `git pull` updates the machine cleanly.
- Claude remains the primary project orchestrator after setup.
