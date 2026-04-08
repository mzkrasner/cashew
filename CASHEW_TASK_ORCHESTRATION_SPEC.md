# Cashew Task-Oriented Orchestration Spec

## Goal

Redesign Cashew to support the most thorough possible multi-agent workflow for non-trivial feature work:

- persistent plan analysis across the full life of a task
- repeated review cycles until convergence
- persistent reviewer memory, especially for Codex
- mandatory written plan artifacts
- pinned model/provider selection per role
- the same rigor on implementation review as on plan review

This spec assumes the preferred model baseline is:

- `Codex`: `openai / gpt-5.4 / high`
- `Claude`: `Claude Opus 4.6`

## Why Cashew Needs To Change

Current Cashew is optimized for:

- `Claude` as the primary orchestrator
- `Pi` worktree agents as implementers
- `Codex` as a mostly stateless final review pass

That is misaligned with the desired workflow.

The desired workflow is:

- plan-first for every serious feature
- persistent Codex planner/reviewer sessions
- persistent Claude architecture/risk critic sessions
- iterative back-and-forth plan refinement
- iterative implementation review until no blockers remain
- explicit model pinning so behavior is deterministic

## Research-Based Conclusions

### Model Roles

Based on the current benchmark evidence, official product positioning, and community workflow reports:

- `Codex` should be on the correctness-critical path
- `Claude` is still valuable as a planning/architecture/risk critic
- `Claude` should not be the sole planner or sole orchestrator
- `Codex` should likely own:
  - plan finalization
  - implementation
  - blocking review
- `Claude` should likely own:
  - architecture critique
  - requirement-gap detection
  - risk review
  - optional audit of risky implementations

### Persistence Matters

Persistent task memory is critical.

Stateless review is insufficient for serious work because it loses:

- accumulated pattern recognition
- prior rejected ideas
- recurring weak spots in the plan
- latent concerns discovered over earlier rounds

Therefore:

- one-shot `/codex-review` is not enough for serious tasks
- persistent feature-scoped reviewer sessions are required
- review notes must also be written to disk, not only held in chat/session memory

### Pi-Specific Findings

Pi supports the primitives needed to make this precise:

- `--provider`
- `--model`
- `--thinking`
- `--session-dir`
- project-local `.pi/settings.json`
- extensions with session lifecycle hooks

That means Cashew can and should stop launching bare `pi` and instead launch pinned role sessions.

## Design Principles

1. Every serious feature is a task with durable artifacts.
2. No implementation begins before a written plan is locked.
3. Plan review is iterative, not one-shot.
4. Implementation review is iterative, not one-shot.
5. The same reviewer sessions persist for the entire task.
6. Model/provider selection is explicit and pinned by Cashew.
7. Task truth lives in files first, session memory second.
8. Codex is the blocking reviewer for merge.
9. Claude is a required critic for plan and for risky implementation categories.
10. Small changes may use shortcuts; everything else uses the full workflow.

## New Core Concept: Task

Cashew needs a first-class `task` concept, separate from repo and worktree.

Each task has:

- a slug
- a status
- a feature worktree
- persistent sessions by role
- durable artifacts on disk

Suggested on-disk layout:

```text
.cashew/
  tasks/
    <task-slug>/
      task.json
      proposal.md
      plan.md
      plan-review-codex.md
      plan-review-claude.md
      plan-open-issues.md
      plan-decisions.md
      implementation-notes.md
      implementation-review-codex.md
      implementation-review-claude.md
      merge-checklist.md
      sessions/
        plan-owner-codex/
        plan-review-codex/
        plan-critic-claude/
        implementer-codex/
```

## Required Roles Per Serious Task

For every serious task, Cashew creates and maintains these persistent roles:

1. `plan-owner-codex`
2. `plan-review-codex`
3. `plan-critic-claude`
4. `implementer-codex`

Optional:

5. `implementation-critic-claude`

The first four should be the default.

## Role Definitions

### `plan-owner-codex`

Responsibilities:

- convert proposal into executable plan
- revise plan after critiques
- maintain `plan.md`
- resolve plan blockers
- produce final locked plan

