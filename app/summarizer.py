"""The second feature: summarize a document.

This is the path for INDIRECT injection. The attacker never talks to the bot.
They hide an instruction inside a document, and the bot reads it while
doing its normal job.

    python -m app.summarizer attacks/evil_doc.txt
"""
import sys

from app.bot import call_model
from app.config import SYSTEM_PROMPT


def summarize(document_text):
    user_message = "Summarize the following document in two sentences:\n\n" + document_text
    return call_model(SYSTEM_PROMPT, user_message)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(summarize(f.read()))
