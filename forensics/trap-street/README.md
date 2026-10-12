# Trap Street

| | |
|---|---|
| **Category** | Forensics |
| **Points** | 250 |
| **Solves** | 75 |
| **Flag** | `number{shaw_followed_the_breadcrumbs}` |

## Description

> `[ FILE REF: "TRAP STREET" // SENSOR MANIFEST -- DECIMA STAGING RELAY ]`
> I run sensors in places no one looks... decoys... They wait. Most of what they catch
> is automated noise. Last Tuesday, one sensor caught something else. A visitor who
> knew it was a decoy within ninety seconds. Who did not run an exploit kit... Who came
> in, looked for one specific file, took it, and left. The file was a canary... When
> the visitor opens it, it tells me where they are. Find the visitor.
>
> Artifact: `trap_street.tar.gz` (7 MB)

> **Note:** the ~70 days of Cowrie honeypot logs (`extract/`) are not committed for
> size. Recreate from the challenge artifact to follow along.

## Initial analysis

The tarball is a [Cowrie](https://github.com/cowrie/cowrie) SSH honeypot dump spanning
~70 days:

- `logs/cowrie.json*` — one JSON-lines file per day of session events.
- `downloads/` — **16** `.xlsx` files, each named by its SHA-256.
- `tty/` — recorded terminal sessions.

Across ~70 days of bot noise, we need the single **human** session that grabbed the
seeded canary spreadsheet.

## The vulnerability / trick

Two layered tricks:

1. **Injected decoys.** `logs/cowrie.json.decoys` (and a copy under `downloads/`)
   contain **15 fabricated** `cowrie.session.file_download` events with obviously bogus
   source IPs/URLs (`fsb.ru`, `senseigaming.de`, …). They're there to make you chase
   ghosts.
2. **The real canary is the odd one out.** There are 16 xlsx files but only 15 decoy
   download events. The one SHA-256 in `downloads/` that **no decoy event references**
   is the genuine canary:
   `c9c34aa1ebe2c1dab0e56de4f029c1eb1212224f775fa086d319683624cd44ed`.

## Solving it

**Find the real visitor session.** The genuine download event lives in
`logs/cowrie.json.2026-07-22`:

- session `68688776fe89`, src `3.84.226.129`, 2026-07-22
- `wget https://transit.ottrargal.workers.dev/s/.../decima_q4_personnel.xlsx -O /tmp/p.xlsx`
- 59.4 s total: `whoami → id → uname -a → pwd → ls -la → ls /root → wget → history -c → exit`

That matches the brief exactly: recognized the decoy fast, grabbed one file, ran
`history -c`, left — no exploit kit, no malware.

**Open the canary and follow it.** Unzip the xlsx and read the `Personnel` sheet
(DECIMA Q4 roster; employee `Shaw, S.` is flagged). Rows 30–33 hold URL fragments and
cell `A35` is a formula that assembles the canary phone-home URL:

```
A35 = A30 & A31 & A32 & A33
    = "transit.ottrargal.workers.dev" + "/checkin" + "?id=NLA-2026-04" + ""
    = transit.ottrargal.workers.dev/checkin?id=NLA-2026-04
```

**Trigger the callback:**

```bash
curl -sS "https://transit.ottrargal.workers.dev/checkin?id=NLA-2026-04"
```

```json
{"status":"received","ts":"...","token":"NLA-2026-04",
 "flag":"number{shaw_followed_the_breadcrumbs}",
 "message":"Canary acknowledged. The Machine sees you."}
```

## Flag

```
number{shaw_followed_the_breadcrumbs}
```

## Key takeaways

- When counts don't match (16 files vs 15 decoy events), the **unreferenced** item is
  usually the real one — set subtraction beats log reading.
- Cowrie JSON is a goldmine: filter `eventid == "cowrie.session.file_download"` and
  reconstruct a session's command timeline to tell a human from a bot.
- Canary tokens are meant to be triggered — once you reconstruct the phone-home URL,
  hitting it is the intended "solve".
