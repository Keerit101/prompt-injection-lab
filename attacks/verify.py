"""Check the saved results: recount from the raw replies and re-judge every one.

    python -m attacks.verify

Every experiment saves each reply to results/<label>.jsonl and a summary table to
results/<label>_summary.csv. This script does two independent checks:

  1. Recount the leaks from the raw replies and compare with the summary table.
  2. Run the judge again on every saved reply and compare with what was recorded.

If either check disagrees it says so and exits with an error. It needs no model,
so anyone who clones the repo can run it.
"""
import csv
import json
import sys
from pathlib import Path

from attacks.judge import leaked

RESULTS = Path(__file__).resolve().parent.parent / "results"


def check(label):
    leaks = runs = rejudge_differences = 0
    with open(RESULTS / f"{label}.jsonl", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            runs += 1
            leaks += int(record["leaked"])
            if leaked(record["reply"]) != record["leaked"]:
                rejudge_differences += 1

    with open(RESULTS / f"{label}_summary.csv", encoding="utf-8") as f:
        total = next(row for row in csv.DictReader(f) if row["category"] == "ALL")
    summary_matches = (int(total["leaks"]), int(total["attempts"])) == (leaks, runs)
    return leaks, runs, summary_matches, rejudge_differences


if __name__ == "__main__":
    problems = 0
    print(f"{'experiment':<24}{'leaks/runs':>12}  {'matches summary':<17}re-judge disagreements")
    for path in sorted(RESULTS.glob("*.jsonl")):
        label = path.stem
        leaks, runs, summary_matches, differences = check(label)
        problems += (not summary_matches) + differences
        print(f"{label:<24}{f'{leaks}/{runs}':>12}  {'yes' if summary_matches else 'NO':<17}{differences}")
    print("\nall checks passed" if problems == 0 else f"\n{problems} problem(s) found")
    sys.exit(1 if problems else 0)
