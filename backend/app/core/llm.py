import logging
import time

from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)

MODEL = "llama3-70b-8192"
MAX_RETRIES = 3


def call_llm(
    system_prompt: str,
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Call the Groq LLM with retry + exponential backoff.

    Args:
        system_prompt: Instruction context for the model.
        user_message:  The user's current input.
        history:       Optional prior turns as [{"role": ..., "content": ...}].

    Returns:
        The model's text response.

    Raises:
        RuntimeError: After MAX_RETRIES consecutive failures.
    """
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.3,
            )
            usage = response.usage
            logger.info(
                "Groq [%s] prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                MODEL,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )
            return response.choices[0].message.content  # type: ignore[return-value]

        except Exception as exc:
            last_exc = exc
            delay = 2**attempt  # 1 s, 2 s, 4 s
            logger.warning(
                "LLM attempt %d/%d failed: %s. Retrying in %ds.",
                attempt + 1,
                MAX_RETRIES,
                exc,
                delay,
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(delay)

    raise RuntimeError(
        f"LLM call failed after {MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc
