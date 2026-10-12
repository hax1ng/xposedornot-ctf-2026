# Aletheia

| | |
|---|---|
| **Category** | OSINT |
| **Points** | 300 |
| **Solves** | 74 |
| **Flag** | `number{forty_two_layers_of_aletheia}` |

## Description

> `[ FILE REF: "ALETHEIA" // SUBJECT: ALETHEIA RESEARCH - RECORD SANITIZED ]`
> Aletheia Research published, for a while, more than they meant to. Then they cleaned
> house... But the page was edited. The past was not. Find what they took down. It points
> to a file they tried to make unreadable wrapped, and wrapped, and wrapped again, in
> every format they could find, including some you'll have to go and build yourself.
> The truth has a floor. Dig until you reach it.
>
> Start: `https://aletheia-research.github.io/`

## Initial analysis — the past lives in git history

The live GitHub Pages site is "spotless": the nav links `/about.html`, `/research.html`,
`/contact.html` all **404**. But GitHub Pages is served from a public repo, and
"the past was not" edited — it's all in git history:

```bash
curl https://api.github.com/orgs/aletheia-research/repos
git clone https://github.com/aletheia-research/aletheia-research.github.io.git repo
cd repo && git log --stat --all
```

Deleted-but-recoverable files:

- `press.html` (deleted in `e9ad951`) — a press release naming a disclosure PDF.
- `reports/AR-2024-NL-disclosure.pdf` (deleted in `e9c0d7f`) — recover with
  `git show c361cea:reports/AR-2024-NL-disclosure.pdf > AR-2024-NL-disclosure.pdf`.
- `data/artifact` (5,347 bytes, still present) — the wrapped file.

The [recovered PDF](AR-2024-NL-disclosure.pdf) says the "supplementary data package" is a
"single compressed archive file with no file extension. Format identification is left as
an exercise" and points at `data/artifact`.

## The core concept — 42 stacked compression/encoding layers

`data/artifact` is a file wrapped **42 times** in a rotating stack of compression,
encoding and archive formats. Each layer is identified purely by its magic bytes, peeled,
and the result fed back in. The layer order (outer → inner):

```
gzip → xz → bzip2 → base64 → zstd → 7z → lzma(alone) → lz4 → tar → .Z(LZW) → zip → xz →
bzip2 → zstd → gzip → lzop → lzip → lrzip → arj → ascii85 → rzip → cab → lzop → lzip →
lrzip → arj → rzip → cab → lzip → lzop → zpaq → lzfse → snappy → zpaq → lzfse → snappy →
zpaq → lzfse → snappy → ASCII text (FLOOR)
```

Most archive layers store a single member named `ledger`; the one `tar` layer holds a
`flag.txt` decoy ("nice try, the floor is deeper than this"), a `README`, and a
`server.log` that is actually the next layer.

## Solving it

[`peel/auto.py`](peel/auto.py) auto-detects each layer by magic bytes and recurses until
it hits non-compressible ASCII (the floor):

```bash
python3 peel/auto.py layer_00
```

The `number{...}` and `flag.txt` decoys along the way don't match the real floor — the
script prints every layer and stops at the floor.

**Tools needed** ("some you'll have to go and build yourself"):

- Standard: `gzip xz bzip2 base64 zstd lz4 7z tar uncompress(.Z) lzip lzop cabextract ascii85`
- Fetched without root via `apt-get download` + `dpkg-deb -x`: **lrzip, rzip, zpaq, lzfse**
  (run with `LD_LIBRARY_PATH` pointed at the extracted libs).
- **Built from source:** **libbsc** (`bsc1`) — `git clone IlyaGrebnov/libbsc && cmake ...`.
- Snappy framed streams were decoded manually in Python (parse frame chunks, decompress
  each block), since the stream decoder segfaulted.

The floor ([`FLOOR.txt`](FLOOR.txt)):

```
[ ALETHEIA // FLOOR ]
You unwrapped me forty-two times. Most stop at ten.
Concealment has a floor, and you are standing on it.

decode:
bnVtYmVye2ZvcnR5X3R3b19sYXllcnNfb2ZfYWxldGhlaWF9

Project: Contingency
```

```bash
echo bnVtYmVye2ZvcnR5X3R3b19sYXllcnNfb2ZfYWxldGhlaWF9 | base64 -d
# -> number{forty_two_layers_of_aletheia}
```

## Flag

```
number{forty_two_layers_of_aletheia}
```

## Key takeaways

- A "sanitized" GitHub Pages site still exposes its **git history** — `git log --all` +
  `git show <commit>:<path>` recover deleted pages and binaries.
- Build a **magic-byte-driven recursive unwrapper** rather than guessing layers; it
  handles arbitrary depth and mixed formats, and ignores decoy `flag.txt` files.
- Obscure codecs (lrzip, rzip, zpaq, lzfse, bsc, snappy-frame) can be obtained without
  root via `apt-get download` + `dpkg-deb -x` + `LD_LIBRARY_PATH`, or built from source.
