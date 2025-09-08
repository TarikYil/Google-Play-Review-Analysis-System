from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from modules.data_collector import GooglePlayCollector
from modules.preprocessor import ReviewPreprocessor
from modules.sentiment_analyzer import SentimentAnalyzer
from modules.fake_detector import FakeReviewDetector
from modules.interesting_detector import InterestingReviewDetector

router = APIRouter()

class AnalysisRequest(BaseModel):
    app_id: str
    app_name: Optional[str] = None
    country: str = "tr"
    language: str = "tr"
    count: int = 1000
    sort: str = "newest"

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str

class AnalysisResult(BaseModel):
    job_id: str
    status: str
    app_info: Dict[str, Any]
    total_reviews: int
    processed_reviews: int
    sentiment_distribution: Dict[str, int]
    fake_reviews_count: int
    interesting_reviews_count: int
    processing_time: float
    created_at: str
    completed_at: Optional[str] = None

@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Google Play uygulaması için yorum analizi başlat"""
    
    # Unique job ID oluştur
    job_id = f"analysis_{request.app_id}_{int(datetime.now().timestamp())}"
    
    # Background task olarak analizi başlat
    background_tasks.add_task(run_analysis, job_id, request)
    
    return AnalysisResponse(
        job_id=job_id,
        status="started",
        message=f"Analysis started for app {request.app_id}"
    )

@router.get("/analyze/{job_id}", response_model=AnalysisResult)
async def get_analysis_result(job_id: str):
    """Analiz sonucunu getir"""
    
    # Shared data path inside container
    result_file = f"/app/shared_data/results_{job_id}.json"
    print(f"DEBUG: Jobid file: {job_id}")
    print(f"DEBUG: Result file: {result_file}")
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        return AnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading analysis result: {str(e)}")

@router.get("/jobs")
async def list_analysis_jobs():
    """Tüm analiz işlerini listele"""
    
    shared_data_dir = "/app/shared_data"
    if not os.path.exists(shared_data_dir):
        return {"jobs": []}
    
    jobs = []
    for filename in os.listdir(shared_data_dir):
        if filename.startswith("results_") and filename.endswith(".json"):
            job_id = filename.replace("results_", "").replace(".json", "")
            try:
                with open(os.path.join(shared_data_dir, filename), 'r', encoding='utf-8') as f:
                    result = json.load(f)
                jobs.append({
                    "job_id": job_id,
                    "status": result.get("status", "unknown"),
                    "app_id": result.get("app_info", {}).get("appId", "unknown"),
                    "created_at": result.get("created_at"),
                    "completed_at": result.get("completed_at")
                })
            except:
                continue
    
    return {"jobs": jobs}

async def run_analysis(job_id: str, request: AnalysisRequest):
    """Analiz işlemini çalıştır"""
    
    start_time = datetime.now()
    result_file = f"/app/shared_data/results_{job_id}.json"
    
    # İlk durum kaydet
    initial_result = {
        "job_id": job_id,
        "status": "running",
        "app_info": {"appId": request.app_id, "title": request.app_name or "Unknown"},
        "total_reviews": 0,
        "processed_reviews": 0,
        "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
        "fake_reviews_count": 0,
        "interesting_reviews_count": 0,
        "processing_time": 0.0,
        "created_at": start_time.isoformat(),
        "completed_at": None
    }
    
    try:
        # Shared data klasörünü oluştur
        os.makedirs("/app/shared_data", exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(initial_result, f, ensure_ascii=False, indent=2, default=str)
        
        # 1. Veri Toplama
        print(f"DEBUG: Starting data collection for {request.app_id}")
        collector = GooglePlayCollector()
        try:
            reviews_data = await collector.collect_reviews(
                app_id=request.app_id,
                country=request.country,
                lang=request.language,
                count=request.count,
                sort=request.sort
            )
            print(f"DEBUG: Data collection successful, got {len(reviews_data.get('reviews', []))} reviews")
        except Exception as e:
            print(f"DEBUG: Data collection failed: {str(e)}")
            raise e
        
        if not reviews_data or "reviews" not in reviews_data:
            raise Exception("No reviews collected")
        
        reviews = reviews_data["reviews"]
        app_info = reviews_data["app_info"]
        
        # 2. Ön İşleme
        preprocessor = ReviewPreprocessor()
        processed_reviews = await preprocessor.preprocess_reviews(reviews)
        
        # 3. Duygu Analizi
        sentiment_analyzer = SentimentAnalyzer()
        sentiment_results = await sentiment_analyzer.analyze_reviews(processed_reviews)
        
        # 4. Sahte Yorum Tespiti
        fake_detector = FakeReviewDetector()
        fake_results = await fake_detector.detect_fake_reviews(processed_reviews)
        
        # 5. İlginç Yorum Tespiti
        interesting_detector = InterestingReviewDetector()
        interesting_results = await interesting_detector.detect_interesting_reviews(processed_reviews)
        
        # Sonuçları birleştir
        final_reviews = []
        sentiment_dist = {"positive": 0, "neutral": 0, "negative": 0}
        fake_count = 0
        interesting_count = 0
        
        for i, review in enumerate(processed_reviews):
            sentiment = sentiment_results[i] if i < len(sentiment_results) else "neutral"
            is_fake = fake_results[i] if i < len(fake_results) else False
            is_interesting = interesting_results[i] if i < len(interesting_results) else False
            
            sentiment_dist[sentiment] += 1
            if is_fake:
                fake_count += 1
            if is_interesting:
                interesting_count += 1
            
            final_reviews.append({
                **review,
                "sentiment": sentiment,
                "is_fake": is_fake,
                "is_interesting": is_interesting
            })
        
        # Sonuçları kaydet
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        final_result = {
            "job_id": job_id,
            "status": "completed",
            "app_info": app_info,
            "total_reviews": len(reviews),
            "processed_reviews": len(final_reviews),
            "sentiment_distribution": sentiment_dist,
            "fake_reviews_count": fake_count,
            "interesting_reviews_count": interesting_count,
            "processing_time": processing_time,
            "created_at": start_time.isoformat(),
            "completed_at": end_time.isoformat()
        }
        
        # Ana sonuç dosyasını kaydet
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)
        
        # Detaylı yorumları ayrı dosyaya kaydet
        reviews_file = f"/app/shared_data/reviews_{job_id}.json"
        with open(reviews_file, 'w', encoding='utf-8') as f:
            json.dump(final_reviews, f, ensure_ascii=False, indent=2, default=str)
        
    except Exception as e:
        # Hata durumunu kaydet
        print(f"DEBUG: Analysis failed with error: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        error_result = {
            **initial_result,
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "completed_at": datetime.now().isoformat()
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, ensure_ascii=False, indent=2, default=str)
