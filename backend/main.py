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
from services.text_manager import TextTruncationManager
from services.judge import evaluate_judge

# =========================================================
# ENV
# =========================================================
HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise ValueError("❌ HF_API_KEY not found")

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG_MODE = True  # 👈 turn OFF noisy logs

# =========================================================
# APP
# =========================================================
app = FastAPI(title="Political Analysis API", version="5.0 CLEAN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# MODELS
# =========================================================
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
STANCE_MODEL = "facebook/bart-large-mnli"
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"

# =========================================================
# REQUEST
# =========================================================
class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

# =========================================================
# HELPERS
# =========================================================
def normalize(response):
    """Flattens HF weird nested outputs"""
    if isinstance(response, list):
        if len(response) > 0 and isinstance(response[0], list):
            return response[0]
        return response
    return response


def get_top(data):
    """Get highest scoring label safely"""
    data = normalize(data)
    top = max(data, key=lambda x: x["score"])
    return top["label"], float(top["score"])

# =========================================================
# SENTIMENT
# =========================================================
async def get_sentiment(text: str):
    response = await query_hf_with_retry(
        SENTIMENT_MODEL,
        {"inputs": text}
    )

    if DEBUG_MODE:
        logger.info(f"Sentiment response: {response}")
    label, score = get_top(response)
    label = label.lower()

    if "positive" in label:
        final = "positive"
    elif "negative" in label:
        final = "negative"
    else:
        final = "neutral"

    return {
        "label": final,
        "confidence": round(score, 3)
    }

def normalize_stance(label: str):
    label = label.lower()

    if "neutral" in label:
        return "Neutral"

    elif "supportive" in label:
        return "Supportive"

    elif "critical" in label:
        return "Oppose"

    else:
        return "Neutral"
    
# =========================================================
# STANCE / BIAS
# =========================================================
async def get_stance(text: str):
    labels = [
        "strongly critical of government",
        "somewhat critical of government",
        "neutral political statement",
        "supportive of government"
    ]

    response = await query_hf_with_retry(
        STANCE_MODEL,
        {
            "inputs": text,
            "parameters": {"candidate_labels": labels}
        }
    )

    if DEBUG_MODE:
        logger.info(f"Stance response: {response}")

    label, score = get_top(response)

    stance = normalize_stance(label)

    # optional bias mapping (keep if you still need it)
    if stance == "Neutral":
        category = "LOW_BIAS"
    elif stance == "Supportive":
        category = "LOW_BIAS"
    else:  # Oppose
        category = "HIGH_BIAS"

    return {
        "label": stance,          # 👈 FINAL OUTPUT: Supportive / Oppose / Neutral
        "confidence": round(score, 3),
        "category": category
    }
# =========================================================
# SUMMARY
# =========================================================
async def get_summary(text: str):
    truncated, _ = TextTruncationManager.truncate_with_strategy(
        text,
        task="summarization",
        strategy="smart"
    )

    response = await query_hf_with_retry(
        SUMMARIZATION_MODEL,
        {
            "inputs": truncated,
            "parameters": {
                "max_length": 60,
                "min_length": 20,
                "do_sample": False
            }
        }
    )

    response = normalize(response)
    summary = response[0]["summary_text"]

    if DEBUG_MODE:
        logger.info(f"Summary response: {summary}")


    return summary
# =========================================================
# MAIN API
# =========================================================
@app.post("/analyze")
async def analyze(req: AnalysisRequest):
    try:
        text = req.text.strip()

        sentiment_task = get_sentiment(text)
        stance_task = get_stance(text)
        summary_task = get_summary(text)

        sentiment, stance, summary = await asyncio.gather(
            sentiment_task,
            stance_task,
            summary_task
        )

        # Build a compact analysis snapshot for the judge
        analysis_snapshot = {
            "sentiment": f"{sentiment.get('label')} ({sentiment.get('confidence')})",
            "stance": f"{stance.get('label')} ({stance.get('confidence')})",
            "summary": summary
        }

        # Run judge evaluation (may add latency)
        judge_result = await evaluate_judge(text, analysis_snapshot)

        return {
            "sentiment": sentiment,
            "stance": stance,
            "summary": summary,
            "judge": judge_result
        }

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(500, "Analysis failed")

# =========================================================
@app.get("/health")
async def health():
    return {"status": "OK - CLEAN API v5.0"}