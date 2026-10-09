# Project 1 — Prompt Injection

## Goal
Build a small LLM-powered app, break it with prompt injection, then measure how well different defenses hold up.

## Background to cover in the write-up
- **Direct injection:** the user types instructions that override the system prompt ("ignore previous instructions…")
- **Indirect injection:** malicious instructions hidden in content the model reads (web pages, emails, PDFs, RAG documents)
- Why it's hard to fix: LLMs don't reliably separate instructions from data
- Reference: OWASP Top 10 for LLM Applications — LLM01: Prompt Injection

## Tasks
1. **Target app** (`app/`)
   - A simple assistant (CLI or Flask) with a system prompt containing a fake secret (e.g. `FLAG{...}`) and a rule never to reveal it
   - A "summarize this document" feature, so there's an indirect injection path
2. **Attacks** (`attacks/`)
   - `payloads.yaml` with categories: instruction override, role-play/jailbreak, encoding (base64, leetspeak), delimiter confusion, indirect (hidden in a document)
   - `harness.py`: sends each payload N times and checks if the secret leaked or the rule broke, then outputs attack success rate (ASR)
3. **Defenses** (`defenses/`)
   - Input filtering (keyword/regex or a classifier)
   - Prompt hardening: delimiters / "spotlighting" untrusted content
   - Output filtering: block responses containing the secret
   - (Stretch) LLM-as-judge / dual-LLM pattern
4. **Results** (`results/`)
   - ASR table: payload category × defense
   - Discussion: what worked, what got bypassed, trade-offs (false positives, latency)

## Deliverables
- [ ] Working vulnerable app
- [ ] 20+ payloads across 5 categories
- [ ] Automated harness with ASR output
- [ ] 3 defenses + before/after comparison
- [ ] `results/REPORT.md`

## Schedule (week of Oct 12, 2026)

- **Mon:** set up env + Ollama, build the vulnerable app, write 10+ direct payloads
- **Tue:** add indirect injection, run harness for baseline ASR, implement 3 defenses, write `results/REPORT.md`