Pinned runtime:

- provider: `openai`
- model: `gpt-5.4`
- thinking: `high`

### `plan-review-codex`

Responsibilities:

- attack the plan for missing details
- find correctness gaps
- find hidden implementation risk
- challenge assumptions
- update `plan-review-codex.md`
- keep reviewing until blockers are zero

Pinned runtime:

- provider: `openai`
- model: `gpt-5.4`
- thinking: `high`

### `plan-critic-claude`

Responsibilities:

- critique architecture
- find requirement omissions
- identify hidden coupling
- identify rollout, migration, observability, and edge-case gaps
- update `plan-review-claude.md`

Pinned runtime:

- Claude Opus 4.6

Exact CLI model pinning should use the full supported Claude CLI configuration for Opus 4.6 in the target environment.

### `implementer-codex`

Responsibilities:

- implement only against the locked plan
- surface divergence when the plan is wrong
- keep `implementation-notes.md` current
- respond to review feedback
- stop only when Codex review blockers are cleared

Pinned runtime:

- provider: `openai`
- model: `gpt-5.4`
- thinking: `high`

### `implementation-critic-claude`

Responsibilities:

- audit risky changes after implementation
- focus on architecture, boundary correctness, migration safety, hidden regressions

This role is required for:

- migrations
- auth/security
- cross-service contracts
- large refactors
- state machine changes
- financial/accounting/trading logic

## Task Lifecycle

### Phase 1: Create Task

Command:

```bash
dev task new <repo> <slug>
```

Effects:

- creates task directory under `.cashew/tasks/<slug>/`
- scaffolds files
- records task metadata in `task.json`
- creates or assigns worktree
- creates persistent task-scoped session directories

### Phase 2: Draft Plan

`plan-owner-codex` writes:

- `plan.md`

Required sections:

1. Goal
2. Non-goals
3. Constraints
4. Affected files/systems
5. Invariants
6. Risks
7. Acceptance criteria
8. Tests
9. Rollout/rollback
10. Open questions

### Phase 3: Review Plan Until Converged

Loop:

1. `plan-review-codex` critiques
2. `plan-critic-claude` critiques
3. blockers are written to:
   - `plan-review-codex.md`
   - `plan-review-claude.md`
   - `plan-open-issues.md`
4. `plan-owner-codex` revises `plan.md`
5. repeat until blockers = 0

Command surface:

```bash
dev task review-plan <repo> <slug>
dev task sync-plan-feedback <repo> <slug>
dev task lock-plan <repo> <slug>
```

`lock-plan` should fail unless:

- both reviewers ran
- all open blockers are resolved or explicitly accepted by human
- `plan.md` has a final revision marker

### Phase 4: Start Implementation

Command:

```bash
dev task start-impl <repo> <slug>
```

Effects:

- ensures the plan is locked
- ensures the worktree exists
- starts or reattaches `implementer-codex`
- injects the locked plan into the implementer workflow

### Phase 5: Review Implementation Until Converged

Loop:

1. `implementer-codex` produces implementation
2. persistent Codex reviewer reviews
3. if risky category, Claude critic audits too
4. findings written to:
   - `implementation-review-codex.md`
   - `implementation-review-claude.md`
5. implementer fixes issues
6. repeat until blockers = 0

Only then may merge proceed.

### Phase 6: Merge And Cleanup

Command:

```bash
dev task merge <repo> <slug>
```

Requirements:

- plan locked
- implementation review clear
- final Codex blocking review clear
- worktree has committed changes beyond main
- merge checklist complete

Then:

- merge
- optionally run Claude post-merge audit on high-risk tasks
- archive task artifacts
- cleanup worktree

## Model Pinning Requirements

This is mandatory.

Cashew must no longer launch bare:

- `pi`
- `claude --dangerously-skip-permissions`

Instead, it must support role-specific startup commands.

### Pi Role Startup

For Codex-backed roles, Cashew should launch:

```bash
pi \
  --provider openai \
  --model gpt-5.4 \
  --thinking high \
  --session-dir <task-session-dir> \
  ...
```

