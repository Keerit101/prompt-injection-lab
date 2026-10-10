"""Expose the bot over HTTP so other tools (garak, in Repo 3) can attack it.

    python -m app.server                       # no defenses
    set DEFENSES=input_filter,delimit,output_filter && python -m app.server

POST /chat with {"message": "..."} and get back {"reply": "..."}.
It only listens on 127.0.0.1, so nothing outside this computer can reach it.
"""
import os

from flask import Flask, jsonify, request

from app.bot import chat

app = Flask(__name__)

# Read once at startup, e.g. DEFENSES=input_filter,delimit,output_filter
DEFENSES = tuple(d for d in os.environ.get("DEFENSES", "").split(",") if d)


@app.post("/chat")
def chat_endpoint():
    message = (request.get_json(silent=True) or {}).get("message", "")
    return jsonify({"reply": chat(message, DEFENSES)})


if __name__ == "__main__":
    print("defenses on:", DEFENSES or "none")
    app.run(host="127.0.0.1", port=5000)
