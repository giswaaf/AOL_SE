"""
File security utilities for validating and sanitizing uploaded files.
Provides comprehensive validation including magic number verification,
filename sanitization, metadata stripping, and security checks.
"""

import os
import re
import hashlib
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

# Try to import magic, fallback gracefully if not available
try:
    import magic
    MAGIC_AVAILABLE = True
    logger.info("python-magic library loaded successfully")
except ImportError as e:
    MAGIC_AVAILABLE = False
    logger.warning(f"python-magic not available: {e}. Using fallback file type detection.")

# Magic number signatures for allowed file types
ALLOWED_MAGIC_NUMBERS = {
    # JPEG
    b'\xff\xd8\xff': 'image/jpeg',
    # PNG
    b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': 'image/png',
    # WebP
    b'RIFF': 'image/webp',  # WebP files start with RIFF, need additional check
}

# Allowed MIME types and extensions
ALLOWED_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp']
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSIONS = (4096, 4096)  # 4K resolution max

# Dangerous filename patterns
DANGEROUS_PATTERNS = [
    r'\.\./',  # Path traversal
    r'\.\.\\',  # Windows path traversal
    r'[<>:"|?*]',  # Windows reserved characters
    r'[\x00-\x1f]',  # Control characters
    r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
]


class FileSecurityValidator:
    """Comprehensive file security validator for uploaded files."""
    
    def __init__(self):
        if MAGIC_AVAILABLE:
            try:
                self.magic_detector = magic.Magic(mime=True)
                logger.info("Magic detector initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize magic detector: {e}")
                self.magic_detector = None
        else:
            self.magic_detector = None
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in filename: {filename}")
                # Generate safe filename based on hash
                safe_name = hashlib.md5(filename.encode()).hexdigest()[:8]
                extension = self._extract_safe_extension(filename)
                return f"file_{safe_name}{extension}"
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Ensure filename isn't too long
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        # Ensure filename isn't empty after sanitization
        if not filename or filename == '.':
            return "unnamed_file.bin"
        
        return filename
    
    def _extract_safe_extension(self, filename: str) -> str:
        """Extract and validate file extension."""
        _, ext = os.path.splitext(filename.lower())
        
        # Check if extension is in allowed list
        for mime_type, extensions in ALLOWED_MIME_TYPES.items():
            if ext in extensions:
                return ext
        
        return '.bin'  # Default safe extension
    
    def validate_magic_number(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate file content using magic numbers (file signatures).
        
        Args:
            file_content: Raw file bytes
            
        Returns:
            Tuple of (is_valid, detected_mime_type)
        """
        if len(file_content) < 8:
            return False, None
        
        # Check magic numbers
        for magic_bytes, mime_type in ALLOWED_MAGIC_NUMBERS.items():
            if file_content.startswith(magic_bytes):
                # Special handling for WebP
                if mime_type == 'image/webp':
                    # WebP files have 'WEBP' at bytes 8-11
                    if len(file_content) >= 12 and file_content[8:12] == b'WEBP':
                        return True, mime_type
                else:
                    return True, mime_type
        
        # Fallback to python-magic for more comprehensive detection
        if MAGIC_AVAILABLE and self.magic_detector:
            try:
                detected_mime = self.magic_detector.from_buffer(file_content)
                if detected_mime in ALLOWED_MIME_TYPES:
                    return True, detected_mime
            except Exception as e:
                logger.warning(f"Magic number detection failed: {e}")
        
        return False, None
    
    def validate_image_properties(self, file_content: bytes) -> Dict[str, Any]:
        """
        Validate image properties and extract metadata.
        
        Args:
            file_content: Raw image bytes
            
        Returns:
            Dictionary with validation results and metadata
        """
        try:
            from io import BytesIO
            image = Image.open(BytesIO(file_content))
            
            # Check image dimensions
            width, height = image.size
            if width > MAX_IMAGE_DIMENSIONS[0] or height > MAX_IMAGE_DIMENSIONS[1]:
                return {
                    'valid': False,
                    'error': f'Image dimensions too large: {width}x{height}. Max: {MAX_IMAGE_DIMENSIONS[0]}x{MAX_IMAGE_DIMENSIONS[1]}'
                }
            
            # Check for suspicious properties
            if width < 10 or height < 10:
                return {
                    'valid': False,
                    'error': 'Image dimensions too small (minimum 10x10 pixels)'
                }
            
            # Extract EXIF data for logging (will be stripped later)
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)[:100]  # Limit value length
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': image.format,
                'mode': image.mode,
                'exif_tags': list(exif_data.keys()) if exif_data else [],
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid image file: {str(e)}'
            }
    
    def strip_metadata(self, file_content: bytes, mime_type: str) -> bytes:
        """
        Strip metadata from image files.
        
        Args:
            file_content: Raw image bytes
            mime_type: MIME type of the image
            
        Returns:
            Image bytes with metadata stripped
        """
        try:
            from io import BytesIO
            
            # Open image
            image = Image.open(BytesIO(file_content))
            
            # Create new image without EXIF data
            if image.mode in ('RGBA', 'LA'):
                # Preserve transparency
                clean_image = Image.new(image.mode, image.size)
                clean_image.paste(image, (0, 0))
            else:
                # Convert to RGB to ensure compatibility
                clean_image = image.convert('RGB')
            
            # Save without metadata
            output = BytesIO()
            format_map = {
                'image/jpeg': 'JPEG',
                'image/png': 'PNG',
                'image/webp': 'WEBP'
            }
            
            save_format = format_map.get(mime_type, 'JPEG')
            
            # Save with optimization and no metadata
            if save_format == 'JPEG':
                clean_image.save(output, format=save_format, quality=85, optimize=True)
            elif save_format == 'PNG':
                clean_image.save(output, format=save_format, optimize=True)
            else:  # WebP
                clean_image.save(output, format=save_format, quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to strip metadata: {e}")
            # Return original content if stripping fails
            return file_content
    
    async def validate_upload_file(
        self, 
        file: UploadFile, 
        max_size: int = MAX_FILE_SIZE,
        strip_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of uploaded file.
        
        Args:
            file: FastAPI UploadFile object
            max_size: Maximum allowed file size in bytes
            strip_metadata: Whether to strip metadata from images
            
        Returns:
            Dictionary with validation results and processed file data
        """
        # Read file content
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        # Basic size check
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {max_size // 1024 // 1024}MB"
            )
        
        # Sanitize filename
        safe_filename = self.sanitize_filename(file.filename or "unnamed")
        
        # Validate magic number
        is_valid_magic, detected_mime = self.validate_magic_number(file_content)
        if not is_valid_magic:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
            )
        
        # Verify MIME type matches content type header
        if file.content_type and file.content_type != detected_mime:
            logger.warning(
                f"MIME type mismatch: header={file.content_type}, detected={detected_mime}"
            )
            # Use detected MIME type for security
        
        # Validate image properties
        image_validation = self.validate_image_properties(file_content)
        if not image_validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=image_validation['error']
            )
        
        # Strip metadata if requested
        processed_content = file_content
        if strip_metadata and detected_mime.startswith('image/'):
            processed_content = self.strip_metadata(file_content, detected_mime)
            logger.info(f"Stripped metadata from {safe_filename}")
        
        # Generate file hash for integrity
        file_hash = hashlib.sha256(processed_content).hexdigest()
        
        return {
            'valid': True,
            'filename': safe_filename,
            'original_filename': file.filename,
            'content': processed_content,
            'size': len(processed_content),
            'mime_type': detected_mime,
            'hash': file_hash,
            'image_properties': image_validation
        }


# Global validator instance
file_validator = FileSecurityValidator()