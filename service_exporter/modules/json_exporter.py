import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

class JSONExporter:
    """JSON export sınıfı"""
    
    def __init__(self):
        self.default_fields = [
            "reviewId", "userName", "content", "score", "thumbsUpCount",
            "at", "sentiment", "is_fake", "is_interesting", "detected_language",
            "text_length", "word_count", "has_emojis", "emoji_count"
        ]
    
    async def export_to_json(
        self,
        job_id: str,
        shared_data_path: str,
        reviews_data_path: str,
        export_dir: str,
        include_fake: bool = True,
        include_interesting_only: bool = False,
        fields: Optional[List[str]] = None
    ) -> str:
        """
        Analiz sonuçlarını JSON formatında export et
        
        Args:
            job_id: İş ID'si
            shared_data_path: Ana sonuç dosyası yolu
            reviews_data_path: Detaylı yorumlar dosyası yolu
            export_dir: Export klasörü
            include_fake: Sahte yorumları dahil et
            include_interesting_only: Sadece ilginç yorumları dahil et
            fields: Export edilecek alanlar
            
        Returns:
            str: Export edilen dosyanın yolu
        """
        
        # Verileri yükle
        with open(shared_data_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        with open(reviews_data_path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        # Filtreleme
        filtered_reviews = self._filter_reviews(reviews, include_fake, include_interesting_only)
        
        if not filtered_reviews:
            raise Exception("No reviews to export after filtering")
        
        # Alanları seç
        export_fields = fields if fields else self.default_fields
        
        # Export verisini hazırla
        export_data = self._prepare_export_data(filtered_reviews, export_fields, analysis_results)
        
        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reviews_{job_id}_{timestamp}.json"
        file_path = os.path.join(export_dir, filename)
        
        # JSON'a kaydet
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        return file_path
    
    def _filter_reviews(
        self, 
        reviews: List[Dict[str, Any]], 
        include_fake: bool, 
        include_interesting_only: bool
    ) -> List[Dict[str, Any]]:
        """Yorumları filtrele"""
        
        filtered = []
        
        for review in reviews:
            # Sahte yorum kontrolü
            if not include_fake and review.get("is_fake", False):
                continue
            
            # Sadece ilginç yorumlar
            if include_interesting_only and not review.get("is_interesting", False):
                continue
            
            filtered.append(review)
        
        return filtered
    
    def _prepare_export_data(
        self, 
        reviews: List[Dict[str, Any]], 
        fields: List[str], 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export verisini hazırla"""
        
        # Sadece belirtilen alanları al
        filtered_reviews = []
        
        for review in reviews:
            filtered_review = {}
            for field in fields:
                if field in review:
                    filtered_review[field] = review[field]
            filtered_reviews.append(filtered_review)
        
        # İstatistikleri hesapla
        statistics = self._calculate_statistics(filtered_reviews)
        
        # Export verisini oluştur
        export_data = {
            "export_info": {
                "job_id": analysis_results.get("job_id"),
                "export_timestamp": datetime.now().isoformat(),
                "total_reviews_in_export": len(filtered_reviews),
                "original_total_reviews": analysis_results.get("total_reviews", 0),
                "fields_included": fields,
                "filters_applied": {
                    "include_fake": True,  # Bu bilgi route'dan gelmiyor, varsayılan
                    "include_interesting_only": False
                }
            },
            "app_info": analysis_results.get("app_info", {}),
            "analysis_summary": {
                "processing_time": analysis_results.get("processing_time", 0),
                "created_at": analysis_results.get("created_at"),
                "completed_at": analysis_results.get("completed_at"),
                "status": analysis_results.get("status")
            },
            "statistics": statistics,
            "reviews": filtered_reviews
        }
        
        return export_data
    
    def _calculate_statistics(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Filtrelenmiş yorumlar için istatistik hesapla"""
        
        if not reviews:
            return {}
        
        stats = {
            "total_count": len(reviews),
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "fake_count": 0,
            "interesting_count": 0,
            "language_distribution": {},
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "average_rating": 0.0,
            "average_text_length": 0.0,
            "emoji_usage": 0
        }
        
        total_rating = 0
        total_length = 0
        
        for review in reviews:
            # Sentiment
            sentiment = review.get("sentiment", "neutral")
            if sentiment in stats["sentiment_distribution"]:
                stats["sentiment_distribution"][sentiment] += 1
            
            # Fake/Interesting
            if review.get("is_fake", False):
                stats["fake_count"] += 1
            if review.get("is_interesting", False):
                stats["interesting_count"] += 1
            
            # Language
            lang = review.get("detected_language", "unknown")
            stats["language_distribution"][lang] = stats["language_distribution"].get(lang, 0) + 1
            
            # Rating
            score = review.get("score", 0)
            if 1 <= score <= 5:
                stats["rating_distribution"][score] += 1
                total_rating += score
            
            # Text length
            text_length = review.get("text_length", 0)
            if text_length > 0:
                total_length += text_length
            
            # Emoji
            if review.get("has_emojis", False):
                stats["emoji_usage"] += 1
        
        # Ortalamalar
        if len(reviews) > 0:
            stats["average_rating"] = total_rating / len(reviews) if total_rating > 0 else 0.0
            stats["average_text_length"] = total_length / len(reviews) if total_length > 0 else 0.0
        
        # Yüzdeler
        stats["sentiment_percentages"] = {
            sentiment: (count / len(reviews)) * 100 
            for sentiment, count in stats["sentiment_distribution"].items()
        }
        
        stats["fake_percentage"] = (stats["fake_count"] / len(reviews)) * 100
        stats["interesting_percentage"] = (stats["interesting_count"] / len(reviews)) * 100
        stats["emoji_usage_percentage"] = (stats["emoji_usage"] / len(reviews)) * 100
        
        return stats
    
    async def export_compact_json(
        self,
        job_id: str,
        shared_data_path: str,
        reviews_data_path: str,
        export_dir: str,
        include_fake: bool = True,
        include_interesting_only: bool = False
    ) -> str:
        """Kompakt JSON export (sadece temel alanlar)"""
        
        compact_fields = ["reviewId", "content", "score", "sentiment", "is_fake", "is_interesting"]
        
        return await self.export_to_json(
            job_id=job_id,
            shared_data_path=shared_data_path,
            reviews_data_path=reviews_data_path,
            export_dir=export_dir,
            include_fake=include_fake,
            include_interesting_only=include_interesting_only,
            fields=compact_fields
        )
