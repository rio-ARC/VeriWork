"""
Contribution Truth - FastAPI Backend
Evidence-Backed Claim Verification Engine
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router

app = FastAPI(
    title="Contribution Truth",
    description="Evidence-Backed Claim Verification Engine - This system doesn't measure activity. It verifies truth.",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Contribution Truth API",
        "version": "0.1.0",
        "status": "operational",
        "tagline": "This system doesn't measure activity. It verifies truth."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from analysis.gemini_client import is_gemini_configured
    
    return {
        "status": "healthy",
        "gemini_api_configured": is_gemini_configured()
    }
