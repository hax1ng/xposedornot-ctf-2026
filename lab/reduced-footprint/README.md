# Reduced Footprint

| | |
|---|---|
| **Category** | Lab |
| **Points** | 100 |
| **Solves** | 50 |
| **Flag** | `number{the_footprint_was_never_reduced}` |

## Description

> `[ FILE REF: S2E2 "Bad Code" // NODE 0447 :: ANOMALY PERSISTENT ]`
> Node 0447 stopped reporting... They called it decommissioned. Idle. Clean. It is none
> of those things. Something on this machine wakes on a schedule, does its work, and
> goes back to sleep... You will find three things that look like they belong. Two of
> them do. The third is keeping someone resident. Open it. Read what it carries. The
> author left a key inside.
>
> Access: `ssh investigator@node0447.northernlights.gg -p 2222` · password `node0447`
> (read-only seat). "Whoever wrote this signs their work."

## Initial analysis

This is a live-box **persistence hunt**. The brief narrows it down for us: something
wakes "on a schedule" and the author "kept the footprint small" — screaming
**scheduled persistence** (cron / `atd` / systemd timer). Three things look legit; two
are, one is the implant.

Log in and look at the usual persistence spots. `systemd` timers are the payoff:

```bash
ssh investigator@node0447.northernlights.gg -p 2222   # password: node0447
ls -la /etc/systemd/system/
systemctl list-timers --all
```

## The core concept

A disguised **systemd timer + service** pair keeps the operator resident:

- `sysupdate.timer` — triggers at boot and every six hours.
- `sysupdate.service` — runs `/usr/local/lib/.sysupdate/run.sh` (note the hidden
  `.sysupdate` directory — the "small footprint").

The payload script hides the flag in a base64 token and is **signed** by the author —
the recurring "bad code" signature that ties this box to the series.

## Solving it

```bash
cat /usr/local/lib/.sysupdate/run.sh
```

```sh
#!/bin/sh
# sysupdate helper - keep the node reachable for maintenance
# signed: bad code
#
# maintenance token (base64):
echo 'bnVtYmVye3RoZV9mb290cHJpbnRfd2FzX25ldmVyX3JlZHVjZWR9' | base64 -d
```

```bash
echo 'bnVtYmVye3RoZV9mb290cHJpbnRfd2FzX25ldmVyX3JlZHVjZWR9' | base64 -d
# -> number{the_footprint_was_never_reduced}
```

The author's signature — **"bad code"** — is worth filing away; it recurs across this
event's Lab challenges.

## Flag

```
number{the_footprint_was_never_reduced}
```

## Key takeaways

- Persistence triage order on Linux: `systemctl list-timers`, `/etc/systemd/system/*`,
  crontabs, `~/.bashrc`, `atq`. "Wakes on a schedule" → look at timers first.
- Hidden dirs (`/usr/local/lib/.sysupdate`) and generic service names (`sysupdate`,
  `cleanup`) are the usual camouflage — compare against what a stock box actually ships.
- Note recurring author "signatures"; CTF series reuse them as cross-challenge hints.
