# Foreman per-issue dev workflow — design notes

**Status:** design only — no Archon YAML yet. Build when the four open decisions below are locked.

A per-issue dev loop that takes a Linear issue from "freshly written" to "merged + journaled," with deliberate stops for quality and learning capture.

---

## Locked decisions

1. **Architecture:** chained — three Archon workflows, each independently runnable and retryable, not one monolithic DAG.
2. **Dev journal format:** single growing file (`Plans/dev-journal.md`), append-only, with hashtag tags. Three canonical tags:
   - `#surprise` — an unexpected finding (becomes LinkedIn article "I didn't expect that...")
   - `#dead-end` — tried something, didn't work (becomes "what I'd do differently")
   - `#mental-model` — a framing shift that changed the approach (becomes the article's spine)

The article-write step (Phase 4 LinkedIn) pulls from these tags. The journal is the article's seed; the tags are its outline.

---

## The three chained workflows

```
archon-foreman-preflight   (cheap, fast, idempotent — runs per issue)
        ↓
archon-foreman-implement   (heavy, long-running — actual work)
        ↓
archon-foreman-ship        (mechanical, audited — commit + push + journal)
```

Each emits a small artifact the next consumes (handoff via `$ARTIFACTS_DIR`):
- preflight → `dispatch-plan.json` (agent count, parallelization within issue, test plan stub)
- implement → `implementation-summary.md` (what changed, what to test)
- ship → updates `Plans/dev-journal.md`, pushes commits, updates Linear

### archon-foreman-preflight

**Purpose:** make sure the issue is tight before any implementation cost is paid.

Node sketch (4 nodes):
1. **grill-limited** (prompt node) — hard cap 5 questions, approval gate at Q3. Output: tightened issue body.
2. **decomposition-check** (prompt node with structured output `{decision, reason, child_issues?}`) — split or proceed. If split, the workflow cancels here and emits child issue stubs.
3. **parallelization-check** (prompt node) — within-issue fan-out plan: can sub-tasks run as parallel agents?
4. **emit-plan** (script node, bun) — writes `dispatch-plan.json`.

Cancellation gates:
- If decomposition-check returns `split` → cancel with the child-issue list.
- If parallelization-check fails to find a fan-out plan but the issue is multi-artifact → soft warning, proceed with single agent.

### archon-foreman-implement

**Purpose:** execute the dispatch plan. Heavy work, longest-running of the three.

Node sketch:
1. **read-dispatch-plan** (bash node) — load `dispatch-plan.json` from preflight.
2. **implement-loop** (loop node, `fresh_context: true`) — per task in the plan, implement. Loop's `until` clause: all tasks marked complete.
3. **self-review** (prompt node, post-loop) — read the diff, flag obvious issues.
4. **emit-summary** (script node) — write `implementation-summary.md` with what changed and the test commands to run.

The `fresh_context: true` on the loop is the **"clear the context"** step you described — between tasks, the loop resets so each implementation iteration doesn't inherit context bias from prior ones.

### archon-foreman-ship

**Purpose:** the audited finishing sequence — test, journal, commit, push.

Node sketch (6 nodes):
1. **read-summary** (bash node) — load `implementation-summary.md`.
2. **run-tests** (bash node) — execute the test commands from the summary. Stop on first failure.
3. **journal-entry** (prompt node) — read the diff + test output, prompt for hashtag-tagged journal entry. Output appended to `Plans/dev-journal.md`.
4. **commit** (bash node) — `git add` + `git commit` with structured message referencing the Linear issue.
5. **push** (bash node) — `git push`.
6. **linear-update** (bash node using `gh` or Linear API) — move issue to "Done" status, post a comment with the commit SHA.

---

## Dev journal format

`Plans/dev-journal.md` lives in the repo, grows append-only. Entry template:

```markdown
## YYYY-MM-DD — MIS-XXXX — <issue title>

**What I built:** <1-2 sentences>

**Test result:** <pass / fail / partial>

**Notes:**
- <observation>  #surprise
- <observation>  #dead-end
- <observation>  #mental-model

**Commit:** <SHA>

---
```

Conventions:
- One entry per issue (not per commit).
- Tags applied to bullets, not the whole entry — granularity matters for later aggregation.
- The "Notes" section is what an LLM later harvests when assembling the LinkedIn article. Sparse notes are fine; verbose ones get truncated.

A Phase 4 sub-workflow (`archon-foreman-article-assembler`) can later read this file, filter by `#mental-model`, and draft the LinkedIn post's spine. See the dedicated design section below.

---

## Future: archon-foreman-article-assembler workflow

**Status:** design only — no YAML yet. Build trigger: Phase 4, when the dev journal has 5-15 closed-issue entries worth of content. Building earlier would over-fit the schema to thin data.

**Purpose:** assemble a LinkedIn post, blog post, retrospective, or McKinsey-style report from two data sources — the dev journal (`Plans/dev-journal.md`) and Linear records (issue descriptions, comments, status transition history). Cross-referenced by `MIS-XXXX` identifier.

### Five-node sketch

```
archon-foreman-article-assembler   (read-only, worktree: false)
    │
    ├─ fetch-linear-issues    ─┐
    ├─ fetch-linear-history    │  parallel — all read-only
    ├─ read-journal           ─┘
    │
    ├─ choose-format-and-spine    (prompt + output_format)
    │
    └─ draft-article              (depends on all of the above)
```

| Node | Type | What it does |
|---|---|---|
| `fetch-linear-issues` | bash | `curl` Linear GraphQL — pull all Foreman project issues + comments. Output JSON to `$ARTIFACTS_DIR/linear-issues.json`. |
| `fetch-linear-history` | bash | `curl` Linear GraphQL — per-issue status transition history (timestamps for Backlog → In Progress → Done). Output `$ARTIFACTS_DIR/linear-history.json`. |
| `read-journal` | bash + script | Copy `Plans/dev-journal.md` to artifacts. Parse by `## YYYY-MM-DD — MIS-XXXX — <title>` headers into structured JSON (per-entry: date, issue ID, what-i-built, test result, tagged-notes-by-hashtag). |
| `choose-format-and-spine` | prompt (with `output_format`) | Reads `$ARGUMENTS` (e.g. `"LinkedIn causal-hook, 250 words"`) → decides format, target length, tone, narrative spine. Spine = the `#mental-model` thread that ties surprises into a coherent argument. |
| `draft-article` | prompt | Drafts the article from the three artifacts + the format decision. Writes to `$ARTIFACTS_DIR/article-draft.md` for human review. Never overwrites a published artifact. |

### Linear GraphQL queries needed

Pre-written so the build doesn't re-derive these:

**Issues + comments in the Foreman project:**

```graphql
query ForemanIssues {
  project(id: "9f42eb5b-b1c1-46e8-887a-a009f867978a") {
    issues(first: 50) {
      nodes {
        identifier
        title
        description
        priority
        state { name type }
        createdAt
        startedAt
        completedAt
        assignee { name }
        attachments { url title }
        comments {
          nodes { body createdAt user { name } }
        }
      }
    }
  }
}
```

**Status transition history per issue:**

```graphql
query IssueHistory($id: String!) {
  issue(id: $id) {
    history(first: 50) {
      nodes {
        createdAt
        fromState { name }
        toState { name }
      }
    }
  }
}
```

Loop over the issue identifiers from the first query; aggregate history into a single artifact for the draft node.

### Journal parsing rules

Entries are separated by `---` lines. Each entry starts with `## YYYY-MM-DD — MIS-XXXX — <title>`. Within an entry:

| Field | Pattern |
|---|---|
| Date | `## (\d{4}-\d{2}-\d{2}) — ...` |
| Issue ID | `## .* — (MIS-\d+) — ...` |
| Title | `## .* — MIS-\d+ — (.*)` |
| What I built | The paragraph after `**What I built:**` |
| Test result | The single line after `**Test result:**` |
| Tagged notes | Bullets with `#surprise`, `#dead-end`, or `#mental-model` hashtag suffix |
| PR link | The line starting with `**PR:**` |

Parser should be permissive — sparse entries (only some fields present) should not fail the run.

### Hashtag → article-section mapping

The mapping is the central design choice of the assembler. It determines what each tag "does" in the article:

| Tag | Article role | Why |
|---|---|---|
| `#mental-model` | **Narrative spine.** The framing shift a reader can steal. Most articles need one strong spine + maybe one supporting frame. | This is the highest-value content — readers share articles for the mental models, not the incident logs. |
| `#surprise` | **Hook surprises.** "I didn't expect X" — the article's hooks and twists. Best used 2-4 times. | Surprises create reader engagement but can't carry an article alone. |
| `#dead-end` | **"What I'd do differently" section.** Used sparingly — one or two near the end. | Demonstrates self-awareness; signals "this person learned, not just shipped." Too many = a litany. |

### Article format options (from `output_format` enum on choose-format-and-spine)

| Format | Length | Tone | Use case |
|---|---|---|---|
| `linkedin-causal-hook` | 200-400 words | candid, first-person | The Phase 4 SA-application LinkedIn post. Hook → surprise → spine → CTA. |
| `blog-post` | 800-1500 words | technical, first-person | Public engineering blog. Multi-section, with code snippets. |
| `retrospective-mckinsey` | 600-1000 words | professional, structured | Internal retrospective for the SA reviewer (or future-you). Situation / complication / resolution. |
| `deck` | 8-12 slides as markdown | terse, visual-first | Foundation for a Loom talk track or a portfolio review deck. |

### What's NOT in this assembler's scope

- **Publishing.** The output is a draft to `$ARTIFACTS_DIR`. Human reviews, polishes, and publishes via the appropriate skill (`linkedin-post`, `linkedin-obsidian-writer`, etc.).
- **Image generation.** No diagram or thumbnail creation — that's the `Media` skill's job.
- **Real-time updates.** This is a snapshot-in-time assembler. Re-run for a fresh draft.
- **Sentiment polish.** The draft is a first pass; the human handles voice consistency, joke insertions, and the specific phrasings that make an article land.

### Build trigger (write this on the wall before Phase 4 starts)

```
IF dev-journal.md has ≥5 entries
AND ≥3 of those entries have a #mental-model tag
AND Linear has ≥5 closed Foreman issues
  → build archon-foreman-article-assembler now (one focused session)
ELSE:
  → continue adding journal entries; defer assembler build.
```

The threshold is empirical — fewer entries means the assembler's output is hollow regardless of how well-built the workflow is.

---

## Open decisions (my defaults, please confirm or override)

1. **Grill-limited stopping rule.**
   *Default:* hard cap at 5 questions, with an Approval node at Q3 ("do we have enough?"). The Q3 checkpoint lets you exit early on tight issues without burning all 5 slots.
2. **Decomposition criteria.**
   *Default:* split if any of {>4h estimated, touches multi-file-domain, multiple independently-failable acceptance criteria, depends on un-merged work}.
3. **Parallelization scope.**
   *Confirmed:* within-issue fan-out only. Cross-issue scheduling is a dispatch-layer concern, not this workflow's.
4. **Test plan source.**
   *Default:* hybrid — workflow checks the Linear issue body for a `## Test plan` section; if absent, prompts the user to write one before proceeding. Issues without test plans don't ship.

---

## What's explicitly out of scope

- **Issue creation** — already in Linear, not the workflow's job.
- **Cross-issue scheduling** — what runs when, dependency resolution between issues. That's a calling-layer concern.
- **Code review** — could be an optional sub-workflow chained in by ship if desired, but not core.
- **Roboflow operations** — training happens in the Roboflow UI. The workflow *verifies* artifacts (e.g., `eval/baseline_metrics.md` exists) but does not *do* the training.
- **Force-push, history rewrite, branch deletion** — destructive ops require explicit user approval, not workflow automation.
- **Article assembly** — the workflow feeds the journal; assembly is a separate Phase 4 workflow.

---

## When to build this

Not before Phase 1 lands. Premature workflow engineering = same anti-pattern as premature hyperparameter tuning: no data to tune against.

Suggested build trigger: after MIS-1158 (`Commit eval/baseline_metrics.md`) is closed manually. At that point, you have one issue cycle of empirical data on what the loop actually needs.

---

## Reference

- Locked architecture decisions in this doc supersede earlier loose discussion.
- The `archon-fix-github-issue` bundled workflow is the closest existing pattern; this design is its more deliberate, journal-aware cousin.
- Per-workflow YAML belongs in `.archon/workflows/` when built. Commands referenced by command nodes belong in `.archon/commands/`.
