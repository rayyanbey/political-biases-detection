from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

from services.hf_client import query_hf_with_retry
from services.output_parser import (
    SentimentLabel,
    BiasLevel,
)
from services.text_manager import TextTruncationManager

# ============================================================================
# ENV CHECK
# ============================================================================
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    raise ValueError("❌ HF_API_KEY not found")

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG_MODE = True

# ============================================================================
# APP
# ============================================================================
app = FastAPI(title="Political Analysis API", version="4.0 FIXED")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
STANCE_MODEL = "facebook/bart-large-mnli"
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"

class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class AnalysisResponse(BaseModel):
    tone: SentimentLabel
    tone_score: float
    tone_confidence: str
    bias: BiasLevel
    bias_score: float
    bias_explanation: str
    summary: str
    truncation_warning: Optional[str] = None

# ============================================================================
# 🔥 NORMALIZER (KEY FIX)
# ============================================================================
def normalize_response(response):
    """
    Converts ANY HF response into clean list format
    """
    if isinstance(response, list):

        # sentiment case: [[{...}]]
        if len(response) > 0 and isinstance(response[0], list):
            return response[0]

        return response

    return response

# ============================================================================
# SENTIMENT
# ============================================================================
async def get_sentiment_analysis(text: str) -> dict:
    try:
        response = await query_hf_with_retry(
            SENTIMENT_MODEL,
            {"inputs": text}
        )

        if DEBUG_MODE:
            logger.info(f"\n🔥 SENTIMENT RAW:\n{response}\n")

        data = normalize_response(response)

        top = data[0]
        label = top["label"].lower()
        score = top["score"]

        if label == "positive":
            final = SentimentLabel.POSITIVE
        elif label == "negative":
            final = SentimentLabel.NEGATIVE
        else:
            final = SentimentLabel.NEUTRAL

        return {
            "label": final,
            "score": float(score),
            "confidence": "high" if score > 0.8 else "medium",
            "raw": response
        }

    except Exception as e:
        logger.error(f"Sentiment error: {e}")
        return {
            "label": SentimentLabel.NEUTRAL,
            "score": 0.5,
            "confidence": "low",
            "raw": str(e)
        }

# ============================================================================
# SUMMARY
# ============================================================================
async def get_summary_analysis(text: str) -> dict:
    try:
        truncated_text, _ = TextTruncationManager.truncate_with_strategy(
            text, task="summarization", strategy="smart"
        )

        response = await query_hf_with_retry(
            SUMMARIZATION_MODEL,
            {"inputs": truncated_text}
        )

        if DEBUG_MODE:
            logger.info(f"\n🧠 SUMMARY RAW:\n{response}\n")

        data = normalize_response(response)

        summary = data[0]["summary_text"]

        return {
            "summary": summary,
            "raw": response
        }

    except Exception as e:
        logger.error(f"Summary error: {e}")
        return {
            "summary": text[:200],
            "raw": str(e)
        }

# ============================================================================
# BIAS
# ============================================================================
async def get_bias_analysis(text: str) -> dict:
    try:
        truncated_text, _ = TextTruncationManager.truncate_with_strategy(
            text, task="bias_detection", strategy="minimal"
        )

        labels = [
            "strongly critical of government",
            "somewhat critical of government",
            "neutral political statement",
            "supportive of government"
        ]

        response = await query_hf_with_retry(
            STANCE_MODEL,
            {
                "inputs": truncated_text,
                "parameters": {"candidate_labels": labels}
            }
        )

        if DEBUG_MODE:
            logger.info(f"\n⚖️ BIAS RAW:\n{response}\n")

        data = normalize_response(response)

        top = data[0]
        label = top["label"].lower()
        score = top["score"]

        if "neutral" in label:
            bias = BiasLevel.LOW
            explanation = "Neutral stance"
        elif "supportive" in label:
            bias = BiasLevel.LOW
            explanation = "Supportive stance"
        elif "somewhat critical" in label:
            bias = BiasLevel.MEDIUM
            explanation = "Moderate criticism"
        else:
            bias = BiasLevel.HIGH
            explanation = "Strong criticism"

        return {
            "bias": bias,
            "score": round(float(score), 3),
            "explanation": explanation,
            "raw": response
        }

    except Exception as e:
        logger.error(f"Bias error: {e}")
        return {
            "bias": BiasLevel.MEDIUM,
            "score": 0.5,
            "explanation": "Failed",
            "raw": str(e)
        }

# ============================================================================
# MAIN PIPELINE
# ============================================================================
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    try:
        text = request.text.strip()

        sentiment_task = get_sentiment_analysis(text)
        summary_task = get_summary_analysis(text)
        bias_task = get_bias_analysis(text)

        sentiment, summary, bias = await asyncio.gather(
            sentiment_task, summary_task, bias_task
        )

        return AnalysisResponse(
            tone=sentiment["label"],
            tone_score=sentiment["score"],
            tone_confidence=sentiment["confidence"],
            bias=bias["bias"],
            bias_score=bias["score"],
            bias_explanation=bias["explanation"],
            summary=summary["summary"],
            truncation_warning=None
        )

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(500, "Analysis failed")

# ============================================================================
@app.get("/health")
async def health():
    return {"status": "OK - FIXED v4.0"}