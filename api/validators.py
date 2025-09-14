#!/usr/bin/env python3
"""
File validation and security checks for Lambda
"""

import magic
import hashlib
import re
from typing import Optional, List
from fastapi import HTTPException, UploadFile
from config import settings
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    """File validation and security checks"""
    
    # Suspicious file patterns that might indicate malware
    SUSPICIOUS_PATTERNS = [
        rb'\x4d\x5a',  # MZ header (executable)
        rb'\x50\x4b\x03\x04',  # ZIP header (could contain malware)
        rb'<script',  # JavaScript
        rb'javascript:',  # JavaScript protocol
        rb'vbscript:',  # VBScript protocol
    ]
    
    # PDF magic numbers
    PDF_SIGNATURES = [
        b'%PDF-1.',  # Standard PDF signature
        b'\x25\x50\x44\x46\x2d',  # PDF signature in hex
    ]
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> None:
        """
        Validate file size against configured limits
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If file is too large
        """
        # Note: In Lambda, we need to be careful about memory usage
        # For very large files, consider streaming validation
        
        if hasattr(file, 'size') and file.size:
            if file.size > settings.max_file_size_bytes:
                logger.warning(f"File too large: {file.size} bytes (max: {settings.max_file_size_bytes})")
                raise HTTPException(
                    status_code=413,
                    detail=f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({settings.max_file_size_mb}MB)"
                )
    
    @staticmethod
    def validate_file_type(file: UploadFile) -> None:
        """
        Validate file type using multiple methods
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If file type is not allowed
        """
        # Check MIME type from upload
        if file.content_type not in settings.allowed_file_types:
            logger.warning(f"Invalid content type: {file.content_type}")
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(settings.allowed_file_types)}"
            )
        
        # Check file extension
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file extension: {file.filename}")
            raise HTTPException(
                status_code=415,
                detail="File must have .pdf extension"
            )
    
    @staticmethod
    async def validate_file_content(file: UploadFile) -> bytes:
        """
        Validate file content and return file bytes
        
        Args:
            file: Uploaded file
            
        Returns:
            File content as bytes
            
        Raises:
            HTTPException: If file content is invalid or suspicious
        """
        try:
            # Read file content
            content = await file.read()
            
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Empty file uploaded"
                )
            
            # Validate actual file size
            actual_size = len(content)
            if actual_size > settings.max_file_size_bytes:
                logger.warning(f"Actual file size too large: {actual_size} bytes")
                raise HTTPException(
                    status_code=413,
                    detail=f"File size ({actual_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({settings.max_file_size_mb}MB)"
                )
            
            # Check if file starts with PDF signature
            if not any(content.startswith(sig) for sig in FileValidator.PDF_SIGNATURES):
                logger.warning("File does not have valid PDF signature")
                raise HTTPException(
                    status_code=415,
                    detail="File does not appear to be a valid PDF"
                )
            
            # Basic malware detection - check for suspicious patterns
            FileValidator._check_suspicious_content(content)
            
            # Additional PDF structure validation
            FileValidator._validate_pdf_structure(content)
            
            logger.info(f"File validation successful: {file.filename}, size: {actual_size} bytes")
            return content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating file content: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error processing file"
            )
    
    @staticmethod
    def _check_suspicious_content(content: bytes) -> None:
        """
        Check for suspicious patterns in file content
        
        Args:
            content: File content as bytes
            
        Raises:
            HTTPException: If suspicious content is found
        """
        for pattern in FileValidator.SUSPICIOUS_PATTERNS:
            if pattern in content:
                logger.warning(f"Suspicious pattern found in file: {pattern}")
                raise HTTPException(
                    status_code=415,
                    detail="File contains suspicious content"
                )
    
    @staticmethod
    def _validate_pdf_structure(content: bytes) -> None:
        """
        Validate basic PDF structure
        
        Args:
            content: File content as bytes
            
        Raises:
            HTTPException: If PDF structure is invalid
        """
        content_str = content.decode('latin-1', errors='ignore')
        
        # Check for required PDF elements
        required_elements = ['%%EOF', 'xref', 'trailer']
        missing_elements = [elem for elem in required_elements if elem not in content_str]
        
        if missing_elements:
            logger.warning(f"PDF missing required elements: {missing_elements}")
            # Note: Some PDFs might not have all elements, so we log but don't fail
        
        # Check for extremely large object counts (potential zip bomb)
        obj_count = content_str.count(' obj')
        if obj_count > 10000:  # Arbitrary limit
            logger.warning(f"PDF has unusually high object count: {obj_count}")
            raise HTTPException(
                status_code=415,
                detail="PDF structure appears suspicious"
            )
    
    @staticmethod
    def get_file_hash(content: bytes) -> str:
        """
        Generate SHA-256 hash of file content
        
        Args:
            content: File content as bytes
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
            
        Raises:
            HTTPException: If filename is invalid
        """
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Remove path traversal attempts
        sanitized = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Only allow alphanumeric, dots, dashes, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+$', sanitized):
            logger.warning(f"Invalid filename characters: {filename}")
            raise HTTPException(
                status_code=400,
                detail="Filename contains invalid characters"
            )
        
        # Limit filename length
        if len(sanitized) > 255:
            logger.warning(f"Filename too long: {len(sanitized)} characters")
            raise HTTPException(
                status_code=400,
                detail="Filename too long (max 255 characters)"
            )
        
        return sanitized

async def validate_uploaded_file(file: UploadFile) -> tuple[bytes, str]:
    """
    Complete file validation pipeline
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (file_content, file_hash)
        
    Raises:
        HTTPException: If any validation fails
    """
    # Validate file size (if available)
    FileValidator.validate_file_size(file)
    
    # Validate file type
    FileValidator.validate_file_type(file)
    
    # Validate and sanitize filename
    sanitized_filename = FileValidator.validate_filename(file.filename or "unknown.pdf")
    
    # Validate file content
    content = await FileValidator.validate_file_content(file)
    
    # Generate file hash for logging/tracking
    file_hash = FileValidator.get_file_hash(content)
    
    logger.info(f"File validation complete - Name: {sanitized_filename}, Hash: {file_hash[:16]}..., Size: {len(content)} bytes")
    
    return content, file_hash