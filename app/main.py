import logging
from fastapi import FastAPI, HTTPException, Request, Depends
import os
from dotenv import load_dotenv
from app.function.notifications import start_scheduler_once
from app.websockets.routes.websockets_routes import router as ws_router

# Load environment variables first before importing STRIPE_CONFIG
load_dotenv(override=True)



app = FastAPI()
app.include_router(ws_router)


# CORS
from fastapi.middleware.cors import CORSMiddleware

# 🔥 Define allowed origins based on the environment
ENV = os.getenv("ENV")


if ENV == "development":
    ALLOWED_ORIGINS = ["*"]  # ✅ Allow all origins in development
    
    # Configure logging at the start of the file
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")

    # Configure logging at the start of the file
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use environment-based CORS
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],
    expose_headers=["X-Transcript"], # Allow all headers
)


# Start the scheduler once
@app.on_event("startup")
async def startup_event():
    start_scheduler_once()



# Registering routers
from app.routes.health_check import health_check_router
from app.routes.realtime import realtime_router
from app.routes.mbti import router as mbti_router
from app.routes.ocean import router as ocean_router
from app.routes.knowledge import router as knowledge_router
from app.routes.knowledge_edges_route import router as knowledge_edges_router
from app.routes.memory_extraction_routes import router as memory_extraction_router
from app.stripe.subscription import router as stripe_router
from app.routes.slang import router as slang_router
from app.routes.moderation_check import router as moderation_router
from app.routes.intent_classifier import router as intent_classifier_router
from app.routes.theory_planned_behavior_route import router as theory_planned_behavior_router
from app.routes.profiles_routes import router as profiles_router
from app.routes.conversation_routes import router as conversation_router
from app.routes.vector_routes import router as vector_router
from app.routes.feedback import router as feedback_router
from app.routes.voice_routes import router as voice_router
from app.routes.orchestration_route import router as orchestration_router
from app.websockets.routes.websockets_routes import router as websockets_router
from app.routes.push_notification_routes import router as push_notifcation_router
from app.routes.finetune_feedback_routes import router as finetune_feedback_router
from app.routes.connect_routes import router as connect_router
from app.routes.phq4_routes import router as phq4_router
from app.routes.auth_routes import router as auth_router

app.include_router(health_check_router)
app.include_router(realtime_router)
app.include_router(mbti_router, prefix="/mbti", tags=["MBTI"])
app.include_router(ocean_router, prefix="/ocean", tags=["OCEAN"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
app.include_router(knowledge_edges_router, prefix="/knowledge_edges", tags=["Knowledge Edges"])
app.include_router(stripe_router, prefix="/app/stripe", tags=["Stripe"])
app.include_router(slang_router, prefix="/slang", tags=["Slang"])
app.include_router(moderation_router, prefix="/moderation", tags=["Moderation"])
app.include_router(intent_classifier_router, prefix="/intent", tags=["Intent"])
app.include_router(theory_planned_behavior_router, prefix="/tpb", tags=["Theory Planned Behavior"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])
app.include_router(conversation_router, prefix="/conversations", tags=["Conversations"])
app.include_router(vector_router, prefix="/vectors", tags=["Vectors"])
app.include_router(memory_extraction_router, prefix="/vectors", tags=["Vectors"])
app.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
app.include_router(voice_router, prefix="/voice", tags=["Voice"])
app.include_router(orchestration_router, prefix="/orchestration", tags=["Orchestration"])
app.include_router(websockets_router, prefix="/ws", tags=["Websockets"])
app.include_router(push_notifcation_router, prefix="/push", tags=["Push Notifications"])
app.include_router(finetune_feedback_router, prefix="/finetune", tags=["Finetune Feedback"])
app.include_router(connect_router, prefix="/connect", tags=["Connect"])
app.include_router(phq4_router, prefix="/phq4", tags=["PHQ4"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

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
        return mbti_data.model_dump()
    else:
        raise HTTPException(status_code=404, detail="No MBTI data found for this user")
    
    
@app.get("/ocean", dependencies=[Depends(limiter.limit("50 per minute"))], include_in_schema=False)
async def get_ocean(user_id: str = Depends(verify_token)):
    service = OceanAnalysisService(user_id)
    ocean_data = service.repository.get_ocean(user_id)

    if ocean_data:
        return ocean_data.model_dump()
    else:
        raise HTTPException(status_code=404, detail="No OCEAN data found for this user")


    