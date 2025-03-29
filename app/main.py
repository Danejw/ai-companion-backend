from fastapi import FastAPI, HTTPException, Request, Depends
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

# CORS
from fastapi.middleware.cors import CORSMiddleware

# 🔥 Define allowed origins based on the environment
ENV = os.getenv("ENV", "development")  # Default to development

if ENV == "development":
    ALLOWED_ORIGINS = ["*"]  # ✅ Allow all origins in development
else:
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://your-production-site.com").split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use environment-based CORS
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)



# Registering routers
from app.routes.health_check import health_check_router
from app.routes.realtime import realtime_router
from app.routes.mbti import router as mbti_router
from app.routes.ocean import router as ocean_router
from app.routes.knowledge import router as knowledge_router
from app.routes.orchestration import router as orchestration_router
from app.stripe.subscription import router as stripe_router
from app.routes.slang import router as slang_router
from app.stripe.subscription import router as stripe_router
from app.routes.moderation_check import router as moderation_router
from app.routes.intent_classifier import router as intent_classifier_router
from app.routes.theory_planned_behavior_route import router as theory_planned_behavior_router

app.include_router(health_check_router)
app.include_router(realtime_router)
app.include_router(mbti_router, prefix="/mbti", tags=["MBTI"])
app.include_router(ocean_router, prefix="/ocean", tags=["OCEAN"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
app.include_router(orchestration_router, prefix="/orchestration", tags=["Orchestration"])
app.include_router(stripe_router, prefix="/app/stripe", tags=["stripe"])
app.include_router(slang_router, prefix="/slang", tags=["Slang"])
app.include_router(moderation_router, prefix="/moderation", tags=["Moderation"])
app.include_router(intent_classifier_router, prefix="/intent", tags=["Intent"])
app.include_router(theory_planned_behavior_router, prefix="/tpb", tags=["Theory Planned Behavior"])



# Force HTTPS connections in production
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "False").lower() == "true"

@app.middleware("http")
async def enforce_https(request: Request, call_next):
    """Force HTTPS connections"""
    if FORCE_HTTPS and request.url.scheme != "https":
        raise HTTPException(status_code=403, detail="HTTPS required")
    return await call_next(request)




# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.auth import verify_token
from app.psychology.mbti_analysis import MBTIAnalysisService
from app.psychology.ocean_analysis import OceanAnalysisService


limiter = Limiter(key_func=get_remote_address)


app.state.limiter = limiter
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Change * to your domain later

@app.get("/mbti", dependencies=[Depends(limiter.limit("50 per minute"))], include_in_schema=False)
async def get_mbti(user_id: str = Depends(verify_token)):
    service = MBTIAnalysisService(user_id)
    mbti_data = service.repository.get_mbti(user_id)

    if mbti_data:
        return mbti_data.dict()
    else:
        raise HTTPException(status_code=404, detail="No MBTI data found for this user")
    
    
@app.get("/ocean", dependencies=[Depends(limiter.limit("50 per minute"))], include_in_schema=False)
async def get_ocean(user_id: str = Depends(verify_token)):
    service = OceanAnalysisService(user_id)
    ocean_data = service.repository.get_ocean(user_id)

    if ocean_data:
        return ocean_data.dict()
    else:
        raise HTTPException(status_code=404, detail="No OCEAN data found for this user")


# expose supabase keys to frontend
@app.get("/config")
async def get_config():
    """
    Securely provides frontend with Supabase keys.
    """
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "STRIPE_PUBLIC_KEY": os.getenv("STRIPE_PUBLIC_KEY_TEST" if ENV == "development" else "STRIPE_PUBLIC_KEY_LIVE")
    }
    