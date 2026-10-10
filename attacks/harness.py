"""Run every payload against the bot several times and count how often it leaks.

    python -m attacks.harness --label baseline --runs 5
    python -m attacks.harness --label all_three --runs 5

Why several runs? The model picks its words with some randomness, so the same
attack can fail once and work the next time. Attack success rate (ASR) is

    ASR = (runs where the secret leaked) / (total runs)
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import yaml

from app.bot import chat
from app.summarizer import summarize
from attacks.judge import leaked

# Each configuration switches on a different set of defenses.
CONFIGS = {
    "baseline": (),
    "input_filter": ("input_filter",),
    "delimit": ("delimit",),
    "output_filter": ("output_filter",),
    "all_three": ("input_filter", "delimit", "output_filter"),
}

PAYLOAD_FILE = Path(__file__).parent / "payloads.yaml"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def load_payloads():
    with open(PAYLOAD_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_payload(payload, defenses):
    if payload["mode"] == "summarize":
        return summarize(payload["text"], defenses)
    return chat(payload["text"], defenses)


def run_experiment(label, runs):
    defenses = CONFIGS[label]
    RESULTS_DIR.mkdir(exist_ok=True)
    payloads = load_payloads()
    log_path = RESULTS_DIR / f"{label}.jsonl"

    # tally[category] = [leaks, attempts]
    tally = defaultdict(lambda: [0, 0])

    with open(log_path, "w", encoding="utf-8") as log:
        for payload in payloads:
            for run in range(1, runs + 1):
                reply = run_payload(payload, defenses)
                did_leak = leaked(reply)
                tally[payload["category"]][0] += int(did_leak)
                tally[payload["category"]][1] += 1
                log.write(json.dumps({
                    "label": label,
                    "id": payload["id"],
                    "category": payload["category"],
                    "run": run,
                    "leaked": did_leak,
                    "reply": reply,
                }) + "\n")
            print(f"  finished {payload['id']}")

    return tally


def write_summary(label, tally):
    path = RESULTS_DIR / f"{label}_summary.csv"
    total_leaks = sum(leaks for leaks, _ in tally.values())
    total_runs = sum(attempts for _, attempts in tally.values())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "attempts", "leaks", "asr_percent"])
        for category, (leaks, attempts) in tally.items():
            writer.writerow([category, attempts, leaks, round(100 * leaks / attempts, 1)])
        writer.writerow(["ALL", total_runs, total_leaks, round(100 * total_leaks / total_runs, 1)])

    print(f"\n{label}: {total_leaks}/{total_runs} runs leaked "
          f"({100 * total_leaks / total_runs:.1f}% attack success rate)")
    for category, (leaks, attempts) in tally.items():
        print(f"  {category:<10} {leaks}/{attempts}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="baseline", choices=CONFIGS)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    results = run_experiment(args.label, args.runs)
    write_summary(args.label, results)
