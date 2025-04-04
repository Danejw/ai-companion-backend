# subscription.py
import stripe
import os
import logging
from fastapi import HTTPException, Request, Depends, APIRouter, Header
from pydantic import BaseModel
from app.stripe.stripe_config import STRIPE_CONFIG
from app.auth import verify_token
from app.supabase.profiles import ProfileRepository


# Define your subscription request model
class SubscriptionRequest(BaseModel):
    plan: str  # Expected values: "basic", "standard", "premium"

class OneTimePurchaseRequest(BaseModel):
    tier: str  # Expected values: "tier1", "tier2", "tier3", "tier4", "tier5"

router = APIRouter()



stripe.api_version = '2025-02-24.acacia'
secret_key = STRIPE_CONFIG["secret_key"]
stripe.api_key = secret_key


# Subscription plan configurations
PLAN_CONFIG = {
    "basic": {
        "credits": 2000,
        "token_allowance": 2000000,
        "price_id": STRIPE_CONFIG["sub_prices"]["basic"]
    },
    "standard": {
        "credits": 6000,
        "token_allowance": 6000000,
        "price_id": STRIPE_CONFIG["sub_prices"]["standard"]
    },
    "premium": {
        "credits": 10000,
        "token_allowance": 10000000,
        "price_id": STRIPE_CONFIG["sub_prices"]["premium"]
    }
}

ONE_TIME_PURCHASE_CONFIG = {
    "tier1": {
        "cost": 2,
        "credits": 100,
        "price_id": STRIPE_CONFIG["one_time_prices"]["tier1"]  # Price ID for Tier 1
    },
    "tier2": {
        "cost": 6,
        "credits": 320,
        "price_id": STRIPE_CONFIG["one_time_prices"]["tier2"]
    },
    "tier3": {
        "cost": 12,
        "credits": 660,
        "price_id": STRIPE_CONFIG["one_time_prices"]["tier3"]
    },
    "tier4": {
        "cost": 24,
        "credits": 1400,
        "price_id": STRIPE_CONFIG["one_time_prices"]["tier4"]
    },
    "tier5": {
        "cost": 48,
        "credits": 3000,
        "price_id": STRIPE_CONFIG["one_time_prices"]["tier5"]
    }
}


@router.post("/create-one-time-checkout-session")
async def create_one_time_checkout_session(purchase_request: OneTimePurchaseRequest,user=Depends(verify_token)):
    try:
        logging.info("Purchase Request: %s", purchase_request)
        
        tier = purchase_request.tier
        
        logging.info("Tier: %s", tier)
        # Retrieve the one-time price ID and credits from the config
        config = ONE_TIME_PURCHASE_CONFIG.get(tier)
        
        logging.info("Config: %s", config)
        
        if not config:
            raise HTTPException(status_code=400, detail="Invalid purchase tier")

        price_id = config["price_id"]
        credits = config["credits"]
        
        logging.info("Credits: %s", credits)
        logging.info("Price ID: %s", price_id)
        
        success_url = os.getenv("STRIPE_SUCCESS_URL")
        cancel_url = os.getenv("STRIPE_CANCEL_URL")
        
        logging.info("Success URL: %s", success_url)
        logging.info("Cancel URL: %s", cancel_url)

        # Create a one-time Checkout Session in payment mode
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',  # one-time payment
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user["id"],
                "tier": tier,
                "credits": credits
            }
        )
        
        logging.info("Session: %s", session)
        logging.info("Session ID: %s", session.id)
        
        return {"sessionId": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create a checkout session for a subscription
#@router.post("/create-checkout-session")
async def create_checkout_session(subscription_request: SubscriptionRequest, user=Depends(verify_token)):
    try:
        plan = subscription_request.plan
        price_id = PLAN_CONFIG[plan]["price_id"]
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=os.getenv("STRIPE_SUCCESS_URL"),
            cancel_url=os.getenv("STRIPE_CANCEL_URL"),
            metadata={
                "user_id": user["id"],
                "plan": plan,
                "credits": PLAN_CONFIG[plan]["credits"]
            },
            subscription_data={
                "metadata": {
                    "user_id": user["id"],
                    "plan": plan,
                    "credits": PLAN_CONFIG[plan]["credits"]
                    }
            }
        )
        return {"sessionId": session.id}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Handle webhook events from Stripe for subscription
@router.post("/webhook") # https://yourdomain.com/app/stripe/webhook) 
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    webhook_secret = STRIPE_CONFIG["webhook_secret"]

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
    except ValueError as e:
        logging.error("❌ Invalid payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logging.error("❌ Invalid signature: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    logging.info("📢 Stripe Event: %s", event_type)

    # ✅ Handle subscription successful payment
    if event_type == "invoice.paid":
        lines = event_data.get("lines", {}).get("data", [])
        if lines and "metadata" in lines[0]:
            metadata = lines[0]["metadata"]
            user_id = metadata.get("user_id")    
            tier = metadata.get("tier")
            credits = metadata.get("credits")

        if not user_id or not tier or not credits:
            logging.warning("⚠️ Missing metadata. Cannot update user subscription.")
        else:
            try:
                credits = int(credits)
                logging.info(f"🎯 Updating user {user_id}: Tier={tier}, Credits={credits}")

                repo = ProfileRepository()
                updated_sub = repo.update_user_subscription(user_id, tier)
                updated_credits = repo.update_user_credit(user_id, credits)

                logging.info("✅ Supabase update response:", "updated_sub:", updated_sub, "updated_credits:", updated_credits)
            except Exception as e:
                logging.error(f"❌ Failed to update Supabase: {e}")



    # Handle one-time payment events (using checkout.session.completed in payment mode)
    elif event_type == "checkout.session.completed" and event_data.get("mode") == "payment":
        metadata = event_data.get("metadata", {})
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        credits = metadata.get("credits")
        if user_id and tier and credits:
            try:
                credits = int(credits)
                repo = ProfileRepository()
                # For one-time purchases, simply add credits (e.g., increment existing credits)
                updated_credits = repo.increment_user_credit(user_id, credits)
                logging.info("✅ Added %s credits to user %s via one-time purchase = %s", credits, user_id, updated_credits)
            except Exception as e:
                logging.error("❌ Failed to update credits for one-time purchase: %s", e)
        else:
            logging.warning("⚠️ One-time purchase metadata missing.")
            
    elif event_type == "invoice.payment_failed":
        logging.warning("💳 Payment failed. Consider notifying the user.")
        
    return {"status": "success"}

@router.get("/stripe/config")
async def get_stripe_config():
    return {"publishableKey": STRIPE_CONFIG["publishable_key"]}

@router.post("/deduct-credits")
async def deduct_credits_endpoint(
    data: dict, 
    user=Depends(verify_token)
):
    user_id = user["id"]
    amount = data.get("amount")
    
    if not amount or not isinstance(amount, int):
        raise HTTPException(
            status_code=400, 
            detail="Invalid amount provided"
        )
    
    repo = ProfileRepository()
    
    # Get current balance first
    current_credits = repo.get_user_credit(user_id)
    if current_credits is None:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )
    
    if current_credits < amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Current balance: {current_credits}"
        )
    
    # Perform atomic deduction
    if not repo.deduct_credits(user_id, amount):
        raise HTTPException(
            status_code=500,
            detail="Failed to process credit deduction"
        )
    
    # Get updated balance
    new_balance = repo.get_user_credit(user_id)
    
    return {
        "user_id": user_id,
        "amount_deducted": amount,
        "new_balance": new_balance
    }