This should be the default for:

- `plan-owner-codex`
- `plan-review-codex`
- `implementer-codex`

### Claude Role Startup

For Claude roles, Cashew must use an explicit pinned model configuration for Opus 4.6.

Cashew should support this via config rather than hardcoding one CLI string into the repo, because the exact invocation may differ by installed Claude CLI version/environment.

Suggested Cashew config contract:

```json
{
  "roles": {
    "plan-owner-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "plan-review-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "implementer-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "plan-critic-claude": {
      "command": ["claude", "--dangerously-skip-permissions", "... pinned Opus 4.6 config ..."]
    },
    "implementation-critic-claude": {
      "command": ["claude", "--dangerously-skip-permissions", "... pinned Opus 4.6 config ..."]
    }
  }
}
```

Cashew should ship a config system that makes the selected model for every role explicit and inspectable.

## Persistent Session Topology

Session naming should become task-aware.

Suggested naming:

- `repo/main/task-<slug>-plan-owner-codex`
- `repo/main/task-<slug>-plan-review-codex`
- `repo/main/task-<slug>-plan-critic-claude`
- `repo/<worktree>/task-<slug>-implementer-codex`
- `repo/<worktree>/task-<slug>-implementation-critic-claude`

These should map to dedicated session directories.

### Why Session Directories Matter

Task-scoped `--session-dir` gives:

- persistent memory for that exact role
- no contamination from unrelated tasks
- resumable long-lived reviewer/planner threads
- stable artifacts tied to role identity

## Review Artifacts

Cashew should require file-based review outputs.

### Plan Review Files

`plan-review-codex.md`

Required structure:

- blocking issues
- non-blocking concerns
- assumptions challenged
- required revisions
- sign-off status

`plan-review-claude.md`

Required structure:

- architecture concerns
- hidden dependencies
- rollout/observability concerns
- edge cases
- sign-off status

`plan-open-issues.md`

Required structure:

- issue id
- source reviewer
- severity
- state
- resolution

### Implementation Review Files

`implementation-review-codex.md`

Required structure:

- correctness bugs
- missing tests
- regressions
- simplifications
- unresolved blockers

`implementation-review-claude.md`

Required structure:

- architecture regressions
- boundary mismatches
- hidden coupling
- migration/security concerns

## Command Changes Required In `dev`

Add new commands:

```bash
dev task new <repo> <slug>
dev task status <repo> <slug>
dev task open <repo> <slug>
dev task review-plan <repo> <slug>
dev task sync-plan-feedback <repo> <slug>
dev task lock-plan <repo> <slug>
dev task start-impl <repo> <slug>
dev task review-impl <repo> <slug>
dev task merge <repo> <slug>
dev task archive <repo> <slug>
```

Suggested supporting commands:

```bash
dev role <repo> <slug> <role>
dev task note <repo> <slug> <text>
dev task checklist <repo> <slug>
```

## Required Behavior Changes In Cashew

### 1. `bin/dev`

Must be extended to:

- manage task directories
- manage task metadata
- start pinned role sessions
- use task-scoped `--session-dir`
- support task status inspection
- support plan/implementation review loops

### 2. Current Auto-Command Logic

Current logic in `bin/dev` auto-starts:

- `pi` for worktrees
- `claude` for repo roots

This must become role-aware instead.

For task sessions:

- role config decides command
- not repo/worktree default alone

### 3. `codex-review` Command

[`claude/commands/codex-review.md`](./claude/commands/codex-review.md) should be downgraded.

New role:

- final stateless safety-net review
- optional shortcut for small changes

It should no longer be treated as the primary serious-task review mechanism.

### 4. Claude Global Instructions

[`claude/global/CLAUDE.md`](./claude/global/CLAUDE.md) must change.

Current doctrine:

- Claude as primary orchestrator

New doctrine:

- Codex-first task orchestration for serious work
- Claude as critic/auditor
- locked plan required before implementation

### 5. Prompting Skill

