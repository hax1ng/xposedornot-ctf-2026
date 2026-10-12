# Pilot

| | |
|---|---|
| **Category** | POI (Person of Interest) |
| **Points** | 100 |
| **Solves** | 85 |
| **Flag** | `number{558247193}` |

## Description

> `[ FILE REF: S1E1 "PILOT" // NEW NUMBER // CONTEXT: NONE ]`
> A number came up... I will tell you almost nothing. That is the point... Here is what
> surfaced with them. Tell me who they are. One more thing, before you decide what you
> think of this person. The evidence says they are dangerous. I am not certain the
> evidence is honest. Find their file. Give me their designation number.
>
> Attachment: [`dossier`](dossier/) — 3 items

## Initial analysis

The dossier has three artifacts:

| File | What it is |
|---|---|
| [`cole_notes.pdf`](dossier/cole_notes.pdf) | An Aletheia Research HR personnel record extract (HR-PR-2026-04417) |
| [`feed_still.jpg`](dossier/feed_still.jpg) | An Axis P3245-LVE CCTV still, CAM 03, 2026-03-11 17:12 |
| [`messages_export.txt`](dossier/messages_export.txt) | A device-backup message thread + a recovered calendar entry |

The ask is narrow: find the person's file and read off their **designation number**. The
twist — "I am not certain the evidence is honest" — is the whole point of the challenge.

## The core concept — read the record, distrust the framing

**Personnel record (`cole_notes.pdf`):**

- Name: **Cole, Maya E.** — Data Analyst II, Northern Lights Data Services
- Reporting manager: **Pierce, Daniel R.**
- **Employee designation: `558247193`**
- An attached analyst note (filed 2026-03-10) documents *her* flagging irregular
  after-hours access to the Northern Lights subject dataset **by her manager** — export
  volumes that don't match any project — which she meant to raise with Compliance.

**CCTV still (`feed_still.jpg`):** a hooded figure photographing someone entering a lit
building at night. EXIF `2026:03:11 17:12`, GPS `12°37'14.88"N 80°11'40.20"E`. No
appended data / no stego (ends cleanly at `FFD9`).

**Messages + calendar (`messages_export.txt`):** confrontational outbound texts
("I know what you are doing with the NL exports", "I have photos now. you will pay",
"Compliance meeting set. This ends.") and a recovered calendar event for a solo meeting
in a restricted sub-level.

**The honest reading:** Maya Cole is the *whistleblower* documenting her manager's
illicit dataset exports. The "dangerous" framing — aggressive texts, a lone meeting in a
restricted area — is the dishonest narrative the prompt warns about. The Machine's number
resolves to **her** personnel file, so her designation is the answer.

## Solving it

There is exactly **one** 9-digit designation across all three files — the others are PDF
xref offsets and a timestamp fragment:

```bash
# confirm the single real designation (not xref offsets)
pdftotext dossier/cole_notes.pdf - | grep -iE 'designation|employee'
grep -aoE '[0-9]{9}' dossier/*.pdf dossier/*.txt | sort -u
exiftool dossier/feed_still.jpg | grep -iE 'date|gps'   # corroborates the 03-11 timeline
```

→ designation `558247193`, verified unique and meaningful across the dossier.

## Flag

```
number{558247193}
```

## Key takeaways

- OSINT/POI puzzles reward **reading the primary record** over the emotional framing;
  here the "evidence" is deliberately engineered to misattribute the aggressor.
- Validate an identifier is *the* answer, not just *a* match: separate the real 9-digit
  designation from incidental 9-digit strings (PDF xref offsets, timestamps).
- Check images for stego/appended data even when the answer is elsewhere (EXIF here only
  corroborated the timeline — the JPEG ended cleanly at `FFD9`).
