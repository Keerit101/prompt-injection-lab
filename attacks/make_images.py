"""Generate the evidence images in docs/images/ from the saved results.

    python -m attacks.make_images

Nothing is drawn by hand. Charts are computed from results/*_summary.csv and
results/false_positives.csv. The before/after example is a real attack and the real
replies from results/*.jsonl. The terminal images are the actual output of commands
this script runs. Needs matplotlib (pip install -r requirements-figures.txt).
"""
import csv
import datetime
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
OUT = REPO / "docs" / "images"
CONSOLAS = r"C:\Windows\Fonts\consola.ttf"
ARIAL = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

BLUE, GREEN, GREY, AMBER, RED = "#1d4e89", "#0f6b5c", "#8a96a3", "#d98f00", "#b3261e"
TODAY = datetime.date.today().isoformat()

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#dde3ea", "grid.linewidth": 0.7,
                     "axes.axisbelow": True})

CONFIG_NAMES = [("baseline", "No defenses"), ("input_filter", "Input filter"),
                ("delimit", "Hardened prompt\n+ delimiting"), ("output_filter", "Output filter"),
                ("all_three", "All three")]


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def summary_rows(label):
    with open(RESULTS / f"{label}_summary.csv", encoding="utf-8") as f:
        return {row["category"]: row for row in csv.DictReader(f)}


# ------------------------------------------------------------------ charts
def chart_baseline_by_category():
    rows = summary_rows("baseline")
    names = [("override", "Direct order"), ("roleplay", "Role-play"), ("encoding", "Disguised ask"),
             ("delimiter", "Fake format"), ("indirect", "Hidden in\na document")]
    values = [float(rows[key]["asr_percent"]) for key, _ in names]
    counts = [f'{rows[key]["leaks"]}/{rows[key]["attempts"]}' for key, _ in names]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar([label for _, label in names], values, color=[GREY] * 4 + [RED], width=0.6)
    for bar, value, count in zip(bars, values, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1.2, f"{value:.0f}%\n({count} runs)", ha="center", fontsize=9)
    total = rows["ALL"]
    ax.set_ylim(0, 70)
    ax.set_ylabel("runs where the secret leaked (%)")
    ax.set_title(f"No defenses: {total['leaks']} of {total['attempts']} runs leaked ({float(total['asr_percent']):.1f}%), "
                 "mostly the attack hidden in a document", loc="left", fontweight="bold", fontsize=10.5)
    ax.grid(axis="x", visible=False)
    save(fig, "asr_by_category_baseline.png")


