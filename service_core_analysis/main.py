from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from routes.analysis_routes import router as analysis_router
from routes.health_routes import router as health_router

app = FastAPI(
    title="Google Play Review Core Analysis Service",
    description="Google Play yorumlarını toplama, işleme ve analiz etme servisi",
    version="1.0.0"
)

# Routes'ları dahil et
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "service": "Google Play Review Core Analysis Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analysis": "/api/v1"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
