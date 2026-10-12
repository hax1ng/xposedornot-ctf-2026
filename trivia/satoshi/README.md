# Satoshi

| | |
|---|---|
| **Category** | Trivia |
| **Points** | 100 |
| **Solves** | 118 |
| **Flag** | `number{a6d72baa3db900b0}` |

## Description

> `[ FILE REF: 2009 JANUARY 03 // PUBLIC LEDGER OBSERVED ]`
> On the day the Machine was tested for the first time, somewhere else, another
> system was being born. Its creator chose anonymity. On January 3, 2009, his
> first transmission embedded a sentence, quoted from a newspaper of that morning.
> The sentence was a comment about the world he was rebelling against. About
> institutions that had failed. About the need for something different.
> I noticed it. I keep it logged.
> Read it. Hash it with SHA-256. Give me the first sixteen hexadecimal
> characters, lowercase.

## Initial analysis

Every clue points at a single real-world event:

- **"2009 JANUARY 03 // PUBLIC LEDGER"** — the Bitcoin **genesis block**, mined by
  Satoshi Nakamoto on 2009-01-03.
- **"creator chose anonymity"** — Satoshi.
- **"first transmission embedded a sentence, quoted from a newspaper of that morning"** —
  the coinbase transaction of the genesis block contains an embedded ASCII string
  taken from the front page of *The Times* that day.

The embedded text is:

```
The Times 03/Jan/2009 Chancellor on brink of second bailout for banks
```

## The core concept

The challenge is a lookup + a hashing step. The only real ambiguity is *what exactly
to hash*: the newspaper headline alone, or the full embedded string including the
`The Times 03/Jan/2009` citation. The "transmission" Satoshi actually logged into the
block is the **complete 69-byte coinbase string**, so that is the correct input.

## Solving it

Hash each candidate and take the first 16 hex chars, lowercase:

```bash
# headline only
python3 -c "import hashlib;print(hashlib.sha256(b'Chancellor on brink of second bailout for banks').hexdigest()[:16])"
# -> 8131e6f4b45754f2

# full embedded coinbase string (the actual "transmission")
python3 -c "import hashlib;print(hashlib.sha256(b'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks').hexdigest()[:16])"
# -> a6d72baa3db900b0
```

The headline-only hash was rejected; the full coinbase string is the accepted answer.

## Flag

```
number{a6d72baa3db900b0}
```

## Key takeaways

- Narrative trivia usually encodes one concrete fact — decode the flavor text literally.
- When a clue says "the sentence he *embedded*", prefer the exact bytes the system
  recorded (the full coinbase string) over the human paraphrase (the headline).
- The literal instruction ("first sixteen hex, lowercase") still goes inside the
  event's `number{...}` wrapper — read the format rules, don't assume.
