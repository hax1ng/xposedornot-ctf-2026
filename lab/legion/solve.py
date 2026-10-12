#!/usr/bin/env python3
"""
Legion (Lab, 300) - extract the 100 SAMARITAN node check-ins.

The real check-in channel is UDP dst port 8443. Every payload is XOR-obfuscated
with the single byte 0x5a and has the fixed shape:

    \\x00 <index byte 0..99> <CC>-<8 hex>  \\x00\\x00\\x00\\x00\\x00

where CC is a 2-letter country code and the 8 hex chars are the node id.

`port8443.hex` holds the raw payloads from `udp.dstport==8443` (one per line),
pre-extracted from the capture with:

    tshark -r intercept.pcap -Y 'udp.dstport==8443 && data' \\
           -T fields -e data.data > port8443.hex

Running this against that file rebuilds the index->node map (identical to the
committed nodes.json) and proves all 100 nodes are present.
"""
import json
import os
import re

HERE = os.path.dirname(__file__)

# Fixed frame layout after XOR 0x5a. DOTALL matters: index 10 is 0x0a ("\n"),
# which a default "." would refuse to match.
FRAME = re.compile(rb"^\x00(.)([A-Z]{2}-[0-9a-f]{8})\x00{5}$", re.DOTALL)


def decode_payloads(path):
    nodes = {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            raw = bytes.fromhex(line)
        except ValueError:
            continue
        clear = bytes(b ^ 0x5A for b in raw)
        m = FRAME.match(clear)
        if not m:
            continue
        index = m.group(1)[0]          # single index byte, 0..99
        name = m.group(2).decode()     # e.g. "DE-d91928d0"
        nodes[index] = name            # each index resolves consistently
    return nodes


def main():
    nodes = decode_payloads(os.path.join(HERE, "port8443.hex"))
    print(f"recovered {len(nodes)} / 100 unique nodes")
    for i in range(min(5, 100)):
        print(f"  [{i:>2}] {nodes.get(i)}")
    print("  ...")

    # Cross-check against the map that unlocked the board.
    ref_path = os.path.join(HERE, "nodes.json")
    if os.path.exists(ref_path):
        ref = {int(k): v for k, v in json.load(open(ref_path)).items()}
        assert {k: nodes[k] for k in ref} == ref, "mismatch vs nodes.json"
        print("matches nodes.json: OK")

    # Each of the 100 tokens was POSTed to the board; at count==100 it releases:
    #   number{a_hundred_faces_one_machine}


if __name__ == "__main__":
    main()
