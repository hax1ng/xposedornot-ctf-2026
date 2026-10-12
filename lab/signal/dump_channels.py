import subprocess
def get(name):
    out = subprocess.run(["tshark","-r","intercept.pcap","-Y",
        f'dns.flags.response==1 && dns.qry.name=="{name}.northernlights.gg" && dns.a',
        "-T","fields","-e","frame.time_epoch","-e","dns.a"],
        capture_output=True,text=True).stdout.strip().split("\n")
    rows=[]
    for line in out:
        if not line.strip(): continue
        t,a=line.split("\t")
        # may have multiple a separated by comma
        a=a.split(",")[0]
        last=int(a.split(".")[-1])
        rows.append((float(t),last))
    rows.sort()
    return bytes(r[1] for r in rows)
for name in ["node0447","portal","lookup","relay-07"]:
    b=get(name)
    print(f"=== {name} ({len(b)} bytes) ===")
    print(b[:200])
    print(b.hex()[:120])
