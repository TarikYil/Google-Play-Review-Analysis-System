from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import os
from routes.export_routes import router as export_router
from routes.health_routes import router as health_router

app = FastAPI(
    title="Google Play Review Export Service",
    description="Analiz sonuçlarını CSV ve JSON formatında export etme servisi",
    version="1.0.0"
)

# Routes'ları dahil et
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(export_router, prefix="/api/v1", tags=["export"])

@app.get("/")
async def root():
    return {
        "service": "Google Play Review Export Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "export": "/api/v1"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
