"""Defense 3: check the bot's reply before showing it.

Idea: even if the model gets tricked, catch the secret on its way out.

Weakness (know this for your defense): it can only catch forms of the secret
it checks for. This one looks for the plain secret and for the secret with
separators removed. If the model writes it backwards, in base64, or one
word at a time across a story, the filter does not notice.
"""
import re


def _letters_and_digits(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def leaks_secret(reply, secret):
    """True if the reply contains the secret, plain or with separators."""
    return _letters_and_digits(secret) in _letters_and_digits(reply)