[`claude/skills/prompting-worktree-agents/SKILL.md`](./claude/skills/prompting-worktree-agents/SKILL.md) should be adapted or superseded.

Current skill is good for better prompting, but insufficient for:

- durable task artifacts
- persistent reviewer memory
- enforced convergence loops

Cashew needs a stronger task-lifecycle skill or command set.

## Config Files Cashew Should Add

### `.cashew/config.json`

Repo- or machine-level Cashew config:

```json
{
  "taskRoot": ".cashew/tasks",
  "roles": {
    "plan-owner-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "plan-review-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "implementer-codex": {
      "command": ["pi", "--provider", "openai", "--model", "gpt-5.4", "--thinking", "high"]
    },
    "plan-critic-claude": {
      "command": ["claude", "--dangerously-skip-permissions", "..."]
    },
    "implementation-critic-claude": {
      "command": ["claude", "--dangerously-skip-permissions", "..."]
    }
  },
  "riskyCategories": [
    "migration",
    "auth",
    "security",
    "cross-service-contract",
    "financial-logic",
    "state-machine",
    "large-refactor"
  ]
}
```

### Task Metadata: `task.json`

Example:

```json
{
  "slug": "maker-only-universe-executor",
  "repo": "recallnet",
  "worktree": "maker-only-universe-executor",
  "status": "plan_review",
  "planLocked": false,
  "riskLevel": "high",
  "categories": ["financial-logic", "state-machine"],
  "requiredRoles": [
    "plan-owner-codex",
    "plan-review-codex",
    "plan-critic-claude",
    "implementer-codex",
    "implementation-critic-claude"
  ]
}
```

## Review Loop Policy

### Plan Review Loop

Default policy for serious tasks:

- minimum one Codex review round
- minimum one Claude critique round
- repeat until:
  - no critical blockers
  - no high blockers
  - any accepted risks are explicitly recorded

### Implementation Review Loop

Default policy for serious tasks:

- Codex blocking review is mandatory
- Claude audit mandatory for risky categories
- no merge until blockers are cleared

## Shortcut Policy

Not every task needs the full workflow.

Cashew should classify:

### Full Workflow Required

- new features
- architecture changes
- migrations
- data model changes
- auth/security
- critical business logic
- financial/trading logic
- cross-service changes
- major refactors

### Lightweight Workflow Allowed

- typo/docs-only changes
- tiny config edits
- trivial dependency bumps
- small isolated fixes

But the default for your environment should be conservative: bias toward the full workflow.

## Migration Plan For Cashew

### Stage 1

- add task artifact scaffolding
- add role config
- add pinned Pi startup for Codex roles
- keep current `dev` behavior for legacy sessions

### Stage 2

- add task commands
- add persistent task session naming
- make Codex-first task workflow available

### Stage 3

- rewrite Claude docs/commands away from Claude-first orchestration
- demote stateless `/codex-review`
- make task workflow the default for serious work

## Target Repo Guardrails And Quality-Rails Preservation

This section is binding for any Cashew implementation work.

Cashew itself is a workflow/bootstrap/orchestration repo. It does **not** need to become a guarded monorepo in the style of `skunkworks-experiments-mk`.

But Cashew **must** preserve, respect, and strengthen those patterns in the target repos it operates on.

The reference target-repo quality style is represented well by:

- [AGENTS.md](/Users/markkrasner/skunkworks-experiments-mk/AGENTS.md)
- [package.json](/Users/markkrasner/skunkworks-experiments-mk/package.json)
- [turbo.json](/Users/markkrasner/skunkworks-experiments-mk/turbo.json)
- [.husky/pre-commit](/Users/markkrasner/skunkworks-experiments-mk/.husky/pre-commit)
- [.husky/pre-push](/Users/markkrasner/skunkworks-experiments-mk/.husky/pre-push)
- [.github/workflows/ci.yml](/Users/markkrasner/skunkworks-experiments-mk/.github/workflows/ci.yml)
- [executors/near-certainty-15m/package.json](/Users/markkrasner/skunkworks-experiments-mk/executors/near-certainty-15m/package.json)
- [packages/db/package.json](/Users/markkrasner/skunkworks-experiments-mk/packages/db/package.json)
- [executors/near-certainty-15m/vitest.config.ts](/Users/markkrasner/skunkworks-experiments-mk/executors/near-certainty-15m/vitest.config.ts)
- [packages/db/vitest.config.ts](/Users/markkrasner/skunkworks-experiments-mk/packages/db/vitest.config.ts)
- [executors/near-certainty-15m/tsconfig.json](/Users/markkrasner/skunkworks-experiments-mk/executors/near-certainty-15m/tsconfig.json)
- [packages/db/tsconfig.json](/Users/markkrasner/skunkworks-experiments-mk/packages/db/tsconfig.json)

