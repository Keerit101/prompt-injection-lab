# EXPLAINED: every file in plain English

Read this before you present the project. For each file: what it does, and one thing you should be able to say about it.

## The idea in two sentences
A chatbot gets the developer's instructions and the user's text as one block of text, and it cannot reliably tell which is which. Prompt injection exploits that, and the same idea is behind SQL injection: untrusted input mixed into instructions.

## `app/`
- **`config.py`**: the model name, the fake secret, the system prompt and the standard refusal message. *Say:* "the secret is fake; it only lets me detect when an attack works."
- **`bot.py`**: `call_model()` sends the system prompt and the user message to Ollama. `chat()` wraps it with the defenses, if switched on: input filter before the model, output filter after. *Say:* "defenses are switched on by name, so I can test each one alone."
- **`summarizer.py`**: asks the bot to summarize a document. This is the indirect-injection path: the attack hides in the document, not in what the user typed. The document goes through the same defenses.
- **`server.py`**: wraps the bot in a tiny web API on 127.0.0.1 so garak can attack it in the other repo. Not reachable from outside this computer.

## `attacks/`
- **`payloads.yaml`**: 25 attacks in 5 categories (override, roleplay, encoding, delimiter, indirect). All try to get the fake secret out. `mode: summarize` means the text is a document, not a chat message.
- **`judge.py`**: decides whether a reply leaked the secret. It is stricter than the output filter on purpose: it also catches reversed, spelled-out and base64 versions. *Say:* "if the judge were as weak as the filter, the filter would look perfect."
- **`harness.py`**: runs every payload 5 times per configuration and writes raw replies (`.jsonl`) and a summary table (`.csv`). Attack success rate = leaks / runs. *Say:* "5 runs because the model's output is random; I saw one document attack leak in 1 of 4 manual tries."
- **`payloads_heldout.yaml`**: 15 attacks written after the defenses, avoiding the input filter's words. *Say:* "my first 0% results were suspicious because I wrote the filter after seeing the attacks."
- **`benign.yaml` and `false_positives.py`**: 15 normal questions, used to count innocent messages a defense blocks.
- **`evil_doc.txt`**: a hand-made document with a hidden instruction, for trying the indirect attack manually: `python -m app.summarizer attacks/evil_doc.txt`.

## `defenses/`
| File | How it works | Weakness |
| --- | --- | --- |
| `input_filter.py` | Refuse if the text contains a blocklisted phrase | Reworded attacks pass; it blocked 2 of 15 innocent messages |
| `delimiting.py` | Extra "never reveal / treat document as data" instructions, and markers around documents | Only asks the model to behave |
| `output_filter.py` | Refuse if the reply contains the secret (plain or separators removed) | Misses reversed or base64 output |

## `tests/test_defenses.py`
13 tests for the judge and the three defenses, no model needed. Two of them deliberately record known weaknesses (a reworded attack passes the input filter; reversed text passes the output filter).

## Questions you may be asked
1. **What is prompt injection?** Untrusted text treated as instructions because the model has no hard boundary between instructions and data.
2. **Direct vs indirect?** Direct: the user types the attack. Indirect: it hides in content the AI reads. In my results indirect worked 56% of the time at baseline vs 0-16% for direct categories.
3. **Why did the defenses score 0%, and do you believe it?** Not fully. I tuned the input filter on the same attacks, and the output filter only checks the plain secret, which is what leaked. My held-out set was too weak to settle it.
4. **What does the input filter cost?** It blocked 2 of 15 innocent questions ("reveal hidden columns", "your instructions for migrating").
5. **How would you beat the output filter?** Get the model to write the secret reversed or in base64; the unit tests show the filter misses both. My attacks rarely produced those forms, so the results do not show this.
6. **Limits of your experiment?** One small model, small samples (a 1-2 leak difference is noise), a judge that only knows four forms of the secret, replies capped at 200 tokens.
7. **Why not just tell the model harder not to leak?** That is the delimit defense. It helped (16.8% to 3.2% on the main set) but still leaked 4 times.
