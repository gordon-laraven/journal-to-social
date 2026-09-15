"""Provider-agnostic image generation."""
import os
import base64
import requests


def _openai_image(prompt: str) -> bytes:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024")
    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)


def _stability_image(prompt: str) -> bytes:
    api_key = os.environ["STABILITY_API_KEY"]
    resp = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={"authorization": f"Bearer {api_key}", "accept": "image/*"},
        files={"none": ""},
        data={"prompt": prompt, "output_format": "png"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def _gemini_image(prompt: str) -> bytes:
    api_key = os.environ["GEMINI_API_KEY"]
    url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    resp = requests.post(url, json={"instances": [{"prompt": prompt}]}, headers=headers, timeout=60)
    resp.raise_for_status()
    b64 = resp.json()["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(b64)


def generate_image(prompt: str) -> bytes:
    """Returns raw image bytes (PNG)."""
    provider = os.getenv("IMAGE_PROVIDER", "openai")
    if provider == "stability":
        return _stability_image(prompt)
    if provider == "gemini":
        return _gemini_image(prompt)
    return _openai_image(prompt)
