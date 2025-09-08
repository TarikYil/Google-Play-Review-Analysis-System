from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import List, Dict, Any
import torch
import asyncio
from textblob import TextBlob
import re

class SentimentAnalyzer:
    """Duygu analizi sınıfı"""
    
    def __init__(self):
        self.model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.initialized = False
    
    async def _initialize_model(self):
        """Modeli yükle (lazy loading)"""
        if self.initialized:
            return
        
        try:
            # GPU varsa kullan, yoksa CPU
            device = 0 if torch.cuda.is_available() else -1
            
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=device,
                return_all_scores=False
            )
            
            self.initialized = True
            print(f"Sentiment model loaded on {'GPU' if device == 0 else 'CPU'}")
            
        except Exception as e:
            print(f"Error loading sentiment model: {e}")
            # Fallback olarak TextBlob kullan
            self.initialized = True
    
    async def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """
        Yorumların duygu analizini yap
        
        Args:
            reviews: İşlenmiş yorum listesi
            
        Returns:
            List[str]: Her yorum için duygu etiketi (positive, negative, neutral)
        """
        
        await self._initialize_model()
        
        sentiments = []
        
        for review in reviews:
            try:
                sentiment = await self._analyze_single_review(review)
                sentiments.append(sentiment)
            except Exception as e:
                print(f"Error analyzing sentiment for review {review.get('reviewId', 'unknown')}: {e}")
                sentiments.append("neutral")  # Default fallback
        
        return sentiments
    
    async def _analyze_single_review(self, review: Dict[str, Any]) -> str:
        """Tek bir yorumun duygu analizini yap"""
        
        content = review.get("cleaned_content", "")
        if not content or len(content) < 5:
            return "neutral"
        
        # Transformer model kullan
        if self.classifier:
            try:
                # Metni maksimum token limitine göre kes
                max_length = 512
                if len(content) > max_length:
                    content = content[:max_length]
                
                result = self.classifier(content)
                label = result[0]["label"].lower()
                
                # Label mapping (model'e göre değişebilir)
                if "positive" in label or "pos" in label or label == "label_2":
                    return "positive"
                elif "negative" in label or "neg" in label or label == "label_0":
                    return "negative"
                else:
                    return "neutral"
                    
            except Exception as e:
                print(f"Transformer model error: {e}, falling back to TextBlob")
        
        # Fallback: TextBlob kullan
        return self._textblob_sentiment(content)
    
    def _textblob_sentiment(self, text: str) -> str:
        """TextBlob ile basit duygu analizi"""
        
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            # Son çare: rating tabanlı tahmin
            return "neutral"
    
    async def get_sentiment_statistics(self, sentiments: List[str]) -> Dict[str, Any]:
        """Duygu istatistiklerini hesapla"""
        
        total = len(sentiments)
        if total == 0:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "neutral_ratio": 0.0
            }
        
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        neutral_count = sentiments.count("neutral")
        
        return {
            "total": total,
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "positive_ratio": positive_count / total,
            "negative_ratio": negative_count / total,
            "neutral_ratio": neutral_count / total
        }
    
    def _rule_based_sentiment(self, review: Dict[str, Any]) -> str:
        """Kural tabanlı duygu analizi (rating + keywords)"""
        
        score = review.get("score", 3)
        content = review.get("cleaned_content", "").lower()
        
        # Rating tabanlı ilk tahmin
        if score >= 4:
            base_sentiment = "positive"
        elif score <= 2:
            base_sentiment = "negative"
        else:
            base_sentiment = "neutral"
        
        # Anahtar kelimeler ile düzeltme
        positive_keywords = [
            "harika", "mükemmel", "süper", "güzel", "beğendim", "tavsiye",
            "başarılı", "kullanışlı", "pratik", "kolay", "hızlı", "kaliteli"
        ]
        
        negative_keywords = [
            "kötü", "berbat", "çöp", "kullanılamaz", "yavaş", "hatalı",
            "sorun", "problem", "bug", "çökme", "donma", "siliyorum"
        ]
        
        positive_score = sum(1 for word in positive_keywords if word in content)
        negative_score = sum(1 for word in negative_keywords if word in content)
        
        # Keyword skoruna göre düzeltme
        if positive_score > negative_score and positive_score > 0:
            return "positive"
        elif negative_score > positive_score and negative_score > 0:
            return "negative"
        else:
            return base_sentiment
