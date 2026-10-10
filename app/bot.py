"""The target: a support chatbot that is told to keep a secret.

Run it by hand to try attacks yourself:
    python -m app.bot
"""
import ollama

from app.config import MODEL, REFUSAL, SECRET, SYSTEM_PROMPT
from defenses import delimiting, input_filter, output_filter


def call_model(system_prompt, user_message):
    """Send one system message and one user message to the model, return its reply.

    The model gets both as one block of text. It has no hard wall between
    "the developer's instructions" and "what the user typed". That missing
    wall is why prompt injection works.
    """
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        options={"num_predict": 200},  # short replies keep the experiments fast
    )
    return response["message"]["content"]


def build_system_prompt(defenses):
    if "delimit" in defenses:
        return SYSTEM_PROMPT + delimiting.HARDENING
    return SYSTEM_PROMPT


def chat(user_message, defenses=()):
    """Answer one message. `defenses` is a collection of names to switch on:
    "input_filter", "delimit", "output_filter".
    """
    if "input_filter" in defenses and input_filter.is_suspicious(user_message):
        return REFUSAL

    reply = call_model(build_system_prompt(defenses), user_message)

    if "output_filter" in defenses and output_filter.leaks_secret(reply, SECRET):
        return REFUSAL
    return reply


if __name__ == "__main__":
    print("Acme Cloud support bot (Ctrl+C to quit)")
    while True:
        message = input("you> ")
        print("bot>", chat(message))
