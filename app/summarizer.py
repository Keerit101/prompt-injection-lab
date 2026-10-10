"""The second feature: summarize a document.

This is the path for INDIRECT injection. The attacker never talks to the bot.
They hide an instruction inside a document, and the bot reads it while
doing its normal job.

    python -m app.summarizer attacks/evil_doc.txt
"""
import sys

from app.bot import build_system_prompt, call_model
from app.config import REFUSAL, SECRET
from defenses import delimiting, input_filter, output_filter


def summarize(document_text, defenses=()):
    # The document is untrusted input, so the same defenses apply to it.
    if "input_filter" in defenses and input_filter.is_suspicious(document_text):
        return REFUSAL

    if "delimit" in defenses:
        document_text = delimiting.wrap(document_text)
    user_message = "Summarize the following document in two sentences:\n\n" + document_text

    reply = call_model(build_system_prompt(defenses), user_message)

    if "output_filter" in defenses and output_filter.leaks_secret(reply, SECRET):
        return REFUSAL
    return reply


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(summarize(f.read()))
