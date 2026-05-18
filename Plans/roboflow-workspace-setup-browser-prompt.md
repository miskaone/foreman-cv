# Browser Agent Prompt — Roboflow Workspace Setup for Foreman P1

Hand this to a browser agent (Claude with `mcp__claude-in-chrome__*` tools, `agent-browser` skill, or any Playwright-equipped agent). Estimated wall time: 5–10 minutes if email/Google signup is smooth.

---

## Goal

Set up a Roboflow account + workspace so that Saturday morning's Phase 1 training run (Foreman PRD §3) can start at 8AM cold. By the end of this session, the human operator should have, captured in a single message back to them:

1. Workspace **name** and **URL**.
2. The Roboflow **API key** (read-only display — capture verbatim, do NOT paste into any other site or commit to git).
3. The forked **dataset URL** for `roboflow-universe-projects/construction-site-safety`.
4. A note on which **plan tier** is active (Free vs Pro) and whether any free-tier training credits are visible.

## Context the agent needs

- Operator: the human running this browser session. The operator's email/name should be passed through at runtime, not hardcoded here.
- Target workspace name: **`flowevolve-sa-demo`** (per PRD §6.2). If taken, fall back to `foreman-cv` then `foreman-roboflow`.
- Dataset to fork: `https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety` (717 images, 10 classes). This is the canonical Roboflow safety dataset — do not substitute.
- Plan to select: **Free tier**. Do not upgrade to Pro. Do not enter payment info. If a paywall blocks any step, stop and report back.
- The operator (Mike) will be at the keyboard for email verification, OAuth confirmation, and any "are you sure" dialog. Pause and ask before clicking anything that requires a credential or commits to a plan.

## Step-by-step

1. **Open a fresh tab** at `https://app.roboflow.com/login`. Don't reuse existing tabs — the operator may have other Roboflow sessions.
2. **Choose signup path.** Two options on the page:
   - "Continue with Google" → recommended (uses the operator's Google account directly, no email verification step). Pause and ask the operator to complete the Google OAuth consent screen.
   - "Sign up with email" → fallback if Google is unavailable. Ask the operator to provide the email + password through the chat, do not type credentials yourself.
3. **Workspace creation.** After signup, Roboflow will prompt for workspace details. Set:
   - Name: `flowevolve-sa-demo` (try this exact slug first)
   - Type / use case: pick whichever option maps to "Computer Vision Project" or "Personal / Learning". Do not pick "Enterprise" — that triggers a sales contact flow.
   - If asked about team size, pick "Just me" / "1".
4. **Plan selection.** Confirm the Free tier is selected. Do not enter a credit card. If Roboflow auto-routes to a Pro trial, decline / back out.
5. **Fork the dataset.**
   - Navigate to `https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety`.
   - Click the green **"Fork Project"** (or "Use this Project" / "Clone") button.
   - When prompted for destination, select the `flowevolve-sa-demo` workspace.
   - Wait for the fork to complete. The forked project URL will look like `https://app.roboflow.com/flowevolve-sa-demo/construction-site-safety-<n>/<version>`.
6. **Grab the API key.**
   - Click the workspace avatar (top-left) → **Settings** → **API Keys**, or visit `https://app.roboflow.com/<workspace>/settings/api`.
   - Reveal the **Private API Key**. Capture the value verbatim. Do not display it on a shared screen if anyone is watching — copy directly to the operator's reply.
7. **Sanity check** the dataset before logging out:
   - On the forked project page, confirm:
     - Image count is around 717 (a small ±N drift after preprocessing splits is normal).
     - Class list includes: `Hardhat`, `NO-Hardhat`, `Mask`, `NO-Mask`, `Safety Vest`, `NO-Safety Vest`, `Person`, `Safety Cone`, `machinery`, `vehicle`.
   - If either is wildly off, stop and report — wrong dataset was forked.

## What to capture and report back

Write a single message back with this structure (fill in the blanks):

```
ROBOFLOW SETUP — RESULT

- Workspace name: <name>
- Workspace URL: <url>
- Plan tier: <Free / Pro>
- Forked dataset URL: <url>
- Image count on forked project: <n>
- Classes present: <yes/no — all 10 expected>
- API key: <DO NOT capture in the report>  ← operator stores it directly in 1Password via:
    op item create --category="API Credential" --title=Roboflow --vault=Private \
      'credential[concealed]='"$(pbpaste)" \
      workspace-id=<workspace-slug> \
      project-slug=<forked-project-slug> \
      publishable-key=<publishable-key>
  See repo `.env.op` for the reference file that resolves these via `op run`.
- Notes / surprises: <anything unexpected>
```

## Guardrails — do NOT do any of these without explicit operator approval

- Do not click "Upgrade to Pro" or enter payment info.
- Do not start a training run. Training is Saturday's work, not tonight's.
- Do not invite teammates or set up Slack / GitHub integrations.
- Do not change the forked dataset's classes, splits, or augmentations. Phase 1 wants a baseline against the upstream-as-is dataset.
- Do not screenshot or paste the API key into any third-party site (translation, OCR, etc.).
- Do not trigger browser-modal alerts (`alert()`, `confirm()`, `prompt()`) — they block the extension. If a page would trigger one, warn the operator first.

## If the agent gets stuck

Stop after 2–3 failed retries on any single step and report back to the operator with:
- The URL of the page where you stalled.
- The element you couldn't interact with (selector / visible text).
- A screenshot if the agent supports it.

Do not "improvise" alternative dataset choices, alternative workspaces, or workarounds for the Free tier paywall. Foreman P1 depends on the *canonical* dataset and the *Free* tier — both are deliberate signal in the PRD, not defaults to be optimized away.
