# Tmpfs

| | |
|---|---|
| **Category** | Forensics |
| **Points** | 300 |
| **Solves** | 63 |
| **Flag** | `number{volatile_storage_has_a_half_life}` |

## Description

> `[ FILE REF: S2E1 "THE CONTINGENCY" // SAFEHOUSE ASSET -- MEMORY ACQUISITION ]`
> He erased what he could see. He erased it from disk. He erased it from the directory
> listing... He did not understand that the process holding his file was still alive,
> and the kernel was still tracking the pages, and the memory had not yet been recycled.
> The disk image is empty. The memory is not. Find what he kept. Find what he was about
> to send. Find who he is.
>
> Artifact: `reyes_memory.7z` (389 MB) → `reyes.lime` (LiME memory image) + symbol JSON

> **Note:** the 389 MB memory image is not committed for size. The included
> [`solve.py`](solve.py) is fully self-contained (the extracted ciphertext is embedded)
> and reproduces the final decrypt without the image.

## Initial analysis

The artifact decompresses to a **LiME** Linux memory image (`reyes.lime`, ~2 GB) plus a
Volatility symbol table (`ubuntu-6.8.0-124-generic.json`). The story is textbook:
"deleted" from disk and directory, but a live process still held the file and the
kernel still had the pages — so it survives in RAM.

Volatility 3 (run under Python 3.13 to avoid a cffi mismatch) gives the process list:

```bash
# symbol json goes in volatility3/symbols/linux/ first
vol -f reyes.lime linux.pslist
vol -f reyes.lime linux.psaux
vol -f reyes.lime -p 1437 linux.envars
```

Interesting processes: `python3(1437)`, plus `tcpdump`, `nc`, `gpg-agent` (the latter
three are red herrings). The Python process is the one holding the secret:

```
python3 /tmp/.cache/vault.py --keytail 0e8a7c5d2f1b3e6a
```

## The core concept

The decryption key is **split across argv and the environment**, both recoverable
straight from process memory:

- `linux.envars` on PID 1437 →
  `VAULT_KEY_HEAD=8b3f7e2a1c4d6f9b`, `VAULT_LOC=/tmp/.cache/.vault.enc`
- the `--keytail` argv → `0e8a7c5d2f1b3e6a`

```
KEY = head + tail = 8b3f7e2a1c4d6f9b0e8a7c5d2f1b3e6a  (16-byte AES-128 key)
```

The encrypted blob itself is still in RAM. Grepping `VLT1` in the LiME image finds the
staging script with `VAULT_ENC_B64="VkxUM..."` — base64 of a `VLT1`-magic blob
(4-byte magic + 288 bytes of ciphertext). It's **AES-128-CBC with a zero IV**.

## Solving it

[`solve.py`](solve.py) base64-decodes the blob, strips the `VLT1` magic, and decrypts
with the reassembled key:

```python
blob = base64.b64decode(b64)
assert blob[:4] == b"VLT1"
ct  = blob[4:]
key = bytes.fromhex("8b3f7e2a1c4d6f9b" + "0e8a7c5d2f1b3e6a")  # head + tail
pt  = AES.new(key, AES.MODE_CBC, b"\x00"*16).decrypt(ct)
```

```
$ python3 solve.py
keylen 16 ctlen 288
unpadded: {
  "operative": "Marcus Reyes",
  "handler": "Greer",
  "program": "Northern Lights / Contingency",
  "auth_phrase": "volatile_storage_has_a_half_life",
  ...
}
```

The `auth_phrase` is the flag body.

## Flag

```
number{volatile_storage_has_a_half_life}
```

## Key takeaways

- RAM forensics with Volatility 3: `linux.pslist` / `linux.psaux` / `linux.envars`
  reconstruct a process's full command line **and** environment — great for secrets
  passed via argv/env.
- Keys split between `argv` and `environ` are a common "don't put it all in one place"
  pattern; memory sees both.
- `strings` + a known magic (`VLT1`) quickly locates a ciphertext blob in a multi-GB
  dump; zero-IV AES-CBC is a frequent CTF shortcut.
