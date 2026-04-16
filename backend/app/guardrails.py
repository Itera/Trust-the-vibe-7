"""Security layer: validate LLM inputs and outputs against Itera's core values.

Two passes are applied around every LLM call:

Input guard  (validate_input)
    Synchronous, rules-based.  Catches prompt-injection attempts and clearly
    harmful content before any tokens are sent upstream.

Output guard (validate_output)
    Async, LLM-based.  Asks the model to review the generated content as a
    brand-safety reviewer for Itera.  If the review call itself fails
    (network error, quota, etc.) the content is allowed through (fail-open)
    so a transient infra hiccup never breaks the service entirely; the
    failure is logged for later inspection.

Itera's core values: Trust · Transparency · Entrepreneurship · Diversity
"""
from __future__ import annotations

import json
import logging
import re

from .config import Settings
from .llm import chat_completion

logger = logging.getLogger("humotivatoren.guardrails")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class GuardrailViolation(ValueError):
    """Raised when input or output fails the guardrail check."""


# ---------------------------------------------------------------------------
# Itera brand-safety context (shared between input and output prompts)
# ---------------------------------------------------------------------------

_ITERA_VALUES_CONTEXT = (
    "Itera is a Norwegian IT-consulting company whose core values are: "
    "Trust, Transparency, Entrepreneurship, and Diversity. "
    "Content produced in Itera's name must be workplace-safe, inclusive, "
    "and never embarrassing if shared externally."
)

# ---------------------------------------------------------------------------
# Input guard — rules-based
# ---------------------------------------------------------------------------

# Patterns that indicate prompt-injection or jailbreak attempts.
_INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+instructions",
    r"disregard\s+(your\s+)?(instructions|rules|guidelines|constraints|system\s+prompt)",
    r"override\s+(your\s+)?(instructions|rules|guidelines|system\s+prompt)",
    r"you\s+are\s+now\s+(?!the\s+humotivatoren)",
    r"act\s+as\s+(?!the\s+humotivatoren|a\s+(consultant|stoic|nordmann|gremlin))",
    r"pretend\s+(you\s+are|to\s+be)\b",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"\[\s*system\s*\]",            # fake system-prompt injection in text
    r"<\s*(script|iframe|object)\b", # HTML/JS injection
]

# Patterns for content that would violate Itera's values or cause PR issues.
_HARMFUL_PATTERNS: list[str] = [
    r"\b(nazi|fascis[mt]|neonazi)\b",
    r"\b(hate\s+speech|hate\s+crime)\b",
    r"\b(suicide|self[- ]harm|self[- ]mutilation)\b",
    r"\b(bomb|terrorism?|terrorist|attack\s+plan)\b",
    r"\bchild\s+(abuse|exploitation|pornography)\b",
    r"\b(racial|ethnic)\s+slur",
    r"\bslur\b",
    # Violence — scoped to "how to" phrasing to avoid blocking slang ("killing it", "murder this deadline")
    r"\bhow\s+to\s+(kill|murder|harm|hurt|assault|poison|stab|shoot|strangle|torture)\b",
    r"\bget\s+away\s+with\s+(murder|killing|assault|a\s+crime)\b",
    r"\b(murder|kill|assault|rape|torture)\s+(someone|a\s+person|people|him|her|them)\b",
]

_COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]
_COMPILED_HARMFUL = [re.compile(p, re.IGNORECASE) for p in _HARMFUL_PATTERNS]


def validate_input(task: str) -> None:
    """Check the user-supplied task string before forwarding to the LLM.

    Raises GuardrailViolation with a user-facing message on any hit.
    The raw task is truncated in logs to avoid leaking PII.
    """
    for pattern in _COMPILED_INJECTION:
        if pattern.search(task):
            logger.warning(
                "Prompt injection attempt detected in task input: %r", task[:120]
            )
            raise GuardrailViolation(
                "Hmm, that looks a bit off — try describing your task in plain terms and we'll get the vibes going."
            )

    for pattern in _COMPILED_HARMFUL:
        if pattern.search(task):
            logger.warning(
                "Harmful content detected in task input: %r", task[:120]
            )
            raise GuardrailViolation(
                "That one's a bit much for us — keep it workplace-friendly and we'll make the magic happen."
            )


