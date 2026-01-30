import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from cerebras.cloud.sdk import Cerebras

logger = logging.getLogger(__name__)


CEREBRAS_API_KEY_ENV = "CEREBRAS_API_KEY"
DEFAULT_MODEL = "llama-3.3-70b"


class CerebrasConfigError(Exception):
    """Raised when Cerebras is not properly configured (e.g. missing API key)."""


class CerebrasAPIError(Exception):
    """Raised for generic upstream API or SDK errors."""


class CerebrasResponseError(CerebrasAPIError):
    """Raised when Cerebras returns a malformed or unexpected response."""


@dataclass
class CerebrasStep:
    step_number: int
    description: str
    latex: str


@dataclass
class CerebrasFinalAnswer:
    latex: str
    explanation: str


class CerebrasTextSolver:
    """
    Service responsible for calling Cerebras Cloud to solve text-based
    (word) math problems and returning a strictly structured JSON payload.

    This is intentionally isolated from the SymPy-based math engine so it
    can be replaced or disabled without touching the core solver.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        self.api_key = api_key or os.environ.get(CEREBRAS_API_KEY_ENV)
        self.model = model
        self._client: Optional[Cerebras] = None

        # Validate at startup but do not crash the whole app; we fail lazily
        # with a clear error when the endpoint is actually called.
        if not self.api_key:
            logger.error(
                "CerebrasTextSolver initialized without %s. "
                "Text AI solving will be unavailable until it is set.",
                CEREBRAS_API_KEY_ENV,
            )
        else:
            try:
                self._client = Cerebras(api_key=self.api_key)
            except Exception as exc:
                # Misconfiguration (e.g. invalid key format)
                logger.error("Failed to initialize Cerebras client: %s", exc)
                self._client = None

    # ------------------------------------------------------------------
    # Prompt construction and parsing helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, problem_text: str, is_retry: bool = False) -> str:
        """
        Build a detailed instruction prompt that forces JSON-only output
        in the exact schema required by the frontend.
        """
        base_instructions = (
            "You are an advanced mathematics tutor similar to Symbolab. "
            "Your job is to solve text-based word problems with complete, "
            "pedagogical, step-by-step explanations.\n\n"
            "Problem:\n"
            f"{problem_text}\n\n"
            "You MUST respond with JSON ONLY, with no markdown, no code fences, "
            "no explanations outside JSON, and no surrounding text. "
            "The JSON must match this schema exactly:\n\n"
            "{\n"
            '  \"problem\": \"...\",                // The problem restated clearly\n'
            '  \"interpretation\": \"...\",         // How you interpret the task in plain language\n'
            '  \"steps\": [\n'
            "    {\n"
            '      \"step_number\": 1,             // Integer step index starting from 1\n'
            '      \"description\": \"...\",       // Explanation of what happens in this step\n'
            '      \"latex\": \"...\"              // Core math for this step in LaTeX (no $)\n'
            "    }\n"
            "  ],\n"
            "  \"final_answer\": {\n"
            '    \"latex\": \"...\",               // Final answer in LaTeX only (no words)\n'
            '    \"explanation\": \"...\"          // Short verbal explanation of the final answer\n'
            "  }\n"
            "}\n\n"
            "Detailed behavior requirements:\n"
            "- Use low temperature reasoning: be deterministic and rigorous.\n"
            "- Identify variables and what is being solved for.\n"
            "- Show all important algebraic or arithmetic steps; do NOT skip directly to the answer.\n"
            "- Make steps similar in detail level to Symbolab solutions.\n"
            "- Use valid LaTeX for all mathematical expressions. Prefer exact fractions over decimals when appropriate.\n"
            "- Do NOT include any markdown, backticks, or commentary outside the JSON object.\n"
        )

        if is_retry:
            retry_suffix = (
                "\nIMPORTANT: Your previous response was invalid because it was not valid JSON "
                "or did not match the required schema. This time you MUST return a single valid "
                "JSON object only, using double quotes for all keys and string values, with no "
                "extra text before or after the JSON."
            )
            return base_instructions + retry_suffix

        return base_instructions

    def _extract_text_from_completion(self, completion: Any) -> str:
        """
        Extract the raw text content from the Cerebras chat completion.

        Cerebras is OpenAI-compatible, so we expect:
        completion.choices[0].message.content
        """
        try:
            choice = completion.choices[0]
            message = getattr(choice, "message", None) or choice["message"]
            text = getattr(message, "content", None) or message["content"]
            if isinstance(text, list):
                # Some OpenAI-compatible clients can return a list of content parts.
                text = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in text)
            return str(text)
        except Exception as exc:
            logger.error("Failed to extract text from Cerebras completion: %s", exc)
            raise CerebrasResponseError("Cerebras returned an unexpected completion format.") from exc

    def _parse_and_validate_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse the JSON text returned by the model and validate its structure.
        """
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("Cerebras returned non-JSON text: %s", raw_text[:200])
            raise CerebrasResponseError("Cerebras response was not valid JSON.") from exc

        if not isinstance(data, dict):
            raise CerebrasResponseError("Cerebras JSON root must be an object.")

        required_top = ["problem", "interpretation", "steps", "final_answer"]
        for key in required_top:
            if key not in data:
                raise CerebrasResponseError(f"Cerebras JSON missing required field: {key}")

        steps = data.get("steps")
        final_answer = data.get("final_answer")

        if not isinstance(steps, list):
            raise CerebrasResponseError("Cerebras JSON 'steps' must be a list.")
        if not isinstance(final_answer, dict):
            raise CerebrasResponseError("Cerebras JSON 'final_answer' must be an object.")

        normalized_steps: List[Dict[str, Any]] = []
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                logger.warning("Skipping non-object step at index %s", idx)
                continue
            step_num = step.get("step_number") or (idx + 1)
            normalized_steps.append(
                {
                    "step_number": int(step_num),
                    "description": str(step.get("description", "")),
                    "latex": str(step.get("latex", "")),
                }
            )

        data["steps"] = normalized_steps
        data["final_answer"] = {
            "latex": str(final_answer.get("latex", "")),
            "explanation": str(final_answer.get("explanation", "")),
        }

        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve_text_problem(self, text: str) -> Dict[str, Any]:
        """
        Execute a Cerebras chat completion to solve the given word problem.

        Returns data in the exact schema requested in the project spec.
        """
        if not self.api_key:
            raise CerebrasConfigError(
                "Cerebras API key is not configured. Please set the "
                f"{CEREBRAS_API_KEY_ENV} environment variable on the server."
            )
        if self._client is None:
            raise CerebrasConfigError("Failed to initialize Cerebras client. Check your API key configuration.")

        if not text or not text.strip():
            raise ValueError("Problem text must not be empty.")

        # We allow one retry if the model does not emit valid JSON.
        last_error: Optional[Exception] = None
        for attempt in range(2):
            is_retry = attempt == 1
            prompt = self._build_prompt(text.strip(), is_retry=is_retry)

            try:
                completion = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.2,
                    stream=False,
                )
            except Exception as exc:
                logger.error("Error while calling Cerebras chat completion: %s", exc)
                raise CerebrasAPIError("Failed to contact Cerebras API.") from exc

            raw_text = self._extract_text_from_completion(completion)

            try:
                return self._parse_and_validate_json(raw_text)
            except CerebrasResponseError as exc:
                last_error = exc
                logger.warning("Cerebras JSON parsing error on attempt %s: %s", attempt + 1, exc)
                # If this was the first attempt, retry once with stricter instructions.
                continue

        # If we get here, both attempts failed to produce valid JSON.
        raise CerebrasResponseError(
            "AI response could not be parsed as valid structured JSON. "
            "Please try again later."
        ) from last_error


# Module-level singleton used by Django views.
cerebras_text_solver = CerebrasTextSolver()

