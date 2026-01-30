import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from cerebras.cloud.sdk import Cerebras

logger = logging.getLogger(__name__)


CEREBRAS_API_KEY_ENV = "CEREBRAS_API_KEY"
EXPLANATION_MODEL = "llama-3.3-70b"


class AIExplanationConfigError(Exception):
    """Raised when AI explanation service is misconfigured (e.g. missing API key)."""


class AIExplanationAPIError(Exception):
    """Raised for upstream Cerebras errors while generating explanations."""


class AIExplanationResponseError(AIExplanationAPIError):
    """Raised when Cerebras returns malformed or unexpected explanation JSON."""


@dataclass
class AIExplanationStep:
    step_number: int
    explanation: str
    latex: str


@dataclass
class AIExplanationResult:
    steps: List[AIExplanationStep]
    final_answer_latex: str


class AIExplanationService:
    """
    Small wrapper around Cerebras for generating pedagogical explanations.

    IMPORTANT: This service does NOT decide whether the AI result is correct.
    The math engine remains the source of truth. Callers must validate the
    returned `final_answer_latex` against the canonical result before using it.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = EXPLANATION_MODEL) -> None:
        self.api_key = api_key or os.environ.get(CEREBRAS_API_KEY_ENV)
        self.model = model
        self._client: Optional[Cerebras] = None

        if not self.api_key:
            logger.info(
                "AIExplanationService initialized without %s. "
                "AI explanations will be disabled.",
                CEREBRAS_API_KEY_ENV,
            )
        else:
            try:
                self._client = Cerebras(api_key=self.api_key)
            except Exception as exc:
                logger.error("Failed to initialize Cerebras client for explanations: %s", exc)
                self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self._client is not None)

    # ------------------------------------------------------------------
    # Prompt construction and parsing
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        problem_text: str,
        operation: str,
        canonical_result_latex: str,
        engine_steps: Optional[List[Dict[str, Any]]] = None,
        previous_ai_final_latex: Optional[str] = None,
    ) -> str:
        """
        Build an instruction prompt that makes it explicit that:
        - The solution is already known and must NOT be changed
        - AI's role is purely explanatory
        """
        base = (
            "You are an advanced mathematics tutor similar to Symbolab.\n\n"
            "You are given a math problem and its CORRECT final result computed by a "
            "deterministic math engine. Your job is ONLY to explain step-by-step how one "
            "can arrive at this result. You MUST NOT change the result.\n\n"
            f"Problem (as typed by the user):\n{problem_text}\n\n"
            f"Operation type: {operation}\n"
            f"Correct final result (LaTeX, authoritative): {canonical_result_latex}\n\n"
        )

        if engine_steps:
            base += "The math engine also produced these internal steps (they are correct but may be terse):\n"
            for idx, step in enumerate(engine_steps, start=1):
                # Steps from engine may already be in {title, latex, explanation} format
                title = str(step.get("title", f"Step {idx}"))
                latex = str(step.get("latex", ""))
                explanation = str(step.get("explanation", ""))
                base += f"- {title}: {latex} | {explanation}\n"
            base += "\nUse these steps as a reference but you may reorganize them for clarity.\n\n"

        if previous_ai_final_latex is not None:
            base += (
                "IMPORTANT: Your previous explanation produced an incorrect final result:\n"
                f"- Your incorrect final result: {previous_ai_final_latex}\n"
                f"- Correct final result (must use this): {canonical_result_latex}\n\n"
                "You MUST now re-generate the explanation so that the final answer EXACTLY "
                "matches the correct result. Do NOT introduce any alternative answers.\n\n"
            )

        base += (
            "Output requirements (VERY IMPORTANT):\n"
            "- You must NOT recompute the result; treat the provided final result as absolute truth.\n"
            "- Explain the reasoning step-by-step, showing key algebraic or calculus operations.\n"
            "- Emulate Symbolab-style pedagogy: no large jumps; show intermediate transformations.\n"
            "- Prefer exact math such as fractions and radicals over decimals.\n"
            "- Return JSON ONLY, with NO markdown, NO code fences, and NO text outside JSON.\n\n"
            "Your JSON must have this exact structure:\n"
            "{\n"
            '  \"steps\": [\n'
            "    {\n"
            '      \"step_number\": 1,\n'
            '      \"explanation\": \"...\",   // human-readable explanation of this step\n'
            '      \"latex\": \"...\"          // LaTeX for the main mathematical content of the step\n'
            "    }\n"
            "  ],\n"
            "  \"final_answer\": {\n"
            '    \"latex\": \"...\"            // MUST be mathematically equivalent to the given correct result\n'
            "  }\n"
            "}\n\n"
            "STRICT RULES:\n"
            "- Do NOT change the numerical or symbolic value of the final answer.\n"
            "- Do NOT propose multiple different final answers.\n"
            "- Use valid LaTeX without $ or \\[ \\] delimiters inside the strings.\n"
            "- Use double quotes for all JSON keys and string values.\n"
        )

        return base

    def _extract_text_from_completion(self, completion: Any) -> str:
        """
        Extract the raw text content from the Cerebras chat completion response.
        """
        try:
            choice = completion.choices[0]
            message = getattr(choice, "message", None) or choice["message"]
            content = getattr(message, "content", None) or message["content"]
            if isinstance(content, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                )
            else:
                text = str(content)
            return text
        except Exception as exc:
            logger.error("Failed to extract explanation text from Cerebras completion: %s", exc)
            raise AIExplanationResponseError("Unexpected explanation completion format.") from exc

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse and validate the JSON explanation structure.
        """
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("Explanation JSON decode failed. Raw: %s", raw_text[:200])
            raise AIExplanationResponseError("Explanation response was not valid JSON.") from exc

        if not isinstance(data, dict):
            raise AIExplanationResponseError("Explanation JSON root must be an object.")

        if "steps" not in data or "final_answer" not in data:
            raise AIExplanationResponseError("Explanation JSON missing 'steps' or 'final_answer'.")

        steps = data.get("steps")
        final = data.get("final_answer")

        if not isinstance(steps, list):
            raise AIExplanationResponseError("Explanation JSON 'steps' must be a list.")
        if not isinstance(final, dict):
            raise AIExplanationResponseError("Explanation JSON 'final_answer' must be an object.")

        normalized_steps: List[AIExplanationStep] = []
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                logger.warning("Skipping non-object explanation step at index %s", idx)
                continue
            step_number = int(step.get("step_number", idx))
            explanation = str(step.get("explanation", "")).strip()
            latex = str(step.get("latex", "")).strip()
            normalized_steps.append(
                AIExplanationStep(
                    step_number=step_number,
                    explanation=explanation,
                    latex=latex,
                )
            )

        final_latex = str(final.get("latex", "")).strip()

        return {
            "steps": normalized_steps,
            "final_answer_latex": final_latex,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_explanation(
        self,
        *,
        problem_text: str,
        operation: str,
        canonical_result_latex: str,
        engine_steps: Optional[List[Dict[str, Any]]] = None,
        previous_ai_final_latex: Optional[str] = None,
    ) -> AIExplanationResult:
        """
        Generate a single explanation attempt from Cerebras.

        This does NOT perform correctness verification; callers must do that.
        """
        if not self.api_key or self._client is None:
            raise AIExplanationConfigError(
                f"AI explanation service is not configured. Set {CEREBRAS_API_KEY_ENV} "
                "to enable AI-generated explanations."
            )

        prompt = self._build_prompt(
            problem_text=problem_text,
            operation=operation,
            canonical_result_latex=canonical_result_latex,
            engine_steps=engine_steps,
            previous_ai_final_latex=previous_ai_final_latex,
        )

        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=False,
            )
        except Exception as exc:
            logger.error("Error calling Cerebras for explanation: %s", exc)
            raise AIExplanationAPIError("Failed to contact Cerebras for explanation.") from exc

        raw_text = self._extract_text_from_completion(completion)
        parsed = self._parse_json(raw_text)

        return AIExplanationResult(
            steps=parsed["steps"],
            final_answer_latex=parsed["final_answer_latex"],
        )


# Module-level singleton
ai_explainer = AIExplanationService()

