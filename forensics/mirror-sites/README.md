# Mirror Sites

| | |
|---|---|
| **Category** | Forensics |
| **Points** | 400 |
| **Solves** | 70 |
| **Flag** | `number{the_clouds_do_not_speak_to_each_other_but_we_do}` |

## Description

> `[ FILE REF: DECIMA CLOUD SERVICES // CLIENT DATA FLOW -- NORTHERN LIGHTS ]`
> A senior engineer... moved a client dataset out of the company... It was read in one
> cloud, staged in a second, mirrored into a third -- a personal tenant. No single
> provider saw the whole thing... I have all three logs. They do not agree. They do not
> even use the same clock. But the data carried the same fingerprint into every cloud it
> touched, and I do not forget a fingerprint. Reconstruct the night. Prove it was one
> person, one object, three clouds. Tell me what they took.
>
> Artifact: `nl-incident-2026.tar.gz` (23 MB)

> **Note:** the 23 MB of multi-cloud logs (`extract/`) are not committed for size.
> [`solve.py`](solve.py) expects them under `extract/nl-incident-2026/`.

## Initial analysis

The tarball contains logs and inventories from three clouds, one bucket each:

| Cloud | Account / bucket | Inventory | MD5 field |
|---|---|---|---|
| GCP | `decima-prod-8841` / `gs://decima-clients-prod` | `gcs_objects_metadata.json` | `md5Hash` (base64) |
| AWS | `481516234297` / `s3://ak-personal-staging` | `s3_inventory_versions.csv` | `ETag` (hex) |
| Azure | `nlmirror01` / container `archive` | `blob_inventory.json` | `Content-MD5` (base64) |

The README warns that **filenames, timestamps and timezones are decoys** ("not
everything inside it is true to the eye"), but "the data carried the same fingerprint
into every cloud."

## The core concept

The one thing an exfiltrator **can't** change as they copy an object between clouds is
its **content MD5**. Each cloud stores that hash in its own encoding:

- GCP `md5Hash` — base64
- AWS `ETag` — already hex (for non-multipart objects)
- Azure `Content-MD5` — base64

Normalize all three to hex and **intersect the three inventories**. Exactly one hash is
common to all three clouds — that's the single exfiltrated object, renamed at each hop.

Each cloud also stashed one base64 **`mfrag`** (message fragment) in the object's
user-metadata. Assembled in read → stage → mirror order they spell the flag.

## Solving it

[`solve.py`](solve.py):

```python
b64hex = lambda b: base64.b64decode(b).hex()
# GCP md5Hash (b64) -> hex ; AWS ETag (hex) ; Azure Content-MD5 (b64) -> hex
for h in set(G) & set(A) & set(Z):       # intersection across all three clouds
    secret = dec(G[h][1]) + dec(A[h][1]) + dec(Z[h][1])   # mfrag read->stage->mirror
    print("number{%s}" % secret)
```

```
fingerprint(md5): c47f74a1d55cf905790b9c97b4640730
  GCP source : exports/2026/q4/nl_client_roster_2026Q4.xlsx
  AWS stage  : staging/tmp/ds_0917.bin
  AZ  mirror : archive/backup_final.dat
  secret     : the_clouds_do_not_speak_to_each_other_but_we_do
```

Fragments:

| Cloud | base64 `mfrag` | decoded |
|---|---|---|
| GCP | `dGhlX2Nsb3Vkc19kb19ub3Rf` | `the_clouds_do_not_` |
| AWS | `c3BlYWtfdG9fZWFjaF9vdGhlcl8=` | `speak_to_each_other_` |
| Azure | `YnV0X3dlX2Rv` | `but_we_do` |

**What they took:** a CLIENT-CONFIDENTIAL roster, `nl_client_roster_2026Q4.xlsx`
(29,201 bytes) — read from the GCP prod bucket, staged in a personal AWS bucket as
`ds_0917.bin`, mirrored into a personal Azure tenant as `backup_final.dat`, then the
Azure copy was deleted to cover tracks.

## Flag

```
number{the_clouds_do_not_speak_to_each_other_but_we_do}
```

## Key takeaways

- **Content hash is the invariant.** When filenames/timestamps are untrustworthy,
  correlate on MD5/SHA — and watch for the same hash wearing three different encodings
  (base64 vs hex) across providers.
- Cross-source correlation = set intersection. Normalize to one representation first.
- Cloud object metadata (`x-amz-meta-*`, GCS `metadata`, Azure `Metadata`) survives
  renames and is a classic place to hide fragments.
