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
        print("re /n \n\n",response)
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

        return {"score": 50, "explanation": "Judge evaluation failed"}

