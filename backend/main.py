from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import logging
from typing import Optional
import os

from services.hf_client import query_hf_with_retry, HFAPIError
from services.output_parser import (
    parse_sentiment_output,
    parse_summarization_output,
    parse_text_generation,
    parse_bias_detection_response,
    SentimentLabel,
    BiasLevel,
)
from services.text_manager import TextTruncationManager, get_truncation_warning
from prompts import get_bias_prompt

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI App Setup
# ============================================================================
app = FastAPI(
    title="Political Text Analysis API",
    description="Analyze political text for tone, bias, and summary",
    version="1.0.0"
)

# CORS Configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class AnalysisRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to analyze (max 5000 characters)"
    )

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
# Model Constants
# ============================================================================
SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"
BIAS_MODEL = "google/flan-t5-large"

# ============================================================================
# Analysis Functions
# ============================================================================

async def get_sentiment_analysis(text: str) -> dict:
    """
    Analyze sentiment (tone) of the text.
    Returns: {"label": SentimentLabel, "score": float, "confidence": str}
    """
    try:
        logger.info(f"Analyzing sentiment for {len(text)} chars")
        
        response = await query_hf_with_retry(
            SENTIMENT_MODEL,
            {"inputs": text},
            max_retries=3
        )
        
        result = parse_sentiment_output(response)
        logger.info(f"Sentiment: {result.label} (score: {result.score})")
        
        return {
            "label": result.label,
            "score": result.score,
            "confidence": result.confidence
        }
    
    except HFAPIError as e:
        logger.error(f"Sentiment API error: {str(e)}")
        # Fallback
        return {
            "label": SentimentLabel.NEUTRAL,
            "score": 0.5,
            "confidence": "low"
        }
    except Exception as e:
        logger.error(f"Unexpected error in sentiment analysis: {str(e)}")
        return {
            "label": SentimentLabel.NEUTRAL,
            "score": 0.5,
            "confidence": "low"
        }

async def get_summary_analysis(text: str) -> str:
    """
    Summarize the text.
    Returns: summary_text (str)
    """
    try:
        # Truncate to BART input limit
        truncated_text, _ = TextTruncationManager.truncate_with_strategy(
            text, task="summarization", strategy="smart"
        )
        
        logger.info(f"Summarizing {len(truncated_text)} chars")
        
        response = await query_hf_with_retry(
            SUMMARIZATION_MODEL,
            {"inputs": truncated_text},
            max_retries=3
        )
        
        summary = parse_summarization_output(response)
        logger.info(f"Summary generated: {len(summary)} chars")
        
        return summary
    
    except HFAPIError as e:
        logger.error(f"Summarization API error: {str(e)}")
        # Fallback: return first 200 chars
        return text[:200] + "..." if len(text) > 200 else text
    except Exception as e:
        logger.error(f"Unexpected error in summarization: {str(e)}")
        return "Summary generation failed."

async def get_bias_analysis(text: str) -> dict:
    """
    Detect political bias in the text.
    Returns: {"bias": BiasLevel, "score": float, "explanation": str}
    """
    try:
        # Truncate to bias model input limit
        truncated_text, _ = TextTruncationManager.truncate_with_strategy(
            text, task="bias_detection", strategy="smart"
        )
        
        logger.info(f"Analyzing bias for {len(truncated_text)} chars")
        
        # Get appropriate prompt variant based on text length
        prompt = get_bias_prompt(truncated_text, variant="few_shot")
        
        response = await query_hf_with_retry(
            BIAS_MODEL,
            {"inputs": prompt},
            max_retries=3,
            read_timeout=45  # Bias detection can take longer
        )
        
        # Extract generated text from response
        generated_text = parse_text_generation(response, prompt=prompt)
        
        # Parse the generated text into structured format
        bias_result = parse_bias_detection_response(generated_text)
        
        logger.info(f"Bias: {bias_result.bias_level} (score: {bias_result.score})")
        
        return {
            "bias": bias_result.bias_level,
            "score": bias_result.score,
            "explanation": bias_result.explanation
        }
    
    except HFAPIError as e:
        logger.error(f"Bias detection API error: {str(e)}")
        # Fallback
        return {
            "bias": BiasLevel.MEDIUM,
            "score": 3.0,
            "explanation": "Analysis inconclusive"
        }
    except Exception as e:
        logger.error(f"Unexpected error in bias analysis: {str(e)}")
        return {
            "bias": BiasLevel.MEDIUM,
            "score": 3.0,
            "explanation": "Analysis inconclusive"
        }

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Political Text Analysis API"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Analyze political text for tone, bias, and summary.
    
    Args:
        request: AnalysisRequest with 'text' field
    
    Returns:
        AnalysisResponse with tone, bias, and summary analysis
    """
    try:
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=422, detail="Text cannot be empty")
        
        # Truncate with warning tracking
        truncated_text, truncation_metadata = TextTruncationManager.truncate_with_strategy(
            text, task="sentiment", strategy="smart"
        )
        
        logger.info(f"Analyzing text: {len(text)} chars, truncated to {len(truncated_text)} chars")
        
        # Run all three analyses in parallel
        sentiment_task = get_sentiment_analysis(truncated_text)
        summary_task = get_summary_analysis(truncated_text)
        bias_task = get_bias_analysis(truncated_text)
        
        results = await asyncio.gather(sentiment_task, summary_task, bias_task)
        
        sentiment_result = results[0]
        summary_result = results[1]
        bias_result = results[2]
        
        # Generate truncation warning if applicable
        truncation_warning = get_truncation_warning(truncation_metadata)
        
        logger.info("Analysis complete, returning results")
        
        return AnalysisResponse(
            tone=sentiment_result["label"],
            tone_score=sentiment_result["score"],
            tone_confidence=sentiment_result["confidence"],
            bias=bias_result["bias"],
            bias_score=bias_result["score"],
            bias_explanation=bias_result["explanation"],
            summary=summary_result,
            truncation_warning=truncation_warning if truncation_warning else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /analyze endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.post("/analyze-sentiment")
async def analyze_sentiment(request: AnalysisRequest):
    """Analyze sentiment only (lighter weight)"""
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="Text cannot be empty")
        
        result = await get_sentiment_analysis(text)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sentiment-only endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.post("/analyze-summary")
async def analyze_summary(request: AnalysisRequest):
    """Summarize text only (lighter weight)"""
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="Text cannot be empty")
        
        summary = await get_summary_analysis(text)
        return {"summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in summary-only endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.post("/analyze-bias")
async def analyze_bias(request: AnalysisRequest):
    """Analyze bias only (lighter weight)"""
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="Text cannot be empty")
        
        result = await get_bias_analysis(text)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bias-only endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Welcome endpoint with API documentation"""
    return {
        "message": "Welcome to Political Text Analysis API",
        "docs": "/docs",
        "endpoints": {
            "POST /analyze": "Full analysis (tone, bias, summary)",
            "POST /analyze-sentiment": "Sentiment only",
            "POST /analyze-summary": "Summary only",
            "POST /analyze-bias": "Bias only",
            "GET /health": "Health check"
        }
    }

# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