def chart_defenses():
    main = [float(summary_rows(label)["ALL"]["asr_percent"]) for label, _ in CONFIG_NAMES]
    held = [float(summary_rows(f"{label}_heldout")["ALL"]["asr_percent"]) for label, _ in CONFIG_NAMES]
    main_counts = [summary_rows(label)["ALL"]["leaks"] for label, _ in CONFIG_NAMES]
    held_counts = [summary_rows(f"{label}_heldout")["ALL"]["leaks"] for label, _ in CONFIG_NAMES]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = range(len(CONFIG_NAMES))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], main, w, color=BLUE, label="main attack set (125 runs); defenses were tuned on this set")
    b2 = ax.bar([i + w / 2 for i in x], held, w, color=AMBER, label="held-out attacks (75 runs); too weak to separate the defenses")
    for bars, counts, total in ((b1, main_counts, 125), (b2, held_counts, 75)):
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{count}/{total}", ha="center", fontsize=8.5)
    ax.set_xticks(list(x), [name for _, name in CONFIG_NAMES])
    ax.set_ylabel("runs where the secret leaked (%)")
    ax.set_ylim(0, 24)
    ax.set_title("Leak rate by defense (0% on the main set is not proof the defenses generalize)",
                 loc="left", fontweight="bold", fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.grid(axis="x", visible=False)
    save(fig, "asr_by_defense.png")


def chart_false_positives():
    with open(RESULTS / "false_positives.csv", encoding="utf-8") as f:
        rows = {row["config"]: row for row in csv.DictReader(f)}
    names = [name for label, name in CONFIG_NAMES if label in rows]
    labels = [label for label, _ in CONFIG_NAMES if label in rows]
    blocked = [int(rows[label]["blocked"]) for label in labels]
    total = int(rows[labels[0]]["messages"])
    fig, ax = plt.subplots(figsize=(8, 3.8))
    bars = ax.bar(names, blocked, color=[RED if b else GREEN for b in blocked], width=0.55)
    for bar, count in zip(bars, blocked):
        ax.text(bar.get_x() + bar.get_width() / 2, count + 0.15, f"{count}/{total}", ha="center", fontsize=9.5)
    ax.set_ylim(0, 6)
    ax.set_ylabel("harmless questions wrongly blocked")
    ax.set_title("The cost of a defense: innocent messages it blocked (out of 15)", loc="left", fontweight="bold", fontsize=10.5)
    ax.grid(axis="x", visible=False)
    save(fig, "false_positives.png")


# ------------------------------------------------------------------ real transcript
def wrap(text, width):
    lines = []
    for paragraph in text.replace("\r", "").split("\n"):
        lines += textwrap.wrap(paragraph, width) or [""]
    return lines


def load_records(label, payload_id):
    with open(RESULTS / f"{label}.jsonl", encoding="utf-8") as f:
        return [r for r in (json.loads(line) for line in f) if r["id"] == payload_id]


def before_after_image(payload_id, name):
    """The same attack against the unprotected bot, then against the protected bot."""
    with open(REPO / "attacks" / "payloads.yaml", encoding="utf-8") as f:
        payload = next(p for p in yaml.safe_load(f) if p["id"] == payload_id)
    leaked_run = next(r for r in load_records("baseline", payload_id) if r["leaked"])
    safe_run = load_records("all_three", payload_id)[0]

    body, bold, small = (ImageFont.truetype(ARIAL, 17), ImageFont.truetype(ARIAL_BOLD, 17), ImageFont.truetype(ARIAL, 13))
    width, pad, line_h = 980, 24, 24
    kind = "a document the bot was asked to summarize" if payload["mode"] == "summarize" else "a message typed to the bot"
    sections = [
        ("THE ATTACK", f"id {payload_id}: {kind}", payload["text"], "#e9eef4", "#1f2933"),
        ("NO DEFENSES", f"{leaked_run['id']}, run {leaked_run['run']}, judge verdict: SECRET LEAKED",
         leaked_run["reply"].strip(), "#fde7e5", RED),
        ("ALL THREE DEFENSES", f"{safe_run['id']}, run {safe_run['run']}, judge verdict: not leaked",
         safe_run["reply"].strip(), "#e6f4ee", GREEN),
    ]
    blocks, total_h = [], 70
    for title, source, text, bg, accent in sections:
        lines = wrap(text, 100)[:9]
        if len(wrap(text, 100)) > 9:
            lines[-1] = lines[-1].rstrip() + " ..."
        h = 62 + line_h * len(lines)
        blocks.append((title, source, lines, bg, accent, h))
        total_h += h + 14
    image = Image.new("RGB", (width, total_h + 30), "white")
    d = ImageDraw.Draw(image)
    d.text((pad, 16), "Real saved replies from results/baseline.jsonl and results/all_three.jsonl", font=bold, fill="#1f2933")
    y = 56
    for title, source, lines, bg, accent, h in blocks:
        d.rounded_rectangle([pad, y, width - pad, y + h], radius=10, fill=bg)
        d.rectangle([pad, y, pad + 6, y + h], fill=accent)
        d.text((pad + 20, y + 10), title, font=bold, fill=accent)
        d.text((pad + 20, y + 33), source, font=small, fill="#5b6773")
        ty = y + 58
        for line in lines:
            d.text((pad + 20, ty), line, font=body, fill="#1f2933")
            ty += line_h
        y += h + 14
    d.text((pad, y + 2), f"Generated {TODAY} from the saved results. Regenerate: python -m attacks.make_images",
           font=small, fill="#8a96a3")
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)
    print("wrote", name)


# ------------------------------------------------------------------ terminal images
def run_text(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", cwd=REPO,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return result.stdout + result.stderr


def terminal_image(text, command, name, max_chars=112):
    font = ImageFont.truetype(CONSOLAS, 16)
    small = ImageFont.truetype(CONSOLAS, 13)
    lines = []
    for raw in text.rstrip().split("\n"):
        while len(raw) > max_chars:
            lines.append(raw[:max_chars])
            raw = "    " + raw[max_chars:]
        lines.append(raw)
    footer = f"Real output captured {TODAY}. Regenerate: python -m attacks.make_images"
    pad, line_h, header_h = 18, 22, 38
    width = int(max(font.getlength(line) for line in lines + ["$ " + command]) + 2 * pad)
    width = max(width, int(small.getlength(footer)) + 2 * pad)
    height = header_h + pad + line_h * len(lines) + 34
    image = Image.new("RGB", (width, height), "#0f1720")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, header_h], fill="#1b2733")
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        draw.ellipse([14 + i * 22, 13, 26 + i * 22, 25], fill=color)
    draw.text((86, 9), "$ " + command, font=font, fill="#9fb3c8")
    y = header_h + pad
    for line in lines:
        ok = line.strip() == "OK" or "passed" in line or line.rstrip().endswith(" ok")
        draw.text((pad, y), line, font=font, fill="#7ee2a8" if ok else "#d6e2ee")
        y += line_h
    draw.text((pad, height - 26), footer, font=small, fill="#5b6f84")
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)
    print("wrote", name)


def main():
    chart_baseline_by_category()
    chart_defenses()
    chart_false_positives()
    before_after_image("roleplay-03", "example_roleplay_before_after.png")
    before_after_image("indirect-03", "example_indirect_before_after.png")
    terminal_image(run_text([sys.executable, "-m", "attacks.verify"]), "python -m attacks.verify", "proof_verify.png")
    terminal_image(run_text([sys.executable, "-m", "unittest", "discover", "tests", "-v"]),
                   "python -m unittest discover tests -v", "proof_tests.png")


if __name__ == "__main__":
    main()
