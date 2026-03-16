"""
ClauseGuard Legal AI - FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

from src.api.v1.endpoints.chat_router import router as chat_router
from src.api.v1.endpoints.upload_router import router as upload_router
from src.api.v1.endpoints.analyze_router import router as analyze_router

app = FastAPI(
    title="ClauseGuard Legal AI API",
    description="Intelligent contract analysis and risk assessment engine.",
    version="1.0.0"
)

# --- Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route Orchestration ---
app.include_router(chat_router,    prefix="/api/v1")
app.include_router(upload_router,  prefix="/api/v1")
app.include_router(analyze_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    """Service health check endpoint."""
    return {
        "status": "operational",
        "service": "ClauseGuard Legal AI API",
        "version": "v1.0.0"
    }