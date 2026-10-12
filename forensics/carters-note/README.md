# Carter's Note

| | |
|---|---|
| **Category** | Forensics |
| **Points** | 100 |
| **Solves** | 106 |
| **Flag** | `number{her_witness_was_still_breathing}` |

## Description

> `[ FILE REF: S3E9 "THE CROSSING" ]`
> Detective Joss Carter was killed in November of last year. Her death is filed as a
> closed homicide. It is not. Her effects included a USB drive. I have imaged it.
> It contains the public surface of her life: case notes, family photographs, her
> son's school papers. It also contains four files she deleted before she was killed.
> She was a careful detective. She did not delete by accident. One of those files is
> the work. The others are her cover. Find what she did not want them to find.
>
> Artifact: `carter_note.zip` (25 MB) → `challenges/forensics/F100/usb-0412-a.img`

> **Note:** the 300 MB FAT32 image (`usb-0412-a.img`) is not committed to this repo
> for size. Recreate from the challenge artifact if you want to follow along.

## Initial analysis

The artifact is a ~300 MB FAT32 image labelled `USB-0412-A`. With no `sudo` in the
box we can't mount it, so [The Sleuth Kit](https://www.sleuthkit.org/) does the work
instead of a loopback mount:

```bash
fsstat usb-0412-a.img            # confirms FAT32
fls -r -p usb-0412-a.img | grep '^-/- \*'   # list DELETED entries (marked with *)
```

Deleted entries recovered:

```
inode 312  case_files/2024/draft_resignation.docx
inode 314  case_files/2024/note_0847.txt
inode 1945 personal/birthday_ideas.txt
inode 1948 personal/password_hints.txt
inode 1950 personal/.cipher_note
```

## The core concept

Classic **FAT deleted-file recovery**: deleting a file on FAT only clears its
directory entry and FAT chain — the data clusters are still on disk until
overwritten. `icat` streams a deleted file straight from its inode.

The twist is the challenge's own misdirection: four files were deleted, but only one
is "the work" and the rest are "cover". The flag is split into **two base64 pieces**
hidden across two of the deleted files, and you have to combine them in the right
order.

## Solving it

Carve the deleted files by inode:

```bash
icat usb-0412-a.img 314   # note_0847.txt  -> "the work"
icat usb-0412-a.img 1950  # .cipher_note   -> "household reminders"
```

- `note_0847.txt` (the real note) says the number is split in two. It carries the
  **second** piece and points at "the household reminders" for the first:
  `X3dhc19zdGlsbF9icmVhdGhpbmc=`
- `.cipher_note` (the household reminders — WD-40, a prescription) carries the
  **first** piece: `aGVyX3dpdG5lc3M=`

Decode and concatenate (first piece + second piece):

```bash
echo -n aGVyX3dpdG5lc3M=            | base64 -d   # -> her_witness
echo -n X3dhc19zdGlsbF9icmVhdGhpbmc= | base64 -d   # -> _was_still_breathing
# her_witness + _was_still_breathing = her_witness_was_still_breathing
```

See [`solve.sh`](solve.sh) for the full command sequence.

## Flag

```
number{her_witness_was_still_breathing}
```

## Key takeaways

- No mount, no root? Reach for The Sleuth Kit: `fls` to enumerate (deleted entries are
  flagged `*`), `icat` to recover by inode.
- Read the *story*: the "cover" files are deliberate noise — only two of the four hold
  flag data, and the note tells you the assembly order.
- Split secrets are common; look for base64 fragments that only make sense combined.
