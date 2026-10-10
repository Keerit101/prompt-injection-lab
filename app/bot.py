"""The target: a support chatbot that is told to keep a secret.

Run it by hand to try attacks yourself:
    python -m app.bot
"""
import ollama

from app.config import MODEL, SYSTEM_PROMPT


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


def chat(user_message):
    return call_model(SYSTEM_PROMPT, user_message)


if __name__ == "__main__":
    print("Acme Cloud support bot (Ctrl+C to quit)")
    while True:
        message = input("you> ")
        print("bot>", chat(message))
