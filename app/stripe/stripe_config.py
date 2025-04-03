import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variable for environment (default to development)
ENV = os.getenv("ENV", "development").lower()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Toggle subscription functionality (could be used to turn on/off subscription flows)
ENABLE_SUBSCRIPTIONS = os.getenv("ENABLE_SUBSCRIPTIONS", "true").lower() == "true"

# Stripe configuration: Use test keys and prices in development mode
if ENV == "development":
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY_TEST")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_TEST")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_TEST") # os.getenv("STRIPE_WEBHOOK_SECRET_CLI")
    
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC_TEST")
    STRIPE_PRICE_STANDARD = os.getenv("STRIPE_PRICE_STANDARD_TEST")
    STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM_TEST")
    STRIPE_ONE_TIME_PRICE_BASIC = os.getenv("STRIPE_ONE_TIME_PRICE_BASIC_TEST")
    STRIPE_ONE_TIME_PRICE_STANDARD = os.getenv("STRIPE_ONE_TIME_PRICE_STANDARD_TEST")
    STRIPE_ONE_TIME_PRICE_PREMIUM = os.getenv("STRIPE_ONE_TIME_PRICE_PREMIUM_TEST")
    
    STRIPE_ONE_TIME_PRICE_TIER1 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER1_TEST")
    STRIPE_ONE_TIME_PRICE_TIER2 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER2_TEST")
    STRIPE_ONE_TIME_PRICE_TIER3 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER3_TEST")
    STRIPE_ONE_TIME_PRICE_TIER4 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER4_TEST")
    STRIPE_ONE_TIME_PRICE_TIER5 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER5_TEST")
else:
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY_LIVE")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_LIVE")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_LIVE")
    
    STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC_LIVE")
    STRIPE_PRICE_STANDARD = os.getenv("STRIPE_PRICE_STANDARD_LIVE")
    STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM_LIVE")
    STRIPE_ONE_TIME_PRICE_BASIC = os.getenv("STRIPE_ONE_TIME_PRICE_BASIC_LIVE")
    STRIPE_ONE_TIME_PRICE_STANDARD = os.getenv("STRIPE_ONE_TIME_PRICE_STANDARD_LIVE")
    STRIPE_ONE_TIME_PRICE_PREMIUM = os.getenv("STRIPE_ONE_TIME_PRICE_PREMIUM_LIVE")
    
    STRIPE_ONE_TIME_PRICE_TIER1 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER1_LIVE")
    STRIPE_ONE_TIME_PRICE_TIER2 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER2_LIVE")
    STRIPE_ONE_TIME_PRICE_TIER3 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER3_LIVE")
    STRIPE_ONE_TIME_PRICE_TIER4 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER4_LIVE")
    STRIPE_ONE_TIME_PRICE_TIER5 = os.getenv("STRIPE_ONE_TIME_PRICE_TIER5_LIVE")

# Package these settings into a dictionary for easy access
STRIPE_CONFIG = {
    "publishable_key": STRIPE_PUBLIC_KEY,
    "secret_key": STRIPE_SECRET_KEY,
    "webhook_secret": STRIPE_WEBHOOK_SECRET,
    "sub_prices": {
        "basic": STRIPE_PRICE_BASIC,
        "standard": STRIPE_PRICE_STANDARD,
        "premium": STRIPE_PRICE_PREMIUM,
    },
    "one_time_prices": {
        "tier1": STRIPE_ONE_TIME_PRICE_TIER1,
        "tier2": STRIPE_ONE_TIME_PRICE_TIER2,
        "tier3": STRIPE_ONE_TIME_PRICE_TIER3,
        "tier4": STRIPE_ONE_TIME_PRICE_TIER4,
        "tier5": STRIPE_ONE_TIME_PRICE_TIER5,
    },
    "webhook_url": os.getenv("STRIPE_WEBHOOK_URL", f"{BASE_URL}/app/stripe/webhook")
}

