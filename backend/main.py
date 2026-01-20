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
# Try multiple locations for frontend files
def find_static_dir():
    """Find the frontend static files directory"""
    possible_paths = [
        Path(__file__).parent / "static",           # Docker: copied to /app/static
        Path(__file__).parent.parent / "frontend",  # Local dev: sibling directory
        Path("/opt/render/project/src/frontend"),   # Render Python runtime
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "index.html").exists():
            return path
    
    return None


STATIC_DIR = find_static_dir()

if STATIC_DIR:
    # Mount static files (CSS, JS)
    if (STATIC_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")
    if (STATIC_DIR / "js").exists():
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
            "docs": "/docs",
            "health": "/health"
        }
