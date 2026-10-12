EVIDENCE INTAKE — NODE 'watchnode' — chain of custody
------------------------------------------------------
Recovered: a surveillance database, SQLite, WAL journaling mode.
You have the full trio:
  surveillance.db      - the main database (checkpointed history)
  surveillance.db-wal  - the write-ahead log (recent, UNFLUSHED transactions)
  surveillance.db-shm  - shared-memory index only. Holds NO records. Ignore for recovery.

HANDLING (read this before you touch anything):
  * Image before you analyze. Work on COPIES of all three files.
  * Do NOT open the original in a normal SQLite client / DB Browser. WAL-mode clients
    CHECKPOINT on open, which flushes and truncates the -wal — destroying any deleted
    records that were still sitting in it. That is the one mistake that loses the case.
  * Deleted rows are not gone: their pre-deletion page images may persist in the -wal
    until a checkpoint. Carving the -wal recovers them.

The node was seized mid-write; the WAL was never checkpointed. Everything the operator
did in their last moments is still in that log. Read the analyst_log for the lead.
