
"""Unified LLM access with a FREE-TIER FAILOVER CHAIN.
Order: Gemini (free tier) -> Groq (free plan) -> OpenRouter (:free).
Every agent MUST import from here — never call a provider directly.
Keys come from environment variables; see .env.example.
Privacy rule: free tiers may train on prompts — send PUBLIC legal
texts and synthetic data only, never client/case data.
"""
import os
import time
import logging

log = logging.getLogger("qanun.llm")

SYSTEM_PROMPT_AR = (
    "أنت مساعد قانوني مصري. أجب بالعربية الفصحى المبسطة. "
    "اعتمد فقط على النصوص القانونية المقدمة لك في السياق، ولا تخترع مواد أو أرقام قوانين. "
    "إذا لم يوجد نص كافٍ، قل ذلك صراحة."
)


class LLMError(Exception):
    pass


def _call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> str:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT_AR,
                "temperature": 0.1},
    )
    return r.text


def _call_groq(prompt: str, model: str = "openai/gpt-oss-120b") -> str:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT_AR},
                  {"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return r.choices[0].message.content


def _call_openrouter(prompt: str, model: str = ":free") -> str:
    import requests
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={"model": model,
              "messages": [{"role": "system", "content": SYSTEM_PROMPT_AR},
                           {"role": "user", "content": prompt}]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


_CHAIN = [
    ("gemini", _call_gemini, "GEMINI_API_KEY"),
    ("groq", _call_groq, "GROQ_API_KEY"),
    ("openrouter", _call_openrouter, "OPENROUTER_API_KEY"),
]


def generate(prompt: str, retries_per_provider: int = 2) -> str:
    """Generate text, walking the failover chain until one provider works."""
    last_err = None
    for name, fn, key in _CHAIN:
        if not os.environ.get(key):
            continue
        for attempt in range(retries_per_provider):
            try:
                log.info("llm provider=%s attempt=%d", name, attempt + 1)
                return fn(prompt)
            except Exception as e:          # noqa: BLE001 - failover must be broad
                last_err = e
                log.warning("provider %s failed: %s", name, e)
                time.sleep(2 * (attempt + 1))
    raise LLMError(f"All free-tier providers failed. Last error: {last_err}")
