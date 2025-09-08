from google_play_scraper import app, reviews, reviews_all, Sort
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

class GooglePlayCollector:
    """Google Play Store'dan yorum toplama sınıfı"""
    
    def __init__(self):
        self.sort_options = {
            "newest": Sort.NEWEST,
            "oldest": Sort.NEWEST,  # OLDEST mevcut değil, NEWEST kullan
            "most_relevant": Sort.MOST_RELEVANT,
            "rating": Sort.MOST_RELEVANT  # RATING mevcut değil, MOST_RELEVANT kullan
        }
    
    async def collect_reviews(
        self,
        app_id: str,
        country: str = "tr",
        lang: str = "tr",
        count: int = 1000,
        sort: str = "newest"
    ) -> Dict[str, Any]:
        """
        Google Play Store'dan yorum topla
        
        Args:
            app_id: Uygulama ID'si (örn: com.whatsapp)
            country: Ülke kodu (tr, us, vb.)
            lang: Dil kodu (tr, en, vb.)
            count: Toplanacak yorum sayısı
            sort: Sıralama türü
            
        Returns:
            Dict: Uygulama bilgileri ve yorumlar
        """
        
        try:
            print(f"DEBUG: Getting app info for {app_id}")
            # Uygulama bilgilerini al
            app_info = app(app_id, lang=lang, country=country)
            print(f"DEBUG: App info received: {app_info.get('title', 'Unknown')}")
            
            # Yorumları al - reviews_all kullanarak tüm yorumları çek
            sort_option = self.sort_options.get(sort, Sort.NEWEST)
            print(f"DEBUG: Getting ALL reviews with sort={sort}, sort_option={sort_option}")
            
            if count >= 1000:  # Çok sayıda yorum isteniyorsa reviews_all kullan
                reviews_result = reviews_all(
                    app_id,
                    sleep_milliseconds=100,  # Rate limiting için
                    lang=lang,
                    country=country,
                    sort=sort_option
                )
                # Count kadar sınırla
                reviews_result = reviews_result[:count]
                continuation_token = None
            else:  # Az sayıda yorum için normal reviews fonksiyonu
                reviews_result, continuation_token = reviews(
                    app_id,
                    lang=lang,
                    country=country,
                    sort=sort_option,
                    count=count
                )
            
            print(f"DEBUG: Got {len(reviews_result)} reviews")
            
            # Yorumları işle
            processed_reviews = []
            for review in reviews_result:
                processed_review = {
                    "reviewId": review.get("reviewId"),
                    "userName": review.get("userName"),
                    "userImage": review.get("userImage"),
                    "content": review.get("content", ""),
                    "score": review.get("score", 0),
                    "thumbsUpCount": review.get("thumbsUpCount", 0),
                    "reviewCreatedVersion": review.get("reviewCreatedVersion"),
                    "at": review.get("at").isoformat() if review.get("at") and hasattr(review.get("at"), 'isoformat') else str(review.get("at")) if review.get("at") else None,
                    "replyContent": review.get("replyContent"),
                    "repliedAt": review.get("repliedAt").isoformat() if review.get("repliedAt") and hasattr(review.get("repliedAt"), 'isoformat') else str(review.get("repliedAt")) if review.get("repliedAt") else None,
                    "appVersion": review.get("appVersion")
                }
                processed_reviews.append(processed_review)
            
            return {
                "app_info": {
                    "appId": app_info.get("appId"),
                    "title": app_info.get("title"),
                    "description": app_info.get("description"),
                    "summary": app_info.get("summary"),
                    "installs": app_info.get("installs"),
                    "minInstalls": app_info.get("minInstalls"),
                    "maxInstalls": app_info.get("maxInstalls"),
                    "score": app_info.get("score"),
                    "ratings": app_info.get("ratings"),
                    "reviews": app_info.get("reviews"),
                    "histogram": app_info.get("histogram"),
                    "price": app_info.get("price"),
                    "free": app_info.get("free"),
                    "currency": app_info.get("currency"),
                    "developer": app_info.get("developer"),
                    "genre": app_info.get("genre"),
                    "genreId": app_info.get("genreId"),
                    "categories": app_info.get("categories"),
                    "icon": app_info.get("icon"),
                    "headerImage": app_info.get("headerImage"),
                    "screenshots": app_info.get("screenshots", []),
                    "video": app_info.get("video"),
                    "videoImage": app_info.get("videoImage"),
                    "contentRating": app_info.get("contentRating"),
                    "adSupported": app_info.get("adSupported"),
                    "released": app_info.get("released"),
                    "updated": str(app_info.get("updated")) if app_info.get("updated") else None,
                    "version": app_info.get("version"),
                    "recentChanges": app_info.get("recentChanges"),
                    "comments": app_info.get("comments", [])
                },
                "reviews": processed_reviews,
                "total_collected": len(processed_reviews),
                "collection_time": datetime.now().isoformat(),
                "continuation_token": continuation_token
            }
            
        except Exception as e:
            raise Exception(f"Error collecting reviews for {app_id}: {str(e)}")
    
    async def collect_more_reviews(
        self,
        app_id: str,
        continuation_token: str,
        country: str = "tr",
        lang: str = "tr",
        count: int = 1000
    ) -> List[Dict[str, Any]]:
        """Daha fazla yorum topla (continuation token ile)"""
        
        try:
            reviews_result, new_token = reviews(
                app_id,
                lang=lang,
                country=country,
                continuation_token=continuation_token,
                count=count
            )
            
            processed_reviews = []
            for review in reviews_result:
                processed_review = {
                    "reviewId": review.get("reviewId"),
                    "userName": review.get("userName"),
                    "userImage": review.get("userImage"),
                    "content": review.get("content", ""),
                    "score": review.get("score", 0),
                    "thumbsUpCount": review.get("thumbsUpCount", 0),
                    "reviewCreatedVersion": review.get("reviewCreatedVersion"),
                    "at": review.get("at").isoformat() if review.get("at") and hasattr(review.get("at"), 'isoformat') else str(review.get("at")) if review.get("at") else None,
                    "replyContent": review.get("replyContent"),
                    "repliedAt": review.get("repliedAt").isoformat() if review.get("repliedAt") and hasattr(review.get("repliedAt"), 'isoformat') else str(review.get("repliedAt")) if review.get("repliedAt") else None,
                    "appVersion": review.get("appVersion")
                }
                processed_reviews.append(processed_review)
            
            return {
                "reviews": processed_reviews,
                "continuation_token": new_token
            }
            
        except Exception as e:
            raise Exception(f"Error collecting more reviews: {str(e)}")
