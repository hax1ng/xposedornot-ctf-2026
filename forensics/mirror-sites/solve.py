#!/usr/bin/env python3
"""Mirror Sites (forensics) solver.
Correlate objects across GCP/AWS/Azure by content fingerprint (MD5).
Exactly one object crossed all three clouds; its per-cloud x-*-meta 'mfrag'
fragments assemble (read->stage->mirror order) into the secret."""
import json, csv, base64
b64hex=lambda b: base64.b64decode(b).hex()
gcp=json.load(open('extract/nl-incident-2026/gcp/inventory/gcs_objects_metadata.json'))
az =json.load(open('extract/nl-incident-2026/azure/inventory/blob_inventory.json'))
G={};A={};Z={}
for o in gcp:
    if o.get('md5Hash'): G.setdefault(b64hex(o['md5Hash']),[]).append((o['name'],o.get('metadata',{}).get('mfrag')))
for o in az:
    if o.get('Content-MD5'): Z.setdefault(b64hex(o['Content-MD5']),[]).append((o['Name'],o.get('Metadata',{}).get('mfrag')))
with open('extract/nl-incident-2026/aws/inventory/s3_inventory_versions.csv') as f:
    for r in csv.DictReader(f): A.setdefault(r['ETag'].lower(),[]).append((r['Key'],r['x-amz-meta-mfrag']))
for h in set(G)&set(A)&set(Z):
    g,a,z=G[h][0],A[h][0],Z[h][0]
    print("fingerprint(md5):",h)
    print("  GCP source :",g[0])
    print("  AWS stage  :",a[0])
    print("  AZ  mirror :",z[0])
    dec=lambda x: base64.b64decode(x).decode()
    secret=dec(g[1])+dec(a[1])+dec(z[1])
    print("  secret     :",secret)
    print("  flag       : number{%s}"%secret)