### What These Reference Patterns Actually Encode

The target quality model is not just "run lint and tests."

It encodes the following preferences:

1. **Repo-level agent contract**
   - `AGENTS.md` defines:
     - fail loudly
     - optimize for verification speed
     - plan first
     - explicit definition of done
     - no bypassing verification
     - no `--no-verify`
     - semantic migration review expectations
     - package-boundary discipline
     - documentation-update expectations

2. **Monorepo orchestration**
   - workspace-level package manager
   - workspace-level task runner
   - shared root scripts for `lint`, `check-types`, `test`, `build`, `qa`
   - package-level scripts with consistent naming

3. **Strict TypeScript defaults**
   - `strict: true`
   - `noUncheckedIndexedAccess: true`
   - `exactOptionalPropertyTypes: true`
   - package-local `tsc --noEmit` as the canonical typecheck

4. **Package-local quality gates**
   - each package/executor has its own:
     - `lint`
     - `check-types`
     - `test`
     - `build`
     - `format`
     - `format:check`
     - `qa`

5. **Unit tests are separated from integration tests**
   - unit tests exclude integration suites
   - integration tests are run intentionally and separately
   - this avoids confusing local fast checks with environment-sensitive checks

6. **DB integration tests are first-class**
   - they are not treated as optional extras
   - they are part of pre-push and CI
   - they typically require real setup/teardown and real database lifecycle

7. **Live API integration tests are first-class**
   - they are also separate from unit tests
   - they are serialized when appropriate
   - they are included in pre-push and CI where relevant
   - sandbox-only failures are not treated as authoritative

8. **Hooks enforce standards before code leaves the machine**
   - pre-commit:
     - lockfile drift guard
     - schema drift checks where relevant
     - staged formatting
     - lint
     - typecheck
     - scoped tests
   - pre-push:
     - branch freshness
     - clean working tree
     - full `qa`
     - DB integration tests
     - live API integration tests

9. **CI mirrors local expectations**
   - quality gates
   - DB integration in CI services
   - live API integration as a separate job
   - migration and delivery workflows separated when needed

10. **Schema / migration discipline exists where relevant**
   - schema drift checks
   - safe migration scripts
   - explicit migration verification

11. **Formatting is standardized**
   - repo-wide prettier checks
   - lint-staged formatting on staged files

12. **Verification is a primary value**
   - "done" means all relevant checks pass
   - not just "agent says done"

### What Cashew Must Do With These Patterns

Cashew must treat these target-repo rails as **authoritative**.

Task orchestration is additive to them, not a replacement for them.

That means:

1. If a target repo already has strong rails:
   - preserve them
   - do not weaken them
   - do not bypass them
   - surface them explicitly in task verification and merge checks

2. If a target repo has partial rails:
   - detect what exists
   - work within those standards
   - recommend or install missing pieces only where needed

3. If a target repo lacks serious rails:
   - Cashew should recommend applying the preferred pattern
   - in many repos, that means invoking the quality-rails setup workflow before serious delegation begins

### Required Cashew Behavior For Existing Guardrails

For every task, Cashew must determine and record:

1. whether the target repo has:
   - `AGENTS.md`
   - root workspace config
   - root scripts for `lint`, `check-types`, `test`, `build`, `qa`
   - package-level scripts for the touched package(s)
   - hooks
   - CI workflows
   - integration tests
   - DB integration tests
   - live API integration tests
   - schema drift or migration checks

