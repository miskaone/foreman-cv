# Contributing to Foreman

A solo-developer protocol. Documented so future-me (or a future collaborator) doesn't have to re-derive it.

---

## Source of truth

- **Issues** live in **Linear** (`Miskaone` workspace, `Foreman` project). Not GitHub Issues — they're intentionally left empty.
- **Code, PRs, and merge history** live on **GitHub** (`miskaone/foreman-cv`).
- **Planning artifacts** (PRD, cheat sheets, design docs, dev journal) live in `Plans/` inside this repo.

If a system feels out of sync, Linear wins for *issue status*; GitHub wins for *what's actually shipped*.

---

## Branching

One branch per Linear issue. Use the branch name Linear generates — it includes the issue ID, which Linear auto-detects to link the PR back to the issue.

Example:
```
mikelydick/mis-1156-fork-construction-site-safety-dataset-into-roboflow
```

Don't rename it. The exact format is what Linear's auto-link relies on.

`main` is protected — no direct pushes (with one exception, see "Bootstrapping" below).

---

## Pull requests

**One PR = one Linear issue = one logical unit of work.** If a change crosses two issues, it's two PRs.

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md). All four sections are mandatory:

1. **What** — one paragraph
2. **Why** — one paragraph + `Closes MIS-XXXX`
3. **Test plan** — checklist of what was tested
4. **Journal entry** — draft of the entry that goes into `Plans/dev-journal.md` on merge

**Merge style: squash-merge** by default. Keeps `main`'s history at one commit per Linear issue.

The branch is deleted on merge. The Linear issue auto-closes via the branch name link.

---

## Commit messages

Inside a feature branch, commit freely — they all get squashed at merge. Don't over-engineer commit messages on feature branches.

For commits that land directly on `main` (rare; see "Bootstrapping"), use Conventional Commits style: `type(scope): description`. Recent examples in this repo:

- `chore(p1): scaffold Archon, 1Password, and P1 execution plan`
- `docs: lock full repo slug to miskaone/foreman-cv`
- `chore: redact PII and Ashby JID before public visibility`

---

## Dev journal

`Plans/dev-journal.md` is the running log of what was learned issue-by-issue. Append on PR merge; never edit prior entries.

Three canonical tags applied to bullet points:
- `#surprise` — unexpected finding
- `#dead-end` — tried something, didn't work
- `#mental-model` — a framing shift that changed the approach

The Phase 4 LinkedIn writeup harvests this file by tag. Sparse notes are fine; verbose ones get truncated.

See `Plans/foreman-dev-workflow-design.md` for the planned Archon workflow that automates this.

---

## Bootstrapping

A small number of setup commits (PRD, initial scaffolding, branch protection itself) landed directly on `main` before this protocol was active. Direct-to-main is **not** the path forward — branch protection is enabled. The only future exceptions are:

- Repo-protection / branch-protection changes themselves (no other path)
- Emergency rollback (force-pushing a revert) — only with explicit user direction

If you're tempted to push direct-to-main for anything else: open a PR instead. It takes 30 seconds and pays compounding interest in the history.

---

## Credentials

All Roboflow credentials live in 1Password under `op://Private/Roboflow/*`. Local env injection via:

```bash
op run --env-file=.env.op -- <command>
```

`.env.op` (committed) contains references, not secrets. Never commit raw API keys or `.env` files.

---

## When in doubt

Read the [PRD](roboflow-sa-capstone-rebuild-prd-v0.1.md) for scope and the [P1 cheat sheet](Plans/P1-cheat-sheet.md) for Phase 1 execution decisions. Both supersede gut instinct.
