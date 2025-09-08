from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

from modules.csv_exporter import CSVExporter
from modules.json_exporter import JSONExporter
from helpers.file_manager import FileManager

router = APIRouter()

class ExportRequest(BaseModel):
    job_id: str
    format: str = "csv"  # csv, json, both
    include_fake: bool = True
    include_interesting_only: bool = False
    fields: Optional[List[str]] = None

class ExportResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None

@router.post("/export", response_model=ExportResponse)
async def export_analysis_results(request: ExportRequest):
    """Analiz sonuçlarını export et"""
    
    try:
        # Analiz sonuçlarını kontrol et
        shared_data_path = f"../shared_data/results_{request.job_id}.json"
        reviews_data_path = f"../shared_data/reviews_{request.job_id}.json"
        
        if not os.path.exists(shared_data_path) or not os.path.exists(reviews_data_path):
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        # Export klasörünü oluştur
        export_dir = "../exports"
        os.makedirs(export_dir, exist_ok=True)
        
        file_manager = FileManager(export_dir)
        
        if request.format == "csv":
            exporter = CSVExporter()
            file_path = await exporter.export_to_csv(
                job_id=request.job_id,
                shared_data_path=shared_data_path,
                reviews_data_path=reviews_data_path,
                export_dir=export_dir,
                include_fake=request.include_fake,
                include_interesting_only=request.include_interesting_only,
                fields=request.fields
            )
        elif request.format == "json":
            exporter = JSONExporter()
            file_path = await exporter.export_to_json(
                job_id=request.job_id,
                shared_data_path=shared_data_path,
                reviews_data_path=reviews_data_path,
                export_dir=export_dir,
                include_fake=request.include_fake,
                include_interesting_only=request.include_interesting_only,
                fields=request.fields
            )
        elif request.format == "both":
            csv_exporter = CSVExporter()
            json_exporter = JSONExporter()
            
            csv_path = await csv_exporter.export_to_csv(
                job_id=request.job_id,
                shared_data_path=shared_data_path,
                reviews_data_path=reviews_data_path,
                export_dir=export_dir,
                include_fake=request.include_fake,
                include_interesting_only=request.include_interesting_only,
                fields=request.fields
            )
            
            json_path = await json_exporter.export_to_json(
                job_id=request.job_id,
                shared_data_path=shared_data_path,
                reviews_data_path=reviews_data_path,
                export_dir=export_dir,
                include_fake=request.include_fake,
                include_interesting_only=request.include_interesting_only,
                fields=request.fields
            )
            
            file_path = f"CSV: {csv_path}, JSON: {json_path}"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv', 'json', or 'both'")
        
        file_size = file_manager.get_file_size(file_path) if request.format != "both" else None
        
        return ExportResponse(
            success=True,
            message="Export completed successfully",
            file_path=file_path,
            file_size=file_size,
            download_url=f"/api/v1/download/{os.path.basename(file_path)}" if request.format != "both" else None
        )
        
    except Exception as e:
        print(f"DEBUG: Export failed with error: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Export edilen dosyayı indir"""
    
    file_path = f"/app/exports/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/list")
async def list_exported_files():
    """Export edilen dosyaları listele"""
    
    export_dir = "/app/exports"
    if not os.path.exists(export_dir):
        return {"files": []}
    
    files = []
    for filename in os.listdir(export_dir):
        file_path = os.path.join(export_dir, filename)
        if os.path.isfile(file_path):
            file_stats = os.stat(file_path)
            files.append({
                "filename": filename,
                "size": file_stats.st_size,
                "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "download_url": f"/api/v1/download/{filename}"
            })
    
    # Dosyaları tarihe göre sırala (en yeni önce)
    files.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"files": files}

@router.delete("/cleanup")
async def cleanup_old_files(max_age_days: int = Query(default=7, ge=1, le=30)):
    """Eski export dosyalarını temizle"""
    
    export_dir = "/app/exports"
    if not os.path.exists(export_dir):
        return {"message": "Export directory does not exist", "cleaned_count": 0}
    
    file_manager = FileManager(export_dir)
    cleaned_count = await file_manager.cleanup_old_files(max_age_days)
    
    return {
        "message": f"Cleanup completed. Removed {cleaned_count} files older than {max_age_days} days",
        "cleaned_count": cleaned_count
    }

@router.get("/formats")
async def get_export_formats():
    """Desteklenen export formatlarını listele"""
    
    return {
        "formats": [
            {
                "name": "csv",
                "description": "Comma-separated values format",
                "extension": ".csv",
                "mime_type": "text/csv"
            },
            {
                "name": "json",
                "description": "JavaScript Object Notation format",
                "extension": ".json",
                "mime_type": "application/json"
            },
            {
                "name": "both",
                "description": "Export both CSV and JSON formats",
                "extension": "multiple",
                "mime_type": "multiple"
            }
        ],
        "available_fields": [
            "reviewId", "userName", "content", "score", "thumbsUpCount",
            "at", "sentiment", "is_fake", "is_interesting", "detected_language",
            "text_length", "word_count", "has_emojis", "emoji_count"
        ]
    }
