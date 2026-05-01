from typing import Tuple, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

class TextTruncationManager:
    """
    Manage text truncation with user feedback.
    Supports multiple truncation strategies with metadata tracking.
    """
    
    # Approximate token counts (rule of thumb: ~4 chars per token)
    MAX_LENGTHS = {
        "sentiment": 512,
        "summarization": 1024,
        "bias_detection": 512,
        "text_generation": 256,
    }
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count using simple heuristic: ~4 characters per token.
        This is approximate but good enough for truncation decisions.
        """
        return len(text) // 4
    
    @staticmethod
    def truncate_with_strategy(
        text: str,
        task: str,
        strategy: str = "middle_preserve"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Truncate text based on task requirements with specified strategy.
        
        Args:
            text: Input text to potentially truncate
            task: Task type (sentiment, summarization, bias_detection, text_generation)
            strategy: Truncation strategy:
                - "start": Keep first N tokens
                - "end": Keep last N tokens
                - "middle_preserve": Keep start + end, remove middle (40/60 split)
                - "smart": Try to preserve sentence boundaries
        
        Returns:
            Tuple of (truncated_text, metadata_dict)
        """
        
        max_tokens = TextTruncationManager.MAX_LENGTHS.get(task, 512)
        original_length = len(text)
        original_tokens = TextTruncationManager.estimate_tokens(text)
        
        metadata = {
            "original_length": original_length,
            "original_tokens": original_tokens,
            "max_tokens": max_tokens,
            "truncated": False,
            "strategy_used": None,
            "user_message": None,
            "truncation_ratio": 1.0,
            "final_tokens": original_tokens,
        }
        
        # No truncation needed
        if original_tokens <= max_tokens:
            return text, metadata
        
        metadata["truncated"] = True
        truncation_ratio = original_tokens / max_tokens
        metadata["truncation_ratio"] = truncation_ratio
        
        # Calculate approximate char limit based on token limit
        max_chars = max_tokens * 4
        
        if strategy == "start":
            truncated_text = text[:max_chars]
            metadata["strategy_used"] = "kept_beginning"
            metadata["user_message"] = (
                f"Text was too long ({original_tokens} tokens). "
                f"Analyzed first {max_tokens} tokens."
            )
        
        elif strategy == "end":
            truncated_text = text[-max_chars:] if len(text) > max_chars else text
            metadata["strategy_used"] = "kept_end"
            metadata["user_message"] = (
                f"Text was too long ({original_tokens} tokens). "
                f"Analyzed last {max_tokens} tokens."
            )
        
        elif strategy == "middle_preserve":
            # Keep 40% from start, 60% from end
            start_chars = int(max_chars * 0.4)
            end_chars = max_chars - start_chars
            
            if len(text) > max_chars:
                truncated_text = text[:start_chars] + " ... " + text[-end_chars:]
            else:
                truncated_text = text
            
            metadata["strategy_used"] = "start_and_end"
            metadata["user_message"] = (
                f"Text was too long ({original_tokens} tokens). "
                f"Analyzed beginning and end sections."
            )
        
        elif strategy == "smart":
            # Try to truncate at sentence boundaries
            truncated_text, strategy_used = TextTruncationManager._smart_truncate(
                text, max_chars
            )
            metadata["strategy_used"] = strategy_used
            metadata["user_message"] = (
                f"Text was too long ({original_tokens} tokens). "
                f"Truncated at sentence boundaries to {max_tokens} tokens."
            )
        
        else:
            # Default to middle_preserve
            start_chars = int(max_chars * 0.4)
            end_chars = max_chars - start_chars
            truncated_text = text[:start_chars] + " ... " + text[-end_chars:]
            metadata["strategy_used"] = "start_and_end_default"
        
        final_tokens = TextTruncationManager.estimate_tokens(truncated_text)
        metadata["final_tokens"] = final_tokens
        
        return truncated_text, metadata
    
    @staticmethod
    def _smart_truncate(text: str, max_chars: int) -> Tuple[str, str]:
        """
        Truncate text at sentence boundaries to preserve meaning.
        Returns: (truncated_text, strategy_name)
        """
        if len(text) <= max_chars:
            return text, "no_truncation"
        
        # Get text up to max_chars
        truncated = text[:max_chars]
        
        # Find last period, exclamation, or question mark within a reasonable window
        # Look back up to 200 chars to find a sentence boundary
        search_start = max(0, len(truncated) - 200)
        last_sentence_end = -1
        
        for i in range(len(truncated) - 1, search_start, -1):
            if truncated[i] in '.!?':
                last_sentence_end = i
                break
        
        if last_sentence_end > search_start:
            # Found a good sentence boundary
            return truncated[:last_sentence_end + 1], "sentence_boundary"
        
        # No sentence boundary found, use paragraph boundary (double newline) if available
        last_paragraph_end = truncated.rfind('\n\n')
        if last_paragraph_end > search_start:
            return truncated[:last_paragraph_end], "paragraph_boundary"
        
        # Fall back to simple boundary
        return truncated, "simple_truncation"

def get_truncation_warning(metadata: Dict[str, Any]) -> str:
    """
    Generate user-friendly truncation warning message.
    Returns empty string if no truncation occurred.
    """
    if not metadata.get("truncated"):
        return ""
    
    ratio = metadata.get("truncation_ratio", 1.0)
    original = metadata.get("original_tokens", 0)
    kept = metadata.get("final_tokens", 0)
    
    if ratio < 1.2:
        icon = "ℹ️"
        severity = "minor"
    elif ratio < 2.0:
        icon = "⚠️"
        severity = "moderate"
    else:
        icon = "⚠️"
        severity = "significant"
    
    message = (
        f"{icon} Text truncated ({severity}): {original} → {kept} tokens\n"
        f"Strategy: {metadata.get('strategy_used', 'unknown')}\n"
        f"Note: Analysis may be incomplete due to truncation"
    )
    
    return message
