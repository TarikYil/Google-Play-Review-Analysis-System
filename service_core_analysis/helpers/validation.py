import re
from typing import Dict, Any, List, Optional

class ValidationHelper:
    """Doğrulama yardımcı sınıfı"""
    
    # Google Play app ID pattern'i
    APP_ID_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$')
    
    # Desteklenen ülke kodları (ISO 3166-1 alpha-2)
    SUPPORTED_COUNTRIES = {
        'tr', 'us', 'gb', 'de', 'fr', 'es', 'it', 'ru', 'jp', 'kr', 'cn',
        'in', 'br', 'mx', 'ca', 'au', 'nl', 'se', 'no', 'dk', 'fi', 'pl'
    }
    
    # Desteklenen dil kodları (ISO 639-1)
    SUPPORTED_LANGUAGES = {
        'tr', 'en', 'de', 'fr', 'es', 'it', 'ru', 'ja', 'ko', 'zh',
        'hi', 'pt', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'ar'
    }
    
    # Desteklenen sıralama seçenekleri
    SUPPORTED_SORT_OPTIONS = {'newest', 'oldest', 'most_relevant', 'rating'}
    
    @classmethod
    def validate_app_id(cls, app_id: str) -> Dict[str, Any]:
        """Google Play app ID'sini doğrula"""
        
        if not app_id:
            return {"valid": False, "error": "App ID is required"}
        
        if not isinstance(app_id, str):
            return {"valid": False, "error": "App ID must be a string"}
        
        if len(app_id) < 3:
            return {"valid": False, "error": "App ID is too short"}
        
        if len(app_id) > 100:
            return {"valid": False, "error": "App ID is too long"}
        
        if not cls.APP_ID_PATTERN.match(app_id):
            return {"valid": False, "error": "Invalid App ID format. Should be like com.example.app"}
        
        return {"valid": True, "error": None}
    
    @classmethod
    def validate_country(cls, country: str) -> Dict[str, Any]:
        """Ülke kodunu doğrula"""
        
        if not country:
            return {"valid": False, "error": "Country code is required"}
        
        if not isinstance(country, str):
            return {"valid": False, "error": "Country code must be a string"}
        
        country = country.lower()
        
        if country not in cls.SUPPORTED_COUNTRIES:
            return {
                "valid": False, 
                "error": f"Unsupported country code. Supported: {', '.join(sorted(cls.SUPPORTED_COUNTRIES))}"
            }
        
        return {"valid": True, "error": None}
    
    @classmethod
    def validate_language(cls, language: str) -> Dict[str, Any]:
        """Dil kodunu doğrula"""
        
        if not language:
            return {"valid": False, "error": "Language code is required"}
        
        if not isinstance(language, str):
            return {"valid": False, "error": "Language code must be a string"}
        
        language = language.lower()
        
        if language not in cls.SUPPORTED_LANGUAGES:
            return {
                "valid": False, 
                "error": f"Unsupported language code. Supported: {', '.join(sorted(cls.SUPPORTED_LANGUAGES))}"
            }
        
        return {"valid": True, "error": None}
    
    @classmethod
    def validate_count(cls, count: int) -> Dict[str, Any]:
        """Yorum sayısını doğrula"""
        
        if not isinstance(count, int):
            return {"valid": False, "error": "Count must be an integer"}
        
        if count < 1:
            return {"valid": False, "error": "Count must be at least 1"}
        
        if count > 10000:
            return {"valid": False, "error": "Count cannot exceed 10000"}
        
        return {"valid": True, "error": None}
    
    @classmethod
    def validate_sort(cls, sort: str) -> Dict[str, Any]:
        """Sıralama seçeneğini doğrula"""
        
        if not sort:
            return {"valid": False, "error": "Sort option is required"}
        
        if not isinstance(sort, str):
            return {"valid": False, "error": "Sort option must be a string"}
        
        sort = sort.lower()
        
        if sort not in cls.SUPPORTED_SORT_OPTIONS:
            return {
                "valid": False, 
                "error": f"Invalid sort option. Supported: {', '.join(cls.SUPPORTED_SORT_OPTIONS)}"
            }
        
        return {"valid": True, "error": None}
    
    @classmethod
    def validate_analysis_request(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiz isteğini doğrula"""
        
        errors = []
        
        # App ID kontrolü
        app_id_validation = cls.validate_app_id(request_data.get("app_id"))
        if not app_id_validation["valid"]:
            errors.append(f"app_id: {app_id_validation['error']}")
        
        # Country kontrolü
        country = request_data.get("country", "tr")
        country_validation = cls.validate_country(country)
        if not country_validation["valid"]:
            errors.append(f"country: {country_validation['error']}")
        
        # Language kontrolü
        language = request_data.get("language", "tr")
        language_validation = cls.validate_language(language)
        if not language_validation["valid"]:
            errors.append(f"language: {language_validation['error']}")
        
        # Count kontrolü
        count = request_data.get("count", 1000)
        count_validation = cls.validate_count(count)
        if not count_validation["valid"]:
            errors.append(f"count: {count_validation['error']}")
        
        # Sort kontrolü
        sort = request_data.get("sort", "newest")
        sort_validation = cls.validate_sort(sort)
        if not sort_validation["valid"]:
            errors.append(f"sort: {sort_validation['error']}")
        
        if errors:
            return {"valid": False, "errors": errors}
        
        return {"valid": True, "errors": []}
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Dosya adını güvenli hale getir"""
        
        # Güvenli olmayan karakterleri temizle
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Çok uzun dosya adlarını kısalt
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:96] + ext
        
        return filename
    
    @classmethod
    def validate_job_id(cls, job_id: str) -> Dict[str, Any]:
        """Job ID'sini doğrula"""
        
        if not job_id:
            return {"valid": False, "error": "Job ID is required"}
        
        if not isinstance(job_id, str):
            return {"valid": False, "error": "Job ID must be a string"}
        
        # Job ID pattern kontrolü
        job_id_pattern = re.compile(r'^analysis_[a-zA-Z0-9._-]+_\d+$')
        if not job_id_pattern.match(job_id):
            return {"valid": False, "error": "Invalid Job ID format"}
        
        return {"valid": True, "error": None}
