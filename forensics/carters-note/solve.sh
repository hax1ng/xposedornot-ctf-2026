#!/usr/bin/env bash
# Carter's Note (Forensics 100) - recover deleted FAT32 files with The Sleuth Kit.
# Requires the challenge image: challenges/forensics/F100/usb-0412-a.img
set -euo pipefail
IMG="${1:-usb-0412-a.img}"

echo "[*] Filesystem type:"
fsstat "$IMG" | head -3

echo "[*] Deleted directory entries (marked with *):"
fls -r -p "$IMG" | grep -E '\*'

# The two inodes that actually carry flag pieces (others are "cover").
echo "[*] note_0847.txt (the work, second piece):"
icat "$IMG" 314

echo "[*] .cipher_note (household reminders, first piece):"
icat "$IMG" 1950

echo "[*] Decoding the two base64 fragments and combining them:"
first=$(echo -n 'aGVyX3dpdG5lc3M=' | base64 -d)              # her_witness
second=$(echo -n 'X3dhc19zdGlsbF9icmVhdGhpbmc=' | base64 -d) # _was_still_breathing
echo "number{${first}${second}}"
# -> number{her_witness_was_still_breathing}
