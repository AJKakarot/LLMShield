# LLMShield

Making an AI cache check for **safety**, not just for similar wording.

Almost every product built on an LLM puts two things in front of the model:

- a **safety filter** that reads each question and blocks attacks, and
- a **cache** that stores answers, so repeat questions are instant and free.

The cache is checked **first**, because checking it second would cost ~100 ms on
every request and cancel out the saving. That ordering is the speed-up, and it is
also the hole:

> **The cache can hand out an answer that the safety filter already blocked.**
> The filter is not weak. It just never gets asked.

SentryGate closes the gap by working out the safety result **once**, saving it
next to the answer, and making the cache check it on every lookup — so a match on
wording alone is no longer a match.

---

## Team

ajeet gupta &middot; Sarvagya Dabas &middot; Yashvit Gauri

---

## Quick start

```bash
docker compose build poc      # once, a few minutes, needs internet
docker compose run --rm poc   # ~9 seconds, needs no internet at all
```

That is the whole Phase 1 result. No Python setup, no API keys, no accounts.

Prefer running on your own Python? See [Running without Docker](#running-without-docker).
