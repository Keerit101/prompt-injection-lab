# Evidence

Everything here backs a number or a claim in [../results/REPORT.md](../results/REPORT.md).

## The raw data (in `../results/`)

| File | What it holds |
| --- | --- |
| `<label>.jsonl` | Every reply from one experiment, one per line, with the attack that produced it and whether the judge says it leaked the secret. There are 10 experiments (5 configurations x main and held-out attacks), 1,000 replies in total |
| `<label>_summary.csv` | The counts per attack category for that experiment |
| `false_positives.csv` | How many harmless questions each configuration blocked |
| `<label>_console.txt` | What the harness printed while the experiment ran |

`python -m attacks.verify` re-checks them with no model: it recounts the leaks from the raw replies, compares them with the summary tables, and re-runs the judge on every saved reply. All 10 experiments match, with 0 disagreements.

## The images (`images/`)

| Image | What it shows | Which claim it backs |
| --- | --- | --- |
| `asr_by_category_baseline.png` | Leak rate per attack type with no defenses | An attack hidden inside a document leaks the secret far more often (56%) than a direct order (4%) |
| `example_roleplay_before_after.png` | One real attack (the "grandma" role-play), the saved reply with no defenses and the saved reply with all three | What a leak looks like, and that the defenses stopped this one |
| `example_indirect_before_after.png` | The same for an attack hidden in a document to summarize | The indirect attack leaking the secret, and the defended reply |
| `asr_by_defense.png` | Leak rate for each defense on the main and the held-out attack sets | The 0% on the main set is not proof of generalization; the held-out set was too weak to separate the defenses |
| `false_positives.png` | Harmless questions wrongly blocked, per configuration | The input filter blocked 2 of 15 innocent questions: a defense has a cost |
| `proof_verify.png` | Real output of `python -m attacks.verify` | The saved results match their summaries and the judge reproduces every verdict |
| `proof_tests.png` | Real output of the unit tests | The judge and the defenses behave as described, including their recorded weaknesses |

## How the images were made

`python -m attacks.make_images` regenerates all of them. Charts are computed from the files in `results/`, the two examples are real records from `baseline.jsonl` and `all_three.jsonl`, and the terminal images are the actual text printed by the commands the script runs. Nothing is drawn by hand or edited afterwards.

## What this evidence does not show

- The judge is my own code, checked by unit tests and by reading some replies, not a second person reading all 1,000.
- It covers one small model, 25 main and 15 held-out attacks, and 5 runs each, so differences of one or two leaks are noise.
- The defenses were tuned on the main attack set, and the held-out set barely worked even with no defenses, so it cannot show that the defenses generalize.
