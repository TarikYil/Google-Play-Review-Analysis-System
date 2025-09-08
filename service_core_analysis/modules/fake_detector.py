from typing import List, Dict, Any, Set
import re
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import asyncio

class FakeReviewDetector:
    """Sahte yorum tespit sınıfı"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'^[A-Z\s!]{10,}$',  # Sadece büyük harf ve ünlem
            r'^(.)\1{5,}',       # Aynı karakterin tekrarı
            r'^\d+\s*\/\s*\d+',  # Sadece rating formatı
            r'^[^\w\s]{5,}',     # Sadece özel karakterler
        ]
        
        self.spam_keywords = {
            'tr': [
                'reklam', 'link', 'tıkla', 'indir', 'ücretsiz para', 
                'kazanç', 'bonus', 'hediye', 'çekiliş', 'kampanya',
                'telegram', 'whatsapp', 'instagram', 'takip et'
            ],
            'en': [
                'click here', 'free money', 'earn money', 'bonus', 'gift',
                'telegram', 'whatsapp', 'instagram', 'follow me', 'link'
            ]
        }
        
        self.generic_templates = [
            "good app", "nice app", "great app", "bad app", "not good",
            "iyi uygulama", "güzel uygulama", "kötü uygulama", "beğenmedim"
        ]
    
    async def detect_fake_reviews(self, reviews: List[Dict[str, Any]]) -> List[bool]:
        """
        Sahte yorumları tespit et
        
        Args:
            reviews: İşlenmiş yorum listesi
            
        Returns:
            List[bool]: Her yorum için sahte olup olmadığı
        """
        
        fake_flags = []
        
        # Benzerlik kontrolü için hash'ler
        content_hashes = {}
        user_review_counts = Counter()
        
        # İlk geçiş: temel istatistikleri topla
        for review in reviews:
            user_name = review.get("userName", "")
            content = review.get("cleaned_content", "")
            
            if user_name:
                user_review_counts[user_name] += 1
            
            if content:
                content_hash = hashlib.md5(content.encode()).hexdigest()
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(review.get("reviewId", ""))
        
        # İkinci geçiş: her yorumu analiz et
        for review in reviews:
            try:
                is_fake = await self._analyze_single_review(
                    review, content_hashes, user_review_counts
                )
                fake_flags.append(is_fake)
            except Exception as e:
                print(f"Error detecting fake review {review.get('reviewId', 'unknown')}: {e}")
                fake_flags.append(False)  # Şüphe durumunda sahte değil say
        
        return fake_flags
    
    async def _analyze_single_review(
        self, 
        review: Dict[str, Any], 
        content_hashes: Dict[str, List[str]], 
        user_review_counts: Counter
    ) -> bool:
        """Tek bir yorumu analiz et"""
        
        suspicious_score = 0
        max_score = 10  # Maksimum şüpheli puan
        
        content = review.get("cleaned_content", "")
        user_name = review.get("userName", "")
        score = review.get("score", 3)
        thumbs_up = review.get("thumbsUpCount", 0)
        
        # 1. İçerik uzunluğu kontrolü
        if len(content) < 10:
            suspicious_score += 2
        elif len(content) > 1000:
            suspicious_score += 1
        
        # 2. Şüpheli pattern kontrolü
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content):
                suspicious_score += 2
                break
        
        # 3. Spam keyword kontrolü
        detected_lang = review.get("detected_language", "unknown")
        spam_words = self.spam_keywords.get(detected_lang, [])
        content_lower = content.lower()
        
        spam_count = sum(1 for word in spam_words if word in content_lower)
        if spam_count > 0:
            suspicious_score += min(spam_count * 2, 4)
        
        # 4. Generic template kontrolü
        for template in self.generic_templates:
            if template.lower() in content_lower:
                suspicious_score += 1
        
        # 5. Kullanıcı davranış analizi
        if user_name:
            user_review_count = user_review_counts.get(user_name, 1)
            if user_review_count > 10:  # Aynı kullanıcıdan çok fazla yorum
                suspicious_score += 2
        
        # 6. Rating vs içerik uyumsuzluğu
        sentiment_score = self._estimate_content_sentiment(content)
        rating_sentiment = self._rating_to_sentiment(score)
        
        if abs(sentiment_score - rating_sentiment) > 2:
            suspicious_score += 2
        
        # 7. Duplicate content kontrolü
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in content_hashes and len(content_hashes[content_hash]) > 1:
            suspicious_score += 3
        
        # 8. Metin özelliklerini kontrol et
        suspicious_score += self._check_text_features(review)
        
        # 9. Timing analizi (eğer tarih bilgisi varsa)
        suspicious_score += self._check_timing_patterns(review)
        
        # Şüpheli puan eşiğine göre karar ver
        return suspicious_score >= (max_score * 0.6)  # %60 eşiği
    
    def _estimate_content_sentiment(self, content: str) -> int:
        """İçerikten basit sentiment skoru çıkar (1-5)"""
        
        positive_words = ["good", "great", "excellent", "amazing", "perfect", 
                         "iyi", "harika", "mükemmel", "süper", "güzel"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst",
                         "kötü", "berbat", "çöp", "kullanılamaz", "sorun"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 4 + min(positive_count - negative_count, 1)
        elif negative_count > positive_count:
            return 2 - min(negative_count - positive_count, 1)
        else:
            return 3
    
    def _rating_to_sentiment(self, rating: int) -> int:
        """Rating'i sentiment skoruna çevir"""
        return max(1, min(5, rating))
    
    def _check_text_features(self, review: Dict[str, Any]) -> int:
        """Metin özelliklerini kontrol et"""
        
        suspicious_score = 0
        
        # Çok fazla büyük harf
        uppercase_ratio = review.get("uppercase_ratio", 0)
        if uppercase_ratio > 0.5:
            suspicious_score += 1
        
        # Çok fazla özel karakter
        special_char_ratio = review.get("special_char_ratio", 0)
        if special_char_ratio > 0.3:
            suspicious_score += 1
        
        # Çok fazla emoji
        emoji_count = review.get("emoji_count", 0)
        content_length = review.get("cleaned_length", 1)
        if emoji_count > 0 and (emoji_count / content_length) > 0.1:
            suspicious_score += 1
        
        # Çok fazla URL
        url_count = review.get("url_count", 0)
        if url_count > 2:
            suspicious_score += 2
        
        return min(suspicious_score, 3)  # Max 3 puan
    
    def _check_timing_patterns(self, review: Dict[str, Any]) -> int:
        """Zamanlama pattern'lerini kontrol et"""
        
        # Bu basit implementasyon
        # Gerçek uygulamada review tarihlerini analiz edebiliriz
        return 0
    
    async def get_fake_statistics(self, fake_flags: List[bool]) -> Dict[str, Any]:
        """Sahte yorum istatistiklerini hesapla"""
        
        total = len(fake_flags)
        if total == 0:
            return {
                "total_reviews": 0,
                "fake_reviews": 0,
                "genuine_reviews": 0,
                "fake_ratio": 0.0
            }
        
        fake_count = sum(fake_flags)
        genuine_count = total - fake_count
        
        return {
            "total_reviews": total,
            "fake_reviews": fake_count,
            "genuine_reviews": genuine_count,
            "fake_ratio": fake_count / total
        }
