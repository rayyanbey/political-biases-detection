import re
import json
from enum import Enum
from typing import Tuple, List, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class BiasLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class SentimentOutput(BaseModel):
    label: SentimentLabel
    score: float
    confidence: str  # "high", "medium", "low"

class BiasAnalysis(BaseModel):
    bias_level: BiasLevel
    score: float  # 1-5
    detected_phrases: List[str]
    explanation: str

def parse_sentiment_output(hf_response: Any) -> SentimentOutput:
    """
    Parse sentiment analysis response from distilbert model.
    HF returns: [{"label": "POSITIVE", "score": 0.95}, ...] or similar
    """
    try:
        if not hf_response or not isinstance(hf_response, list):
            logger.warning("Invalid sentiment response format, defaulting to NEUTRAL")
            return SentimentOutput(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                confidence="low"
            )
        
        result = hf_response[0]
        score = float(result.get("score", 0.5))
        label = result.get("label", "").upper().strip()
        
        # Normalize label
        label_map = {
            "POSITIVE": SentimentLabel.POSITIVE,
            "NEGATIVE": SentimentLabel.NEGATIVE,
            "NEUTRAL": SentimentLabel.NEUTRAL,
            "POS": SentimentLabel.POSITIVE,
            "NEG": SentimentLabel.NEGATIVE,
            "LABEL_1": SentimentLabel.POSITIVE,  # Alternative label format
            "LABEL_0": SentimentLabel.NEGATIVE,
        }
        
        normalized_label = label_map.get(label, SentimentLabel.NEUTRAL)
        
        # Determine confidence level
        if score >= 0.9:
            confidence = "high"
        elif score >= 0.7:
            confidence = "medium"
        else:
            confidence = "low"
        
        return SentimentOutput(
            label=normalized_label,
            score=score,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error parsing sentiment output: {str(e)}")
        return SentimentOutput(
            label=SentimentLabel.NEUTRAL,
            score=0.5,
            confidence="low"
        )

def parse_summarization_output(hf_response: Any) -> str:
    """
    Parse summarization response from BART model.
    HF returns: [{"summary_text": "..."}]
    """
    try:
        if not hf_response or not isinstance(hf_response, list):
            logger.warning("Invalid summarization response format")
            return "Summary generation failed."
        
        summary = hf_response[0].get("summary_text", "").strip()
        
        # Remove boilerplate patterns
        summary = re.sub(r'^\W*summary\W*:?\s*', '', summary, flags=re.IGNORECASE)
        summary = re.sub(r'^#+\s*', '', summary)  # Remove markdown headers
        summary = re.sub(r'\s+', ' ', summary)  # Normalize whitespace
        
        if not summary or len(summary.strip()) < 10:
            logger.warning("Generated summary too short, using fallback")
            return "Summary generation incomplete."
        
        # Truncate to reasonable length if too long
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        return summary
    
    except Exception as e:
        logger.error(f"Error parsing summarization output: {str(e)}")
        return "Summary generation failed."

def parse_text_generation(hf_response: Any, prompt: str = "") -> str:
    """
    Parse text generation response from FLAN-T5 model.
    HF returns: [{"generated_text": "full_text_including_prompt"}]
    """
    try:
        if not hf_response or not isinstance(hf_response, list):
            logger.warning("Invalid text generation response format")
            return ""
        
        generated_text = hf_response[0].get("generated_text", "").strip()
        
        # Remove prompt from output if it appears at the beginning
        if prompt and generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        # Clean up common artifacts
        generated_text = generated_text.strip()
        
        if not generated_text:
            logger.warning("Generated text is empty after cleanup")
            return ""
        
        return generated_text
    
    except Exception as e:
        logger.error(f"Error parsing text generation output: {str(e)}")
        return ""

def parse_bias_detection_response(model_output: str) -> BiasAnalysis:
    """
    Parse FLAN-T5 bias detection output into structured BiasAnalysis.
    Looks for patterns: "NONE", "LOW", "MEDIUM", "HIGH", and numeric scores 1-5.
    """
    try:
        output_lower = model_output.lower()
        
        # Pattern matching for bias levels
        bias_patterns = {
            r'\bhigh\b': (BiasLevel.HIGH, 5.0),
            r'\bmedium\b': (BiasLevel.MEDIUM, 3.0),
            r'\blow\b': (BiasLevel.LOW, 2.0),
            r'\bnone\b': (BiasLevel.NONE, 1.0),
            r'\bno\s+bias\b': (BiasLevel.NONE, 1.0),
        }
        
        bias_level = BiasLevel.MEDIUM
        score = 3.0
        
        for pattern, (level, value) in bias_patterns.items():
            if re.search(pattern, output_lower):
                bias_level = level
                score = value
                break
        
        # Try to extract numeric score if present
        score_matches = re.findall(r'(?:score|rate|severity|bias\s+level)[:\s]+([1-5])', output_lower)
        if score_matches:
            try:
                score = float(score_matches[0])
            except (ValueError, IndexError):
                pass
        
        # Extract quoted phrases (biased language)
        phrases = re.findall(r'"([^"]+)"', model_output)
        phrases = [p.strip() for p in phrases if len(p.strip()) > 3][:3]
        
        # Clean explanation: take first 2-3 sentences
        explanation = model_output.strip()
        explanation = re.sub(r'^\W*bias\W*:?\s*', '', explanation, flags=re.IGNORECASE)
        
        # Truncate to 200 chars max
        if len(explanation) > 200:
            explanation = explanation[:197] + "..."
        
        if not explanation:
            explanation = f"Detected {bias_level.value} bias (score: {int(score)}/5)"
        
        return BiasAnalysis(
            bias_level=bias_level,
            score=score,
            detected_phrases=phrases,
            explanation=explanation
        )
    
    except Exception as e:
        logger.error(f"Error parsing bias detection output: {str(e)}")
        return BiasAnalysis(
            bias_level=BiasLevel.MEDIUM,
            score=3.0,
            detected_phrases=[],
            explanation="Analysis inconclusive"
        )

def validate_output_quality(output: str, min_length: int = 10) -> Tuple[bool, str]:
    """
    Validate output meets quality threshold.
    Returns: (is_valid, reason)
    """
    if not output or len(output.strip()) < min_length:
        return False, "Output too short"
    
    lower_output = output.lower()
    if lower_output in ["error", "none", "unknown", "n/a", "failed", "error occurred"]:
        return False, "Invalid placeholder response"
    
    # Check for corrupted output patterns
    if output.count("@") > 5 or output.count("#") > 10 or output.count("$") > 3:
        return False, "Likely corrupted output"
    
    return True, "Valid"


def parse_judge_output(model_output: str) -> dict:
    """
    Parse judge LLM output and return a dict with keys: score (int 0-100),
    explanation (str). Attempts to parse strict JSON first, then falls back
    to regex extraction.
    """
    try:
        if not model_output or not isinstance(model_output, str):
            return {"score": 50, "explanation": "No judge output"}

        # Try to locate a JSON object in the output
        json_match = re.search(r"\{[\s\S]*\}", model_output)
        if json_match:
            try:
                payload = json.loads(json_match.group(0))
                score = int(payload.get("score", payload.get("score", 50)))
                explanation = str(payload.get("explanation", ""))
                score = max(0, min(100, score))
                if not explanation:
                    explanation = "No explanation provided"
                return {"score": score, "explanation": explanation}
            except Exception:
                pass

        # Fallback: look for a numeric score in text
        score_search = re.search(r"(score|rating)[:\s]+(\d{1,3})", model_output, flags=re.IGNORECASE)
        if score_search:
            try:
                score = int(score_search.group(2))
                score = max(0, min(100, score))
            except Exception:
                score = 50
        else:
            # Map simple keywords to ranges
            low_map = r"\b(incorrect|wrong|poor|bad)\b"
            high_map = r"\b(correct|accurate|good|excellent)\b"
            if re.search(high_map, model_output, flags=re.IGNORECASE):
                score = 90
            elif re.search(low_map, model_output, flags=re.IGNORECASE):
                score = 20
            else:
                score = 50

        # Extract explanation as first two sentences
        sentences = re.split(r"(?<=[.!?])\s+", model_output.strip())
        explanation = " ".join(sentences[:2]).strip()
        if not explanation:
            explanation = "No explanation available"

        return {"score": int(score), "explanation": explanation}

    except Exception as e:
        logger.error(f"Error parsing judge output: {str(e)}")
        return {"score": 50, "explanation": "Parsing failed"}
