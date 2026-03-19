---
name: prompting-worktree-agents
description: >
  Socratic prompting loop for worktree agents. Use this skill whenever you are
  about to send implementation instructions to a worktree agent — it ensures the
  agent reasons through the problem before writing code. Also use it when the user
  asks to "prompt the agent", "have it think first", or when you're orchestrating
  multiple worktree agents on non-trivial tasks.
---

# Prompting Worktree Agents (Socratic Loop)

Before a worktree agent touches code, walk it through a structured reasoning
loop so it understands the problem, the constraints, and has a concrete plan
with clear acceptance criteria. This catches bad assumptions early and produces
better first attempts.

## When to Use the Full Loop vs. a Quick Prompt

**Full loop (five prompts):** Risky changes, complex features, anything touching
data integrity, multi-service coordination, or unfamiliar parts of the codebase.

**Quick version (single prompt):** Small bug fixes, straightforward refactors, or
tasks where the agent already has deep context. In this case, just ask: "Explain
your approach before you start — what are you changing, what could break, and how
will you verify it works?"

When in doubt, use the full loop. The cost is a few minutes; the cost of a bad
first attempt is much higher.

## The Five Prompts

Send these **one at a time**. Wait for the agent to respond to each before
sending the next. This forces the agent to build understanding incrementally
rather than rushing to a plan.

### 1. Understand the problem

Ground the agent in the actual code and context. Don't let it theorize — make
it look.

```bash
dev send-pi <repo>/<worktree>/pi "Before you start, read the relevant code and
explain: what is actually happening now, what should be happening instead, and
where in the codebase does this live?"
```

### 2. Identify constraints, risks, and assumptions

Now that the agent has context, push it to think about what could go wrong and
what it's assuming to be true.

```bash
dev send-pi <repo>/<worktree>/pi "What constraints apply to this change?
Think about: existing tests, data integrity, other code that depends on this,
edge cases that could bite us. Also state your key assumptions — what are you
taking for granted that might be wrong?"
```

### 3. Propose the smallest viable plan

Only now should the agent propose what to do. Explicitly ask for the minimum
change — agents over-engineer by default.

```bash
dev send-pi <repo>/<worktree>/pi "Propose the smallest implementation plan
that solves this problem: what files you'll change, in what order, what tests
you'll add or update. Name the specific files and modules you expect to touch.
Is this the minimum change needed, or can it be simpler?"
```

### 4. Define acceptance criteria and non-goals

Before giving the go-ahead, establish what "done" looks like and what's
explicitly out of scope.

```bash
dev send-pi <repo>/<worktree>/pi "Define the acceptance criteria for this
change: what specific tests must pass, what behavior must be observable, what
edge cases must be handled. Also state the non-goals — what are we intentionally
NOT changing?"
```

### 5. Go-ahead (tied to the approved plan)

Summarize what the agent said back to it. Correct anything that's off. Approve
the specific plan and boundaries — not a vague "go ahead."

```bash
dev send-pi <repo>/<worktree>/pi "Good. Here's what I'm approving: [summary of
plan from step 3]. Acceptance criteria: [from step 4]. Non-goals: [from step 4].
[Any corrections or additions].

Implement this plan — no broader changes. When done: commit all changes using
conventional commit format (type(scope): message) with a structured body.
Include 'Co-Authored-By: Codex <noreply@openai.com>' as the last line of every
commit. Run 'codex review --base main', fix any issues, commit the fixes, then
report done with your commit hash."
```

## Between Each Prompt

Always read the agent's response before sending the next question:

```bash
dev pi-status <repo>/<worktree>/pi --messages 1
```

Acknowledge briefly (1-2 sentences), then send the next prompt. If the response
is vague or hand-wavy, ask a follow-up that forces specificity: "Which file?
Which function? What's the actual data flow?" Don't move on until the answer
is grounded in the code.

## Judging Response Quality

**Good signs:**
- References specific files, functions, line numbers
- Identifies concrete edge cases (not just "there might be edge cases")
- Names the exact files/modules it expects to touch
- States assumptions explicitly
- Acceptance criteria are testable, not vague
- Non-goals demonstrate understanding of scope boundaries
- Plan has a clear order of operations
- Mentions how to verify the change works (tests, manual checks)

**Red flags:**
- Generic statements that could apply to any codebase
- "I'll handle edge cases" without naming them
- No mention of existing tests or how they're affected
- Plan jumps straight to the happy path without considering failure modes
- Acceptance criteria are just "tests pass" with no specifics
- Can't name the files it will touch
- Assumptions are absent or trivially obvious

If you see red flags, don't proceed. Ask one more targeted question to force
the agent to get specific. If it still can't, the task may need to be broken
down further or the agent needs more context.

## Escalation Triggers

Instruct the agent that it must **stop and ask back** (not guess) when it hits:
- Unexpected architecture mismatch with the plan
- Dirty or conflicting files in the target area
- Failing unrelated tests it didn't expect
- Migration or data-loss risk not covered in the plan
- Missing context it needs to proceed

Include this in the go-ahead message when appropriate.

## Conditional Overlays

Not every task needs every overlay. Add these to the loop when triggered:

### Rollback plan (data/infra/production changes only)

If the change touches database schemas, data migrations, infrastructure, or
production-exposed behavior, add after step 2:

```bash
dev send-pi <repo>/<worktree>/pi "This change touches [data/infra/production].
How can it be rolled back if something goes wrong? Be specific — what's the
reversal mechanism?"
```

### Mid-implementation checkpoints (large/uncertain work only)

For large features where course correction is cheaper than rework, define
milestone-based checkpoints in the go-ahead:

> "Pause after the API contract and tests are in place — report back before
> wiring the implementation. Then pause again before the migration."

Use milestones, not time intervals. Don't checkpoint small/medium tasks — it
interrupts flow.

### Parallel work context (multiple active worktrees)

If other agents are working on related code, inject context from the
orchestrator — don't ask the agent to guess:

> "Related active work: agent in fix-payments is modifying src/execution/engine.ts.
> Avoid touching that file."

## Best Practices

- **Always check before sending:** `dev pi-status <session> --messages 1` before
  every message. Never nudge blind.
- **Default to queued delivery:** `dev send-pi <session> "message"` with no flags.
  This queues the message for when the agent finishes its current turn. Only use
  `--steer` to interrupt genuinely off-track or unsafe work.
- **Adapt the questions to the task.** The five prompts above are templates.
  Tailor them to the specific problem — reference the issue, the module, the
  domain. Generic questions get generic answers.
- **Don't turn this into ceremony.** For simple tasks, the quick version is fine.
  The full loop exists for when the cost of a bad first attempt is high.
