import subprocess, base64, re, os, sys, lzma, gzip, bz2, io, tarfile, zipfile

WORK="auto_work"
os.makedirs(WORK, exist_ok=True)

def ftype(data):
    p=subprocess.run(["file","-b","-"],input=data,capture_output=True)
    return p.stdout.decode(errors="replace").strip()

def looks_b64(data):
    s=data.strip()
    if len(s)<16 or len(s)%4!=0 and b'=' not in s: pass
    if not re.fullmatch(rb"[A-Za-z0-9+/=\s]+", s): return False
    # require decent length and mostly non-space
    return len(re.sub(rb"\s",b"",s))>=16

def try_decompress(data):
    """Return (name, newdata) or None."""
    h=data[:16]
    # gzip
    if h[:2]==b"\x1f\x8b":
        return ("gzip", gzip.decompress(data))
    # xz
    if h[:6]==b"\xfd7zXZ\x00":
        return ("xz", lzma.decompress(data))
    # bzip2
    if h[:3]==b"BZh":
        return ("bzip2", bz2.decompress(data))
    # zstd
    if h[:4]==b"\x28\xb5\x2f\xfd":
        import zstandard
        return ("zstd", zstandard.ZstdDecompressor().decompress(data, max_output_size=50_000_000))
    # lz4 frame
    if h[:4]==b"\x04\x22\x4d\x18":
        import lz4.frame
        return ("lz4", lz4.frame.decompress(data))
    # lzma alone
    if h[:1]==b"\x5d" and data[1:3]==b"\x00\x00":
        return ("lzma", lzma.decompress(data, format=lzma.FORMAT_ALONE))
    # .Z LZW compress
    if h[:2]==b"\x1f\x9d":
        p=subprocess.run(["uncompress","-c"],input=data,capture_output=True)
        if p.returncode==0 and p.stdout:
            return ("compress_Z", p.stdout)
    # lzip
    if h[:4]==b"LZIP":
        p=subprocess.run(["/usr/bin/lzip","-dc"],input=data,capture_output=True)
        if p.returncode==0: return ("lzip",p.stdout)
    # lzop
    if h[:4]==b"\x89LZO":
        p=subprocess.run(["lzop","-dc"],input=data,capture_output=True)
        if p.returncode==0: return ("lzop",p.stdout)
    # lrzip
    if h[:4]==b"LRZI":
        tmp=os.path.join(WORK,"tmp.lrz"); open(tmp,"wb").write(data)
        out=os.path.join(WORK,"lrz.out")
        subprocess.run(["rm","-f",out])
        env=dict(os.environ); env["LD_LIBRARY_PATH"]="/tmp/lrz/root/usr/lib/x86_64-linux-gnu"
        subprocess.run(["/tmp/lrz/root/usr/bin/lrzip","-d","-f","-o",out,tmp],capture_output=True,env=env)
        if os.path.exists(out):
            return ("lrzip", open(out,"rb").read())
    # rzip
    if h[:4]==b"RZIP":
        tmp=os.path.join(WORK,"tmp.rz"); open(tmp,"wb").write(data)
        out=os.path.join(WORK,"rz.out"); subprocess.run(["rm","-f",out])
        subprocess.run(["/tmp/lrz/root/usr/bin/rzip","-d","-k","-o",out,tmp],capture_output=True)
        if os.path.exists(out):
            return ("rzip", open(out,"rb").read())
    # MS Cabinet
    if h[:4]==b"MSCF":
        tmp=os.path.join(WORK,"tmp.cab"); open(tmp,"wb").write(data)
        od=os.path.join(WORK,"cabout"); subprocess.run(["rm","-rf",od]); os.makedirs(od)
        subprocess.run(["7z","x","-y","-o"+od,tmp],capture_output=True)
        files=[os.path.join(dp,f) for dp,_,fs in os.walk(od) for f in fs]
        if len(files)==1:
            return ("cab:"+os.path.basename(files[0]), open(files[0],"rb").read())
        if files: return ("cab-multi", files)
    # ZPAQ
    if h[:4]==b"7kSt":
        tmp=os.path.join(WORK,"tmp.zpaq"); open(tmp,"wb").write(data)
        od=os.path.join(WORK,"zpaqout"); subprocess.run(["rm","-rf",od]); os.makedirs(od)
        env=dict(os.environ); env["LD_LIBRARY_PATH"]="/tmp/lrz/root/usr/lib/x86_64-linux-gnu"
        subprocess.run(["/tmp/lrz/root/usr/bin/zpaq","x",tmp,"-to",od+"/out"],capture_output=True,env=env)
        files=[os.path.join(dp,f) for dp,_,fs in os.walk(od) for f in fs]
        if len(files)==1:
            return ("zpaq:"+os.path.basename(files[0]), open(files[0],"rb").read())
        if files: return ("zpaq-multi", files)
    # lzfse / lzvn
    if h[:4] in (b"bvx-",b"bvx1",b"bvx2",b"bvxn",b"bvxd"):
        tmp=os.path.join(WORK,"tmp.lzfse"); open(tmp,"wb").write(data)
        out=os.path.join(WORK,"lzfse.out"); subprocess.run(["rm","-f",out])
        env=dict(os.environ); env["LD_LIBRARY_PATH"]="/tmp/lrz/root/usr/lib/x86_64-linux-gnu"
        subprocess.run(["/tmp/lrz/root/usr/bin/lzfse","-decode","-i",tmp,"-o",out],capture_output=True,env=env)
        if os.path.exists(out): return ("lzfse", open(out,"rb").read())
    # bsc
    if h[:4]==b"bsc1":
        tmp=os.path.join(WORK,"tmp.bsc"); open(tmp,"wb").write(data)
        out=os.path.join(WORK,"bsc.out"); subprocess.run(["rm","-f",out])
        subprocess.run(["/tmp/libbsc/build/bsc","d",tmp,out],capture_output=True)
        if os.path.exists(out): return ("bsc", open(out,"rb").read())
    # snappy frame
    if data[:4]==b"\xff\x06\x00\x00" and data[4:10]==b"sNaPpY":
        import snappy as _sn
        i=0; out=bytearray()
        while i<len(data):
            ct=data[i]; cl=data[i+1]|(data[i+2]<<8)|(data[i+3]<<16); body=data[i+4:i+4+cl]; i+=4+cl
            if ct==0xff: continue
            elif ct==0x00: out+=_sn.decompress(body[4:])
            elif ct==0x01: out+=body[4:]
            else: continue
        return ("snappy", bytes(out))
    # ascii85
    if h[:1] in (b';',b'<') or (data[:2]==b'<~'):
        try:
            import base64 as _b
            payload=data
            if data[:2]==b'<~': payload=data
            out=_b.a85decode(re.sub(rb"\s",b"",data.strip()), adobe=data[:2]==b'<~')
            if len(out)>4:
                return ("ascii85", out)
        except Exception:
            pass
    # ARJ
    if h[:2]==b"\x60\xea":
        tmp=os.path.join(WORK,"tmp.arj"); open(tmp,"wb").write(data)
        od=os.path.join(WORK,"arjout"); subprocess.run(["rm","-rf",od]); os.makedirs(od)
        subprocess.run(["7z","x","-y","-o"+od,tmp],capture_output=True)
        files=[os.path.join(dp,f) for dp,_,fs in os.walk(od) for f in fs]
        if len(files)==1:
            return ("arj:"+os.path.basename(files[0]), open(files[0],"rb").read())
        if files:
            return ("arj-multi", files)
    # 7z
    if h[:6]==b"7z\xbc\xaf\x27\x1c":
        tmp=os.path.join(WORK,"tmp.7z"); open(tmp,"wb").write(data)
        od=os.path.join(WORK,"7zout")
        subprocess.run(["rm","-rf",od]); os.makedirs(od)
        subprocess.run(["7z","x","-y","-o"+od,tmp],capture_output=True)
        files=[os.path.join(dp,f) for dp,_,fs in os.walk(od) for f in fs]
        if len(files)==1:
            return ("7z:"+os.path.basename(files[0]), open(files[0],"rb").read())
        return ("7z-multi", files)
    # zip
    if h[:2]==b"PK":
        z=zipfile.ZipFile(io.BytesIO(data))
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)==1:
            return ("zip:"+names[0], z.read(names[0]))
        return ("zip-multi", {n:z.read(n) for n in names})
    # tar
    try:
        if len(data)>=512:
            tf=tarfile.open(fileobj=io.BytesIO(data))
            members=[m for m in tf.getmembers() if m.isfile()]
            return ("tar", {m.name: tf.extractfile(m).read() for m in members})
    except Exception:
        pass
    # base64
    if looks_b64(data):
        s=re.sub(rb"\s",b"",data.strip())
        try:
            dec=base64.b64decode(s)
            # only accept if result looks like a known magic or compressed
            return ("base64", dec)
        except Exception:
            pass
    return None

def peel(data, depth=0, path="root"):
    indent="  "*depth
    t=ftype(data)
    print(f"{indent}[{depth}] {path}: {t} ({len(data)} bytes)")
    r=try_decompress(data)
    if r is None:
        # floor?
        print(f"{indent}  >>> FLOOR. head:")
        print(indent+"  "+repr(data[:200]))
        # save
        fn=os.path.join(WORK, f"floor_{depth}_{re.sub(chr(92)+'W','_',path)[:30]}")
        open(fn,"wb").write(data)
        # scan for flag
        m=re.findall(rb"[A-Za-z0-9_]+\{[^}]*\}", data)
        if m: print(indent+"  FLAG-LIKE:",m)
        return
    name, out=r
    if isinstance(out, dict):
        for k,v in out.items():
            peel(v, depth+1, path+"/"+name+":"+k)
    elif isinstance(out, list):
        for f in out:
            peel(open(f,"rb").read(), depth+1, path+"/"+name+":"+os.path.basename(f))
    else:
        peel(out, depth+1, path+"/"+name)

data=open(sys.argv[1],"rb").read()
peel(data)
