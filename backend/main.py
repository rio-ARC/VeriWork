"""
VeriWork - FastAPI Backend
Evidence-Backed Claim Verification Engine
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router as api_router

app = FastAPI(
    title="VeriWork",
    description="Evidence-Backed Claim Verification Engine - This system doesn't measure activity. It verifies truth.",
    version="1.0.0"
)

# CORS for API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from analysis.gemini_client import is_gemini_configured
    
    return {
        "status": "healthy",
        "gemini_api_configured": is_gemini_configured()
    }


# Serve frontend static files
# Check if frontend directory exists (in deployment, it's copied to /app/static)
STATIC_DIR = Path(__file__).parent / "static"
if not STATIC_DIR.exists():
    # Development: frontend is in sibling directory
    STATIC_DIR = Path(__file__).parent.parent / "frontend"

if STATIC_DIR.exists():
    # Mount static files (CSS, JS)
    app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")
    
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend index.html"""
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        """Root endpoint - API info (when no frontend available)"""
        return {
            "name": "VeriWork API",
            "version": "1.0.0",
            "status": "operational",
            "tagline": "This system doesn't measure activity. It verifies truth.",
            "docs": "/docs"
        }
