"""
File management utilities
"""
import os
import asyncio
import mimetypes
from typing import List, Generator, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, downloads_dir: str):
        self.downloads_dir = Path(downloads_dir)
        self.supported_extensions = {
            # Documents
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
            # Videos
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            # Audio
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            # Others
            '.apk', '.exe', '.dmg', '.iso', '.torrent'
        }
    
    def ensure_downloads_dir(self) -> None:
        """Create downloads directory if it doesn't exist"""
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloads directory: {self.downloads_dir}")
    
    def get_all_files(self) -> List[Path]:
        """Get all supported files from downloads directory"""
        if not self.downloads_dir.exists():
            logger.warning(f"Downloads directory does not exist: {self.downloads_dir}")
            return []
        
        files = []
        skipped_empty = 0
        
        for file_path in self.downloads_dir.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.supported_extensions and
                not file_path.name.startswith('.')):
                
                try:
                    # Check file size and skip empty files
                    file_size = file_path.stat().st_size
                    if file_size == 0:
                        skipped_empty += 1
                        continue
                    
                    files.append(file_path)
                    
                except (OSError, IOError) as e:
                    logger.warning(f"Cannot access file {file_path.name}: {e}")
                    continue
        
        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x.stat().st_mtime)
        
        logger.info(f"Found {len(files)} files to process")
        if skipped_empty > 0:
            logger.info(f"Skipped {skipped_empty} empty files")
        
        return files
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get file information"""
        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': stat.st_mtime,
                'mime_type': mime_type or 'application/octet-stream',
                'extension': file_path.suffix.lower()
            }
        except (OSError, IOError) as e:
            logger.error(f"Cannot get file info for {file_path.name}: {e}")
            # Return a safe default
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': 0,
                'size_mb': 0.0,
                'modified': 0,
                'mime_type': 'application/octet-stream',
                'extension': file_path.suffix.lower()
            }
    
    def is_file_accessible(self, file_path: Path) -> bool:
        """Check if file is accessible and not being written to"""
        try:
            # Check if file exists and is readable
            if not file_path.exists() or not os.access(file_path, os.R_OK):
                return False
            
            # Check if file is empty
            if file_path.stat().st_size == 0:
                return False
            
            # Try to open file to check if it's not locked
            with open(file_path, 'rb') as f:
                f.read(1)
            
            return True
        except (OSError, IOError, PermissionError):
            return False
    
    async def wait_for_file_stability(self, file_path: Path, timeout: int = 30) -> bool:
        """Wait for file to be stable (not being written to)"""
        try:
            initial_size = file_path.stat().st_size
            
            # If file is empty, don't wait for stability
            if initial_size == 0:
                return False
            
            for _ in range(timeout):
                await asyncio.sleep(1)
                try:
                    current_size = file_path.stat().st_size
                    
                    # File became empty during wait
                    if current_size == 0:
                        logger.warning(f"File became empty during stability check: {file_path.name}")
                        return False
                    
                    # File size is stable and accessible
                    if current_size == initial_size and self.is_file_accessible(file_path):
                        return True
                    
                    initial_size = current_size
                except OSError:
                    continue
            
            # Final check after timeout
            return self.is_file_accessible(file_path)
            
        except OSError:
            return False
    
    def get_file_stats(self) -> dict:
        """Get statistics about files in downloads directory"""
        if not self.downloads_dir.exists():
            return {'total_files': 0, 'empty_files': 0, 'valid_files': 0, 'total_size_mb': 0}
        
        total_files = 0
        empty_files = 0
        valid_files = 0
        total_size = 0
        
        try:
            for file_path in self.downloads_dir.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.supported_extensions and
                    not file_path.name.startswith('.')):
                    
                    total_files += 1
                    try:
                        file_size = file_path.stat().st_size
                        if file_size == 0:
                            empty_files += 1
                        else:
                            valid_files += 1
                            total_size += file_size
                    except OSError:
                        continue
        
        except Exception as e:
            logger.error(f"Error getting file stats: {e}")
        
        return {
            'total_files': total_files,
            'empty_files': empty_files,
            'valid_files': valid_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def cleanup_empty_files(self, delete: bool = False) -> int:
        """Find and optionally delete empty files"""
        empty_files = []
        
        if not self.downloads_dir.exists():
            return 0
        
        try:
            for file_path in self.downloads_dir.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.supported_extensions and
                    not file_path.name.startswith('.')):
                    
                    try:
                        if file_path.stat().st_size == 0:
                            empty_files.append(file_path)
                            if delete:
                                file_path.unlink()
                                logger.info(f"Deleted empty file: {file_path.name}")
                    except OSError as e:
                        logger.warning(f"Cannot process file {file_path.name}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error during empty files cleanup: {e}")
        
        if not delete and empty_files:
            logger.info(f"Found {len(empty_files)} empty files (use delete=True to remove them)")
        
        return len(empty_files)
