import json
import os
from typing import Any, Dict, List
from datetime import datetime
import aiofiles

class FileUtils:
    """Dosya işlemleri yardımcı sınıfı"""
    
    @staticmethod
    async def save_json(data: Any, file_path: str) -> bool:
        """JSON dosyasını asenkron olarak kaydet"""
        try:
            # Klasör yoksa oluştur
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
            return True
        except Exception as e:
            print(f"Error saving JSON to {file_path}: {e}")
            return False
    
    @staticmethod
    async def load_json(file_path: str) -> Any:
        """JSON dosyasını asenkron olarak yükle"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            print(f"Error loading JSON from {file_path}: {e}")
            return None
    
    @staticmethod
    def ensure_directory(directory_path: str) -> bool:
        """Klasörün var olduğundan emin ol"""
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Dosya boyutunu al"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Dosyanın var olup olmadığını kontrol et"""
        return os.path.exists(file_path)
    
    @staticmethod
    def generate_filename(prefix: str, job_id: str, extension: str = "json") -> str:
        """Dosya adı oluştur"""
        return f"{prefix}_{job_id}.{extension}"
    
    @staticmethod
    async def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
        """Eski dosyaları temizle"""
        if not os.path.exists(directory):
            return 0
        
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
        except Exception as e:
            print(f"Error cleaning up old files: {e}")
        
        return cleaned_count
