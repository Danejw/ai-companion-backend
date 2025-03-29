import logging
import math
import tiktoken


USD_PER_CREDIT = 0.001 # $0.001 per credit or 1000 credits per dollar
PROFIT_MARGIN_MULTIPLIER = 1.5 # 50% profit margin
ENCODING="o200k_base"

LLM_PRICING_USD_PER_TOKEN = {

    # --- GPT-4o Models ---
    "gpt-4o": {
        "prompt": 2.50 / 1_000_000,  # $2.50 per 1M input tokens
        "completion": 10.00 / 1_000_000, # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "prompt": 0.150 / 1_000_000, # $0.15 per 1M input tokens
        "completion": 0.600 / 1_000_000, # $0.60 per 1M output tokens
    },
    # Note: gpt-4o also has 'cached_input' pricing ($1.25 / 1M tokens) which might apply in some contexts (e.g., Assistants API).
    # Note: gpt-4o-mini also has 'cached_input' pricing ($0.075 / 1M tokens).

    # --- GPT-4 Turbo Models (Often Aliased/Replaced by GPT-4o, but check if specific versions used) ---
    "gpt-4-turbo": { # This might represent the latest Turbo version, check model list (Could be gpt-4-turbo-2024-04-09 or similar)
        "prompt": 10.00 / 1_000_000, # $10.00 per 1M input tokens
        "completion": 30.00 / 1_000_000, # $30.00 per 1M output tokens
    },
    "gpt-4-turbo-preview": { # Often refers to models like gpt-4-0125-preview, pricing usually matches gpt-4-turbo
        "prompt": 10.00 / 1_000_000,
        "completion": 30.00 / 1_000_000,
    },
    # Vision pricing for gpt-4-turbo is usually the same text pricing + an image-based cost if images are input.

    # --- Older GPT-4 Models ---
    "gpt-4": { # Base GPT-4 (e.g., 8k context)
        "prompt": 30.00 / 1_000_000, # $30.00 per 1M input tokens
        "completion": 60.00 / 1_000_000, # $60.00 per 1M output tokens
    },
    "gpt-4-32k": { # GPT-4 32k context
        "prompt": 60.00 / 1_000_000, # $60.00 per 1M input tokens
        "completion": 120.00 / 1_000_000, # $120.00 per 1M output tokens
    },

    # --- GPT-3.5 Turbo Models ---
    "gpt-3.5-turbo": { # Alias for latest recommended 3.5 Turbo (e.g., gpt-3.5-turbo-0125)
        "prompt": 0.50 / 1_000_000,  # $0.50 per 1M input tokens
        "completion": 1.50 / 1_000_000,  # $1.50 per 1M output tokens
    },
    "gpt-3.5-turbo-1106": {
        "prompt": 1.00 / 1_000_000,  # $1.00 per 1M input tokens
        "completion": 2.00 / 1_000_000,  # $2.00 per 1M output tokens
    },
    # Other older gpt-3.5-turbo versions might exist with different pricing, but 0125 is common.

    # --- Embedding Models (Only Input Cost) ---
    "text-embedding-3-large": {
        "prompt": 0.13 / 1_000_000,  # $0.13 per 1M input tokens
        "completion": 0.0, # No output token cost for embeddings
    },
    "text-embedding-3-small": {
        "prompt": 0.02 / 1_000_000,  # $0.02 per 1M input tokens
        "completion": 0.0, # No output token cost for embeddings
    },
    "text-embedding-ada-002": { # Legacy
        "prompt": 0.10 / 1_000_000,  # $0.10 per 1M input tokens
        "completion": 0.0, # No output token cost for embeddings
    },

     # --- New Reasoning Models (Example) ---
    "o1-mini": { # Example from search results - verify official status/pricing
        "prompt": 1.10 / 1_000_000,
        "completion": 4.40 / 1_000_000,
        # Also mentions cached input pricing
    },


    # --- Fallback ---
     "DEFAULT_FALLBACK": { # Use if a model called isn't explicitly listed - choose a reasonable default
        "prompt": 1.00 / 1_000_000,
        "completion": 2.00 / 1_000_000
    }
}


def count_tokens(text: str) -> int:
    """Counts tokens using tiktoken for a given text and model."""
    try:
        encoding = tiktoken.get_encoding(ENCODING)
        num_tokens = len(encoding.encode(text))
        return num_tokens
    
    except Exception as e:
        logging.warning(f"Warning: Could not count tokens encoding failed and defaulted to fallback. Error: {e}")
        # Fallback or default logic if needed, e.g., estimate based on chars/words
        return len(text) // 4 # Very rough estimate everthing is 4 characters
    
def calculate_provider_cost(text: str, model: str = "gpt-4o-mini") -> float:
    """Calculates the cost of tokens for a given text and model."""
    global LLM_PRICING_USD_PER_TOKEN
    try:
        if model not in LLM_PRICING_USD_PER_TOKEN:
            logging.warning(f"Warning: Model {model} not found in LLM_PRICING_USD_PER_TOKEN. Using DEFAULT_FALLBACK.")
            model = "DEFAULT_FALLBACK"
            
        pricing = LLM_PRICING_USD_PER_TOKEN[model]
        input_tokens = count_tokens(text)
        output_tokens = count_tokens(text)
        cost = (pricing["prompt"] * input_tokens) + (pricing["completion"] * output_tokens)
        return cost
    except Exception as e:
        logging.error(f"Error calculating token cost for model {model}: {e}")
        return 0.0

def calculate_credits_to_deduct(token_cost : float) -> int:
    """Calculates the integer number of credits to deduct from the user."""
    if token_cost < 0: # Safety check
        logging.error(f"Provider cost cannot be negative: {token_cost}")
        return 0

    # Apply profit margin
    selling_price_usd = token_cost * PROFIT_MARGIN_MULTIPLIER

    # Convert to credits
    if USD_PER_CREDIT <= 0:
        logging.error(f"USD_PER_CREDIT must be positive: {USD_PER_CREDIT}")
        return 0 # Cannot calculate credits

    credits_float = selling_price_usd / USD_PER_CREDIT

    # Round up to the nearest whole credit
    credits_int = math.ceil(credits_float)

    # Ensure at least 1 credit is charged for any non-zero cost (optional, ceil usually handles this)
    if selling_price_usd > 0 and credits_int == 0:
         credits_int = 1

    return credits_int

def calculate_credits_for_purchase(payment_usd: float) -> int:
    """Calculates the integer number of credits a user receives for a USD payment."""
    if payment_usd <= 0:
        return 0
    if USD_PER_CREDIT <= 0:
        logging.error(f"USD_PER_CREDIT must be positive: {USD_PER_CREDIT}")
        return 0

    credits_float = payment_usd / USD_PER_CREDIT

    # Round down to the nearest whole credit for purchases
    credits_int = math.floor(credits_float)
    return credits_int
