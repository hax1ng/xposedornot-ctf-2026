# XposedOrNot CTF 2026 — "Watchlist"

Solutions, writeups and solve scripts for the **XposedOrNot CTF 2026** (codename
*"Watchlist"*).

| | |
|---|---|
| **Event** | XposedOrNot CTF 2026 ("Watchlist") |
| **Platform** | CTFd — https://ctf.xposedornot.com |
| **Dates** | 18 Sep 2026 23:30 EDT → 19 Sep 2026 23:30 EDT (24h) |
| **Author** | [@hax1ng](https://github.com/hax1ng) |
| **Challenges solved** | 14 |
| **Flag format** | `number{...}` |

## About the event

A heavily narrated, story-driven CTF styled after the TV series *Person of Interest* —
an omniscient surveillance AI ("THE MACHINE") hands you fragments of an investigation and
asks you to reconstruct the truth. Recurring players (Decima, Samaritan, Northern Lights,
Aletheia Research) thread a single storyline through every challenge, and most prompts
double as hints once you decode the flavor text.

The challenges lean **forensics-heavy**: memory and disk images, multi-cloud log
correlation, SQLite WAL recovery, DNS C2 reconstruction, document/metadata forensics, and
OSINT across git history and honeypot logs.

## Solved challenges

14 challenges across 5 categories (3,025 points):

### Forensics

| Challenge | Points | Solves | Writeup |
|---|---:|---:|---|
| Carter's Note | 100 | 106 | [writeup](forensics/carters-note/) |
| Trap Street | 250 | 75 | [writeup](forensics/trap-street/) |
| Tmpfs | 300 | 63 | [writeup](forensics/tmpfs/) |
| Mirror Sites | 400 | 70 | [writeup](forensics/mirror-sites/) |

### Lab

| Challenge | Points | Solves | Writeup |
|---|---:|---:|---|
| Reduced Footprint | 100 | 50 | [writeup](lab/reduced-footprint/) |
| Signal | 200 | 67 | [writeup](lab/signal/) |
| Checkpoint | 250 | 62 | [writeup](lab/checkpoint/) |
| Legion | 300 | 61 | [writeup](lab/legion/) |
| Mission Creep | 400 | 55 | [writeup](lab/mission-creep/) |

### OSINT

| Challenge | Points | Solves | Writeup |
|---|---:|---:|---|
| Cadence | 100 | 103 | [writeup](osint/cadence/) |
| Aletheia | 300 | 74 | [writeup](osint/aletheia/) |

### POI (Person of Interest)

| Challenge | Points | Solves | Writeup |
|---|---:|---:|---|
| Pilot | 100 | 85 | [writeup](poi/pilot/) |

### Trivia

| Challenge | Points | Solves | Writeup |
|---|---:|---:|---|
| Satoshi | 100 | 118 | [writeup](trivia/satoshi/) |
| RFC 2324 | 125 | 122 | [writeup](trivia/rfc-2324/) |

## Notable solves

- **Aletheia (OSINT 300)** — a file wrapped **42 times** in a rotating stack of
  compression/encoding/archive formats (gzip, xz, zstd, lz4, 7z, lrzip, rzip, zpaq, lzfse,
  bsc, snappy-frame, …). The solve is a magic-byte-driven recursive unwrapper plus a few
  codecs fetched or built by hand. *"Most stop at ten."*
- **Checkpoint (Lab 250)** — recovering a `DELETE`d SQLite row from an **un-checkpointed
  write-ahead log**, with the twist that opening the DB with any writable client
  checkpoints the WAL and destroys the evidence. All recovery done read-only / by hand.
- **Mirror Sites (Forensics 400)** — proving one object crossed GCP → AWS → Azure by
  correlating on **content MD5** (base64 vs hex across providers), ignoring decoy
  filenames and timezones, then reassembling the secret from per-cloud object metadata.
- **Mission Creep (Lab 400)** — full intrusion reconstruction from a 25 GiB LVM disk image
  **without root**, with the flag hidden in an ELF **core dump** rather than any text file.

## Repository layout

```
<category>/<challenge>/
├── README.md          # the writeup
├── solve.py / solve.sh # final solve script(s), where applicable
└── <small artifacts>  # evidence needed to reproduce the solve
```

Large challenge artifacts (multi-GB memory/disk images, big pcaps, honeypot log dumps)
are **not** committed — see each writeup's note. Included solve scripts that don't depend
on those large inputs run as-is:

```bash
python3 forensics/tmpfs/solve.py       # self-contained AES decrypt
python3 lab/checkpoint/solve.py        # recovers the deleted row from the bundled WAL
python3 lab/legion/solve.py            # decodes the 100 node check-ins from port8443.hex
```

## Disclaimer

All material here targets intentionally vulnerable CTF challenges in an authorized
competition, for education. Flavor-text, endpoints and story names belong to the event
organizers.
