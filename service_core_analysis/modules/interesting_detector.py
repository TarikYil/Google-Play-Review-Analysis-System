from typing import List, Dict, Any
import re
import asyncio
from collections import Counter

class InterestingReviewDetector:
    """İlginç yorum tespit sınıfı"""
    
    def __init__(self):
        # Mizahi ifadeler
        self.humor_patterns = [
            r'😂|😄|😆|🤣|😁',  # Gülen emojiler
            r'haha|ahaha|lol|:D|xD',  # Gülme ifadeleri
            r'komik|eğlenceli|gülmek|kahkaha',  # Mizah kelimeleri
        ]
        
        # Yaratıcı ifadeler
        self.creative_keywords = {
            'tr': [
                'hayal', 'yaratıcı', 'özgün', 'farklı', 'yenilikçi', 'orijinal',
                'tasarım', 'sanat', 'estetik', 'görsel', 'hikaye', 'karakter'
            ],
            'en': [
                'creative', 'innovative', 'original', 'unique', 'artistic', 'design',
                'aesthetic', 'visual', 'story', 'character', 'imagination'
            ]
        }
        
        # Yapıcı eleştiri kelimeleri
        self.constructive_keywords = {
            'tr': [
                'öneri', 'tavsiye', 'geliştirilmeli', 'eklenmeli', 'özellik',
                'güncelleme', 'iyileştirme', 'geliştirici', 'feedback', 'daha iyi'
            ],
            'en': [
                'suggestion', 'recommend', 'improve', 'feature', 'update',
                'enhancement', 'developer', 'feedback', 'better', 'should add'
            ]
        }
        
        # Detaylı analiz kelimeleri
        self.detailed_keywords = [
            'çünkü', 'nedeni', 'sebep', 'because', 'reason', 'why', 'how',
            'nasıl', 'neden', 'örneğin', 'mesela', 'for example', 'such as'
        ]
        
        # Duygusal ifadeler
        self.emotional_patterns = [
            r'[!]{2,}',  # Çoklu ünlem
            r'[?]{2,}',  # Çoklu soru
            r'[A-Z]{3,}',  # Büyük harfli kelimeler
            r'❤️|💕|💖|😍|🥰',  # Aşk emojileri
            r'😢|😭|💔|😞|😔',  # Üzgün emojiler
        ]
    
    async def detect_interesting_reviews(self, reviews: List[Dict[str, Any]]) -> List[bool]:
        """
        İlginç yorumları tespit et
        
        Args:
            reviews: İşlenmiş yorum listesi
            
        Returns:
            List[bool]: Her yorum için ilginç olup olmadığı
        """
        
        interesting_flags = []
        
        for review in reviews:
            try:
                is_interesting = await self._analyze_single_review(review)
                interesting_flags.append(is_interesting)
            except Exception as e:
                print(f"Error detecting interesting review {review.get('reviewId', 'unknown')}: {e}")
                interesting_flags.append(False)
        
        return interesting_flags
    
    async def _analyze_single_review(self, review: Dict[str, Any]) -> bool:
        """Tek bir yorumu analiz et"""
        
        content = review.get("cleaned_content", "")
        original_content = review.get("original_content", "")
        
        if not content or len(content) < 20:  # Çok kısa yorumlar ilginç değil
            return False
        
        interest_score = 0
        max_score = 15
        
        # 1. Uzunluk analizi - detaylı yorumlar daha ilginç
        length_score = self._calculate_length_score(content)
        interest_score += length_score
        
        # 2. Mizah tespiti
        humor_score = self._detect_humor(original_content)
        interest_score += humor_score
        
        # 3. Yaratıcılık tespiti
        creativity_score = self._detect_creativity(content, review)
        interest_score += creativity_score
        
        # 4. Yapıcı eleştiri tespiti
        constructive_score = self._detect_constructive_feedback(content, review)
        interest_score += constructive_score
        
        # 5. Duygusal yoğunluk
        emotional_score = self._detect_emotional_intensity(original_content)
        interest_score += emotional_score
        
        # 6. Detaylı analiz
        detail_score = self._detect_detailed_analysis(content)
        interest_score += detail_score
        
        # 7. Benzersizlik (kelime çeşitliliği)
        uniqueness_score = self._calculate_uniqueness(content)
        interest_score += uniqueness_score
        
        # 8. Etkileşim potansiyeli (thumbs up vs ortalama)
        engagement_score = self._calculate_engagement_score(review)
        interest_score += engagement_score
        
        # İlginçlik eşiği
        return interest_score >= (max_score * 0.5)  # %50 eşiği
    
    def _calculate_length_score(self, content: str) -> int:
        """Uzunluk tabanlı skor hesapla"""
        
        word_count = len(content.split())
        
        if word_count >= 50:  # Çok detaylı
            return 3
        elif word_count >= 25:  # Orta detaylı
            return 2
        elif word_count >= 15:  # Az detaylı
            return 1
        else:
            return 0
    
    def _detect_humor(self, content: str) -> int:
        """Mizah tespiti"""
        
        humor_score = 0
        content_lower = content.lower()
        
        for pattern in self.humor_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                humor_score += 2
        
        # Mizahi kelimeler
        humor_words = ['komik', 'gülmek', 'eğlenceli', 'funny', 'hilarious', 'amusing']
        for word in humor_words:
            if word in content_lower:
                humor_score += 1
        
        return min(humor_score, 4)  # Max 4 puan
    
    def _detect_creativity(self, content: str, review: Dict[str, Any]) -> int:
        """Yaratıcılık tespiti"""
        
        creativity_score = 0
        content_lower = content.lower()
        detected_lang = review.get("detected_language", "tr")
        
        creative_words = self.creative_keywords.get(detected_lang, self.creative_keywords['tr'])
        
        for word in creative_words:
            if word in content_lower:
                creativity_score += 1
        
        # Metafor ve benzetmeler
        metaphor_patterns = ['gibi', 'benzer', 'sanki', 'like', 'as if', 'similar']
        for pattern in metaphor_patterns:
            if pattern in content_lower:
                creativity_score += 1
        
        return min(creativity_score, 3)  # Max 3 puan
    
    def _detect_constructive_feedback(self, content: str, review: Dict[str, Any]) -> int:
        """Yapıcı eleştiri tespiti"""
        
        constructive_score = 0
        content_lower = content.lower()
        detected_lang = review.get("detected_language", "tr")
        
        constructive_words = self.constructive_keywords.get(detected_lang, self.constructive_keywords['tr'])
        
        for word in constructive_words:
            if word in content_lower:
                constructive_score += 1
        
        # Çözüm önerileri
        solution_patterns = ['şöyle olsa', 'böyle yapılsa', 'eklenirse', 'if you add', 'should be']
        for pattern in solution_patterns:
            if pattern in content_lower:
                constructive_score += 2
        
        return min(constructive_score, 4)  # Max 4 puan
    
    def _detect_emotional_intensity(self, content: str) -> int:
        """Duygusal yoğunluk tespiti"""
        
        emotional_score = 0
        
        for pattern in self.emotional_patterns:
            matches = re.findall(pattern, content)
            emotional_score += len(matches)
        
        # Çok fazla duygusal ifade de spam olabilir
        return min(emotional_score, 2)  # Max 2 puan
    
    def _detect_detailed_analysis(self, content: str) -> int:
        """Detaylı analiz tespiti"""
        
        detail_score = 0
        content_lower = content.lower()
        
        for keyword in self.detailed_keywords:
            if keyword in content_lower:
                detail_score += 1
        
        # Sayısal veriler
        number_pattern = r'\d+\.\d+|\d+%|\d+/\d+|\d+ (gün|saat|dakika|day|hour|minute)'
        if re.search(number_pattern, content):
            detail_score += 1
        
        # Karşılaştırmalar
        comparison_words = ['daha', 'en', 'better', 'worse', 'best', 'worst', 'versus', 'compared']
        for word in comparison_words:
            if word in content_lower:
                detail_score += 1
                break
        
        return min(detail_score, 3)  # Max 3 puan
    
    def _calculate_uniqueness(self, content: str) -> int:
        """Benzersizlik skoru hesapla"""
        
        words = content.lower().split()
        if len(words) < 10:
            return 0
        
        # Kelime çeşitliliği oranı
        unique_words = len(set(words))
        diversity_ratio = unique_words / len(words)
        
        if diversity_ratio > 0.8:
            return 2
        elif diversity_ratio > 0.6:
            return 1
        else:
            return 0
    
    def _calculate_engagement_score(self, review: Dict[str, Any]) -> int:
        """Etkileşim skoru hesapla"""
        
        thumbs_up = review.get("thumbsUpCount", 0)
        
        # Basit eşikler (gerçek uygulamada ortalama ile karşılaştırılabilir)
        if thumbs_up >= 10:
            return 2
        elif thumbs_up >= 5:
            return 1
        else:
            return 0
    
    async def get_interesting_statistics(self, interesting_flags: List[bool]) -> Dict[str, Any]:
        """İlginç yorum istatistiklerini hesapla"""
        
        total = len(interesting_flags)
        if total == 0:
            return {
                "total_reviews": 0,
                "interesting_reviews": 0,
                "boring_reviews": 0,
                "interesting_ratio": 0.0
            }
        
        interesting_count = sum(interesting_flags)
        boring_count = total - interesting_count
        
        return {
            "total_reviews": total,
            "interesting_reviews": interesting_count,
            "boring_reviews": boring_count,
            "interesting_ratio": interesting_count / total
        }
    
    async def categorize_interesting_reviews(
        self, 
        reviews: List[Dict[str, Any]], 
        interesting_flags: List[bool]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """İlginç yorumları kategorilere ayır"""
        
        categories = {
            "humorous": [],
            "creative": [],
            "constructive": [],
            "detailed": [],
            "emotional": []
        }
        
        for i, (review, is_interesting) in enumerate(zip(reviews, interesting_flags)):
            if not is_interesting:
                continue
            
            content = review.get("cleaned_content", "")
            original_content = review.get("original_content", "")
            
            # Her kategori için ayrı kontrol
            if self._detect_humor(original_content) > 0:
                categories["humorous"].append(review)
            
            if self._detect_creativity(content, review) > 0:
                categories["creative"].append(review)
            
            if self._detect_constructive_feedback(content, review) > 0:
                categories["constructive"].append(review)
            
            if self._detect_detailed_analysis(content) > 0:
                categories["detailed"].append(review)
            
            if self._detect_emotional_intensity(original_content) > 0:
                categories["emotional"].append(review)
        
        return categories
