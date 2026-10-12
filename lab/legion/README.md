# Legion

| | |
|---|---|
| **Category** | Lab |
| **Points** | 300 |
| **Solves** | 61 |
| **Flag** | `number{a_hundred_faces_one_machine}` |

## Description

> `[ FILE REF: S4E11 "If-Then-Else" // INTERCEPT :: DISTRIBUTED CHECK-IN ]`
> It does not live in one place. That is how it hides. SAMARITAN runs its errands
> through a hundred small machines, scattered across a hundred countries... I caught
> them talking one capture, a hundred voices buried in the static of a thousand more
> that do not matter. Pull them apart. Find all hundred. Name each one to me and I will
> light it on the board as you go.
>
> Artifact: `intercept.pcap` (34,133 UDP packets) · Board: `nc 3.233.72.100 8081` ·
> Submit: `POST http://3.233.72.100:8080/submit` · flag releases at 100 nodes.

> **Note:** the 2.8 MB pcap is not committed. The extracted check-in payloads are kept
> in [`port8443.hex`](port8443.hex) and the recovered node map in
> [`nodes.json`](nodes.json), which [`solve.py`](solve.py) runs against.

## Initial analysis

The capture is 100 % UDP. Wireshark's heuristics scatter packets across dozens of
dissectors (NTP, DNS, RTCP, …) — all noise. Looking at the destination-port histogram:

```bash
capinfos intercept.pcap
tshark -r intercept.pcap -T fields -e udp.dstport | sort | uniq -c | sort -rn
```

Big buckets at 123/443/3478/80/53/9100 plus a long tail of random high ports — and one
oddly busy port: **8443 (9,209 packets)**. That's the real check-in channel.

## The core concept — XOR-obfuscated check-ins

Pull the 8443 payloads and look at the bytes:

```bash
tshark -r intercept.pcap -Y 'udp.dstport==8443 && data' -T fields -e data.data > port8443.hex
```

Every payload XORs to a fixed frame under the single key byte **`0x5a`**:

```
\x00 <index 0..99> <CC>-<8 hex>  \x00\x00\x00\x00\x00
```

e.g. `5a581e1f773e636b6368623e6a5a5a5a5a5a ^ 0x5a`
→ `\x00\x02DE-d91928d0\x00\x00\x00\x00\x00` → index **2**, node **`DE-d91928d0`**
(country code + hex id — "scattered across a hundred countries").

## Solving it

[`solve.py`](solve.py) XORs each payload, matches the frame with a regex, and maps every
index 0–99 to its node name:

```python
FRAME = re.compile(rb"^\x00(.)([A-Z]{2}-[0-9a-f]{8})\x00{5}$", re.DOTALL)
clear = bytes(b ^ 0x5A for b in raw)
# NOTE: re.DOTALL is essential - index 10 is 0x0a ("\n"), which plain "." rejects.
```

```
$ python3 solve.py
recovered 100 / 100 unique nodes
  [ 0] US-b0ad2b92
  [ 1] GB-7746a9e0
  [ 2] DE-d91928d0
  ...
matches nodes.json: OK
```

The `re.DOTALL` detail matters: index 10 is the newline byte `0x0a`, which a default `.`
won't match — that's the node (`CA-4e53e1b5`) most people miss.

Then POST each of the 100 tokens to the board (team-name regex is
`[A-Za-z0-9_-]{1,32}`, so no spaces):

```python
POST http://3.233.72.100:8080/submit  {"team": "Cyberdyne_Systems_Model_101", "token": "DE-d91928d0"}
# at count == 100:
# {"ok": true, "done": true, "count": 100, "flag": "number{a_hundred_faces_one_machine}"}
```

## Flag

```
number{a_hundred_faces_one_machine}
```

## Key takeaways

- In a mostly-noise capture, the **destination-port histogram** is the fastest way to
  find the real channel; ignore Wireshark's misguided heuristic dissections.
- Single-byte XOR is trivial to spot once you have a hunch at the plaintext shape (the
  trailing `\x5a\x5a...` padding in the raw bytes *is* the XOR key repeated over nulls).
- Mind edge cases in regex extraction: `re.DOTALL` so control bytes (here `\n` = index 10)
  don't silently drop a record.
