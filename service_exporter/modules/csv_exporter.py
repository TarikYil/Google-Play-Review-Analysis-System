import pandas as pd
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

class CSVExporter:
    """CSV export sınıfı"""
    
    def __init__(self):
        self.default_fields = [
            "reviewId", "userName", "content", "score", "thumbsUpCount",
            "at", "sentiment", "is_fake", "is_interesting", "detected_language",
            "text_length", "word_count", "has_emojis", "emoji_count"
        ]
    
    async def export_to_csv(
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
        Analiz sonuçlarını CSV formatında export et
        
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
        
        # DataFrame oluştur
        df = self._create_dataframe(filtered_reviews, export_fields, analysis_results)
        
        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reviews_{job_id}_{timestamp}.csv"
        file_path = os.path.join(export_dir, filename)
        
        # CSV'ye kaydet
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # Excel uyumluluğu için utf-8-sig
        
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
    
    def _create_dataframe(
        self, 
        reviews: List[Dict[str, Any]], 
        fields: List[str], 
        analysis_results: Dict[str, Any]
    ) -> pd.DataFrame:
        """DataFrame oluştur"""
        
        # Sadece belirtilen alanları al
        filtered_data = []
        
        for review in reviews:
            row = {}
            for field in fields:
                if field in review:
                    value = review[field]
                    # Tarih formatını düzenle
                    if field == "at" and value:
                        try:
                            # ISO formatını daha okunabilir hale getir
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            row[field] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            row[field] = value
                    else:
                        row[field] = value
                else:
                    row[field] = None
            
            filtered_data.append(row)
        
        df = pd.DataFrame(filtered_data)
        
        # Sütun sırasını düzenle
        ordered_columns = []
        for field in fields:
            if field in df.columns:
                ordered_columns.append(field)
        
        df = df[ordered_columns]
        
        # Veri tiplerini optimize et
        df = self._optimize_datatypes(df)
        
        return df
    
    def _optimize_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame veri tiplerini optimize et"""
        
        # Boolean alanları
        boolean_fields = ["is_fake", "is_interesting", "has_emojis", "has_urls", "has_mentions", "has_hashtags"]
        for field in boolean_fields:
            if field in df.columns:
                df[field] = df[field].astype(bool)
        
        # Integer alanları
        int_fields = ["score", "thumbsUpCount", "text_length", "word_count", "emoji_count", "url_count"]
        for field in int_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0).astype(int)
        
        # Float alanları
        float_fields = ["uppercase_ratio", "punctuation_ratio", "digit_ratio", "avg_word_length"]
        for field in float_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0.0).astype(float)
        
        # String alanları için NaN'ları boş string yap
        string_fields = ["reviewId", "userName", "content", "sentiment", "detected_language"]
        for field in string_fields:
            if field in df.columns:
                df[field] = df[field].fillna("")
        
        return df
    
    async def export_summary_csv(
        self,
        job_id: str,
        analysis_results: Dict[str, Any],
        export_dir: str
    ) -> str:
        """Özet istatistikleri CSV olarak export et"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{job_id}_{timestamp}.csv"
        file_path = os.path.join(export_dir, filename)
        
        # Özet verileri hazırla
        summary_data = [
            {"Metric": "Total Reviews", "Value": analysis_results.get("total_reviews", 0)},
            {"Metric": "Processed Reviews", "Value": analysis_results.get("processed_reviews", 0)},
            {"Metric": "Positive Reviews", "Value": analysis_results.get("sentiment_distribution", {}).get("positive", 0)},
            {"Metric": "Neutral Reviews", "Value": analysis_results.get("sentiment_distribution", {}).get("neutral", 0)},
            {"Metric": "Negative Reviews", "Value": analysis_results.get("sentiment_distribution", {}).get("negative", 0)},
            {"Metric": "Fake Reviews", "Value": analysis_results.get("fake_reviews_count", 0)},
            {"Metric": "Interesting Reviews", "Value": analysis_results.get("interesting_reviews_count", 0)},
            {"Metric": "Processing Time (seconds)", "Value": analysis_results.get("processing_time", 0)},
            {"Metric": "Analysis Date", "Value": analysis_results.get("created_at", "")},
            {"Metric": "App ID", "Value": analysis_results.get("app_info", {}).get("appId", "")},
            {"Metric": "App Title", "Value": analysis_results.get("app_info", {}).get("title", "")},
            {"Metric": "App Rating", "Value": analysis_results.get("app_info", {}).get("score", "")},
            {"Metric": "App Installs", "Value": analysis_results.get("app_info", {}).get("installs", "")},
        ]
        
        df = pd.DataFrame(summary_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path
