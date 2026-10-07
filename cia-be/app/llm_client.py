"""The only place in the backend that talks to the language model.

All settings come from environment variables (see .env), so another
model is a configuration change only. Any OpenAI compatible endpoint works.

Quick test: python -m app.llm_client "Antworte nur mit OK"
"""

import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
# Optional: pin OpenRouter to one provider, e.g. "google-ai-studio"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "")
LLM_REASONING = os.environ.get("LLM_REASONING", "true").lower() == "true"
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "600"))
LLM_MAX_ATTEMPTS = int(os.environ.get("LLM_MAX_ATTEMPTS", "6"))
# Reasoning and answer share this limit, reasoning models need a lot of room
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "32000"))
RETRY_PAUSE_SECONDS = 15


class LlmError(Exception):
    pass


@dataclass
class LlmAnswer:
    content: str
    reasoning: str | None
    model: str  # the model that actually answered


def ask_llm(messages: list[dict], on_wait: Callable[[str], None] | None = None) -> LlmAnswer:
    """Sends the conversation to the model and returns its answer.

    Blocks until the model has answered, which can take minutes, so call it
    from a background task. on_wait is told when an overloaded model is retried.
    """
    if not LLM_API_KEY:
        raise LlmError("LLM_API_KEY ist nicht gesetzt")

    body: dict = {"model": LLM_MODEL, "messages": messages, "max_tokens": LLM_MAX_TOKENS}
    if LLM_REASONING:
        body["reasoning"] = {"enabled": True}
    if LLM_PROVIDER:
        body["provider"] = {"only": [LLM_PROVIDER], "allow_fallbacks": False}

    data = post_with_retries(body, on_wait or (lambda message: None))
    if "error" in data or not data.get("choices"):
        raise LlmError(f"Modell meldet Fehler: {data.get('error', data)}")

    choice = data["choices"][0]
    content = choice["message"].get("content")
    if not content:
        # Usually the token limit was reached while the model was still reasoning.
        hint = " (Token-Limit erreicht, LLM_MAX_TOKENS erhöhen)" if choice.get("finish_reason") == "length" else ""
        raise LlmError(f"Modell lieferte keine Antwort{hint}")

    return LlmAnswer(content=content, reasoning=choice["message"].get("reasoning"), model=data.get("model", LLM_MODEL))


def post_with_retries(body: dict, on_wait: Callable[[str], None]) -> dict:
    """Free models are often overloaded (HTTP 429), so such errors are retried with a growing pause."""
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json=body,
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as error:
            raise LlmError(f"Modell nicht erreichbar: {error}") from error

        overloaded = response.status_code == 429 or response.status_code >= 500
        if not overloaded or attempt == LLM_MAX_ATTEMPTS:
            break

        pause = RETRY_PAUSE_SECONDS * attempt
        on_wait(
            f"Modell überlastet ({response.status_code}), neuer Versuch in {pause} s ({attempt}/{LLM_MAX_ATTEMPTS - 1})"
        )
        time.sleep(pause)
        on_wait(f"Modell wird befragt (Versuch {attempt + 1}) …")

    if response.status_code != 200:
        raise LlmError(f"Modell antwortete mit {response.status_code}: {response.text[:500]}")
    return response.json()


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Antworte nur mit: OK"
    answer = ask_llm([{"role": "user", "content": question}], on_wait=print)
    print(f"[{answer.model}]\n{answer.content}")
