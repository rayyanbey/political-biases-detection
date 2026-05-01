"""
Bias detection prompts for FLAN-T5 model.
Provides multiple prompt variants optimized for different scenarios.
"""

# ============================================================================
# VARIANT 1: Few-Shot Learning (Recommended for accuracy)
# ============================================================================
# FLAN-T5 excels with 2-3 examples that demonstrate the task clearly

def get_few_shot_bias_prompt(text: str) -> str:
    """
    Few-shot prompt with examples for better bias detection.
    Provides context through positive and negative examples.
    """
    return f"""Classify political bias in the following text as NONE, LOW, MEDIUM, or HIGH.

Examples:

Text: "Both parties have proposed different economic approaches with varying merits."
Bias: NONE (neutral presentation of multiple viewpoints)

Text: "Socialist policies will destroy our economy and harm hardworking families."
Bias: HIGH (strong emotional language, one-sided framing against one ideology)

Text: "The incumbent's policies have contributed to economic growth this quarter."
Bias: MEDIUM (positive framing without acknowledging counterarguments or context)

Now classify this text:

Text: "{text}"
Bias Level:"""


# ============================================================================
# VARIANT 2: Chain-of-Thought (Better reasoning, slightly slower)
# ============================================================================
# Chain-of-thought prompting improves reasoning in language models

def get_chain_of_thought_bias_prompt(text: str) -> str:
    """
    Chain-of-thought prompt that asks the model to reason step-by-step.
    Often produces more accurate and explainable results.
    """
    return f"""Detect and classify political bias in the following text step-by-step.

Text: "{text}"

Step 1 - Identify loaded language: Look for emotionally charged adjectives or adverbs that favor one side.
Step 2 - Check for false equivalencies: Does the text treat fundamentally different positions as equivalent?
Step 3 - Assess perspective balance: Are multiple viewpoints presented fairly or is one privileged?
Step 4 - Identify omissions: What relevant context or counterarguments are missing?
Step 5 - Determine bias level: Based on analysis, rate as NONE (fair), LOW (slight lean), MEDIUM (noticeable bias), or HIGH (strong bias).

Your reasoning:
Step 1 - Loaded language:
Step 2 - False equivalencies:
Step 3 - Perspective balance:
Step 4 - Omissions:
Step 5 - Final Bias Level:"""


# ============================================================================
# VARIANT 3: Direct Instruction (Fast, good for simple texts)
# ============================================================================
# Straightforward instruction without examples, faster but potentially less accurate

def get_direct_instruction_bias_prompt(text: str) -> str:
    """
    Direct instruction without examples.
    Fastest variant, suitable for simple texts.
    """
    return f"""You are a political bias detector. Analyze the following text and classify its political bias.

Instructions:
- Look for partisan language and framing
- Note loaded adjectives, emotional language, or exaggeration
- Check if multiple perspectives are presented
- Rate bias on a scale: NONE (no bias), LOW (minor bias), MEDIUM (noticeable bias), HIGH (strong bias)

Text: "{text}"

Bias Classification:"""


# ============================================================================
# VARIANT 4: Detailed Analysis with Explanation
# ============================================================================
# Returns structured output with explanation for transparency

def get_detailed_analysis_bias_prompt(text: str) -> str:
    """
    Detailed analysis prompt requesting structured output with explanation.
    Good for understanding why bias was detected.
    """
    return f"""Analyze political bias in the text below and provide a structured response.

Text: "{text}"

Provide:
1. Bias Level (NONE/LOW/MEDIUM/HIGH)
2. Confidence (1-5, where 5 is very confident)
3. Specific biased phrases or language (if any)
4. Brief explanation (1-2 sentences) of detected bias
5. Suggested neutral alternative (if biased)

Response:"""


# ============================================================================
# Helper function to select prompt variant
# ============================================================================

def get_bias_prompt(text: str, variant: str = "few_shot") -> str:
    """
    Get bias detection prompt based on selected variant.
    
    Args:
        text: The text to analyze for bias
        variant: Prompt variant to use:
            - "few_shot": Recommended, most accurate with examples
            - "chain_of_thought": Best for reasoning/explanation
            - "direct": Fastest, minimal context
            - "detailed": Structured output with explanation
    
    Returns:
        Formatted prompt string ready for FLAN-T5
    """
    variants = {
        "few_shot": get_few_shot_bias_prompt,
        "chain_of_thought": get_chain_of_thought_bias_prompt,
        "cot": get_chain_of_thought_bias_prompt,  # Alias
        "direct": get_direct_instruction_bias_prompt,
        "detailed": get_detailed_analysis_bias_prompt,
    }
    
    prompt_fn = variants.get(variant, get_few_shot_bias_prompt)
    return prompt_fn(text)


# ============================================================================
# Recommended prompt strategy based on text characteristics
# ============================================================================

def recommend_prompt_variant(text: str) -> str:
    """
    Recommend which prompt variant to use based on text characteristics.
    
    Args:
        text: The input text to analyze
    
    Returns:
        Name of recommended variant
    """
    word_count = len(text.split())
    
    # For very short texts, use direct prompt (faster)
    if word_count < 50:
        return "direct"
    
    # For medium texts, use few-shot (balanced accuracy/speed)
    elif word_count < 300:
        return "few_shot"
    
    # For longer texts, use chain-of-thought (more careful reasoning)
    else:
        return "chain_of_thought"
