"""
PDF Validator Module

This module validates PDF files to determine if they can be processed
for transaction extraction. It performs various checks without extracting
any data.
"""

import os
import logging
from typing import Optional, Tuple
import pypdf

from .validation_result import ValidationResult, PDFType
from .error_codes import ErrorCode, get_error_message

logger = logging.getLogger(__name__)


class PDFValidator:
    """
    Validates PDF files for processing compatibility.

    This validator performs sequential checks to determine if a PDF
    can be processed, providing clear feedback on any issues found.
    """

    # Hard limits as per plan
    MAX_PAGES = 200
    MAX_FILE_SIZE_MB = 25
    MIN_TEXT_LENGTH = 100

    def validate(self, pdf_path: str, password: Optional[str] = None) -> ValidationResult:
        """
        Validate a PDF file for processing compatibility.

        Args:
            pdf_path: Absolute path to the PDF file
            password: Optional password for encrypted PDFs

        Returns:
            ValidationResult containing validation status and details
        """
        logger.info(f"Starting PDF validation for: {pdf_path}")

        try:
            # Step 1: File integrity check
            if not self._is_valid_pdf_file(pdf_path):
                return self._create_error_result(
                    ErrorCode.NOT_PDF,
                    PDFType.INVALID
                )

            # Step 2: File size check
            file_size_mb = self._get_file_size_mb(pdf_path)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                return self._create_error_result(
                    ErrorCode.FILE_TOO_LARGE,
                    PDFType.INVALID,
                    metadata={"file_size_mb": file_size_mb},
                    file_size_mb=file_size_mb
                )

            # Step 3: PDF structure validation and content analysis
            return self._validate_pdf_content(pdf_path, password, file_size_mb)

        except Exception as e:
            logger.error(f"Unexpected error during PDF validation: {e}", exc_info=True)
            return self._create_error_result(
                ErrorCode.CORRUPTED,
                PDFType.INVALID,
                metadata={"validation_error": str(e)}
            )

    def _is_valid_pdf_file(self, pdf_path: str) -> bool:
        """Check if file is actually a PDF using magic bytes."""
        try:
            # Check if file exists
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file does not exist: {pdf_path}")
                return False

            # Check magic bytes
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                is_pdf = header == b'%PDF'

            logger.debug(f"Magic bytes check: {'PASS' if is_pdf else 'FAIL'}")
            return is_pdf

        except Exception as e:
            logger.error(f"Error checking PDF magic bytes: {e}")
            return False

    def _get_file_size_mb(self, pdf_path: str) -> float:
        """Get file size in MB."""
        try:
            size_bytes = os.path.getsize(pdf_path)
            size_mb = size_bytes / (1024 * 1024)
            logger.debug(f"File size: {size_mb:.2f}MB")
            return size_mb
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0.0

    def _validate_pdf_content(self, pdf_path: str, password: Optional[str], file_size_mb: float) -> ValidationResult:
        """Validate PDF structure and content."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)

                # Handle encryption
                if pdf_reader.is_encrypted:
                    if not password:
                        return self._create_error_result(
                            ErrorCode.ENCRYPTED_NO_PASSWORD,
                            PDFType.INVALID,
                            metadata={"encryption": True}
                        )

                    # Try to decrypt
                    decrypt_result = pdf_reader.decrypt(password)
                    if decrypt_result == 0:
                        # Try trimmed password (common issue)
                        trimmed_password = password.strip()
                        if trimmed_password != password:
                            decrypt_result = pdf_reader.decrypt(trimmed_password)

                        if decrypt_result == 0:
                            return self._create_error_result(
                                ErrorCode.WRONG_PASSWORD,
                                PDFType.INVALID,
                                metadata={"encryption": True}
                            )

                # Check page count
                page_count = len(pdf_reader.pages)
                logger.debug(f"Page count: {page_count}")

                if page_count == 0:
                    return self._create_error_result(
                        ErrorCode.EMPTY_PDF,
                        PDFType.INVALID,
                        metadata={"page_count": 0}
                    )

                if page_count > self.MAX_PAGES:
                    return self._create_error_result(
                        ErrorCode.TOO_MANY_PAGES,
                        PDFType.INVALID,
                        metadata={"page_count": page_count},
                        page_count=page_count
                    )

                # Analyze content type
                pdf_type, text_length = self._analyze_pdf_content(pdf_reader)
                logger.debug(f"PDF type: {pdf_type}, text length: {text_length}")

                # Create metadata
                metadata = {
                    "page_count": page_count,
                    "file_size_mb": file_size_mb,
                    "text_length": text_length,
                    "has_encryption": pdf_reader.is_encrypted
                }

                # Extract additional metadata if available
                if pdf_reader.metadata:
                    pdf_metadata = self._extract_pdf_metadata(pdf_reader)
                    metadata.update(pdf_metadata)

                # Check if scanned PDF (not supported yet)
                if pdf_type == PDFType.SCANNED:
                    return self._create_error_result(
                        ErrorCode.NO_TEXT_CONTENT,
                        PDFType.SCANNED,
                        metadata=metadata,
                        confidence_score=0.3
                    )

                # All validations passed
                return ValidationResult(
                    is_valid=True,
                    pdf_type=pdf_type,
                    error_code=ErrorCode.VALID,
                    error_message=get_error_message(ErrorCode.VALID),
                    metadata=metadata,
                    confidence_score=1.0
                )

        except Exception as e:
            logger.error(f"Error validating PDF structure: {e}", exc_info=True)
            return self._create_error_result(
                ErrorCode.CORRUPTED,
                PDFType.INVALID,
                metadata={"structure_error": str(e)}
            )

    def _analyze_pdf_content(self, pdf_reader) -> Tuple[PDFType, int]:
        """
        Analyze if PDF is text-based or scanned.

        Returns:
            Tuple of (PDFType, text_length)
        """
        total_text = ""
        has_images = False

        # Sample first 5 pages or all pages if less
        pages_to_check = min(5, len(pdf_reader.pages))
        logger.debug(f"Analyzing content of {pages_to_check} pages")

        try:
            for i in range(pages_to_check):
                page = pdf_reader.pages[i]

                # Extract text
                text = page.extract_text() or ""
                total_text += text

                # Check for images (indicates possible scan)
                if not has_images:
                    try:
                        if '/Resources' in page and '/XObject' in page['/Resources']:
                            xobjects = page['/Resources']['/XObject']
                            for obj_name in xobjects:
                                xobject = xobjects[obj_name]
                                if hasattr(xobject, 'get') and xobject.get('/Subtype') == '/Image':
                                    has_images = True
                                    break
                    except Exception as e:
                        logger.debug(f"Error checking for images in page {i}: {e}")

        except Exception as e:
            logger.warning(f"Error analyzing PDF content: {e}")
            # If we can't analyze content, assume it might be problematic
            return PDFType.INVALID, 0

        text_length = len(total_text.strip())

        # Classification logic
        if text_length < self.MIN_TEXT_LENGTH:
            if has_images:
                return PDFType.SCANNED, text_length
            else:
                return PDFType.INVALID, text_length
        elif has_images and text_length >= self.MIN_TEXT_LENGTH:
            return PDFType.HYBRID, text_length
        else:
            return PDFType.TEXT_BASED, text_length

    def _extract_pdf_metadata(self, pdf_reader) -> dict:
        """Extract PDF metadata safely."""
        metadata = {}

        try:
            if pdf_reader.metadata:
                # Safely extract metadata fields
                for key, field_name in [
                    ('/Title', 'title'),
                    ('/Author', 'author'),
                    ('/Subject', 'subject'),
                    ('/Creator', 'creator'),
                    ('/Producer', 'producer')
                ]:
                    value = pdf_reader.metadata.get(key)
                    if value:
                        metadata[field_name] = str(value)

                # Handle dates carefully
                for key, field_name in [
                    ('/CreationDate', 'creation_date'),
                    ('/ModDate', 'modification_date')
                ]:
                    value = pdf_reader.metadata.get(key)
                    if value:
                        metadata[field_name] = str(value)

        except Exception as e:
            logger.debug(f"Error extracting PDF metadata: {e}")

        return metadata

    def _create_error_result(
        self,
        error_code: ErrorCode,
        pdf_type: PDFType,
        metadata: dict = None,
        confidence_score: float = 0.0,
        **kwargs
    ) -> ValidationResult:
        """Create a validation error result."""
        return ValidationResult(
            is_valid=False,
            pdf_type=pdf_type,
            error_code=error_code,
            error_message=get_error_message(error_code, **kwargs),
            metadata=metadata or {},
            confidence_score=confidence_score
        )