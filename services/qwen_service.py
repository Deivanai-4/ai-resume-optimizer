"""
Qwen Service — Centralized Hugging Face / Together AI Qwen Client
=================================================================
Single source of truth for all Qwen API calls in the application.

Usage (inside Flask app context only):
    from services.qwen_service import call_qwen, parse_qwen_json

    raw   = call_qwen("Your prompt here", max_tokens=1024)
    data  = parse_qwen_json(raw)           # dict or None

Security rules:
  - Token is NEVER logged, printed, or returned in responses.
  - Errors are logged with sanitised messages only.
  - Token is loaded exclusively from Flask app config (which reads .env).
"""
import json
import logging
import re
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_config():
    """
    Pull Qwen connection settings from Flask app config.
    Supports both QWEN_* and HF_* env-var naming conventions.
    Returns (token, model, provider) or raises RuntimeError.
    """
    from flask import current_app

    cfg = current_app.config

    # Token — accept either QWEN_TOKEN or HF_TOKEN
    token = (cfg.get("QWEN_TOKEN") or cfg.get("HF_TOKEN") or "").strip()

    # Model — accept either QWEN_MODEL or HF_MODEL, fallback to known good model
    model = (
        cfg.get("QWEN_MODEL")
        or cfg.get("HF_MODEL")
        or "Qwen/Qwen2.5-7B-Instruct"
    ).strip()

    # Provider — accept either QWEN_PROVIDER or HF_PROVIDER, fallback to together
    provider = (
        cfg.get("QWEN_PROVIDER")
        or cfg.get("HF_PROVIDER")
        or "together"
    ).strip()

    return token, model, provider


def _make_client(token: str, provider: str):
    """
    Build an InferenceClient with an explicit provider.
    Explicit provider= bypasses the auto-router (which rejects non-hf_ tokens).
    """
    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is not installed. "
            "Run: pip install 'huggingface_hub>=0.21.0'"
        ) from exc

    if not provider or provider.lower() in ('auto', 'none', 'default'):
        return InferenceClient(token=token, timeout=45)
    return InferenceClient(token=token, provider=provider, timeout=45)


def _strip_markdown_fences(text: str) -> str:
    """
    Remove leading/trailing markdown code fences such as:
        ```json ... ```   or   ``` ... ```
    so that the remainder can be parsed as plain JSON.
    """
    if not text:
        return text
    # Remove ```json or ``` at the start
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text.strip(), flags=re.IGNORECASE)
    # Remove trailing ```
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def _classify_error(exc: Exception) -> tuple[str, bool]:
    """
    Classify an exception into (message, should_retry).
    Returns a safe message that NEVER includes the token value.
    """
    err = str(exc)

    if "401" in err or "Unauthorized" in err or "Invalid username or password" in err:
        return "HF 401 Unauthorized — check HF_TOKEN in .env", False

    if "429" in err or "Rate limit" in err.lower():
        return "HF 429 Rate limited — backing off", True

    if any(code in err for code in ("500", "502", "503", "504")):
        return "HF 5xx server error — backing off", True

    if "not supported by provider" in err.lower():
        return (
            "Model not supported by the configured provider — "
            "check QWEN_MODEL / QWEN_PROVIDER in .env",
            False,
        )

    if "Cannot select auto-router" in err:
        return (
            "Auto-router rejected — ensure QWEN_PROVIDER is set explicitly in .env",
            False,
        )

    if "timeout" in err.lower():
        return "Request timed out", True

    return f"Unexpected error: {type(exc).__name__}", False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_qwen(
    prompt: str,
    max_tokens: int = 1500,
    retries: int = 2,
    temperature: float = 0.3,
) -> str | None:
    """
    Send a prompt to Qwen and return the raw text response.

    Args:
        prompt:      The user prompt to send.
        max_tokens:  Maximum tokens to generate (default 1500).
        retries:     Number of retry attempts on transient errors (default 2).
        temperature: Sampling temperature (lower = more deterministic JSON).

    Returns:
        The model's text response, or None if all attempts fail.

    Notes:
        - Must be called within a Flask application context.
        - Token is never written to logs.
    """
    token, model, provider = _get_config()

    if not token:
        logger.warning(
            "QWEN: No token configured (QWEN_TOKEN / HF_TOKEN is empty). "
            "AI calls will fall back to smart stubs."
        )
        return None

    try:
        client = _make_client(token, provider)
    except RuntimeError as exc:
        logger.error(f"QWEN: Client init failed — {exc}")
        return None

    logger.debug(f"QWEN: Calling model={model} provider={provider} max_tokens={max_tokens}")

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                logger.warning(f"QWEN: Empty response on attempt {attempt}/{retries}")
                last_error = "empty response"
                continue

            logger.debug(f"QWEN: Received {len(content)} chars on attempt {attempt}")
            return content

        except Exception as exc:
            msg, should_retry = _classify_error(exc)
            logger.error(f"QWEN attempt {attempt}/{retries}: {msg}")
            last_error = msg

            if not should_retry:
                break

            if attempt < retries:
                wait = 2 ** (attempt - 1)      # 1s, 2s, 4s …
                logger.info(f"QWEN: Retrying in {wait}s …")
                time.sleep(wait)

    logger.error(f"QWEN: All {retries} attempt(s) failed. Last error: {last_error}")
    return None


