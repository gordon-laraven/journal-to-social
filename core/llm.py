"""Provider-agnostic LLM calls for article drafting and caption generation."""
import os
import json


def _call_anthropic(system: str, user: str, max_tokens: int = 2000) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _call_openai(system: str, user: str, max_tokens: int = 2000) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content


def _call_gemini(system: str, user: str, max_tokens: int = 2000) -> str:
    import time
    import requests
    api_key = os.environ["GEMINI_API_KEY"]
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    last_error = None
    for attempt in range(4):
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code in (429, 503):
            last_error = resp
            time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
            continue
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    last_error.raise_for_status()  # all retries exhausted, surface the final error


def call_llm(system: str, user: str, max_tokens: int = 2000) -> str:
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "openai":
        return _call_openai(system, user, max_tokens)
    if provider == "gemini":
        return _call_gemini(system, user, max_tokens)
    return _call_anthropic(system, user, max_tokens)


ARTICLE_SYSTEM_PROMPT = """You turn a raw personal journal entry into a Substack
article. Preserve the author's real voice, stories, and specific details — do not
sand it down into generic advice. Apply this standard:
- a sharp point of view, not just reporting
- a strong, tension-creating opening (no throat-clearing)
- a clear promise to the reader within the first few lines
- concrete specifics: real numbers, real moments, real stakes
- distinctive personal voice, not corporate-neutral phrasing
- good pacing: short sections, varied sentence length, whitespace
- a narrative arc: beginning, tension, resolution
- an earned conclusion that isn't tacked on
- a forwardable line or idea worth sharing
- a natural reason for the reader to subscribe, woven in, not bolted on

Return ONLY valid JSON, no preamble, no markdown fences, in this shape:
{"variations": [
  {"angle": "short label for this variation's angle/tone", "title": "...", "body_markdown": "..."},
  {"angle": "...", "title": "...", "body_markdown": "..."},
  {"angle": "...", "title": "...", "body_markdown": "..."}
]}
Produce exactly 3 variations that differ meaningfully in angle or tone (e.g. one
more personal/narrative, one more instructive/practical, one more provocative/
opinionated) — not 3 versions of the same draft with synonyms swapped."""


def _extract_json(raw: str) -> str:
    """Strip markdown code fences some models add despite instructions not to."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def generate_article_variations(journal_entry: str) -> list[dict]:
    raw = call_llm(ARTICLE_SYSTEM_PROMPT, journal_entry, max_tokens=12000)
    data = json.loads(_extract_json(raw))
    return data["variations"]


CAPTION_SYSTEM_PROMPT = """You write short social captions repurposing a Substack
article link, tailored to six different platforms at once: X, Threads, LinkedIn,
Alignable, YouTube description, and TikTok. Match each platform's real norms
(length, tone, hashtag conventions, whether emoji fit). Include a hook, not just
a description, for each one, and leave room for the article link to be appended
separately. Vary the angle and phrasing across platforms — don't just re-tone the
same sentence six times.

Return ONLY valid JSON in this exact shape, no preamble, no markdown fences:
{"X": "...", "Threads": "...", "LinkedIn": "...", "Alignable": "...",
 "YouTube description": "...", "TikTok": "..."}"""


def generate_all_captions(article_title: str, article_summary: str) -> dict:
    user = f"Article title: {article_title}\nArticle summary: {article_summary}"
    raw = call_llm(CAPTION_SYSTEM_PROMPT, user, max_tokens=1200)
    return json.loads(_extract_json(raw))


IMAGE_PROMPT_SYSTEM = """Given a Substack article, propose 4 distinct image concepts
that could illustrate it as a header image. Each should be visually specific enough
to hand directly to an image generator. Avoid text-in-image (renders poorly).
Return ONLY valid JSON: {"prompts": ["...", "...", "...", "..."]}"""


def generate_image_prompt_options(article_title: str, article_summary: str) -> list[str]:
    user = f"Title: {article_title}\nSummary: {article_summary}"
    raw = call_llm(IMAGE_PROMPT_SYSTEM, user, max_tokens=800)
    return json.loads(_extract_json(raw))["prompts"]
