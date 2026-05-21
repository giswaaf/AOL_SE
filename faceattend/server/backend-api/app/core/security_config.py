"""
Security configuration for file uploads and other security-sensitive operations.
Centralizes security settings and provides validation utilities.
"""

import os
from typing import Dict, List, Any
from pydantic import BaseModel, Field

class FileUploadSecurityConfig(BaseModel):
    """Configuration for file upload security settings."""
    
    # File size limits (in bytes)
    max_file_size: int = Field(default=5 * 1024 * 1024, description="Maximum file size in bytes")
    max_image_dimensions: tuple = Field(default=(4096, 4096), description="Maximum image dimensions (width, height)")
    
    # Allowed file types
    allowed_mime_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="Allowed MIME types for uploads"
    )
    
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".webp"],
        description="Allowed file extensions"
    )
    
    # Security features
    strip_metadata: bool = Field(default=True, description="Strip EXIF and other metadata from images")
    validate_magic_numbers: bool = Field(default=True, description="Validate file signatures/magic numbers")
    sanitize_filenames: bool = Field(default=True, description="Sanitize uploaded filenames")
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting for uploads")
    
    # Cloudinary security settings
    cloudinary_quality: str = Field(default="auto:good", description="Cloudinary quality setting")
    cloudinary_fetch_format: str = Field(default="auto", description="Cloudinary format optimization")
    cloudinary_invalidate_cache: bool = Field(default=True, description="Invalidate CDN cache on upload")


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting settings."""
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    redis_enabled: bool = Field(default=True, description="Enable Redis for rate limiting")
    
    # Rate limit windows and thresholds
    file_upload_limit: int = Field(default=10, description="File uploads per hour per user")
    avatar_upload_limit: int = Field(default=5, description="Avatar uploads per hour per user")
    face_image_upload_limit: int = Field(default=20, description="Face image uploads per hour per user")
    
    # Time windows (in seconds)
    upload_window: int = Field(default=3600, description="Rate limit window in seconds (1 hour)")
    
    # Memory fallback settings
    memory_cleanup_interval: int = Field(default=3600, description="Memory store cleanup interval in seconds")


class SecurityConfig(BaseModel):
    """Main security configuration."""
    
    # File upload security
    file_upload: FileUploadSecurityConfig = Field(default_factory=FileUploadSecurityConfig)
    
    # Rate limiting
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    
    # Audit logging
    audit_logging_enabled: bool = Field(default=True, description="Enable audit logging for security events")
    log_file_hashes: bool = Field(default=True, description="Log file hashes for integrity tracking")
    
    # Additional security headers
    security_headers_enabled: bool = Field(default=True, description="Enable security headers middleware")
    
    # Environment-specific overrides
    environment: str = Field(default="development", description="Current environment")
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


# Load configuration from environment variables
def load_security_config() -> SecurityConfig:
    """Load security configuration with environment variable overrides."""
    
    config_dict = {}
    
    # File upload overrides
    if os.getenv("MAX_FILE_SIZE"):
        config_dict.setdefault("file_upload", {})["max_file_size"] = int(os.getenv("MAX_FILE_SIZE"))
    
    if os.getenv("STRIP_METADATA"):
        config_dict.setdefault("file_upload", {})["strip_metadata"] = os.getenv("STRIP_METADATA").lower() == "true"
    
    # Rate limiting overrides
    if os.getenv("REDIS_URL"):
        config_dict.setdefault("rate_limiting", {})["redis_url"] = os.getenv("REDIS_URL")
    
    if os.getenv("RATE_LIMIT_ENABLED"):
        config_dict.setdefault("rate_limiting", {})["redis_enabled"] = os.getenv("RATE_LIMIT_ENABLED").lower() == "true"
    
    # Environment
    if os.getenv("ENVIRONMENT"):
        config_dict["environment"] = os.getenv("ENVIRONMENT")
    
    return SecurityConfig(**config_dict)


# Global security configuration instance
security_config = load_security_config()


# Security validation utilities
def validate_file_extension(filename: str) -> bool:
    """Validate file extension against allowed list."""
    if not filename:
        return False
    
    ext = os.path.splitext(filename.lower())[1]
    return ext in security_config.file_upload.allowed_extensions


def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type against allowed list."""
    return mime_type in security_config.file_upload.allowed_mime_types


def get_max_file_size() -> int:
    """Get maximum allowed file size."""
    return security_config.file_upload.max_file_size


def get_max_image_dimensions() -> tuple:
    """Get maximum allowed image dimensions."""
    return security_config.file_upload.max_image_dimensions


def is_security_feature_enabled(feature: str) -> bool:
    """Check if a security feature is enabled."""
    feature_map = {
        "strip_metadata": security_config.file_upload.strip_metadata,
        "validate_magic_numbers": security_config.file_upload.validate_magic_numbers,
        "sanitize_filenames": security_config.file_upload.sanitize_filenames,
        "rate_limiting": security_config.rate_limiting.redis_enabled,
        "audit_logging": security_config.audit_logging_enabled,
        "security_headers": security_config.security_headers_enabled,
    }
    
    return feature_map.get(feature, False)


# Security event logging
def log_security_event(event_type: str, user_id: str, details: Dict[str, Any], level: str = "INFO"):
    """Log security-related events for audit purposes."""
    import logging
    
    if not security_config.audit_logging_enabled:
        return
    
    logger = logging.getLogger("security_audit")
    
    log_entry = {
        "event_type": event_type,
        "user_id": user_id,
        "timestamp": os.environ.get("REQUEST_TIMESTAMP", "unknown"),
        "environment": security_config.environment,
        **details
    }
    
    if level.upper() == "WARNING":
        logger.warning(f"Security Event: {log_entry}")
    elif level.upper() == "ERROR":
        logger.error(f"Security Event: {log_entry}")
    else:
        logger.info(f"Security Event: {log_entry}")


# Export commonly used values
MAX_FILE_SIZE = security_config.file_upload.max_file_size
MAX_IMAGE_DIMENSIONS = security_config.file_upload.max_image_dimensions
ALLOWED_MIME_TYPES = security_config.file_upload.allowed_mime_types
ALLOWED_EXTENSIONS = security_config.file_upload.allowed_extensions