def parse_qwen_json(text: str | None) -> dict | None:
    """
    Clean and parse a Qwen response that should contain a JSON object.

    Handles:
      - Leading/trailing markdown fences (```json … ```)
      - Text before/after the JSON block
      - Invalid JSON (returns None safely)

    Returns:
        Parsed dict, or None if parsing fails.
    """
    if not text:
        return None

    cleaned = _strip_markdown_fences(text)

    # Extract the first {...} block even if there is surrounding text
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0 or end <= start:
        logger.warning("QWEN: No JSON object found in response")
        return None

    json_str = cleaned[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning(f"QWEN: JSON parse error — {exc}")
        return None


def parse_qwen_json_array(text: str | None) -> list | None:
    """
    Clean and parse a Qwen response that should contain a JSON array.

    Returns:
        Parsed list, or None if parsing fails.
    """
    if not text:
        return None

    cleaned = _strip_markdown_fences(text)
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start < 0 or end <= start:
        return None

    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        return None

def extract_profile_from_resume(text: str) -> dict | None:
    """
    Extracts structured profile data (Experience, Education, Projects, Skills) from raw resume text using Qwen.
    """
    prompt = f"""
You are an expert resume parser. I will provide you with the raw text extracted from a resume.
Please extract the structured information and return it STRICTLY as a JSON object matching the following schema.
Do not include any explanation or markdown formatting, just the raw JSON object.

Schema:
{{
  "basic": {{
    "full_name": "...",
    "email": "...",
    "phone": "...",
    "location": "...",
    "career_objective": "..."
  }},
  "skills": [
    {{ "skill_name": "...", "category": "Programming/Framework/Database/Cloud/Other", "proficiency": "Intermediate", "proficiency_percent": 75 }}
  ],
  "education": [
    {{
      "degree": "...",
      "field_of_study": "...",
      "institution": "...",
      "start_year": "YYYY",
      "end_year": "YYYY",
      "cgpa": "...",
      "description": "..."
    }}
  ],
  "experience": [
    {{
      "job_title": "...",
      "company_name": "...",
      "location": "...",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "description": "..."
    }}
  ],
  "projects": [
    {{
      "title": "...",
      "description": "...",
      "technologies": "...",
      "github_url": "...",
      "live_url": "..."
    }}
  ],
  "certifications": [
    {{
      "cert_name": "...",
      "issuing_org": "...",
      "issue_date": "YYYY-MM"
    }}
  ]
}}

Raw Resume Text:
{text}
"""
    raw_response = call_qwen(prompt, max_tokens=2500, temperature=0.1)
    if not raw_response:
        with open("qwen_debug.log", "a") as f:
            f.write("call_qwen returned None\n")
        return None
        
    parsed = parse_qwen_json(raw_response)
    if not parsed:
        with open("qwen_debug.log", "a") as f:
            f.write(f"Failed to parse JSON. Raw response was:\n{raw_response}\n\n")
    return parsed
