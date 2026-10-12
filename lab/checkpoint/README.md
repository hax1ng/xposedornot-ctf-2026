# Checkpoint

| | |
|---|---|
| **Category** | Lab |
| **Points** | 250 |
| **Solves** | 62 |
| **Flag** | `number{the_log_remembers_what_the_table_forgot}` |

## Description

> `[ FILE REF: S5E10 "THE DAY THE WORLD WENT AWAY" ]`
> Before it was seized, an operator ran a purge, one record, erased on a written order.
> The deletion was committed. It was not finished. The database will tell you the record
> is gone. The database is wrong. A system writes ahead of itself; it speaks before it
> remembers. They told the table to forget her. They did not wait for the log to agree
> with the table. The node is read-only. Handle it the wrong way and you will finish the
> purge for them. Connect. Recover what they erased. Tell me who she was.
>
> Artifact: `checkpoint_evidence.tar.gz` → [`surveillance.db`](evidence/checkpoint_evidence/)
> + `-wal` + `-shm` + README

## Initial analysis

The evidence is a SQLite database with its **write-ahead log** (`-wal`) and shared-memory
index (`-shm`) still alongside it. Schema:

```
subjects(id PK, alias, ssn, status, priority, last_seen, intel)
analyst_log(ts, entry)
```

Read the main DB **read-only** (crucial — see below):

```bash
sqlite3 'file:surveillance.db?immutable=1' "SELECT status, COUNT(*) FROM subjects GROUP BY status;"
# all 1888 subjects report IRRELEVANT; analyst_log looks empty
```

But applying the WAL reveals the analyst lead:

> PURGE DIRECTIVE (handler GREER): erase the asset flagged RELEVANT before seizure.
> Target designation ends 0001. All others are cover.

## The vulnerability / trick — an un-checkpointed WAL

In SQLite WAL mode, committed changes are appended to `-wal` first and only later folded
into the main DB file by a **checkpoint**. Here the `DELETE` of the RELEVANT row was
committed to the table, **but the WAL was never checkpointed** — so the *pre-deletion*
image of that page still sits in `-wal`.

> ⚠️ **The hazard the challenge warns about:** opening the trio with a normal (writable)
> `sqlite3` client automatically checkpoints the WAL and **truncates `-wal`**, destroying
> the deleted row — "you will finish the purge for them." This happened once on a work
> copy and had to be recovered by re-extracting the tarball. So everything is done
> read-only: `immutable=1` for the main DB, and **manual parsing** of the WAL frames.

## Solving it

[`solve.py`](solve.py) parses the WAL frame-by-frame and overlays the pre-deletion pages
onto an in-memory copy of the DB, then reads it with an immutable (read-only) connection:

```python
pgsz = struct.unpack('>I', wal[8:12])[0]           # page size from WAL header
# walk 24-byte frame headers + page bodies
for pgno, page in frames[:29]:                     # frames up to the RELEVANT page image
    img[(pgno-1)*pgsz : pgno*pgsz] = page
open('/tmp/recovered.db','wb').write(img)
con = sqlite3.connect('file:/tmp/recovered.db?immutable=1', uri=True)
row = con.execute("SELECT * FROM subjects WHERE status='RELEVANT'").fetchone()
```

```
$ python3 solve.py
recovered row: (999001, 'PRIMARY', '000-00-0001', 'RELEVANT', 'CRITICAL', '2026-09-19',
                'dGhlX2xvZ19yZW1lbWJlcnNfd2hhdF90aGVfdGFibGVfZm9yZ290')
intel decoded: the_log_remembers_what_the_table_forgot
FLAG: number{the_log_remembers_what_the_table_forgot}
```

The recovered row's `intel` field is base64 → the flag body.

## Flag

```
number{the_log_remembers_what_the_table_forgot}
```

## Key takeaways

- A SQLite `.db` + `-wal` + `-shm` trio is a forensic opportunity: the WAL holds recent
  (possibly "deleted") page images not yet merged into the main file.
- **Never open evidence with a writable client.** Checkpointing truncates the WAL and
  destroys exactly what you came for. Use `?immutable=1` / parse the WAL by hand.
- WAL format is simple: 32-byte header (page size at offset 8), then repeating
  24-byte frame headers + full page bodies. Overlay frames to reconstruct past state.
