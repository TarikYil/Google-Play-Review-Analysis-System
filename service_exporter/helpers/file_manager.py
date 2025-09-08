import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

class FileManager:
    """Dosya yönetimi yardımcı sınıfı"""
    
    def __init__(self, base_directory: str):
        self.base_directory = base_directory
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        """Base klasörün var olduğundan emin ol"""
        os.makedirs(self.base_directory, exist_ok=True)
    
    def get_file_size(self, file_path: str) -> int:
        """Dosya boyutunu al"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except:
            return 0
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Dosya bilgilerini al"""
        file_path = os.path.join(self.base_directory, filename)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            file_stats = os.stat(file_path)
            return {
                "filename": filename,
                "full_path": file_path,
                "size": file_stats.st_size,
                "created_at": datetime.fromtimestamp(file_stats.st_ctime),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime),
                "is_file": os.path.isfile(file_path),
                "extension": os.path.splitext(filename)[1].lower()
            }
        except Exception as e:
            print(f"Error getting file info for {filename}: {e}")
            return None
    
    def list_files(self, extension_filter: str = None) -> List[Dict[str, Any]]:
        """Klasördeki dosyaları listele"""
        files = []
        
        try:
            for filename in os.listdir(self.base_directory):
                file_info = self.get_file_info(filename)
                if file_info and file_info["is_file"]:
                    if extension_filter is None or file_info["extension"] == extension_filter:
                        files.append(file_info)
        except Exception as e:
            print(f"Error listing files: {e}")
        
        # Dosyaları tarihe göre sırala (en yeni önce)
        files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return files
    
    async def cleanup_old_files(self, max_age_days: int = 7) -> int:
        """Eski dosyaları temizle"""
        if not os.path.exists(self.base_directory):
            return 0
        
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        try:
            for filename in os.listdir(self.base_directory):
                file_path = os.path.join(self.base_directory, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"Removed old file: {filename}")
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        return cleaned_count
    
    def delete_file(self, filename: str) -> bool:
        """Dosyayı sil"""
        file_path = os.path.join(self.base_directory, filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            return False
    
    def get_directory_size(self) -> int:
        """Klasörün toplam boyutunu al"""
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(self.base_directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            print(f"Error calculating directory size: {e}")
        
        return total_size
    
    def get_directory_stats(self) -> Dict[str, Any]:
        """Klasör istatistiklerini al"""
        files = self.list_files()
        
        stats = {
            "total_files": len(files),
            "total_size": self.get_directory_size(),
            "file_types": {},
            "oldest_file": None,
            "newest_file": None,
            "average_file_size": 0
        }
        
        if files:
            # Dosya türlerini say
            for file_info in files:
                ext = file_info["extension"] or "no_extension"
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            
            # En eski ve en yeni dosya
            stats["oldest_file"] = min(files, key=lambda x: x["created_at"])["filename"]
            stats["newest_file"] = max(files, key=lambda x: x["created_at"])["filename"]
            
            # Ortalama dosya boyutu
            total_size = sum(f["size"] for f in files)
            stats["average_file_size"] = total_size / len(files)
        
        return stats
    
    def format_file_size(self, size_bytes: int) -> str:
        """Dosya boyutunu okunabilir formata çevir"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def archive_old_files(self, max_age_days: int = 30, archive_dir: str = "archive") -> int:
        """Eski dosyaları arşivle"""
        archive_path = os.path.join(self.base_directory, archive_dir)
        os.makedirs(archive_path, exist_ok=True)
        
        archived_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        try:
            for filename in os.listdir(self.base_directory):
                file_path = os.path.join(self.base_directory, filename)
                
                if os.path.isfile(file_path) and not file_path.startswith(archive_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_time:
                        archive_file_path = os.path.join(archive_path, filename)
                        os.rename(file_path, archive_file_path)
                        archived_count += 1
                        print(f"Archived old file: {filename}")
        
        except Exception as e:
            print(f"Error during archiving: {e}")
        
        return archived_count
