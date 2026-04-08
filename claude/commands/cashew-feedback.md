---
name: cashew-feedback
description: Capture structured local feedback about Cashew workflow friction into the local Cashew repo
argument-hint: [short summary]
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Cashew Feedback

Use this command when the user notices Cashew friction, confusing behavior, workflow gaps, or setup/runtime issues and wants that captured locally for later triage.

This command is **local-only**. It does **not** create a GitHub issue.

## Goal

Create a structured feedback artifact inside the local Cashew repo so the problem is not lost.

Default artifact location:
- `.cashew/feedback/<timestamp>-<slug>.md`

If the current repo is not the Cashew repo, try to locate the Cashew repo from:
- `readlink "$(command -v dev)"` and walk up to the repo root
- otherwise, ask the user where their Cashew repo lives before proceeding

## Inputs

$ARGUMENTS

If the user gave a short summary, use it as the seed title/summary.

If key details are missing, ask concise follow-up questions for:
- expected behavior
- actual behavior
- repro steps
- current context

## Context to capture

When available, include:
- current project/repo
- current task slug
- current slice id
- current session / role
- whether the issue is about:
  - setup
  - session management
  - project orchestration
  - task workflow
  - slice workflow
  - review loop
  - Pi/Codex integration
  - Claude integration
  - docs / onboarding

## Output format

Write a markdown file with this structure:

```md
# Cashew Feedback: <title>

## Summary

## Area

## Expected Behavior

## Actual Behavior

## Reproduction

## Current Context

## Impact

## Suspected Cause

## Suggested Improvement

## Captured At
```

Guidelines:
- Keep it factual and concise
- Preserve user wording where useful
- Prefer actionable reproduction steps
- If some fields are unknown, write `Unknown`

## Slug / filename

Use:
- timestamp in UTC, e.g. `2026-04-08T19-30-00Z`
- short slug from the title/summary

Example:
- `.cashew/feedback/2026-04-08T19-30-00Z-task-slice-feedback.md`

## Final response

After writing the file:
- report the exact file path
- summarize the captured issue in 1-3 bullets
- mention that it was saved locally only
