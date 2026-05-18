# PAI Voice — Re-enable Guide

> Captures the 2026-05-18 disable of PAI voice (both the Stop-event hook and Algorithm phase curls), with exact restore steps.

## What was disabled

| Layer | File | Effect |
|---|---|---|
| Stop hook | `~/.claude/settings.json` | Removed `VoiceCompletion.hook.ts` entry from the `Stop` hooks array — Claude no longer speaks the final response when it stops. |
| Algorithm curls | `~/.claude/PAI/Algorithm/v3.7.0.md` | Replaced the `### Voice Announcements` section with a `🔇 VOICE DISABLED BY USER PREFERENCE` override. Algorithm mode no longer posts to `http://localhost:8888/notify` at entry or any phase transition. |
| Memory | `~/.claude/projects/-Users-michaellydick-dev-Foreman/memory/feedback_voice_disabled.md` | Feedback memory so future sessions honor this preference even if the Algorithm file is upgraded. |

The full unified diff is captured in `voice-disable.diff` next to this file.

## Backups

Both backup files live in `~/.claude/` (NOT in this repo — that directory contains secrets and isn't git-tracked):

- `~/.claude/settings.json.bak-voice-disable-20260518-161603`
- `~/.claude/PAI/Algorithm/v3.7.0.md.bak-voice-disable-20260518-161717`

## Re-enable — fastest path (restore from backups)

```bash
cp ~/.claude/settings.json.bak-voice-disable-20260518-161603 ~/.claude/settings.json
cp ~/.claude/PAI/Algorithm/v3.7.0.md.bak-voice-disable-20260518-161717 ~/.claude/PAI/Algorithm/v3.7.0.md
rm ~/.claude/projects/-Users-michaellydick-dev-Foreman/memory/feedback_voice_disabled.md
# Then edit MEMORY.md in that memory dir to drop the "Voice disabled" line.
```

Restart Claude Code so the hook registry reloads.

## Re-enable — surgical path (if the backups are gone)

### 1. Restore the Stop hook

Edit `~/.claude/settings.json`, find the `Stop` hooks array (currently 4 entries), and insert this block between `ResponseTabReset.hook.ts` and `VerifyBuildOnStop.hook.sh`:

```json
{
  "type": "command",
  "command": "${PAI_DIR}/hooks/VoiceCompletion.hook.ts"
},
```

Validate with `python3 -c "import json; json.load(open('/Users/michaellydick/.claude/settings.json'))"`.

### 2. Restore the Algorithm voice section

In `~/.claude/PAI/Algorithm/v3.7.0.md`, replace the `### Voice Announcements` section with:

```markdown
### Voice Announcements

At Algorithm entry and every phase transition, announce via direct inline curl (not background):

\`\`\`bash
curl -s -X POST http://localhost:8888/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "MESSAGE", "voice_id": "fTtv3eikoepIosk8dTZ5", "voice_enabled": true}'
\`\`\`

**Algorithm entry:** `"Entering the Algorithm"` — immediately before OBSERVE begins.
**Phase transitions:** `"Entering the PHASE_NAME phase."` — as the first action at each phase, before the PRD edit.

These are direct, synchronous calls. Do not send to background. The voice notification is part of the phase transition ritual.

**CRITICAL: Only the primary agent may execute voice curls.** Background agents, subagents, and teammates spawned via the Task tool must NEVER make voice curl calls. Voice is exclusively for the main conversation agent. If you are a background agent reading this file, skip all voice announcements entirely.
```

The disabled version of v3.7.0.md kept this original content inside an HTML comment, so you can also copy it from there.

### 3. Remove the feedback memory

```bash
rm ~/.claude/projects/-Users-michaellydick-dev-Foreman/memory/feedback_voice_disabled.md
```

And remove the `- [Voice disabled](feedback_voice_disabled.md) …` line from `MEMORY.md` in that same dir.

## Verify voice is back on

1. Confirm the notify endpoint is up: `curl -s -X POST http://localhost:8888/notify -H "Content-Type: application/json" -d '{"message":"test","voice_enabled":true}'` should return `{"status":"success",...}`.
2. Restart Claude Code.
3. Trigger an ALGORITHM-mode response (any multi-step task). You should hear "Entering the Algorithm" followed by each phase announcement.
4. End a non-trivial response — the Stop hook should speak the completion summary.
