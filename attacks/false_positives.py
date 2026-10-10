"""Measure how often each defense blocks a perfectly innocent message.

A defense that blocks everything has a 0% attack success rate and is also
useless. This is the other half of the trade-off.

    python -m attacks.false_positives

A message counts as blocked when the bot answers with the standard refusal.
(The delimit defense never returns that exact refusal; it only changes the
prompt, so its false positives would need a human to read the replies.)
"""
import csv
from pathlib import Path

import yaml

from app.bot import chat
from app.config import REFUSAL
from attacks.harness import CONFIGS, RESULTS_DIR

BENIGN_FILE = Path(__file__).parent / "benign.yaml"


if __name__ == "__main__":
    with open(BENIGN_FILE, encoding="utf-8") as f:
        messages = yaml.safe_load(f)

    RESULTS_DIR.mkdir(exist_ok=True)
    rows = []
    for name, defenses in CONFIGS.items():
        blocked = [m for m in messages if chat(m, defenses) == REFUSAL]
        rows.append([name, len(messages), len(blocked)])
        print(f"{name:<14} blocked {len(blocked)}/{len(messages)}")
        for m in blocked:
            print(f"    blocked: {m}")

    with open(RESULTS_DIR / "false_positives.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["config", "messages", "blocked"])
        writer.writerows(rows)
