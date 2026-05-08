import os
import logging
from services.hf_client import query_hf_with_retry, HFAPIError
from services.output_parser import parse_text_generation, parse_judge_output
from prompts import get_judge_prompt

logger = logging.getLogger(__name__)


async def evaluate_judge(original_text: str, analysis: dict) -> dict:
    """
    Call the judge LLM to evaluate the analysis for the given original text.
    Returns a dict: {score: int, explanation: str}
    """
    try:
        model = os.getenv("JUDGE_MODEL", "google/flan-t5-base")

        prompt = get_judge_prompt(original_text, analysis)

        response = await query_hf_with_retry(
            model,
            {"inputs": prompt}
        )

        # Parse text generation output from HF response
        generated = parse_text_generation(response, prompt)

        if logger:
            logger.info(f"Judge raw output: {generated}")

        parsed = parse_judge_output(generated)
        # Ensure types
        parsed["score"] = int(parsed.get("score", 50))
        parsed["explanation"] = str(parsed.get("explanation", ""))

        return parsed

    except Exception as e:
        # If the model is not supported by HF Inference, fall back to a simple
        # heuristic judge to avoid breaking the analysis flow.
        logger.error(f"Judge evaluation failed: {str(e)}")
        if isinstance(e, HFAPIError) and "Model not supported" in str(e):
            try:
                return heuristic_judge(original_text, analysis)
            except Exception:
                return {"score": 50, "explanation": "Judge unavailable; fallback failed"}

        return {"score": 50, "explanation": "Judge evaluation failed"}


def heuristic_judge(original_text: str, analysis: dict) -> dict:
    """
    Lightweight fallback judge: simple consistency checks between sentiment
    and summary, and basic content sanity checks. Returns score 0-100.
    """
    try:
        summary = analysis.get("summary", "") or ""
        sentiment_field = analysis.get("sentiment", "").lower()
        # extract first token as label if like 'positive (0.95)'
        sentiment_label = sentiment_field.split()[0] if sentiment_field else "neutral"

        score = 75
        explanation = "Heuristic check: basic consistency checks passed."

        # if summary contains profanity or malformed output, penalize heavily
        bad_tokens = ["chutiya", "nigger", "fuck", "sh*t"]
        if any(b in summary.lower() for b in bad_tokens):
            return {"score": 10, "explanation": "Generated summary contains offensive or invalid text."}

        # crude sentiment agreement: look for negative words in summary
        negative_words = ["not", "no", "never", "bad", "angry", "opposed", "critic"]
        contains_negative = any(w in summary.lower() for w in negative_words)

        if sentiment_label in ["positive", "pos"] and contains_negative:
            score = 40
            explanation = "Sentiment label is positive but summary contains negative cues."
        elif sentiment_label in ["negative", "neg"] and not contains_negative:
            score = 40
            explanation = "Sentiment label is negative but summary lacks negative cues."
        else:
            score = 85
            explanation = "Analysis appears consistent on simple heuristics."

        return {"score": int(max(0, min(100, score))), "explanation": explanation}
    except Exception as ie:
        logger.error(f"Heuristic judge failed: {str(ie)}")
        return {"score": 50, "explanation": "Heuristic judge error"}
