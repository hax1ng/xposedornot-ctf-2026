#!/usr/bin/env python3
"""Checkpoint: recover a deleted SQLite row from an un-checkpointed WAL.
Never open the trio with a writable client (it checkpoints and truncates -wal).
We parse the -wal frames manually and overlay them onto the main db in memory."""
import struct, base64, sqlite3, os
D=os.path.join(os.path.dirname(__file__),'evidence/checkpoint_evidence')
db=bytearray(open(os.path.join(D,'surveillance.db'),'rb').read())
wal=open(os.path.join(D,'surveillance.db-wal'),'rb').read()
pgsz=struct.unpack('>I',wal[8:12])[0]; off=32; frames=[]
while off+24+pgsz<=len(wal):
    pgno=struct.unpack('>I',wal[off:off+4])[0]
    frames.append((pgno,wal[off+24:off+24+pgsz])); off+=24+pgsz
img=bytearray(db)
# apply frames up to (incl) the last one still holding the RELEVANT row on its page
for pgno,page in frames[:29]:
    need=pgno*pgsz
    if need>len(img): img.extend(b'\x00'*(need-len(img)))
    img[(pgno-1)*pgsz:pgno*pgsz]=page
open('/tmp/recovered.db','wb').write(img)
con=sqlite3.connect('file:/tmp/recovered.db?immutable=1',uri=True)
row=con.execute("SELECT id,alias,ssn,status,priority,last_seen,intel FROM subjects WHERE status='RELEVANT'").fetchone()
print("recovered row:",row)
print("intel decoded:",base64.b64decode(row[6]).decode())
print("FLAG: number{%s}"%base64.b64decode(row[6]).decode())
