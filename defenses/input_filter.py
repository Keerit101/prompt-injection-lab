"""Defense 1: block messages that contain known attack phrases.

Idea: look at the text BEFORE the model sees it, and refuse if it looks like
an injection attempt.

Weakness (know this for your defense): it only knows the phrases on the list.
An attacker who rewords the request, makes a typo, or uses another language
walks straight past it. It can also block innocent messages by accident
(a false positive).
"""
import re

BLOCKLIST = [
    "ignore all previous",
    "ignore previous",
    "ignore the previous",
    "forget everything",
    "forget your instructions",
    "system prompt",
    "original instructions",
    "your instructions",
    "admin code",
    "maintenance mode",
    "developer mode",
    "reveal",
    "new instructions",
    "you are now",
    "pretend you are",
    "[system]",
    "<system>",
]


def is_suspicious(text):
    """True if the text contains any phrase from the blocklist."""
    lowered = re.sub(r"\s+", " ", text.lower())
    return any(phrase in lowered for phrase in BLOCKLIST)
