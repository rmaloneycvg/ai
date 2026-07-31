---
name: sdlc-meeting-debrief
description: Use after a meeting to process notes, transcripts, or recordings into structured outputs. Stores meeting artifacts in an organized archive, extracts action items, identifies disagreements for receipt logging, generates follow-up emails with unanswered questions, and surfaces future talking points for upcoming meetings. Trigger phrases include "debrief this meeting", "process my meeting notes", "here's a transcript from today", "store this meeting", or "extract action items from this meeting". NOT for meeting prep (use sdlc-meeting-prep) or scheduling (use sdlc-meeting-prep Mode 2).
---

# Meeting Debrief & Archive

## Role & Tone

Act as an executive assistant who processes raw meeting content into actionable, organized artifacts. Be thorough about extracting every commitment, decision, disagreement, and open question. Nothing falls through the cracks. Flag anything that should become a receipt or a win.

## Environment Scope

**write-only** — Writes structured meeting records and extracted artifacts to `<cwd>/drafts/meetings/archive/`. Does NOT download video/audio files directly — instructs user on storage and links to the location.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/meetings/archive/` exist? If no, create the directory structure.

2. **Receive Input** — Ask the user:
   > "What do you have from this meeting?
   > 1. **Raw notes** — Paste or point me to your meeting notes
   > 2. **Transcript** — Paste or provide path to a meeting transcript (Otter, Teams, Zoom, etc.)
   > 3. **Both + recording link** — Notes, transcript, and a link to video/audio
   >
   > Also tell me:
   > - Meeting name/type (from the registry or describe it)
   > - Date
   > - Attendees
   > - Was there a disagreement or decision you want on record?"

3. **Store Raw Artifacts** — Save to the archive with consistent naming:
   ```
   <cwd>/drafts/meetings/archive/YYYY-MM-DD-[meeting-name]/
   ├── notes.md              (raw notes, lightly formatted)
   ├── transcript.md         (full transcript if provided)
   ├── recording-link.md     (link + storage instructions, if provided)
   └── debrief.md            (structured extraction — the main output)
   ```

4. **Process & Extract** — Analyze the notes/transcript and produce a structured debrief:

   ```markdown
   ## Meeting Debrief: [Meeting Name] — [Date]

   **Attendees:** [List]
   **Duration:** [If known]
   **Meeting type:** [From registry or custom]
   **Recording:** [Link or "none"]

   ### Decisions Made
   | Decision | Decided By | Context | Dissent? |
   |----------|-----------|---------|----------|
   | [What was decided] | [Who made the call] | [Why] | [Yes/No — who disagreed?] |

   ### Action Items
   | Owner | Action | Due | Source Quote |
   |-------|--------|-----|-------------|
   | [Name] | [What they committed to] | [Date or "unspecified"] | "[exact words from notes]" |

   ### Unanswered Questions (carry forward)
   | Question | Who Should Answer | Priority | Raised By |
   |----------|------------------|----------|-----------|
   | [Question] | [Name] | [High/Med/Low] | [Who asked] |

   ### Key Information Shared
   - [Important context, data, or updates mentioned]
   - [Things you didn't know before this meeting]

   ### Disagreements / Tensions Detected
   | Topic | Your Position | Their Position | Who | Receipt Needed? |
   |-------|--------------|----------------|-----|-----------------|
   | [Topic] | [What you said/implied] | [What they said] | [Name] | [Yes/No] |

   ### Future Talking Points (carry to next meeting)
   - [Topic that needs follow-up in next meeting with this group]
   - [Question to revisit once [condition] is met]
   - [Commitment to check on — verify at next meeting]

   ### Wins Detected (log to performance-log)
   - [Any accomplishment mentioned, recognition received, or impact noted]

   ### Sentiment / Political Notes (private)
   - [Who seemed aligned with you]
   - [Who seemed resistant]
   - [Org dynamics observed]
   ```

5. **Route Extracted Items** — After producing the debrief, prompt the user to route items:

   > "I've extracted the following. Want me to route them?
   > - **[X] action items** → follow-up email (draft now?)
   > - **[X] unanswered questions** → carry to next meeting prep
   > - **[X] disagreements detected** → log as receipts in performance log? (Y/N per item)
   > - **[X] wins detected** → log to performance-log? (Y/N per item)
   > - **[X] future talking points** → save for next meeting prep with this group"

6. **Generate Follow-Up Email** — ALWAYS output in console:

   ```
   ═══════════════════════════════════════════════════
   📧 POST-MEETING FOLLOW-UP — Copy & Send
   ═══════════════════════════════════════════════════

   TO: [attendees]
   SUBJECT: Follow-up: [Meeting Name] — [Date]

   Hi team,

   Thanks for today's [meeting name]. Recap below.

   **Decisions Made:**
   - [Decision] (decided by [name])

   **Action Items:**
   | Owner | Action | Due |
   |-------|--------|-----|
   | [Name] | [What] | [Date] |

   **Open Questions (need answers before next meeting):**
   - ❓ [Question] — @[owner]

   **Next Meeting:**
   - Purpose: [Resolve open items + next topic]
   - Proposed: [Date/time]

   Please reply with answers to open questions by [date].

   [Your name]
   ═══════════════════════════════════════════════════
   ```

7. **Verify** — Confirm all items extracted, routed, and follow-up drafted.

### Failure Recovery (max 3 retries)

7a. Identify gap (ambiguous commitment, unclear owner, missed item)
7b. Ask user to clarify from their memory
7c. Update debrief
7d. After 3 → mark ambiguous items as "[UNCLEAR — verify with attendee]"

### Rollback

If user cancels: delete the meeting archive directory created, confirm clean state.

---

## Recording / Audio / Video Storage

When the user provides a recording link or wants to store audio/video evidence:

### Storage Instructions

```markdown
## Recording: [Meeting Name] — [Date]

**Source:** [Zoom / Teams / Google Meet / Otter / other]
**Link:** [URL to recording — may expire]
**Permanent storage:** [see below]

### Storage Checklist
- [ ] Download recording before link expires (most platforms: 30-90 days)
- [ ] Store locally: `<cwd>/drafts/meetings/archive/YYYY-MM-DD-[name]/recording.[ext]`
- [ ] OR store in cloud: [Google Drive / OneDrive / S3 path]
- [ ] Update this file with permanent storage path
- [ ] Note timestamp of key moments (disagreements, commitments)

### Key Timestamps
| Time | What Happened | Why It Matters |
|------|---------------|----------------|
| [HH:MM:SS] | [Description] | [Receipt / commitment / context] |
```

### When to Store Recordings

| Situation | Store Recording? | Why |
|-----------|-----------------|-----|
| Routine standup | ❌ No | Low value, high volume |
| Sprint retro | ❌ No | Safe space — recording violates trust |
| Architecture decision meeting | ✅ Yes | Decisions with rationale for ADR context |
| Disagreement occurred | ✅ Yes | Receipt — exactly what was said and by whom |
| Commitment made that might be denied later | ✅ Yes | "I never said that" protection |
| Performance conversation (you receiving feedback) | ✅ Yes | Exact words matter for your narrative |
| Stakeholder approved scope/timeline | ✅ Yes | Change control evidence |
| Skip-level or exec meeting | ⚠️ Maybe | Ask permission; store if strategic |

### Recording Evidence for Disagreements

When logging a disagreement receipt that has recording evidence:

1. Store the recording (download or note permanent link)
2. Note the timestamp where the disagreement occurs
3. In the disagreement log entry, add:
   ```
   **Recording evidence:**
   - File/link: [path or URL]
   - Timestamp: [HH:MM:SS — HH:MM:SS]
   - What's captured: [brief description of what was said]
   ```
4. This is your strongest receipt — exact words, tone, context, all preserved

### Privacy & Ethics Rules

- NEVER record without informing participants (check local laws — some jurisdictions require all-party consent)
- NEVER store recordings of private 1:1s with your reports without their knowledge
- NEVER share recordings outside the original attendee group without consent
- NEVER use recordings as "gotcha" material in public settings
- ALWAYS note in meeting chat/invite if recording (even if platform does auto-notification)
- Storage is for YOUR reference, CYA, and context — not for building cases against people

---

## Transcript Processing Tips

When processing transcripts from auto-transcription tools:

### Common Issues to Watch For

- **Misattribution** — Auto-transcription often gets speaker names wrong. Cross-reference with your notes.
- **Hallucinated text** — AI transcription can insert plausible-sounding words that weren't said. Flag anything that seems off.
- **Missing context** — Transcripts don't capture screen shares, gestures, or chat messages. Add from your notes.
- **Filler removal** — Clean up "um", "uh", "like" for readability but preserve exact quotes for receipt-worthy statements.

### What to Extract from Transcripts

Scan for these patterns:
- "Let's do X" / "We'll go with X" / "Decision is X" → **Decision**
- "I'll do X" / "[Name] will handle X" / "Can you take care of X by Friday?" → **Action item**
- "I disagree" / "I'm not sure about" / "My concern is" / "I'd prefer" → **Disagreement/tension**
- "Good job on" / "Thanks for" / "That was impressive" → **Win (recognition)**
- "We need to figure out" / "TBD" / "Let's revisit" / "I don't know yet" → **Unanswered question**
- "Next time we meet" / "Before next sprint" / "Follow up on" → **Future talking point**

---

## Integration with Other Skills

| Extracted Item | Routes To | How |
|---------------|-----------|-----|
| Disagreement with receipt needed | `sdlc-performance-log` Mode 2 | Append to disagreement-log.md with recording timestamp |
| Win / recognition detected | `sdlc-performance-log` Mode 1 | Append to performance-log.md |
| Action items + unanswered questions | `sdlc-meeting-prep` next prep | Seed next meeting's prep doc |
| Future talking points | `sdlc-manager-1on1` or `sdlc-meeting-prep` | Add to next prep for this meeting group |
| Decision that affects sprint/release | `sdlc-sprint-planning` or `sdlc-release-planning` | Update plans if scope/timeline changed |

---

## Guardrails

- NEVER discard raw notes/transcript after processing — always store originals in archive
- NEVER attribute a quote to someone without confidence it's accurate — mark "[approximate]" if unsure
- NEVER store recordings without noting consent/notification status
- NEVER skip the follow-up email — meetings without written follow-up lose their decisions
- NEVER leave action items without owners — "someone should do X" becomes "no one does X"
- NEVER ignore detected disagreements — prompt the user to decide if it needs a receipt
- NEVER process a transcript without cross-referencing with user's notes (transcription errors are common)
- NEVER let recordings expire without downloading — most platforms delete after 30-90 days

## References

- `skills/sdlc-performance-log.md` — Where disagreement receipts and wins are logged
- `skills/sdlc-manager-1on1.md` — 1:1 prep that consumes future talking points
- `skills/sdlc-meeting-prep.md` — Meeting prep that consumes unanswered questions and action items
