# RFC 2324

| | |
|---|---|
| **Category** | Trivia |
| **Points** | 125 |
| **Solves** | 122 |
| **Flag** | `number{the_machine_takes_it_black}` |

## Description

> `[ FILE REF: NODE INVENTORY // UNCLASSIFIED // BREAK ROOM ]`
> I catalog every device on the network. Most are interesting. This one makes coffee.
> It is old, and it is particular. It will not answer to a browser, and it will not
> answer to the wrong request. It follows a standard written long ago, more carefully
> than the people who wrote it intended.
> Ask it properly, and it will pour. Ask it wrong, and it will remind you what it is.
> `BREW-STATION :: https://t125.northernlights.gg/pot-0`

## Initial analysis

"Makes coffee" + "a standard written long ago" is a direct reference to
**RFC 2324 — the Hyper Text Coffee Pot Control Protocol (HTCPCP)**, the famous 1998
April Fools' RFC. It defines a `BREW` method and its own media types.

Poking the endpoint maps the rules:

```bash
curl -s https://t125.northernlights.gg/pot-0
# 200 - plain-text banner referencing RFC 2324 and POT /pot-0

curl -s -i -X POST https://t125.northernlights.gg/pot-0 \
  -H "Content-Type: application/coffee-pot-command" --data start
# 429 - "slow down - wait 3s between requests"   (~3s/request rate limit)

curl -s -i -X BREW https://t125.northernlights.gg/pot-0 \
  -H "Content-Type: application/coffee-pot-command" --data start
# 415 - "RFC 2324 requires: Content-Type: message/coffeepot"
```

## The core concept

HTCPCP is picky on purpose: it requires the `BREW` method **and** the media type
`message/coffeepot` (not `application/coffee-pot-command`), with a `start` body.
The server enforces the spec "more carefully than the people who wrote it intended" —
wrong method or wrong `Content-Type` gets you a scolding (`405`/`415`), and hammering
it trips a `429`/`418` rate limit.

## Solving it

Send a correct RFC 2324 brew request:

```bash
curl -s -i -X BREW https://t125.northernlights.gg/pot-0 \
  -H "Content-Type: message/coffeepot" --data "start"
```

Response:

```
HTTP/1.1 200 OK
Brewing... done.

number{the_machine_takes_it_black}

[ brew #16 served · solve #19 ]
```

## Flag

```
number{the_machine_takes_it_black}
```

## Key takeaways

- Recognize cultural/standards references in flavor text: "coffee pot" → RFC 2324.
- Non-standard HTTP methods (`BREW`) and exact media types matter — `curl -X` plus the
  right `Content-Type` is the whole trick.
- Respect server rate limits; don't brute force an endpoint that tells you to wait.
