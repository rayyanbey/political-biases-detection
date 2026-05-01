import httpx
import asyncio
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_API_URL = "https://api-inference.huggingface.co/models"

class HFAPIError(Exception):
    """Custom exception for Hugging Face API errors"""
    pass

async def query_hf_with_retry(
    model_id: str,
    payload: Dict[str, Any],
    max_retries: int = 3,
    backoff_base: float = 0.5,
    connect_timeout: int = 10,
    read_timeout: int = 30,
) -> Dict[str, Any]:
    """
    Query Hugging Face Inference API with exponential backoff retry logic.
    
    Args:
        model_id: Hugging Face model identifier (e.g., "distilbert-base-uncased-...")
        payload: Request payload (e.g., {"inputs": text})
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_base: Base for exponential backoff in seconds (default: 0.5)
        connect_timeout: Connection timeout in seconds (default: 10)
        read_timeout: Read timeout in seconds (default: 30)
    
    Returns:
        Parsed JSON response from the API
    
    Raises:
        HFAPIError: For authentication errors, invalid models, or non-retryable errors
        asyncio.TimeoutError: If all retries are exhausted and timeout occurs
    """
    
    if not HF_API_KEY:
        raise HFAPIError("HF_API_KEY not set in environment variables")
    
    url = f"{HF_API_URL}/{model_id}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    
    retryable_status_codes = {429, 502, 503, 504}
    non_retryable_status_codes = {401, 403, 404, 400}
    
    timeout = httpx.Timeout(connect_timeout, read=read_timeout)
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} for model {model_id}")
                
                response = await client.post(url, json=payload, headers=headers)
                
                # Handle non-retryable auth/validation errors
                if response.status_code in non_retryable_status_codes:
                    error_detail = response.text
                    if response.status_code == 401:
                        raise HFAPIError(f"Unauthorized: Invalid or expired HF_API_KEY")
                    elif response.status_code == 403:
                        raise HFAPIError(f"Forbidden: Token revoked or access denied")
                    elif response.status_code == 404:
                        raise HFAPIError(f"Model not found: {model_id}")
                    elif response.status_code == 400:
                        raise HFAPIError(f"Bad request: {error_detail}")
                
                # Handle rate limiting and service errors (retryable)
                if response.status_code in retryable_status_codes:
                    if attempt < max_retries - 1:
                        # Extract Retry-After header if present
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            wait_time = float(retry_after)
                            logger.warning(f"Rate limited. Waiting {wait_time}s before retry")
                        else:
                            wait_time = backoff_base * (2 ** attempt)
                            logger.warning(f"Service error ({response.status_code}). Retrying in {wait_time}s")
                        
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise HFAPIError(
                            f"Failed after {max_retries} attempts. Last status: {response.status_code}"
                        )
                
                # Success
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        raise HFAPIError(f"Failed to parse JSON response: {str(e)}")
                
                # Other unexpected status codes
                raise HFAPIError(
                    f"Unexpected status code {response.status_code}: {response.text}"
                )
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                wait_time = backoff_base * (2 ** attempt)
                logger.info(f"Retrying after timeout in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                raise HFAPIError(f"Timeout after {max_retries} attempts")
        
        except httpx.ConnectError as e:
            logger.error(f"Connection error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = backoff_base * (2 ** attempt)
                await asyncio.sleep(wait_time)
            else:
                raise HFAPIError(f"Connection failed after {max_retries} attempts: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff_base * (2 ** attempt))
            else:
                raise HFAPIError(f"Request failed after {max_retries} attempts: {str(e)}")
    
    raise HFAPIError(f"Failed after {max_retries} attempts")