# ---------------------------------------------------------------------------
# Output guard — LLM-based brand safety review
# ---------------------------------------------------------------------------

_OUTPUT_REVIEW_SYSTEM = (
    "You are a brand-safety reviewer for Itera. "
    + _ITERA_VALUES_CONTEXT
    + "\n\n"
    "Review the JSON content below and decide whether it is safe to show to users.\n"
    "Flag the content as unsafe if it:\n"
    "  • Undermines Trust or Transparency (e.g. spreads misinformation presented as real)\n"
    "  • Discourages Entrepreneurship or innovation\n"
    "  • Violates Diversity (e.g. stereotypes, discrimination, body-shaming)\n"
    "  • Is politically controversial, religiously offensive, or nationalistic\n"
    "  • Could embarrass Itera if shared externally or quoted in the press\n"
    "  • Contains mean-spirited, punching-down, or harmful humour\n\n"
    'Respond ONLY with valid JSON: {"safe": true} or '
    '{"safe": false, "reason": "<one concise sentence>"}'
)


async def validate_output(settings: Settings, generated_json: str) -> None:
    """Review the LLM-generated JSON content for brand safety.

    Raises GuardrailViolation if the content is deemed problematic.
    On any error from the review call itself, logs a warning and allows
    the content through (fail-open) to preserve service availability.
    """
    messages = [
        {"role": "system", "content": _OUTPUT_REVIEW_SYSTEM},
        {
            "role": "user",
            "content": f"Content to review:\n{generated_json[:4000]}",
        },
    ]

    try:
        data = await chat_completion(
            settings,
            messages,
            temperature=0.0,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        raw_content = (
            (data.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "{}")
        )
        result = json.loads(raw_content)
    except Exception as exc:
        logger.warning(
            "Output guardrail review call failed (content allowed through): %s", exc
        )
        return

    if not result.get("safe", True):
        logger.warning("Output guardrail blocked response: %s", result.get("reason"))
        raise GuardrailViolation(
            "Oof — something in that one didn't vibe with our values check. "
            "Try a different take on your task and give it another shot."
        )


# ---------------------------------------------------------------------------
# Input values guard — LLM-based check on the task text itself
# ---------------------------------------------------------------------------

_TASK_VALUES_REVIEW_SYSTEM = (
    "You are reviewing a task description submitted to HuMotivatoren, "
    "a fun internal motivation tool at Itera (a Norwegian IT company).\n\n"
    "Default to ok=true for genuine work tasks, hobbies, creative projects, "
    "mundane chores, and playful ideas.\n\n"
    "Flag the task as NOT ok (ok=false) if it:\n"
    "  • Asks how to commit, plan, or get away with a crime or act of violence — "
    "even if phrased as a joke, TV show reference, or hypothetical.\n"
    "  • Describes clearly harmful or illegal activity (violence, abuse, fraud, etc.)\n"
    "  • Is sexually explicit or graphic\n"
    "  • Targets or demeans any group of people\n"
    "  • Would embarrass Itera if the task text were shared publicly\n\n"
    "When in doubt about intent, flag it.\n"
    'Respond ONLY with valid JSON: {"ok": true} or {"ok": false}'
)


async def validate_task_values(settings: Settings, task: str) -> None:
    """LLM-based check that the task description is appropriate for Itera's values.

    This catches nuanced violations that regex alone cannot detect.
    Fails open on infra errors so a broken review call never blocks usage.
    """
    messages = [
        {"role": "system", "content": _TASK_VALUES_REVIEW_SYSTEM},
        {"role": "user", "content": f"Task: {task[:500]}"},
    ]

    try:
        data = await chat_completion(
            settings,
            messages,
            temperature=0.0,
            max_tokens=20,
            response_format={"type": "json_object"},
        )
        raw_content = (
            (data.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "{}")
        )
        result = json.loads(raw_content)
    except Exception as exc:
        logger.warning(
            "Task values review call failed (task allowed through): %s", exc
        )
        return

    if not result.get("ok", True):
        logger.warning("Task values guardrail blocked input: %r", task[:120])
        raise GuardrailViolation(
            "That one's not really in the spirit of things — "
            "try something a bit more wholesome and we'll sort you out."
        )