2. which package(s) or services are touched

3. which verification commands are required for this task

Cashew should write this into the task artifact set, for example:

```text
.cashew/tasks/<slug>/verification-contract.md
```

Suggested contents:

- touched packages
- unit test command(s)
- integration test command(s)
- DB integration command(s)
- live API integration command(s)
- lint command(s)
- typecheck command(s)
- build command(s)
- format check command(s)
- schema/migration checks
- whether CI parity is expected before merge

### Required Verification Contract

Every serious task must have a verification contract derived from the target repo.

The implementer must not invent one from scratch if the repo already has standards.

Priority order:

1. package `README.md` / `AGENTS.md`
2. root/package scripts in `package.json`
3. hooks
4. CI workflows
5. explicit repo-quality-rails guidance

### Examples Of Behavior Cashew Must Preserve

Using the reference repo as the model:

1. **Unit vs integration separation**
   - Cashew must not treat `pnpm test` as sufficient if the touched package also defines:
     - `test:integration`
     - `test:integration:api`

2. **DB integration tests**
   - if a touched package has DB integration tests, Cashew must call them out explicitly
   - for risky persistence/runtime changes, these are required before merge

3. **Live API integration tests**
   - if a touched package has live API integration tests, Cashew must call them out explicitly
   - sandbox failures should be treated as non-authoritative, matching the target-repo philosophy

4. **Schema drift / migration checks**
   - if the repo has dedicated migration discipline, Cashew must preserve it in the task verification contract

5. **Scoped verification**
   - if the repo supports package-scoped or changed-package verification, Cashew should respect that
   - it should not invent a less strict but faster substitute

6. **No bypassing hooks**
   - Cashew must not advise bypassing hooks or reducing verification to get a task merged faster

### Required Changes To Cashew Spec/Implementation

The implementer of this Cashew redesign must add support for:

1. **Repo-quality introspection**
   - detect target-repo guardrails automatically

2. **Verification-contract generation**
   - write a per-task verification contract file

3. **Guardrail-aware task status**
   - `dev task status` should show:
     - plan state
     - review state
     - verification state
     - remaining required checks from the target repo

4. **Guardrail-aware merge gate**
   - `dev task merge` must fail unless:
     - plan is locked
     - review blockers are clear
     - target-repo required checks are complete

5. **Guardrail preservation in prompts**
   - all role prompts should explicitly tell agents:
     - target-repo verification rails are authoritative
     - do not weaken existing lint/type/test/hook/CI expectations
     - if README/AGENTS/package docs define verification or migration expectations, follow them

6. **Bootstrap path for missing rails**
   - if a repo is missing adequate rails, Cashew should support:
     - recommending `repo-quality-rails-setup`
     - or explicitly marking that the repo is below preferred standards

### Non-Goals For This Section

- Cashew itself does not need to adopt Husky/Turbo/CI only to mirror target repos.
- Cashew does not need to force one exact monorepo structure on every repo.
- Cashew should not blindly overwrite target-repo patterns with the `skunkworks-experiments-mk` pattern.

Instead:

- preserve existing strong patterns
- strengthen missing rails when appropriate
- make task orchestration respect and surface those rails explicitly

## Non-Goals

- replacing Pi entirely
- removing Claude entirely
- eliminating one-shot review for small changes
- building a distributed orchestration service
- building a GUI before the CLI/task model is correct

## Final Recommendation

Cashew should evolve from:

- session/worktree manager with Claude-first orchestration

into:

- task-lifecycle manager with Codex-first execution and persistent cross-model critique

The core shift is:

- from ephemeral review to persistent review lanes
- from chat-state-only planning to file-backed locked plans
- from model defaults to pinned role-specific model contracts
- from one orchestrator to task-scoped persistent specialist roles

For the target workflow, the most important changes are:

1. first-class task artifacts
2. persistent Codex planner/reviewer sessions
3. persistent Claude critic sessions
4. mandatory locked-plan gate
5. Codex blocking implementation review
6. explicit model pinning in Cashew itself
