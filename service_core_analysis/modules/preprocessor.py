import re
import html
from typing import List, Dict, Any
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import asyncio

class ReviewPreprocessor:
    """Yorum ön işleme sınıfı"""
    
    def __init__(self):
        self.emoji_pattern = re.compile("["
                                      u"\U0001F600-\U0001F64F"  # emoticons
                                      u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                      u"\U0001F680-\U0001F6FF"  # transport & map
                                      u"\U0001F1E0-\U0001F1FF"  # flags
                                      "]+", flags=re.UNICODE)
        
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@[A-Za-z0-9_]+')
        self.hashtag_pattern = re.compile(r'#[A-Za-z0-9_]+')
    
    async def preprocess_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Yorumları ön işleme tabi tut
        
        Args:
            reviews: Ham yorum listesi
            
        Returns:
            List: İşlenmiş yorum listesi
        """
        
        processed_reviews = []
        seen_contents = set()  # Duplicate detection için
        
        for review in reviews:
            try:
                processed_review = await self._process_single_review(review)
                
                # Duplicate kontrolü
                content_hash = processed_review["cleaned_content"].lower().strip()
                if content_hash and content_hash not in seen_contents and len(content_hash) > 10:
                    seen_contents.add(content_hash)
                    processed_reviews.append(processed_review)
                    
            except Exception as e:
                # Hatalı yorumu atla ama log'la
                print(f"Error processing review {review.get('reviewId', 'unknown')}: {str(e)}")
                continue
        
        return processed_reviews
    
    async def _process_single_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir yorumu işle"""
        
        content = review.get("content", "")
        
        # HTML decode
        content = html.unescape(content)
        
        # Temizleme işlemleri
        cleaned_content = self._clean_text(content)
        
        # Dil tespiti
        detected_language = self._detect_language(cleaned_content)
        
        # Metin özellikleri
        text_features = self._extract_text_features(content, cleaned_content)
        
        # İşlenmiş yorumu döndür
        processed_review = {
            **review,  # Orijinal alanları koru
            "original_content": content,
            "cleaned_content": cleaned_content,
            "detected_language": detected_language,
            "text_length": len(content),
            "cleaned_length": len(cleaned_content),
            "word_count": len(cleaned_content.split()) if cleaned_content else 0,
            "has_emojis": bool(self.emoji_pattern.search(content)),
            "has_urls": bool(self.url_pattern.search(content)),
            "has_mentions": bool(self.mention_pattern.search(content)),
            "has_hashtags": bool(self.hashtag_pattern.search(content)),
            "emoji_count": len(self.emoji_pattern.findall(content)),
            "url_count": len(self.url_pattern.findall(content)),
            "mention_count": len(self.mention_pattern.findall(content)),
            "hashtag_count": len(self.hashtag_pattern.findall(content)),
            **text_features
        }
        
        return processed_review
    
    def _clean_text(self, text: str) -> str:
        """Metni temizle"""
        
        if not text:
            return ""
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text)
        
        # Başta ve sonda boşluk temizle
        text = text.strip()
        
        # Çok kısa metinleri filtrele
        if len(text) < 5:
            return ""
        
        return text
    
    def _detect_language(self, text: str) -> str:
        """Dil tespiti yap"""
        
        if not text or len(text) < 10:
            return "unknown"
        
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"
    
    def _extract_text_features(self, original: str, cleaned: str) -> Dict[str, Any]:
        """Metin özelliklerini çıkar"""
        
        features = {}
        
        if not cleaned:
            return {
                "uppercase_ratio": 0.0,
                "punctuation_ratio": 0.0,
                "digit_ratio": 0.0,
                "special_char_ratio": 0.0,
                "avg_word_length": 0.0,
                "sentence_count": 0,
                "exclamation_count": 0,
                "question_count": 0
            }
        
        # Büyük harf oranı
        features["uppercase_ratio"] = sum(1 for c in cleaned if c.isupper()) / len(cleaned)
        
        # Noktalama oranı
        punctuation_count = sum(1 for c in cleaned if not c.isalnum() and not c.isspace())
        features["punctuation_ratio"] = punctuation_count / len(cleaned)
        
        # Rakam oranı
        features["digit_ratio"] = sum(1 for c in cleaned if c.isdigit()) / len(cleaned)
        
        # Özel karakter oranı
        special_char_count = sum(1 for c in cleaned if not c.isalnum() and not c.isspace() and c not in ".,!?;:")
        features["special_char_ratio"] = special_char_count / len(cleaned)
        
        # Ortalama kelime uzunluğu
        words = cleaned.split()
        if words:
            features["avg_word_length"] = sum(len(word) for word in words) / len(words)
        else:
            features["avg_word_length"] = 0.0
        
        # Cümle sayısı
        features["sentence_count"] = len(re.split(r'[.!?]+', cleaned))
        
        # Ünlem ve soru işareti sayısı
        features["exclamation_count"] = original.count("!")
        features["question_count"] = original.count("?")
        
        return features
